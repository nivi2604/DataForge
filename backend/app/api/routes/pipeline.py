from fastapi import APIRouter

from app.models.pipeline import Pipeline
from app.models.pipeline_node import PipelineNode
from app.schemas.pipeline import (
    PipelineCreate,
    PipelineNodeCreate,
    PipelineNodeResponse,
    PipelineResponse,
    PipelineUpdate,
)
from app.services.pipeline_service import PipelineService

router = APIRouter(prefix="/pipelines", tags=["pipelines"])
pipeline_service = PipelineService()


@router.get("", response_model=list[PipelineResponse])
def list_pipelines() -> list[PipelineResponse]:
    # TODO: Implement list pipelines.
    raise NotImplementedError


@router.get("/{pipeline_id}", response_model=PipelineResponse)
def get_pipeline(pipeline_id: str) -> PipelineResponse:
    # TODO: Implement get pipeline by id.
    raise NotImplementedError


@router.post("", response_model=PipelineResponse)
def create_pipeline(payload: PipelineCreate) -> PipelineResponse:
    # TODO: Implement create pipeline.
    raise NotImplementedError


@router.put("/{pipeline_id}", response_model=PipelineResponse)
def update_pipeline(pipeline_id: str, payload: PipelineUpdate) -> PipelineResponse:
    # TODO: Implement update pipeline.
    raise NotImplementedError


@router.delete("/{pipeline_id}")
def delete_pipeline(pipeline_id: str) -> dict[str, str]:
    # TODO: Implement delete pipeline.
    raise NotImplementedError


@router.get("/{pipeline_id}/nodes", response_model=list[PipelineNodeResponse])
def list_pipeline_nodes(pipeline_id: str) -> list[PipelineNodeResponse]:
    # TODO: Implement list pipeline nodes.
    raise NotImplementedError


@router.post("/{pipeline_id}/nodes", response_model=PipelineNodeResponse)
def create_pipeline_node(pipeline_id: str, payload: PipelineNodeCreate) -> PipelineNodeResponse:
    # TODO: Implement create pipeline node.
    raise NotImplementedError


@router.put("/{pipeline_id}/nodes/{node_id}", response_model=PipelineNodeResponse)
def update_pipeline_node(pipeline_id: str, node_id: str, payload: PipelineNodeCreate) -> PipelineNodeResponse:
    # TODO: Implement update pipeline node.
    raise NotImplementedError


@router.delete("/{pipeline_id}/nodes/{node_id}")
def delete_pipeline_node(pipeline_id: str, node_id: str) -> dict[str, str]:
    # TODO: Implement delete pipeline node.
    raise NotImplementedError
