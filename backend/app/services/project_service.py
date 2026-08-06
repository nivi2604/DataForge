from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.models.project import Project
from app.models.workspace import Workspace
from app.repositories.project_repository import ProjectRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Project service with validation and CRUD orchestration."""

    def __init__(self) -> None:
        self.project_repository = ProjectRepository()
        self.workspace_repository = WorkspaceRepository()

    def list_projects(self, workspace_id: str | None = None) -> list[Project]:
        if workspace_id:
            return self.project_repository.get_projects_by_workspace(workspace_id)
        return self.project_repository.list_projects()

    def get_project(self, project_id: str) -> Project:
        project = self.project_repository.get_project_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    def create_project(self, payload: ProjectCreate) -> Project:
        name = (payload.name or "").strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project name is required")

        workspace_id = (payload.workspace_id or "").strip()
        if not workspace_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workspace ID is required")

        workspace = self.workspace_repository.get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        project = Project(
            workspace_id=workspace_id,
            name=name,
            description=payload.description,
            status=payload.status or "active",
        )
        return self.project_repository.create_project(project)

    def update_project(self, project_id: str, payload: ProjectUpdate) -> Project:
        existing_project = self.project_repository.get_project_by_id(project_id)
        if not existing_project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        if payload.name is not None:
            name = (payload.name or "").strip()
            if not name:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project name is required")

        if payload.workspace_id is not None:
            workspace_id = (payload.workspace_id or "").strip()
            if not workspace_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workspace ID is required")
            workspace = self.workspace_repository.get_workspace(workspace_id)
            if not workspace:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        project = Project(
            workspace_id=payload.workspace_id if payload.workspace_id is not None else existing_project.workspace_id,
            name=payload.name if payload.name is not None else existing_project.name,
            description=payload.description if payload.description is not None else existing_project.description,
            status=payload.status if payload.status is not None else existing_project.status,
        )
        return self.project_repository.update_project(project_id, project)

    def delete_project(self, project_id: str) -> None:
        project = self.project_repository.get_project_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        self.project_repository.delete_project(project_id)
