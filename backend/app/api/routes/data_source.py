from fastapi import APIRouter, Header, Response, status

from app.api.routes.auth import auth_service
from app.core.security import get_current_user
from app.models.data_source import DataSource
from app.schemas.data_source import (
    DataSourceCreate,
    DataSourceResponse,
    DataSourceUpdate,
    TestConnectionRequest,
    TestConnectionResponse,
)
from app.services.data_source_service import DataSourceService

router = APIRouter(prefix="/data-sources", tags=["data-sources"])
data_source_service = DataSourceService()


def _require_authentication(authorization: str | None) -> None:
    get_current_user(authorization, auth_service.user_repository)


@router.get("", response_model=list[DataSourceResponse])
def list_data_sources(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> list[DataSourceResponse]:
    _require_authentication(authorization)
    data_sources = data_source_service.list_data_sources()
    return [
        DataSourceResponse(
            id=data_source.id or "",
            project_id=data_source.project_id,
            name=data_source.name,
            type=data_source.type,
            connection_details=data_source.connection_details,
            status=data_source.status,
            created_at=data_source.created_at,
            updated_at=data_source.updated_at,
        )
        for data_source in data_sources
    ]


@router.get("/{data_source_id}", response_model=DataSourceResponse)
def get_data_source(
    data_source_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> DataSourceResponse:
    _require_authentication(authorization)
    data_source = data_source_service.get_data_source(data_source_id)
    return DataSourceResponse(
        id=data_source.id or "",
        project_id=data_source.project_id,
        name=data_source.name,
        type=data_source.type,
        connection_details=data_source.connection_details,
        status=data_source.status,
        created_at=data_source.created_at,
        updated_at=data_source.updated_at,
    )


@router.post("", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED)
def create_data_source(
    payload: DataSourceCreate,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> DataSourceResponse:
    _require_authentication(authorization)
    data_source = data_source_service.create_data_source(payload)
    return DataSourceResponse(
        id=data_source.id or "",
        project_id=data_source.project_id,
        name=data_source.name,
        type=data_source.type,
        connection_details=data_source.connection_details,
        status=data_source.status,
        created_at=data_source.created_at,
        updated_at=data_source.updated_at,
    )


@router.put("/{data_source_id}", response_model=DataSourceResponse)
def update_data_source(
    data_source_id: str,
    payload: DataSourceUpdate,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> DataSourceResponse:
    _require_authentication(authorization)
    data_source = data_source_service.update_data_source(data_source_id, payload)
    return DataSourceResponse(
        id=data_source.id or "",
        project_id=data_source.project_id,
        name=data_source.name,
        type=data_source.type,
        connection_details=data_source.connection_details,
        status=data_source.status,
        created_at=data_source.created_at,
        updated_at=data_source.updated_at,
    )


@router.delete("/{data_source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_data_source(
    data_source_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> Response:
    _require_authentication(authorization)
    data_source_service.delete_data_source(data_source_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{data_source_id}/test-connection", response_model=TestConnectionResponse)
def test_connection(
    data_source_id: str,
    payload: TestConnectionRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> TestConnectionResponse:
    _require_authentication(authorization)
    return data_source_service.test_connection(data_source_id, payload)

