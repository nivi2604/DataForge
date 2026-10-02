"""
GitHub webhook endpoint.

POST /github/webhook
  - Accepts GitHub pull_request events.
  - Verifies HMAC-SHA256 signature with GITHUB_WEBHOOK_SECRET.
  - Rejects invalid signatures (401).
  - Dispatches PR opened/synchronize/reopened to PRValidationService.
  - Idempotent: duplicate delivery IDs are safely ignored.
"""

import hashlib
import hmac
import json
import logging
import os

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.repositories.github_pr_validation_repository import GithubPRValidationRepository
from app.services.pr_validation_service import PRValidationService

logger = logging.getLogger(__name__)

webhook_router = APIRouter(prefix="/github", tags=["github-webhook"])

_pr_validation_service = PRValidationService()
_validation_repo = GithubPRValidationRepository()

# Actions that trigger a DataForge pipeline validation
_PR_VALIDATION_ACTIONS = {"opened", "synchronize", "reopened"}


def _get_webhook_secret() -> bytes | None:
    """Read webhook secret from environment at call time (allows test override)."""
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    return secret.encode() if secret else None


def _verify_signature(secret: bytes, payload: bytes, sig_header: str | None) -> bool:
    """
    Verify the GitHub webhook HMAC-SHA256 signature.
    Returns True when the signature matches, False otherwise.
    """
    if not sig_header or not sig_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig_header)


@webhook_router.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    x_github_event: str | None = Header(default=None, alias="X-GitHub-Event"),
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
    x_github_delivery: str | None = Header(default=None, alias="X-GitHub-Delivery"),
):
    """Receive and process GitHub webhook events."""
    payload_bytes = await request.body()

    # --- Signature verification ---
    secret = _get_webhook_secret()
    if secret:
        if not _verify_signature(secret, payload_bytes, x_hub_signature_256):
            logger.warning("Rejected webhook with invalid signature (delivery=%s)", x_github_delivery)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )
    else:
        logger.warning(
            "GITHUB_WEBHOOK_SECRET is not set — skipping signature verification. "
            "Set this environment variable in production."
        )

    # --- Parse event ---
    try:
        event_data = json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

    event_type = x_github_event or ""

    # --- Only handle pull_request events ---
    if event_type != "pull_request":
        logger.debug("Ignoring GitHub event type: %s", event_type)
        return {"status": "ignored", "reason": f"Unsupported event type: {event_type}"}

    action = event_data.get("action", "")
    if action not in _PR_VALIDATION_ACTIONS:
        logger.debug("Ignoring pull_request action: %s", action)
        return {"status": "ignored", "reason": f"No validation required for action: {action}"}

    # --- Extract PR fields ---
    pr = event_data.get("pull_request", {})
    repository = event_data.get("repository", {})
    repository_name = repository.get("full_name", "")
    pr_number = pr.get("number")
    head_branch = pr.get("head", {}).get("ref", "")
    base_branch = pr.get("base", {}).get("ref", "")
    commit_sha = pr.get("head", {}).get("sha", "")
    pr_html_url = pr.get("html_url", "")

    if not repository_name or not pr_number:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing repository or PR number in webhook payload",
        )

    delivery_id = x_github_delivery or f"{repository_name}#{pr_number}@{commit_sha}"
    logger.info(
        "Processing pull_request webhook: repo=%s pr=#%d action=%s delivery=%s",
        repository_name, pr_number, action, delivery_id,
    )

    # Dispatch to service (synchronous — acceptable for webhook processing)
    try:
        result = _pr_validation_service.handle_pr_event(
            delivery_id=delivery_id,
            action=action,
            repository_name=repository_name,
            pr_number=pr_number,
            head_branch=head_branch,
            base_branch=base_branch,
            commit_sha=commit_sha,
            pr_html_url=pr_html_url,
        )
        return {
            "status": "accepted",
            "validation_id": result.id if result else None,
            "validation_status": result.status if result else None,
        }
    except Exception as exc:
        logger.exception("Error processing webhook delivery %s: %s", delivery_id, exc)
        # Return 202 anyway — we don't want GitHub to retry on our internal errors
        return {"status": "error", "detail": str(exc)}


@webhook_router.get("/pr-validations", tags=["github-webhook"])
def list_pr_validations(repository_name: str | None = None, limit: int = 30):
    """List recent PR validation records (for the DataForge frontend)."""
    if repository_name:
        records = _validation_repo.list_for_repository(repository_name, limit=limit)
    else:
        records = _validation_repo.list_all(limit=limit)

    return [
        {
            "id": r.id,
            "repository_name": r.repository_name,
            "pr_number": r.pr_number,
            "head_branch": r.head_branch,
            "base_branch": r.base_branch,
            "commit_sha": r.commit_sha,
            "pr_html_url": r.pr_html_url,
            "pipeline_file_path": r.pipeline_file_path,
            "status": r.status,
            "result_summary": r.result_summary,
            "failure_reason": r.failure_reason,
            "execution_id": r.execution_id,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
        for r in records
    ]
