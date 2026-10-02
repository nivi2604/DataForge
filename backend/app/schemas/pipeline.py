from dataclasses import dataclass


@dataclass
class PipelineCreate:
    project_id: str
    name: str
    description: str | None = None
    version: str | None = None
    status: str | None = None


@dataclass
class PipelineUpdate:
    project_id: str | None = None
    name: str | None = None
    description: str | None = None
    version: str | None = None
    status: str | None = None


@dataclass
class PipelineResponse:
    id: str
    project_id: str | None = None
    name: str | None = None
    description: str | None = None
    version: str | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class PipelineNodeCreate:
    node_type: str
    configuration: str | None = None
    sequence_index: int = 0
    position_x: int | None = None
    position_y: int | None = None


@dataclass
class PipelineNodeResponse:
    id: str
    pipeline_id: str | None = None
    node_type: str | None = None
    configuration: str | None = None
    sequence_index: int | None = None
    position_x: int | None = None
    position_y: int | None = None


@dataclass
class PipelineVersionCreate:
    description: str | None = None


@dataclass
class PipelineVersionResponse:
    id: str
    pipeline_id: str | None = None
    version_number: int | None = None
    created_by: str | None = None
    description: str | None = None
    pipeline_snapshot: str | None = None
    created_at: str | None = None
    github_branch: str | None = None
    github_commit_sha: str | None = None
    github_pr_url: str | None = None

@dataclass
class PipelineVersionGithubPush:
    connection_id: str
    branch: str
    commit_message: str
    create_pr: bool = False
    pr_title: str | None = None
    pr_base: str | None = None
