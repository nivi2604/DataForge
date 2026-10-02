from fastapi import APIRouter, Header, Response, status

from app.api.routes.auth import auth_service
from app.core.security import get_current_user
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService
from app.services.authorization_service import AuthorizationService

router = APIRouter(prefix="/projects", tags=["projects"])
project_service = ProjectService()


def _require_authentication(authorization: str | None) -> User:
    return get_current_user(authorization, auth_service.user_repository)


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    workspace_id: str | None = None,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> list[ProjectResponse]:
    user = _require_authentication(authorization)
    if workspace_id:
        AuthorizationService.verify_workspace_access(workspace_id, user.id)
    projects = project_service.list_projects(workspace_id=workspace_id)
    projects = AuthorizationService.filter_projects(projects, user.id)
    return [
        ProjectResponse(
            id=project.id or "",
            workspace_id=project.workspace_id,
            name=project.name,
            description=project.description,
            status=project.status,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        for project in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ProjectResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_project_access(project_id, user.id)
    project = project_service.get_project(project_id)
    return ProjectResponse(
        id=project.id or "",
        workspace_id=project.workspace_id,
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ProjectResponse:
    user = _require_authentication(authorization)
    if payload.workspace_id:
        AuthorizationService.verify_workspace_access(payload.workspace_id, user.id)
    project = project_service.create_project(payload)
    return ProjectResponse(
        id=project.id or "",
        workspace_id=project.workspace_id,
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ProjectResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_project_access(project_id, user.id)
    if payload.workspace_id:
        AuthorizationService.verify_workspace_access(payload.workspace_id, user.id)
    project = project_service.update_project(project_id, payload)
    return ProjectResponse(
        id=project.id or "",
        workspace_id=project.workspace_id,
        name=project.name,
        description=project.description,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> Response:
    user = _require_authentication(authorization)
    AuthorizationService.verify_project_access(project_id, user.id)
    project_service.delete_project(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
