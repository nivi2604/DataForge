from datetime import datetime, timezone
from uuid import uuid4

from app.db.session import SessionLocal
from app.models.workspace import Workspace


class WorkspaceRepository:
    """SQLAlchemy-backed workspace repository."""

    def list_workspaces(self) -> list[Workspace]:
        with SessionLocal() as session:
            return list(session.query(Workspace).all())

    def get_workspace(self, workspace_id: str) -> Workspace | None:
        with SessionLocal() as session:
            return session.get(Workspace, workspace_id)

    def get_workspace_by_id(self, workspace_id: str) -> Workspace | None:
        return self.get_workspace(workspace_id)

    def get_workspaces_by_organization(self, organization_id: str) -> list[Workspace]:
        with SessionLocal() as session:
            return list(session.query(Workspace).filter(Workspace.organization_id == organization_id).all())

    def create_workspace(self, workspace: Workspace) -> Workspace:
        if not workspace.id:
            workspace.id = str(uuid4())
        if not workspace.created_at:
            workspace.created_at = datetime.now(timezone.utc).isoformat()
        with SessionLocal() as session:
            session.add(workspace)
            session.commit()
            session.refresh(workspace)
            return workspace

    def update_workspace(self, workspace_id: str, workspace: Workspace) -> Workspace:
        with SessionLocal() as session:
            existing_workspace = session.get(Workspace, workspace_id)
            if not existing_workspace:
                raise KeyError(workspace_id)

            for field in ["organization_id", "name", "description"]:
                value = getattr(workspace, field, None)
                if value is not None:
                    setattr(existing_workspace, field, value)

            session.commit()
            session.refresh(existing_workspace)
            return existing_workspace

    def delete_workspace(self, workspace_id: str) -> None:
        with SessionLocal() as session:
            workspace = session.get(Workspace, workspace_id)
            if not workspace:
                raise KeyError(workspace_id)
            session.delete(workspace)
            session.commit()
