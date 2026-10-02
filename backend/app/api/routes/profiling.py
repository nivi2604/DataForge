"""
DataForge — Data Profiling API Route
=====================================
POST /profiling/profile
    Body: { "data_source_id": "<id>" }
    Returns: structured profile of the dataset.
"""

import csv
import io
import json
from pathlib import Path

from fastapi import APIRouter, Header
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.api.routes.auth import auth_service
from app.core.security import get_current_user
from app.models.user import User
from app.repositories.data_source_repository import DataSourceRepository
from app.services.authorization_service import AuthorizationService
from app.services.data_profiling_service import DataProfilingService

router = APIRouter(prefix="/profiling", tags=["profiling"])
ds_repo = DataSourceRepository()


def _require_authentication(authorization: str | None) -> User:
    return get_current_user(authorization, auth_service.user_repository)


class ProfilingRequest(BaseModel):
    data_source_id: str


def _load_data(ds) -> list[dict]:
    """Load data from a data source into a list of dicts (read-only)."""
    conn = json.loads(ds.connection_details or "{}")

    if ds.type == "CSV":
        path = conn.get("path")
        if not path or not Path(path).is_file():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"CSV file not found at path: {path}",
            )
        with open(path, mode="r", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    elif ds.type == "JSON":
        path = conn.get("path")
        if not path or not Path(path).is_file():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"JSON file not found at path: {path}",
            )
        with open(path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="JSON data must be a list of objects",
            )
        return data

    elif ds.type == "Parquet":
        try:
            import pandas as pd
        except ImportError:
            raise HTTPException(status_code=500, detail="pandas is required to profile Parquet files")
        path = conn.get("path")
        if not path or not Path(path).is_file():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Parquet file not found at path: {path}",
            )
        df = pd.read_parquet(path)
        return df.to_dict(orient="records")

    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Profiling is supported for CSV, JSON, and Parquet data sources. "
                f"Type '{ds.type}' requires a live connection and cannot be profiled inline."
            ),
        )


@router.post("/profile")
def profile_data_source(
    payload: ProfilingRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict:
    """
    Profile a file-based data source.

    Returns:
        row_count, column_count, duplicate stats, per-column statistics
        (inferred type, missing count, unique count, min, max, mean, median).
    """
    user = _require_authentication(authorization)
    AuthorizationService.verify_data_source_access(payload.data_source_id, user.id)

    ds = ds_repo.get_data_source_by_id(payload.data_source_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Data source not found")

    data = _load_data(ds)
    profile = DataProfilingService.profile(data)
    profile["data_source_id"] = payload.data_source_id
    profile["data_source_name"] = ds.name
    profile["data_source_type"] = ds.type
    return profile
