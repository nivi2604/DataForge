import json
import socket
import zipfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException, status

from app.api.routes.project import project_service
from app.models.data_source import DataSource
from app.repositories.data_source_repository import DataSourceRepository
from app.schemas.data_source import DataSourceCreate, DataSourceUpdate, TestConnectionRequest, TestConnectionResponse


class DataSourceService:
    """Data source service with type-aware validation and connection testing."""

    _SUPPORTED_TYPES = {
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "csv": "CSV",
        "excel": "Excel",
        "rest api": "REST API",
    }

    def __init__(self) -> None:
        self.data_source_repository = DataSourceRepository()
        self.project_repository = project_service.project_repository

    def list_data_sources(self) -> list[DataSource]:
        return [self._sanitize_data_source(data_source) for data_source in self.data_source_repository.list_data_sources()]

    def get_data_source(self, data_source_id: str) -> DataSource:
        data_source = self.data_source_repository.get_data_source_by_id(data_source_id)
        if not data_source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")
        return self._sanitize_data_source(data_source)

    def create_data_source(self, payload: DataSourceCreate) -> DataSource:
        name = (payload.name or "").strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data source name is required")

        project_id = (payload.project_id or "").strip()
        if not project_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project ID is required")

        project = self.project_repository.get_project_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        normalized_type = self._normalize_type(payload.type)
        details = self._validate_connection_details(normalized_type, payload.connection_details)

        data_source = DataSource(
            project_id=project_id,
            name=name,
            type=normalized_type,
            connection_details=details,
            status=payload.status or "active",
        )
        created_data_source = self.data_source_repository.create_data_source(data_source)
        return self._sanitize_data_source(created_data_source)

    def update_data_source(self, data_source_id: str, payload: DataSourceUpdate) -> DataSource:
        existing_data_source = self.data_source_repository.get_data_source_by_id(data_source_id)
        if not existing_data_source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")

        if payload.name is not None:
            name = (payload.name or "").strip()
            if not name:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data source name is required")

        if payload.project_id is not None:
            project_id = (payload.project_id or "").strip()
            if not project_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project ID is required")
            project = self.project_repository.get_project_by_id(project_id)
            if not project:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        normalized_type = self._normalize_type(payload.type) if payload.type is not None else existing_data_source.type
        details = (
            self._validate_connection_details(normalized_type, payload.connection_details)
            if payload.connection_details is not None
            else existing_data_source.connection_details
        )

        data_source = DataSource(
            project_id=payload.project_id if payload.project_id is not None else existing_data_source.project_id,
            name=payload.name if payload.name is not None else existing_data_source.name,
            type=normalized_type,
            connection_details=details,
            status=payload.status if payload.status is not None else existing_data_source.status,
        )
        updated_data_source = self.data_source_repository.update_data_source(data_source_id, data_source)
        return self._sanitize_data_source(updated_data_source)

    def delete_data_source(self, data_source_id: str) -> None:
        data_source = self.data_source_repository.get_data_source_by_id(data_source_id)
        if not data_source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")
        self.data_source_repository.delete_data_source(data_source_id)

    def test_connection(self, data_source_id: str, payload: TestConnectionRequest) -> TestConnectionResponse:
        data_source = self.data_source_repository.get_data_source_by_id(data_source_id)
        if not data_source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")

        details = payload.connection_details or data_source.connection_details
        normalized_type = self._normalize_type(data_source.type)
        parsed_details = self._parse_connection_details(details)
        try:
            self._probe_connection(normalized_type, parsed_details)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except URLError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Connection test failed: {exc}") from exc

        return TestConnectionResponse(success=True, message="Connection test successful")

    def _normalize_type(self, data_type: str | None) -> str:
        if not data_type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data source type is required")
        normalized = data_type.strip().lower()
        if normalized not in self._SUPPORTED_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported data source type",
            )
        return self._SUPPORTED_TYPES[normalized]

    def _parse_connection_details(self, connection_details: str | dict | None) -> dict:
        if connection_details is None:
            return {}
        if isinstance(connection_details, dict):
            return connection_details
        try:
            return json.loads(connection_details)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Connection details must be valid JSON") from exc

    def _sanitize_data_source(self, data_source: DataSource) -> DataSource:
        sanitized_details = self._sanitize_connection_details(data_source.connection_details)
        return DataSource(
            id=data_source.id,
            project_id=data_source.project_id,
            name=data_source.name,
            type=data_source.type,
            connection_details=sanitized_details,
            status=data_source.status,
            created_at=data_source.created_at,
            updated_at=data_source.updated_at,
        )

    def _sanitize_connection_details(self, connection_details: str | None) -> str | None:
        if not connection_details:
            return connection_details

        parsed_details = self._parse_connection_details(connection_details)
        if not isinstance(parsed_details, dict):
            return connection_details

        sensitive_keys = {"password", "secret", "token", "api_key", "access_key", "secret_key", "authorization"}
        sanitized_details = {}
        for key, value in parsed_details.items():
            if key.lower() in sensitive_keys:
                sanitized_details[key] = "***"
            else:
                sanitized_details[key] = value

        return json.dumps(sanitized_details)

    def _validate_connection_details(self, data_type: str, connection_details: str | dict | None) -> str:
        parsed_details = self._parse_connection_details(connection_details)
        if data_type == "PostgreSQL":
            required = {"host", "port", "database", "username", "password"}
        elif data_type == "MySQL":
            required = {"host", "port", "database", "username", "password"}
        elif data_type == "CSV":
            required = {"path"}
        elif data_type == "Excel":
            required = {"path"}
        elif data_type == "REST API":
            required = {"url"}
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported data source type")

        missing = sorted(required.difference(parsed_details.keys()))
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing connection details: {', '.join(missing)}",
            )

        if data_type == "REST API":
            url = str(parsed_details["url"]).strip()
            if not url.startswith(("http://", "https://")):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="REST API URL must start with http:// or https://")

        return json.dumps(parsed_details)

    def _probe_connection(self, data_type: str, details: dict) -> None:
        if data_type in {"PostgreSQL", "MySQL"}:
            required = {"host", "port", "database", "username", "password"}
            if not required.issubset(details):
                raise ValueError("Missing connection details for database source")

            host = str(details["host"])
            port = int(details["port"])
            try:
                with socket.create_connection((host, port), timeout=3):
                    pass
            except OSError as exc:  # pragma: no cover - environment dependent
                raise ValueError(f"Connection failed: {exc}") from exc
            return

        if data_type == "CSV":
            path = Path(str(details["path"]))
            if not path.exists() or not path.is_file():
                raise ValueError("CSV file does not exist")
            return

        if data_type == "Excel":
            path = Path(str(details["path"]))
            if not path.exists() or not path.is_file():
                raise ValueError("Excel file does not exist")
            try:
                with zipfile.ZipFile(path) as workbook:
                    workbook.read("xl/workbook.xml")
            except (zipfile.BadZipFile, KeyError) as exc:
                raise ValueError("Excel file is not a valid workbook") from exc
            return

        if data_type == "REST API":
            url = str(details["url"])
            request = Request(url, method="GET")
            with urlopen(request, timeout=5) as response:
                response.read(1)
            return

        raise ValueError("Unsupported data source type")
