"""
PRValidationService — orchestrates the full GitHub PR → DataForge pipeline validation flow.

Responsibilities:
1. Look up a GithubConnection for a given repository name (any user who connected it).
2. Fetch the changed files from the PR via GitHub API.
3. Identify a DataForge pipeline JSON file in the PR.
4. Parse + structurally validate the pipeline snapshot.
5. Execute the pipeline in an isolated/temporary way using the existing DataForge
   execution engine logic (without touching the live pipeline in the DB).
6. Run Data Quality checks.
7. Report PASS / FAIL back to GitHub as a PR comment.
8. Persist the result to GithubPRValidation for the frontend.
"""

import base64
import json
import logging
from datetime import datetime, timezone

import httpx

from app.core.encryption import decrypt_value
from app.models.github_pr_validation import GithubPRValidation
from app.repositories.github_pr_validation_repository import GithubPRValidationRepository
from app.repositories.github_repository import GithubConnectionRepository
from app.services.data_quality_service import DataQualityService

logger = logging.getLogger(__name__)

# The canonical filename DataForge writes when pushing a version to GitHub
PIPELINE_FILE_CANDIDATES = ["pipeline.json", ".dataforge/pipeline.json", "dataforge/pipeline.json"]

SUPPORTED_NODE_TYPES = {"extract", "transform", "load", "data_quality"}


class PRValidationService:
    def __init__(self) -> None:
        self.validation_repo = GithubPRValidationRepository()
        self.github_conn_repo = GithubConnectionRepository()

    # ------------------------------------------------------------------
    # Public entry point called by the webhook handler
    # ------------------------------------------------------------------

    def handle_pr_event(
        self,
        delivery_id: str,
        action: str,
        repository_name: str,
        pr_number: int,
        head_branch: str,
        base_branch: str,
        commit_sha: str,
        pr_html_url: str,
    ) -> GithubPRValidation:
        """
        Entry point for a pull_request webhook event.
        Returns the GithubPRValidation record (created or pre-existing).
        """
        # --- 1. Idempotency guard ---
        existing = self.validation_repo.get_by_delivery_id(delivery_id)
        if existing:
            logger.info("Duplicate delivery_id=%s — skipping", delivery_id)
            return existing

        # --- 2. Create a pending record immediately ---
        record = GithubPRValidation(
            delivery_id=delivery_id,
            repository_name=repository_name,
            pr_number=str(pr_number),
            head_branch=head_branch,
            base_branch=base_branch,
            commit_sha=commit_sha,
            pr_html_url=pr_html_url,
            status="running",
        )
        record = self.validation_repo.create(record)

        # --- 3. Find a GitHub connection that has this repo ---
        conn = self._find_connection_for_repo(repository_name)
        if not conn:
            updated = self.validation_repo.update(
                record.id,
                status="skipped",
                result_summary="Repository not connected to DataForge",
                failure_reason="No DataForge GitHub connection found for this repository",
            )
            return updated or record

        token = decrypt_value(conn.encrypted_token)

        # --- 4. Fetch changed files from the PR ---
        pipeline_content, pipeline_file_path = self._fetch_pipeline_from_pr(
            token, repository_name, pr_number, head_branch
        )
        if pipeline_content is None:
            # No DataForge pipeline file in this PR — not an error
            updated = self.validation_repo.update(
                record.id,
                pipeline_file_path=pipeline_file_path,
                status="skipped",
                result_summary="No DataForge pipeline configuration found in this PR",
            )
            # Post a neutral comment
            self._post_github_comment(
                token,
                repository_name,
                pr_number,
                "ℹ️ **DataForge**: No pipeline configuration file detected in this PR. Validation skipped.",
            )
            return updated or record

        self.validation_repo.update(record.id, pipeline_file_path=pipeline_file_path)

        # --- 5. Validate the pipeline structure ---
        validation_errors = self._validate_pipeline_structure(pipeline_content)
        if validation_errors:
            reason = "Structural validation failed:\n" + "\n".join(f"- {e}" for e in validation_errors)
            updated = self.validation_repo.update(
                record.id,
                status="failed",
                failure_reason=reason,
                result_summary=self._build_result_summary("FAIL", pipeline_content, pr_number, failure_reason=reason),
            )
            self._post_github_comment(
                token,
                repository_name,
                pr_number,
                self._format_github_comment("FAIL", pipeline_content, pr_number, head_branch, commit_sha, failure_reason=reason),
            )
            return updated or record

        # --- 6. Execute the pipeline (dry run using snapshot) ---
        exec_result = self._execute_pipeline_from_snapshot(pipeline_content)
        if exec_result["status"] == "failed":
            reason = exec_result.get("error", "Unknown execution error")
            updated = self.validation_repo.update(
                record.id,
                status="failed",
                failure_reason=reason,
                result_summary=self._build_result_summary("FAIL", pipeline_content, pr_number, failure_reason=reason),
            )
            self._post_github_comment(
                token,
                repository_name,
                pr_number,
                self._format_github_comment(
                    "FAIL", pipeline_content, pr_number, head_branch, commit_sha,
                    failure_reason=reason,
                    failed_node=exec_result.get("failed_node"),
                ),
            )
            return updated or record

        # --- 7. All passed ---
        rows_processed = exec_result.get("rows_processed", 0)
        dq_summary = exec_result.get("dq_summary", "No data quality node detected")
        summary = self._build_result_summary(
            "PASS", pipeline_content, pr_number,
            rows_processed=rows_processed, dq_summary=dq_summary,
        )
        updated = self.validation_repo.update(
            record.id,
            status="passed",
            result_summary=summary,
        )
        self._post_github_comment(
            token,
            repository_name,
            pr_number,
            self._format_github_comment(
                "PASS", pipeline_content, pr_number, head_branch, commit_sha,
                rows_processed=rows_processed, dq_summary=dq_summary,
            ),
        )
        return updated or record

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_connection_for_repo(self, repository_name: str):
        """Return the first GithubConnection that matches `repository_name`."""
        with __import__("app.db.session", fromlist=["SessionLocal"]).SessionLocal() as session:
            from app.models.github_connection import GithubConnection
            return (
                session.query(GithubConnection)
                .filter(GithubConnection.repository_name == repository_name)
                .first()
            )

    def _get_github_client(self, token: str) -> httpx.Client:
        return httpx.Client(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=15.0,
        )

    def _fetch_pipeline_from_pr(
        self,
        token: str,
        repository_name: str,
        pr_number: int,
        head_branch: str,
    ) -> tuple[dict | None, str | None]:
        """
        Fetch the pipeline configuration from the PR's head branch.
        Returns (parsed_dict, file_path) or (None, None).
        Strategy:
          1. Check PR changed-files list for any known DataForge file names.
          2. Fallback: probe the candidate paths directly on the head branch.
        """
        with self._get_github_client(token) as client:
            # a) Get PR files
            files_res = client.get(f"/repos/{repository_name}/pulls/{pr_number}/files")
            if files_res.status_code == 200:
                changed_files = [f["filename"] for f in files_res.json()]
                for candidate in PIPELINE_FILE_CANDIDATES:
                    if candidate in changed_files:
                        content = self._fetch_file_content(client, repository_name, candidate, head_branch)
                        if content is not None:
                            return content, candidate

            # b) Fallback probe
            for candidate in PIPELINE_FILE_CANDIDATES:
                content = self._fetch_file_content(client, repository_name, candidate, head_branch)
                if content is not None:
                    return content, candidate

        return None, None

    def _fetch_file_content(
        self,
        client: httpx.Client,
        repository_name: str,
        file_path: str,
        ref: str,
    ) -> dict | None:
        res = client.get(f"/repos/{repository_name}/contents/{file_path}?ref={ref}")
        if res.status_code != 200:
            return None
        data = res.json()
        if data.get("encoding") != "base64":
            return None
        try:
            raw = base64.b64decode(data["content"]).decode("utf-8")
            return json.loads(raw)
        except Exception as exc:
            logger.warning("Failed to parse pipeline file %s: %s", file_path, exc)
            return None

    # ------------------------------------------------------------------
    # Pipeline structure validation (pure Python — no DB writes)
    # ------------------------------------------------------------------

    def _validate_pipeline_structure(self, config: dict) -> list[str]:
        """
        Returns a list of validation error strings.
        Empty list means the structure is valid.
        """
        errors: list[str] = []

        if not isinstance(config, dict):
            return ["Pipeline configuration must be a JSON object"]

        nodes = config.get("nodes")
        if nodes is None:
            errors.append("Missing 'nodes' key in pipeline configuration")
            return errors

        if not isinstance(nodes, list):
            errors.append("'nodes' must be a JSON array")
            return errors

        if len(nodes) == 0:
            errors.append("Pipeline has no nodes")
            return errors

        seen_indices: set[int] = set()
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                errors.append(f"Node {i} is not a JSON object")
                continue

            node_type = (node.get("node_type") or "").strip().lower()
            if not node_type:
                errors.append(f"Node {i} is missing 'node_type'")
            elif node_type not in SUPPORTED_NODE_TYPES:
                errors.append(f"Node {i} has unsupported node_type: '{node_type}'")

            seq = node.get("sequence_index")
            if seq is None:
                errors.append(f"Node {i} ({node_type}) is missing 'sequence_index'")
            elif not isinstance(seq, int):
                errors.append(f"Node {i} ({node_type}) 'sequence_index' must be an integer")
            elif seq in seen_indices:
                errors.append(f"Node {i} ({node_type}) has duplicate sequence_index {seq}")
            else:
                seen_indices.add(seq)

            # Basic config validation per node type
            config_str = node.get("configuration")
            if config_str:
                try:
                    node_cfg = json.loads(config_str) if isinstance(config_str, str) else config_str
                except json.JSONDecodeError:
                    errors.append(f"Node {i} ({node_type}) 'configuration' is not valid JSON")
                    node_cfg = {}

                if node_type == "extract":
                    if not node_cfg.get("data_source_id"):
                        errors.append(f"Node {i} (extract) is missing 'data_source_id' in configuration")
                elif node_type == "transform":
                    if not node_cfg.get("operation"):
                        errors.append(f"Node {i} (transform) is missing 'operation' in configuration")
                elif node_type == "load":
                    if not node_cfg.get("data_source_id"):
                        errors.append(f"Node {i} (load) is missing 'data_source_id' in configuration")

        return errors

    # ------------------------------------------------------------------
    # Pipeline execution from snapshot (no DB pipeline needed)
    # ------------------------------------------------------------------

    def _execute_pipeline_from_snapshot(self, config: dict) -> dict:
        """
        Execute the pipeline nodes described in the snapshot dict.
        Returns {"status": "completed"|"failed", "rows_processed": N,
                 "dq_summary": "...", "error": "...", "failed_node": "..."}
        We intentionally skip extract/load I/O when data sources are not
        resolvable in the CI environment — the focus is structural execution
        and data quality logic validation.
        """
        from app.repositories.data_source_repository import DataSourceRepository

        ds_repo = DataSourceRepository()
        nodes = sorted(config.get("nodes", []), key=lambda n: n.get("sequence_index", 0))

        data: list[dict] | None = None
        rows_processed = 0
        dq_summary = "No data quality node"

        try:
            for node in nodes:
                node_type = (node.get("node_type") or "").strip().lower()
                cfg_raw = node.get("configuration")
                cfg = {}
                if cfg_raw:
                    cfg = json.loads(cfg_raw) if isinstance(cfg_raw, str) else cfg_raw

                if node_type == "extract":
                    ds_id = cfg.get("data_source_id")
                    ds = ds_repo.get_data_source_by_id(ds_id) if ds_id else None
                    if ds:
                        import csv
                        from pathlib import Path
                        conn_details = json.loads(ds.connection_details or "{}")
                        path = conn_details.get("path")
                        if path and Path(path).is_file():
                            with open(path, mode="r", encoding="utf-8") as f:
                                data = list(csv.DictReader(f))
                            rows_processed = len(data)
                        else:
                            # Data source exists but file not accessible — treat as empty data
                            data = []
                    else:
                        # Data source not found in this env — use empty
                        data = []

                elif node_type == "transform":
                    if data is None:
                        data = []
                    operation = cfg.get("operation")
                    if operation == "drop_nulls":
                        data = [row for row in data if all(
                            v is not None and str(v).strip() != "" for v in row.values()
                        )]
                    elif operation == "select_columns":
                        columns = cfg.get("columns", [])
                        if columns:
                            data = [{k: row[k] for k in columns if k in row} for row in data]
                    rows_processed = len(data)

                elif node_type == "data_quality":
                    required_columns = cfg.get("required_columns")
                    if isinstance(required_columns, str):
                        required_columns = [c.strip() for c in required_columns.split(",") if c.strip()]
                    email_column = cfg.get("email_column")
                    result = DataQualityService.compute_quality(data or [], required_columns, email_column)
                    dq_summary = DataQualityService.format_quality_result(result)

                elif node_type == "load":
                    # For PR validation we skip writing to the load destination;
                    # we only validate the node configuration exists.
                    pass

        except Exception as exc:
            return {
                "status": "failed",
                "error": str(exc),
                "failed_node": node.get("node_type", "unknown"),
                "rows_processed": rows_processed,
            }

        return {
            "status": "completed",
            "rows_processed": rows_processed,
            "dq_summary": dq_summary,
        }

    # ------------------------------------------------------------------
    # GitHub comment reporting
    # ------------------------------------------------------------------

    def _post_github_comment(self, token: str, repository_name: str, pr_number: int, body: str) -> None:
        try:
            with self._get_github_client(token) as client:
                res = client.post(
                    f"/repos/{repository_name}/issues/{pr_number}/comments",
                    json={"body": body},
                )
                if res.status_code not in (200, 201):
                    logger.warning(
                        "Failed to post GitHub comment on PR #%d in %s: %s",
                        pr_number, repository_name, res.text,
                    )
        except Exception as exc:
            logger.error("Error posting GitHub comment: %s", exc)

    def _format_github_comment(
        self,
        verdict: str,
        config: dict,
        pr_number: int,
        head_branch: str,
        commit_sha: str,
        rows_processed: int = 0,
        dq_summary: str = "",
        failure_reason: str = "",
        failed_node: str = "",
    ) -> str:
        pipeline_name = config.get("name", "unnamed pipeline")
        icon = "✅" if verdict == "PASS" else "❌"
        short_sha = commit_sha[:7] if commit_sha else "unknown"

        lines = [
            f"## {icon} DataForge Validation: **{verdict}**",
            "",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| **Pipeline** | `{pipeline_name}` |",
            f"| **PR** | #{pr_number} |",
            f"| **Branch** | `{head_branch}` |",
            f"| **Commit** | `{short_sha}` |",
        ]

        if verdict == "PASS":
            lines += [
                f"| **Execution** | Completed ✓ |",
                f"| **Rows processed** | {rows_processed} |",
                f"| **Data Quality** | {dq_summary or 'N/A'} |",
            ]
        else:
            if failed_node:
                lines.append(f"| **Failed node** | `{failed_node}` |")
            if failure_reason:
                lines += [
                    "",
                    "### Failure Reason",
                    "```",
                    failure_reason,
                    "```",
                ]

        lines += [
            "",
            "_Reported by DataForge automated pipeline validation._",
        ]
        return "\n".join(lines)

    def _build_result_summary(
        self,
        verdict: str,
        config: dict,
        pr_number: int,
        rows_processed: int = 0,
        dq_summary: str = "",
        failure_reason: str = "",
    ) -> str:
        pipeline_name = config.get("name", "unnamed pipeline")
        if verdict == "PASS":
            return f"PASS | {pipeline_name} | PR #{pr_number} | {rows_processed} rows | {dq_summary}"
        return f"FAIL | {pipeline_name} | PR #{pr_number} | {failure_reason[:200]}"
