from fastapi import APIRouter, Header, Response, status

from app.api.routes.auth import auth_service
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.pipeline import (
    PipelineCreate,
    PipelineNodeCreate,
    PipelineNodeResponse,
    PipelineResponse,
    PipelineUpdate,
    PipelineVersionCreate,
    PipelineVersionResponse,
    PipelineVersionGithubPush,
)
from app.services.pipeline_service import PipelineService
from app.services.authorization_service import AuthorizationService


router = APIRouter(prefix="/pipelines", tags=["pipelines"])
pipeline_service = PipelineService()


def _require_authentication(authorization: str | None) -> User:
    return get_current_user(authorization, auth_service.user_repository)


def _to_response(pipeline) -> PipelineResponse:
    return PipelineResponse(
        id=pipeline.id or "",
        project_id=pipeline.project_id,
        name=pipeline.name,
        description=pipeline.description,
        version=pipeline.version,
        status=pipeline.status,
        created_at=pipeline.created_at,
        updated_at=pipeline.updated_at,
    )


@router.get("", response_model=list[PipelineResponse])
def list_pipelines(
    project_id: str | None = None,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> list[PipelineResponse]:
    user = _require_authentication(authorization)
    if project_id:
        AuthorizationService.verify_project_access(project_id, user.id)
    pipelines = pipeline_service.list_pipelines(project_id=project_id)
    pipelines = AuthorizationService.filter_pipelines(pipelines, user.id)
    return [_to_response(pipeline) for pipeline in pipelines]


@router.get("/{pipeline_id}", response_model=PipelineResponse)
def get_pipeline(
    pipeline_id: str,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> PipelineResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)

    pipeline = pipeline_service.get_pipeline(pipeline_id)

    return _to_response(pipeline)


@router.post(
    "",
    response_model=PipelineResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_pipeline(
    payload: PipelineCreate,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> PipelineResponse:
    user = _require_authentication(authorization)
    if payload.project_id:
        AuthorizationService.verify_project_access(payload.project_id, user.id)

    pipeline = pipeline_service.create_pipeline(payload)

    return _to_response(pipeline)


@router.put("/{pipeline_id}", response_model=PipelineResponse)
def update_pipeline(
    pipeline_id: str,
    payload: PipelineUpdate,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> PipelineResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)

    pipeline = pipeline_service.update_pipeline(
        pipeline_id,
        payload,
    )

    return _to_response(pipeline)


@router.delete(
    "/{pipeline_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_pipeline(
    pipeline_id: str,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> Response:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)
    pipeline_service.delete_pipeline(pipeline_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


def _to_node_response(node) -> PipelineNodeResponse:
    return PipelineNodeResponse(
        id=node.id or "",
        pipeline_id=node.pipeline_id,
        node_type=node.node_type,
        configuration=node.configuration,
        sequence_index=node.sequence_index,
        position_x=node.position_x,
        position_y=node.position_y,
    )


@router.get("/{pipeline_id}/nodes", response_model=list[PipelineNodeResponse])
def list_pipeline_nodes(
    pipeline_id: str,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> list[PipelineNodeResponse]:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)

    nodes = pipeline_service.list_pipeline_nodes(pipeline_id)

    return [_to_node_response(node) for node in nodes]


@router.get("/{pipeline_id}/nodes/{node_id}", response_model=PipelineNodeResponse)
def get_pipeline_node(
    pipeline_id: str,
    node_id: str,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> PipelineNodeResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)

    node = pipeline_service.get_pipeline_node(pipeline_id, node_id)

    return _to_node_response(node)


@router.post(
    "/{pipeline_id}/nodes",
    response_model=PipelineNodeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_pipeline_node(
    pipeline_id: str,
    payload: PipelineNodeCreate,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> PipelineNodeResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)

    node = pipeline_service.create_pipeline_node(pipeline_id, payload)

    return _to_node_response(node)


@router.put("/{pipeline_id}/nodes/{node_id}", response_model=PipelineNodeResponse)
def update_pipeline_node(
    pipeline_id: str,
    node_id: str,
    payload: PipelineNodeCreate,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> PipelineNodeResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)

    node = pipeline_service.update_pipeline_node(
        pipeline_id,
        node_id,
        payload,
    )

    return _to_node_response(node)


@router.delete(
    "/{pipeline_id}/nodes/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_pipeline_node(
    pipeline_id: str,
    node_id: str,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> Response:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)

    pipeline_service.delete_pipeline_node(pipeline_id, node_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )

def _to_version_response(version) -> PipelineVersionResponse:
    return PipelineVersionResponse(
        id=version.id or "",
        pipeline_id=version.pipeline_id,
        version_number=version.version_number,
        created_by=version.created_by,
        description=version.description,
        pipeline_snapshot=version.pipeline_snapshot,
        created_at=version.created_at,
        github_branch=version.github_branch,
        github_commit_sha=version.github_commit_sha,
        github_pr_url=version.github_pr_url,
    )

@router.get("/{pipeline_id}/versions", response_model=list[PipelineVersionResponse])
def list_pipeline_versions(
    pipeline_id: str,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> list[PipelineVersionResponse]:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)

    versions = pipeline_service.list_pipeline_versions(pipeline_id)
    return [_to_version_response(v) for v in versions]

@router.get("/{pipeline_id}/versions/{version_id}", response_model=PipelineVersionResponse)
def get_pipeline_version(
    pipeline_id: str,
    version_id: str,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> PipelineVersionResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)

    version = pipeline_service.get_pipeline_version(pipeline_id, version_id)
    return _to_version_response(version)

@router.post(
    "/{pipeline_id}/versions",
    response_model=PipelineVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_pipeline_version(
    pipeline_id: str,
    payload: PipelineVersionCreate,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> PipelineVersionResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)

    version = pipeline_service.create_pipeline_version(
        pipeline_id=pipeline_id,
        description=payload.description,
        user_id=user.id,
    )
    return _to_version_response(version)

@router.get("/{pipeline_id}/versions/{v1_id}/compare/{v2_id}", response_model=list[str])
def compare_pipeline_versions(
    pipeline_id: str,
    v1_id: str,
    v2_id: str,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> list[str]:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)

    return pipeline_service.compare_pipeline_versions(pipeline_id, v1_id, v2_id)

@router.post(
    "/{pipeline_id}/versions/{version_id}/rollback",
    response_model=PipelineVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def rollback_pipeline_version(
    pipeline_id: str,
    version_id: str,
    payload: PipelineVersionCreate,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> PipelineVersionResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)

    version = pipeline_service.rollback_pipeline_version(
        pipeline_id=pipeline_id,
        version_id=version_id,
        user_id=user.id,
        rollback_message=payload.description,
    )
    return _to_version_response(version)

from app.api.routes.github import github_service
from app.schemas.github import GithubCommitCreate, GithubPullRequestCreate
import json

@router.post(
    "/{pipeline_id}/versions/{version_id}/github-push",
    response_model=PipelineVersionResponse,
)
def push_pipeline_version_to_github(
    pipeline_id: str,
    version_id: str,
    payload: PipelineVersionGithubPush,
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
) -> PipelineVersionResponse:
    user = _require_authentication(authorization)
    AuthorizationService.verify_pipeline_access(pipeline_id, user.id)

    # 1. Get the version
    version = pipeline_service.get_pipeline_version(pipeline_id, version_id)

    # 2. Push to GitHub
    commit_payload = GithubCommitCreate(
        branch=payload.branch,
        message=payload.commit_message,
        content=json.loads(version.pipeline_snapshot) if version.pipeline_snapshot else {},
        file_path=f"pipelines/{pipeline_id}/version_{version.version_number}.json"
    )

    commit = github_service.create_commit(user.id, payload.connection_id, commit_payload)

    # 3. Create PR if requested
    pr_url = None
    if payload.create_pr and payload.pr_title and payload.pr_base:
        pr_payload = GithubPullRequestCreate(
            title=payload.pr_title,
            head=payload.branch,
            base=payload.pr_base,
            body=f"DataForge pipeline update for pipeline {pipeline_id} version {version.version_number}."
        )
        pr = github_service.create_pull_request(user.id, payload.connection_id, pr_payload)
        pr_url = pr.html_url

    # 4. Update the Pipeline Version in database
    version = pipeline_service.update_pipeline_version_github_info(
        pipeline_id, version_id, payload.branch, commit.sha, pr_url
    )

    return _to_version_response(version)