from app.models.execution_log import ExecutionLog
from app.models.pipeline_execution import PipelineExecution


class ExecutionRepository:
    """Placeholder execution repository."""

    def create_execution(self, execution: PipelineExecution) -> PipelineExecution:
        # TODO: Implement repository logic for creating an execution record.
        raise NotImplementedError

    def list_executions(self) -> list[PipelineExecution]:
        # TODO: Implement repository logic for listing executions.
        raise NotImplementedError

    def get_execution(self, execution_id: str) -> PipelineExecution:
        # TODO: Implement repository logic for fetching an execution.
        raise NotImplementedError

    def get_execution_logs(self, execution_id: str) -> list[ExecutionLog]:
        # TODO: Implement repository logic for fetching execution logs.
        raise NotImplementedError

    def update_execution(self, execution_id: str, execution: PipelineExecution) -> PipelineExecution:
        # TODO: Implement repository logic for updating an execution.
        raise NotImplementedError
