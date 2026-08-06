from datetime import datetime, timezone
from uuid import uuid4

from app.db.session import SessionLocal
from app.models.project import Project


class ProjectRepository:
    """SQLAlchemy-backed project repository."""

    def list_projects(self) -> list[Project]:
        with SessionLocal() as session:
            return list(session.query(Project).all())

    def get_project(self, project_id: str) -> Project | None:
        with SessionLocal() as session:
            return session.get(Project, project_id)

    def get_project_by_id(self, project_id: str) -> Project | None:
        return self.get_project(project_id)

    def get_projects_by_workspace(self, workspace_id: str) -> list[Project]:
        with SessionLocal() as session:
            return list(session.query(Project).filter(Project.workspace_id == workspace_id).all())

    def create_project(self, project: Project) -> Project:
        if not project.id:
            project.id = str(uuid4())
        if not project.created_at:
            project.created_at = datetime.now(timezone.utc).isoformat()
        if not project.updated_at:
            project.updated_at = project.created_at
        with SessionLocal() as session:
            session.add(project)
            session.commit()
            session.refresh(project)
            return project

    def update_project(self, project_id: str, project: Project) -> Project:
        with SessionLocal() as session:
            existing_project = session.get(Project, project_id)
            if not existing_project:
                raise KeyError(project_id)

            for field in ["workspace_id", "name", "description", "status"]:
                value = getattr(project, field, None)
                if value is not None:
                    setattr(existing_project, field, value)

            existing_project.updated_at = datetime.now(timezone.utc).isoformat()
            session.commit()
            session.refresh(existing_project)
            return existing_project

    def delete_project(self, project_id: str) -> None:
        with SessionLocal() as session:
            project = session.get(Project, project_id)
            if not project:
                raise KeyError(project_id)
            session.delete(project)
            session.commit()
