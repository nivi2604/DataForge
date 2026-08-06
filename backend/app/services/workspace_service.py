from fastapi import HTTPException, status

from app.models.workspace import Workspace
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate


class WorkspaceService:
    """Workspace service with validation and CRUD orchestration."""

    def __init__(self) -> None:
        self.workspace_repository = WorkspaceRepository()
        self.organization_repository = OrganizationRepository()

    def list_workspaces(self, organization_id: str | None = None) -> list[Workspace]:
        if organization_id:
            return self.workspace_repository.get_workspaces_by_organization(organization_id)
        return self.workspace_repository.list_workspaces()

    def get_workspace(self, workspace_id: str) -> Workspace:
        workspace = self.workspace_repository.get_workspace_by_id(workspace_id)
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        return workspace

    def create_workspace(self, payload: WorkspaceCreate) -> Workspace:
        name = (payload.name or "").strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workspace name is required")

        organization_id = (payload.organization_id or "").strip()
        if not organization_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization ID is required")

        organization = self.organization_repository.get_organization(organization_id)
        if not organization:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        workspace = Workspace(
            organization_id=organization_id,
            name=name,
            description=payload.description,
        )
        return self.workspace_repository.create_workspace(workspace)

    def update_workspace(self, workspace_id: str, payload: WorkspaceUpdate) -> Workspace:
        existing_workspace = self.workspace_repository.get_workspace_by_id(workspace_id)
        if not existing_workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        if payload.name is not None:
            name = (payload.name or "").strip()
            if not name:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workspace name is required")

        if payload.organization_id is not None:
            organization_id = (payload.organization_id or "").strip()
            if not organization_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization ID is required")

            organization = self.organization_repository.get_organization(organization_id)
            if not organization:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        workspace = Workspace(
            organization_id=payload.organization_id if payload.organization_id is not None else existing_workspace.organization_id,
            name=payload.name if payload.name is not None else existing_workspace.name,
            description=payload.description if payload.description is not None else existing_workspace.description,
        )
        return self.workspace_repository.update_workspace(workspace_id, workspace)

    def delete_workspace(self, workspace_id: str) -> None:
        workspace = self.workspace_repository.get_workspace_by_id(workspace_id)
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        self.workspace_repository.delete_workspace(workspace_id)
