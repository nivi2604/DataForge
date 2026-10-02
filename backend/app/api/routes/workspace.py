from fastapi import APIRouter, Header, Response, status

from app.api.routes.auth import auth_service
from app.core.security import get_current_user
from app.models.workspace import Workspace
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.services.workspace_service import WorkspaceService
from app.services.authorization_service import AuthorizationService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])
workspace_service = WorkspaceService()


def _require_authentication(authorization: str | None) -> User:
    return get_current_user(authorization, auth_service.user_repository)


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(
    organization_id: str | None = None,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> list[WorkspaceResponse]:
    user = _require_authentication(authorization)
    if organization_id:
        AuthorizationService.verify_organization_access(organization_id, user.id)
    workspaces = workspace_service.list_workspaces(organization_id=organization_id)
    workspaces = AuthorizationService.filter_workspaces(workspaces, user.id)
    return [
        WorkspaceResponse(
            id=workspace.id or "",
            organization_id=workspace.organization_id,
            name=workspace.name,
            description=workspace.description,
            created_at=workspace.created_at,
        )
        for workspace in workspaces
    ]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> WorkspaceResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_workspace_access(workspace_id, user.id)
    workspace = workspace_service.get_workspace(workspace_id)
    return WorkspaceResponse(
        id=workspace.id or "",
        organization_id=workspace.organization_id,
        name=workspace.name,
        description=workspace.description,
        created_at=workspace.created_at,
    )


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    payload: WorkspaceCreate,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> WorkspaceResponse:
    user = _require_authentication(authorization)
    if payload.organization_id:
        AuthorizationService.verify_organization_access(payload.organization_id, user.id)
    workspace = workspace_service.create_workspace(payload)
    return WorkspaceResponse(
        id=workspace.id or "",
        organization_id=workspace.organization_id,
        name=workspace.name,
        description=workspace.description,
        created_at=workspace.created_at,
    )


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
    workspace_id: str,
    payload: WorkspaceUpdate,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> WorkspaceResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_workspace_access(workspace_id, user.id)
    if payload.organization_id:
        AuthorizationService.verify_organization_access(payload.organization_id, user.id)
    workspace = workspace_service.update_workspace(workspace_id, payload)
    return WorkspaceResponse(
        id=workspace.id or "",
        organization_id=workspace.organization_id,
        name=workspace.name,
        description=workspace.description,
        created_at=workspace.created_at,
    )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> Response:
    user = _require_authentication(authorization)
    AuthorizationService.verify_workspace_access(workspace_id, user.id)
    workspace_service.delete_workspace(workspace_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
