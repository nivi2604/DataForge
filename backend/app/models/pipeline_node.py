from dataclasses import dataclass


@dataclass
class PipelineNode:
    id: str | None = None
    pipeline_id: str | None = None
    node_type: str | None = None
    configuration: str | None = None
    position_x: int | None = None
    position_y: int | None = None
