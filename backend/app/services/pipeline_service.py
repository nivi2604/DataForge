from app.models.pipeline import Pipeline
from app.models.pipeline_node import PipelineNode
from app.schemas.pipeline import PipelineCreate, PipelineNodeCreate, PipelineUpdate


class PipelineService:
    """Placeholder pipeline service."""

    def list_pipelines(self) -> list[Pipeline]:
        # TODO: Implement list pipelines.
        raise NotImplementedError

    def get_pipeline(self, pipeline_id: str) -> Pipeline:
        # TODO: Implement get pipeline by id.
        raise NotImplementedError

    def create_pipeline(self, payload: PipelineCreate) -> Pipeline:
        # TODO: Implement create pipeline.
        raise NotImplementedError

    def update_pipeline(self, pipeline_id: str, payload: PipelineUpdate) -> Pipeline:
        # TODO: Implement update pipeline.
        raise NotImplementedError

    def delete_pipeline(self, pipeline_id: str) -> None:
        # TODO: Implement delete pipeline.
        raise NotImplementedError

    def list_pipeline_nodes(self, pipeline_id: str) -> list[PipelineNode]:
        # TODO: Implement list pipeline nodes.
        raise NotImplementedError

    def create_pipeline_node(self, pipeline_id: str, payload: PipelineNodeCreate) -> PipelineNode:
        # TODO: Implement create pipeline node.
        raise NotImplementedError

    def update_pipeline_node(self, pipeline_id: str, node_id: str, payload: PipelineNodeCreate) -> PipelineNode:
        # TODO: Implement update pipeline node.
        raise NotImplementedError

    def delete_pipeline_node(self, pipeline_id: str, node_id: str) -> None:
        # TODO: Implement delete pipeline node.
        raise NotImplementedError
