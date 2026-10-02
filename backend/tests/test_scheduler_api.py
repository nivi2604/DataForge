import json
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.organization import Organization
from app.models.workspace import Workspace
from app.models.project import Project
from app.models.pipeline import Pipeline
from app.models.pipeline_node import PipelineNode
from app.models.pipeline_execution import PipelineExecution
from app.models.pipeline_schedule import PipelineSchedule
from app.models.execution_log import ExecutionLog
from app.models.user import User
from app.services.scheduler_service import SchedulerService
from app.main import app

@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)

