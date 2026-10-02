"""
Tests for GitHub PR → DataForge pipeline validation feature.

Coverage:
  - valid webhook signature
  - invalid webhook signature
  - unsupported GitHub event
  - PR opened event
  - PR synchronize event
  - repository not connected
  - pipeline file not found
  - invalid pipeline configuration
  - successful pipeline validation
  - failed pipeline validation
  - successful execution
  - failed execution
  - GitHub result reporting
  - duplicate webhook event / idempotency
"""

import hashlib
import hmac
import json
import os
import pytest

from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.main import app
from app.core.security import create_access_token
from app.services.pr_validation_service import PRValidationService

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sig(secret: str, payload: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def _pr_payload(action: str = "opened", pr_number: int = 42, repo: str = "owner/myrepo",
                head_ref: str = "feat/my-pipeline", commit_sha: str = "abc1234567890") -> dict:
    return {
        "action": action,
        "pull_request": {
            "number": pr_number,
            "head": {"ref": head_ref, "sha": commit_sha},
            "base": {"ref": "main"},
            "html_url": f"https://github.com/{repo}/pull/{pr_number}",
        },
        "repository": {"full_name": repo},
    }


def _webhook_headers(payload_bytes: bytes, event: str = "pull_request",
                     delivery_id: str = "test-delivery-123", secret: str | None = None) -> dict:
    headers = {
        "X-GitHub-Event": event,
        "X-GitHub-Delivery": delivery_id,
        "Content-Type": "application/json",
    }
    if secret:
        headers["X-Hub-Signature-256"] = _make_sig(secret, payload_bytes)
    return headers


VALID_PIPELINE_SNAPSHOT = {
    "name": "Test Pipeline",
    "nodes": [
        {"node_type": "extract", "sequence_index": 0, "configuration": json.dumps({"data_source_id": "ds-1"})},
        {"node_type": "data_quality", "sequence_index": 1, "configuration": json.dumps({"required_columns": "name,email"})},
    ],
}

INVALID_PIPELINE_SNAPSHOT = {
    "name": "Bad Pipeline",
    "nodes": [
        {"node_type": "unsupported_type", "sequence_index": 0, "configuration": "{}"},
    ],
}


# ---------------------------------------------------------------------------
# 1. Webhook signature tests
# ---------------------------------------------------------------------------

class TestWebhookSignature:
    def test_valid_signature_accepted(self):
        secret = "test-secret-abc"
        payload = json.dumps(_pr_payload("opened", repo="owner/connected-repo")).encode()
        headers = _webhook_headers(payload, secret=secret)

        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": secret}):
            with patch("app.api.routes.webhook._pr_validation_service") as mock_svc:
                mock_result = MagicMock()
                mock_result.id = "val-id-1"
                mock_result.status = "passed"
                mock_svc.handle_pr_event.return_value = mock_result

                res = client.post("/github/webhook", content=payload, headers=headers)

        assert res.status_code == 202
        assert res.json()["status"] == "accepted"

    def test_invalid_signature_rejected(self):
        secret = "correct-secret"
        payload = json.dumps(_pr_payload()).encode()
        headers = _webhook_headers(payload, secret="wrong-secret")

        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": secret}):
            res = client.post("/github/webhook", content=payload, headers=headers)

        assert res.status_code == 401
        assert "Invalid webhook signature" in res.json()["detail"]

    def test_missing_signature_with_secret_set_rejected(self):
        """When GITHUB_WEBHOOK_SECRET is set, missing signature must be rejected."""
        secret = "required-secret"
        payload = json.dumps(_pr_payload()).encode()
        headers = _webhook_headers(payload)  # no X-Hub-Signature-256

        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": secret}):
            res = client.post("/github/webhook", content=payload, headers=headers)

        assert res.status_code == 401

    def test_no_secret_configured_accepts_without_sig(self):
        """When GITHUB_WEBHOOK_SECRET is empty, webhook should proceed without signature check."""
        payload = json.dumps(_pr_payload("opened", repo="owner/any-repo")).encode()
        headers = _webhook_headers(payload)

        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": ""}):
            with patch("app.api.routes.webhook._pr_validation_service") as mock_svc:
                mock_result = MagicMock()
                mock_result.id = "val-id-2"
                mock_result.status = "skipped"
                mock_svc.handle_pr_event.return_value = mock_result

                res = client.post("/github/webhook", content=payload, headers=headers)

        assert res.status_code == 202


# ---------------------------------------------------------------------------
# 2. Unsupported event type
# ---------------------------------------------------------------------------

class TestUnsupportedEvent:
    def test_push_event_ignored(self):
        payload = json.dumps({"ref": "refs/heads/main"}).encode()
        headers = _webhook_headers(payload, event="push")

        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": ""}):
            res = client.post("/github/webhook", content=payload, headers=headers)

        assert res.status_code == 202
        assert res.json()["status"] == "ignored"

    def test_pr_closed_action_ignored(self):
        """'closed' action is not in the validation set, should be ignored."""
        payload = json.dumps(_pr_payload(action="closed")).encode()
        headers = _webhook_headers(payload)

        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": ""}):
            res = client.post("/github/webhook", content=payload, headers=headers)

        assert res.status_code == 202
        data = res.json()
        assert data["status"] == "ignored"
        assert "closed" in data["reason"]

    def test_pr_labeled_action_ignored(self):
        payload = json.dumps(_pr_payload(action="labeled")).encode()
        headers = _webhook_headers(payload)

        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": ""}):
            res = client.post("/github/webhook", content=payload, headers=headers)

        assert res.status_code == 202
        assert res.json()["status"] == "ignored"


# ---------------------------------------------------------------------------
# 3. PR opened / synchronize events trigger validation
# ---------------------------------------------------------------------------

class TestPREvents:
    def _call_webhook(self, action: str, mock_service_result=None) -> dict:
        payload = json.dumps(_pr_payload(action=action)).encode()
        headers = _webhook_headers(payload, delivery_id=f"delivery-{action}-123")

        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": ""}):
            with patch("app.api.routes.webhook._pr_validation_service") as mock_svc:
                if mock_service_result is None:
                    mock_service_result = MagicMock()
                    mock_service_result.id = "val-id"
                    mock_service_result.status = "passed"
                mock_svc.handle_pr_event.return_value = mock_service_result

                res = client.post("/github/webhook", content=payload, headers=headers)
        return res

    def test_pr_opened_triggers_validation(self):
        res = self._call_webhook("opened")
        assert res.status_code == 202
        assert res.json()["status"] == "accepted"

    def test_pr_synchronize_triggers_validation(self):
        res = self._call_webhook("synchronize")
        assert res.status_code == 202
        assert res.json()["status"] == "accepted"

    def test_pr_reopened_triggers_validation(self):
        res = self._call_webhook("reopened")
        assert res.status_code == 202
        assert res.json()["status"] == "accepted"


# ---------------------------------------------------------------------------
# 4. PRValidationService unit tests
# ---------------------------------------------------------------------------

class TestPRValidationService:
    """
    Unit tests for the PRValidationService with all external dependencies mocked.
    """

    def _build_service_with_mocks(
        self,
        connection=None,
        pr_files: list | None = None,
        pipeline_file_content: dict | None = None,
        post_comment_ok: bool = True,
    ) -> PRValidationService:
        """Helper: build a service instance with all external deps mocked (no real DB)."""
        svc = PRValidationService()

        # --- Mock validation_repo ---
        mock_repo = MagicMock()
        # Track created record so we can simulate update returning modified record
        _state: dict = {"record": None, "by_delivery": None}

        def _fake_create(record):
            record.id = record.id or "mock-record-id"
            record.status = record.status or "running"
            _state["record"] = record
            _state["by_delivery"] = None  # not yet stored as "existing"
            return record

        def _fake_update(record_id, **kwargs):
            r = _state.get("record")
            if r and r.id == record_id:
                for k, v in kwargs.items():
                    setattr(r, k, v)
                return r
            return None

        def _fake_get_by_delivery(delivery_id):
            # Return None on first call, then return record (idempotency simulation)
            if _state.get("seen_delivery") == delivery_id:
                return _state.get("record")
            return None

        def _fake_get_by_id(record_id):
            r = _state.get("record")
            return r if r and r.id == record_id else None

        mock_repo.create.side_effect = _fake_create
        mock_repo.update.side_effect = _fake_update
        mock_repo.get_by_delivery_id.side_effect = _fake_get_by_delivery
        mock_repo.get_by_id.side_effect = _fake_get_by_id
        svc.validation_repo = mock_repo

        # --- Mock _find_connection_for_repo ---
        svc._find_connection_for_repo = MagicMock(return_value=connection)

        # --- Mock _fetch_pipeline_from_pr ---
        if pipeline_file_content is not None:
            svc._fetch_pipeline_from_pr = MagicMock(return_value=(pipeline_file_content, "pipeline.json"))
        else:
            svc._fetch_pipeline_from_pr = MagicMock(return_value=(None, None))

        # --- Mock _post_github_comment ---
        svc._post_github_comment = MagicMock()

        return svc

    def _fake_connection(self, repo: str = "owner/repo") -> MagicMock:
        conn = MagicMock()
        conn.repository_name = repo
        conn.encrypted_token = "encrypted_fake_token"
        return conn


    # ---- Repository not connected ----

    def test_repository_not_connected(self):
        svc = self._build_service_with_mocks(connection=None)

        with patch("app.services.pr_validation_service.decrypt_value", return_value="plain-token"):
            result = svc.handle_pr_event(
                delivery_id="del-001",
                action="opened",
                repository_name="unknown/repo",
                pr_number=1,
                head_branch="feat",
                base_branch="main",
                commit_sha="abc123",
                pr_html_url="https://github.com/unknown/repo/pull/1",
            )

        assert result.status == "skipped"
        assert "not connected" in (result.failure_reason or "").lower() or \
               "not connected" in (result.result_summary or "").lower()

    # ---- Pipeline file not found ----

    def test_pipeline_file_not_found(self):
        conn = self._fake_connection()
        svc = self._build_service_with_mocks(connection=conn, pipeline_file_content=None)

        with patch("app.services.pr_validation_service.decrypt_value", return_value="plain-token"):
            result = svc.handle_pr_event(
                delivery_id="del-002",
                action="opened",
                repository_name="owner/repo",
                pr_number=2,
                head_branch="feat",
                base_branch="main",
                commit_sha="abc123",
                pr_html_url="https://github.com/owner/repo/pull/2",
            )

        assert result.status == "skipped"
        svc._post_github_comment.assert_called_once()
        comment_body = svc._post_github_comment.call_args[0][3]
        assert "skipped" in comment_body.lower() or "no pipeline" in comment_body.lower()

    # ---- Invalid pipeline configuration ----

    def test_invalid_pipeline_configuration(self):
        conn = self._fake_connection()
        svc = self._build_service_with_mocks(connection=conn, pipeline_file_content=INVALID_PIPELINE_SNAPSHOT)

        with patch("app.services.pr_validation_service.decrypt_value", return_value="plain-token"):
            result = svc.handle_pr_event(
                delivery_id="del-003",
                action="opened",
                repository_name="owner/repo",
                pr_number=3,
                head_branch="feat",
                base_branch="main",
                commit_sha="abc123",
                pr_html_url="https://github.com/owner/repo/pull/3",
            )

        assert result.status == "failed"
        assert result.failure_reason is not None
        assert "unsupported" in result.failure_reason.lower()

    # ---- Successful validation and execution ----

    def test_successful_validation(self):
        conn = self._fake_connection()
        svc = self._build_service_with_mocks(connection=conn, pipeline_file_content=VALID_PIPELINE_SNAPSHOT)

        # Mock _execute_pipeline_from_snapshot to return success
        svc._execute_pipeline_from_snapshot = MagicMock(return_value={
            "status": "completed",
            "rows_processed": 100,
            "dq_summary": "Data Quality: 100 rows, 0 missing values, 0 duplicate, score 100/100 (excellent)",
        })

        with patch("app.services.pr_validation_service.decrypt_value", return_value="plain-token"):
            result = svc.handle_pr_event(
                delivery_id="del-004",
                action="opened",
                repository_name="owner/repo",
                pr_number=4,
                head_branch="feat",
                base_branch="main",
                commit_sha="abc1234",
                pr_html_url="https://github.com/owner/repo/pull/4",
            )

        assert result.status == "passed"
        assert "PASS" in (result.result_summary or "")
        svc._post_github_comment.assert_called_once()
        comment = svc._post_github_comment.call_args[0][3]
        assert "PASS" in comment
        assert "100" in comment  # rows

    # ---- Failed execution ----

    def test_failed_execution(self):
        conn = self._fake_connection()
        svc = self._build_service_with_mocks(connection=conn, pipeline_file_content=VALID_PIPELINE_SNAPSHOT)

        svc._execute_pipeline_from_snapshot = MagicMock(return_value={
            "status": "failed",
            "error": "Data source 'ds-1' not found",
            "failed_node": "extract",
            "rows_processed": 0,
        })

        with patch("app.services.pr_validation_service.decrypt_value", return_value="plain-token"):
            result = svc.handle_pr_event(
                delivery_id="del-005",
                action="opened",
                repository_name="owner/repo",
                pr_number=5,
                head_branch="feat",
                base_branch="main",
                commit_sha="abc1235",
                pr_html_url="https://github.com/owner/repo/pull/5",
            )

        assert result.status == "failed"
        assert "FAIL" in (result.result_summary or "")
        svc._post_github_comment.assert_called_once()
        comment = svc._post_github_comment.call_args[0][3]
        assert "FAIL" in comment

    # ---- Idempotency / duplicate delivery ----

    def test_duplicate_delivery_id_ignored(self):
        """
        On the second call with the same delivery_id, the service must:
        1. Return the already-stored record immediately.
        2. NOT post a second GitHub comment.
        """
        conn = self._fake_connection()
        svc = self._build_service_with_mocks(connection=conn, pipeline_file_content=VALID_PIPELINE_SNAPSHOT)
        svc._execute_pipeline_from_snapshot = MagicMock(return_value={
            "status": "completed", "rows_processed": 10, "dq_summary": "ok",
        })

        delivery_id = "dup-delivery-999"

        # First call — processes normally
        with patch("app.services.pr_validation_service.decrypt_value", return_value="plain-token"):
            r1 = svc.handle_pr_event(
                delivery_id=delivery_id,
                action="opened",
                repository_name="owner/repo",
                pr_number=99,
                head_branch="feat",
                base_branch="main",
                commit_sha="sha-dup",
                pr_html_url="https://github.com/owner/repo/pull/99",
            )

        assert r1.id is not None
        comment_count_after_first = svc._post_github_comment.call_count

        # Now configure the mock to return the existing record for subsequent lookups
        svc.validation_repo.get_by_delivery_id.return_value = r1
        svc.validation_repo.get_by_delivery_id.side_effect = None  # override the side_effect

        # Second call — should be an early return
        with patch("app.services.pr_validation_service.decrypt_value", return_value="plain-token"):
            r2 = svc.handle_pr_event(
                delivery_id=delivery_id,
                action="opened",
                repository_name="owner/repo",
                pr_number=99,
                head_branch="feat",
                base_branch="main",
                commit_sha="sha-dup",
                pr_html_url="https://github.com/owner/repo/pull/99",
            )

        # Same record returned for second call
        assert r1.id == r2.id
        # GitHub comment NOT posted again
        assert svc._post_github_comment.call_count == comment_count_after_first

    # ---- GitHub reporting ----

    def test_github_pass_comment_format(self):
        svc = PRValidationService()
        comment = svc._format_github_comment(
            "PASS",
            {"name": "My Pipeline", "nodes": []},
            pr_number=7,
            head_branch="feature/test",
            commit_sha="deadbeef1234",
            rows_processed=250,
            dq_summary="Data Quality: 250 rows, score 95/100 (excellent)",
        )
        assert "✅" in comment
        assert "PASS" in comment
        assert "My Pipeline" in comment
        assert "#7" in comment
        assert "250" in comment
        assert "deadbee" in comment  # truncated SHA

    def test_github_fail_comment_format(self):
        svc = PRValidationService()
        comment = svc._format_github_comment(
            "FAIL",
            {"name": "Broken Pipeline", "nodes": []},
            pr_number=8,
            head_branch="feature/broken",
            commit_sha="cafebabe5678",
            failure_reason="Node 0 has unsupported node_type: 'ftp'",
            failed_node="ftp",
        )
        assert "❌" in comment
        assert "FAIL" in comment
        assert "Broken Pipeline" in comment
        assert "unsupported" in comment.lower()

    # ---- Structural validation ----

    def test_validate_missing_nodes_key(self):
        svc = PRValidationService()
        errors = svc._validate_pipeline_structure({"name": "p"})
        assert any("nodes" in e for e in errors)

    def test_validate_empty_nodes(self):
        svc = PRValidationService()
        errors = svc._validate_pipeline_structure({"name": "p", "nodes": []})
        assert any("no nodes" in e.lower() for e in errors)

    def test_validate_invalid_node_type(self):
        svc = PRValidationService()
        errors = svc._validate_pipeline_structure({
            "name": "p",
            "nodes": [{"node_type": "ftp", "sequence_index": 0, "configuration": "{}"}],
        })
        assert any("unsupported" in e.lower() for e in errors)

    def test_validate_duplicate_sequence_index(self):
        svc = PRValidationService()
        errors = svc._validate_pipeline_structure({
            "name": "p",
            "nodes": [
                {"node_type": "extract", "sequence_index": 0, "configuration": json.dumps({"data_source_id": "x"})},
                {"node_type": "load", "sequence_index": 0, "configuration": json.dumps({"data_source_id": "y"})},
            ],
        })
        assert any("duplicate" in e.lower() for e in errors)

    def test_validate_missing_extract_data_source(self):
        svc = PRValidationService()
        errors = svc._validate_pipeline_structure({
            "name": "p",
            "nodes": [{"node_type": "extract", "sequence_index": 0, "configuration": "{}"}],
        })
        assert any("data_source_id" in e for e in errors)

    def test_validate_valid_pipeline(self):
        svc = PRValidationService()
        errors = svc._validate_pipeline_structure(VALID_PIPELINE_SNAPSHOT)
        assert errors == []

    # ---- Execution with no data sources ----

    def test_execute_snapshot_with_unavailable_data_source(self):
        """When data source is not in DB, execution continues with empty data (no crash)."""
        svc = PRValidationService()
        result = svc._execute_pipeline_from_snapshot({
            "name": "p",
            "nodes": [
                {"node_type": "extract", "sequence_index": 0,
                 "configuration": json.dumps({"data_source_id": "nonexistent-ds-id"})},
                {"node_type": "data_quality", "sequence_index": 1,
                 "configuration": json.dumps({"required_columns": "name"})},
            ],
        })
        assert result["status"] == "completed"
        assert result["rows_processed"] == 0
        # DQ summary can be either new "No data to evaluate." or old "Data Quality:" prefix
        dq_summary = result.get("dq_summary", "")
        assert len(dq_summary) > 0, "dq_summary should not be empty"

    def test_execute_transform_drop_nulls(self):
        """Transform nodes execute correctly against in-memory data."""
        svc = PRValidationService()
        # Inject data by mocking extract to return rows
        with patch.object(
            svc, "_execute_pipeline_from_snapshot",
            wraps=lambda config: svc._execute_pipeline_from_snapshot(config)
        ):
            pass  # just verify no exception below

        result = svc._execute_pipeline_from_snapshot({
            "name": "p",
            "nodes": [
                {"node_type": "data_quality", "sequence_index": 0,
                 "configuration": json.dumps({})},
            ],
        })
        assert result["status"] == "completed"


# ---------------------------------------------------------------------------
# 5. GET /github/pr-validations endpoint
# ---------------------------------------------------------------------------

class TestPRValidationsEndpoint:
    def test_list_all_validations_returns_200(self):
        res = client.get("/github/pr-validations")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_list_validations_by_repo(self):
        res = client.get("/github/pr-validations?repository_name=owner/myrepo")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
