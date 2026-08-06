from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer

from app.api.routes.auth import router as auth_router
from app.api.routes.data_source import router as data_source_router
from app.api.routes.organization import router as organization_router
from app.api.routes.project import router as project_router
from app.api.routes.workspace import router as workspace_router
from app.db.session import init_db

bearer_scheme = HTTPBearer()

app = FastAPI(title="DataForge API", version="1.0.0")

init_db()


def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"bearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
app.include_router(auth_router)
app.include_router(organization_router)
app.include_router(project_router)
app.include_router(workspace_router)
app.include_router(data_source_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to DataForge API"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}
