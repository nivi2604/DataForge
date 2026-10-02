from fastapi import HTTPException, status
from app.db.session import SessionLocal
from sqlalchemy.orm import Session
from app.models.organization import Organization
from app.models.workspace import Workspace
from app.models.project import Project
from app.models.data_source import DataSource
from app.models.pipeline import Pipeline
from app.models.pipeline_node import PipelineNode
from app.models.pipeline_schedule import PipelineSchedule
from app.models.pipeline_execution import PipelineExecution
from app.models.execution_log import ExecutionLog

class AuthorizationService:
    @staticmethod
    def verify_organization_access(organization_id: str, user_id: str, session: Session | None = None) -> None:
        db = session or SessionLocal()
        try:
            org = db.query(Organization).filter(Organization.id == organization_id).first()
            if not org:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
            if org.owner_id != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        finally:
            if session is None:
                db.close()

    @staticmethod
    def verify_workspace_access(workspace_id: str, user_id: str, session: Session | None = None) -> None:
        db = session or SessionLocal()
        try:
            workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
            if not workspace:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
            AuthorizationService.verify_organization_access(workspace.organization_id, user_id, db)
        finally:
            if session is None:
                db.close()

    @staticmethod
    def verify_project_access(project_id: str, user_id: str, session: Session | None = None) -> None:
        db = session or SessionLocal()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
            AuthorizationService.verify_workspace_access(project.workspace_id, user_id, db)
        finally:
            if session is None:
                db.close()

    @staticmethod
    def verify_data_source_access(data_source_id: str, user_id: str, session: Session | None = None) -> None:
        db = session or SessionLocal()
        try:
            ds = db.query(DataSource).filter(DataSource.id == data_source_id).first()
            if not ds:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")
            AuthorizationService.verify_project_access(ds.project_id, user_id, db)
        finally:
            if session is None:
                db.close()

    @staticmethod
    def verify_pipeline_access(pipeline_id: str, user_id: str, session: Session | None = None) -> None:
        db = session or SessionLocal()
        try:
            pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
            if not pipeline:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
            AuthorizationService.verify_project_access(pipeline.project_id, user_id, db)
        finally:
            if session is None:
                db.close()

    @staticmethod
    def verify_pipeline_node_access(node_id: str, user_id: str, session: Session | None = None) -> None:
        db = session or SessionLocal()
        try:
            node = db.query(PipelineNode).filter(PipelineNode.id == node_id).first()
            if not node:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline node not found")
            AuthorizationService.verify_pipeline_access(node.pipeline_id, user_id, db)
        finally:
            if session is None:
                db.close()

    @staticmethod
    def verify_schedule_access(schedule_id: str, user_id: str, session: Session | None = None) -> None:
        db = session or SessionLocal()
        try:
            schedule = db.query(PipelineSchedule).filter(PipelineSchedule.id == schedule_id).first()
            if not schedule:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline schedule not found")
            AuthorizationService.verify_pipeline_access(schedule.pipeline_id, user_id, db)
        finally:
            if session is None:
                db.close()

    @staticmethod
    def verify_execution_access(execution_id: str, user_id: str, session: Session | None = None) -> None:
        db = session or SessionLocal()
        try:
            execution = db.query(PipelineExecution).filter(PipelineExecution.id == execution_id).first()
            if not execution:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline execution not found")
            AuthorizationService.verify_pipeline_access(execution.pipeline_id, user_id, db)
        finally:
            if session is None:
                db.close()

    @staticmethod
    def filter_organizations(organizations, user_id: str):
        return [org for org in organizations if org.owner_id == user_id]

    @staticmethod
    def filter_workspaces(workspaces, user_id: str):
        valid = []
        for ws in workspaces:
            try:
                AuthorizationService.verify_organization_access(ws.organization_id, user_id)
                valid.append(ws)
            except HTTPException:
                pass
        return valid

    @staticmethod
    def filter_projects(projects, user_id: str):
        valid = []
        for p in projects:
            try:
                AuthorizationService.verify_workspace_access(p.workspace_id, user_id)
                valid.append(p)
            except HTTPException:
                pass
        return valid

    @staticmethod
    def filter_data_sources(data_sources, user_id: str):
        valid = []
        for ds in data_sources:
            try:
                AuthorizationService.verify_project_access(ds.project_id, user_id)
                valid.append(ds)
            except HTTPException:
                pass
        return valid

    @staticmethod
    def filter_pipelines(pipelines, user_id: str):
        valid = []
        for p in pipelines:
            try:
                AuthorizationService.verify_project_access(p.project_id, user_id)
                valid.append(p)
            except HTTPException:
                pass
        return valid
