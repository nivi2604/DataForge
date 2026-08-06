from fastapi import APIRouter, Header, Response, status

from app.api.routes.auth import auth_service
from app.core.security import get_current_user
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationResponse, OrganizationUpdate
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])
organization_service = OrganizationService()


def _require_authentication(authorization: str | None) -> None:
    return get_current_user(authorization, auth_service.user_repository)


@router.get("", response_model=list[OrganizationResponse])
def list_organizations(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> list[OrganizationResponse]:
    _require_authentication(authorization)
    organizations = organization_service.list_organizations()
    return [
        OrganizationResponse(
            id=organization.id or "",
            name=organization.name,
            description=organization.description,
            owner_id=organization.owner_id,
            created_at=organization.created_at,
        )
        for organization in organizations
    ]


@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(
    organization_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> OrganizationResponse:
    _require_authentication(authorization)
    organization = organization_service.get_organization(organization_id)
    return OrganizationResponse(
        id=organization.id or "",
        name=organization.name,
        description=organization.description,
        owner_id=organization.owner_id,
        created_at=organization.created_at,
    )


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreate,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> OrganizationResponse:
    current_user = _require_authentication(authorization)
    organization = organization_service.create_organization(payload, owner_id=current_user.id or "")
    return OrganizationResponse(
        id=organization.id or "",
        name=organization.name,
        description=organization.description,
        owner_id=organization.owner_id,
        created_at=organization.created_at,
    )


@router.put("/{organization_id}", response_model=OrganizationResponse)
def update_organization(
    organization_id: str,
    payload: OrganizationUpdate,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> OrganizationResponse:
    current_user = _require_authentication(authorization)
    organization = organization_service.update_organization(organization_id, payload, owner_id=current_user.id or "")
    return OrganizationResponse(
        id=organization.id or "",
        name=organization.name,
        description=organization.description,
        owner_id=organization.owner_id,
        created_at=organization.created_at,
    )


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(
    organization_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> Response:
    current_user = _require_authentication(authorization)
    organization_service.delete_organization(organization_id, owner_id=current_user.id or "")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
