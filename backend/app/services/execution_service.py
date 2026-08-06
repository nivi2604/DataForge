from app.models.execution_log import ExecutionLog
from app.models.pipeline_execution import PipelineExecution
from app.schemas.execution import ExecutePipelineRequest


class ExecutionService:
    """Placeholder execution service."""

    def execute_pipeline(self, pipeline_id: str, payload: ExecutePipelineRequest) -> PipelineExecution:
        # TODO: Implement pipeline execution orchestration.
        raise NotImplementedError

    def list_executions(self) -> list[PipelineExecution]:
        # TODO: Implement listing executions.
        raise NotImplementedError

    def get_execution(self, execution_id: str) -> PipelineExecution:
        # TODO: Implement fetching a single execution.
        raise NotImplementedError

    def get_execution_logs(self, execution_id: str) -> list[ExecutionLog]:
        # TODO: Implement fetching execution logs.
        raise NotImplementedError

    def cancel_execution(self, execution_id: str) -> PipelineExecution:
        # TODO: Implement cancellation flow.
        raise NotImplementedError
