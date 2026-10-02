from fastapi import APIRouter, Header, status, Response
from app.core.security import get_current_user
from app.api.routes.auth import auth_service
from app.schemas.github import (
    GithubConnectionCreate, GithubConnectionResponse, GithubBranch,
    GithubCommit, GithubPullRequest, GithubPullRequestCreate, GithubCommitCreate
)
from app.services.github_service import GithubService
from pydantic import BaseModel

router = APIRouter(prefix="/github", tags=["github"])
github_service = GithubService()

def _require_auth(authorization: str | None) -> str:
    user = get_current_user(authorization, auth_service.user_repository)
    return user.id

@router.post("/connections", response_model=GithubConnectionResponse, status_code=status.HTTP_201_CREATED)
def create_connection(
    payload: GithubConnectionCreate,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user_id = _require_auth(authorization)
    return github_service.create_connection(user_id, payload)

@router.get("/connections", response_model=list[GithubConnectionResponse])
def list_connections(authorization: str | None = Header(default=None, alias="Authorization")):
    user_id = _require_auth(authorization)
    return github_service.list_connections(user_id)

@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    connection_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user_id = _require_auth(authorization)
    github_service.delete_connection(user_id, connection_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/connections/{connection_id}/branches", response_model=list[GithubBranch])
def list_branches(
    connection_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user_id = _require_auth(authorization)
    return github_service.get_branches(user_id, connection_id)

class CreateBranchRequest(BaseModel):
    new_branch: str
    base_branch: str

@router.post("/connections/{connection_id}/branches", response_model=GithubBranch)
def create_branch(
    connection_id: str,
    payload: CreateBranchRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user_id = _require_auth(authorization)
    return github_service.create_branch(user_id, connection_id, payload.new_branch, payload.base_branch)

@router.post("/connections/{connection_id}/commits", response_model=GithubCommit)
def create_commit(
    connection_id: str,
    payload: GithubCommitCreate,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user_id = _require_auth(authorization)
    return github_service.create_commit(user_id, connection_id, payload)

@router.get("/connections/{connection_id}/pulls", response_model=list[GithubPullRequest])
def list_pull_requests(
    connection_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user_id = _require_auth(authorization)
    return github_service.list_pull_requests(user_id, connection_id)

@router.post("/connections/{connection_id}/pulls", response_model=GithubPullRequest)
def create_pull_request(
    connection_id: str,
    payload: GithubPullRequestCreate,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user_id = _require_auth(authorization)
    return github_service.create_pull_request(user_id, connection_id, payload)

@router.post("/connections/{connection_id}/pulls/{pr_number}/merge")
def merge_pull_request(
    connection_id: str,
    pr_number: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user_id = _require_auth(authorization)
    github_service.merge_pull_request(user_id, connection_id, pr_number)
    return {"success": True}

@router.post("/connections/{connection_id}/pulls/{pr_number}/close")
def close_pull_request(
    connection_id: str,
    pr_number: int,
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    user_id = _require_auth(authorization)
    github_service.close_pull_request(user_id, connection_id, pr_number)
    return {"success": True}
