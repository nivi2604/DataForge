from app.models.pipeline import Pipeline
from app.models.pipeline_node import PipelineNode


class PipelineRepository:
    """Placeholder pipeline repository."""

    def list_pipelines(self) -> list[Pipeline]:
        # TODO: Implement repository query for listing pipelines.
        raise NotImplementedError

    def get_pipeline(self, pipeline_id: str) -> Pipeline:
        # TODO: Implement repository query for getting a pipeline.
        raise NotImplementedError

    def create_pipeline(self, pipeline: Pipeline) -> Pipeline:
        # TODO: Implement repository query for creating a pipeline.
        raise NotImplementedError

    def update_pipeline(self, pipeline_id: str, pipeline: Pipeline) -> Pipeline:
        # TODO: Implement repository query for updating a pipeline.
        raise NotImplementedError

    def delete_pipeline(self, pipeline_id: str) -> None:
        # TODO: Implement repository query for deleting a pipeline.
        raise NotImplementedError

    def list_pipeline_nodes(self, pipeline_id: str) -> list[PipelineNode]:
        # TODO: Implement repository query for listing pipeline nodes.
        raise NotImplementedError

    def create_pipeline_node(self, pipeline_id: str, node: PipelineNode) -> PipelineNode:
        # TODO: Implement repository query for creating a pipeline node.
        raise NotImplementedError

    def update_pipeline_node(self, pipeline_id: str, node_id: str, node: PipelineNode) -> PipelineNode:
        # TODO: Implement repository query for updating a pipeline node.
        raise NotImplementedError

    def delete_pipeline_node(self, pipeline_id: str, node_id: str) -> None:
        # TODO: Implement repository query for deleting a pipeline node.
        raise NotImplementedError
