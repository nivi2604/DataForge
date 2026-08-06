from fastapi import HTTPException, status

from app.models.organization import Organization
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.organization import OrganizationCreate, OrganizationUpdate


class OrganizationService:
    """Organization service with business validation and ownership checks."""

    def __init__(self) -> None:
        self.organization_repository = OrganizationRepository()

    def list_organizations(self) -> list[Organization]:
        return self.organization_repository.list_organizations()

    def get_organization(self, organization_id: str) -> Organization:
        organization = self.organization_repository.get_organization_by_id(organization_id)
        if not organization:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        return organization

    def create_organization(self, payload: OrganizationCreate, owner_id: str) -> Organization:
        name = (payload.name or "").strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization name is required")

        normalized_name = name.lower()
        for organization in self.organization_repository.list_organizations():
            if organization.owner_id == owner_id and (organization.name or "").lower() == normalized_name:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Organization name already exists for this owner",
                )

        organization = Organization(
            name=name,
            description=payload.description,
            owner_id=owner_id,
        )
        return self.organization_repository.create_organization(organization)

    def update_organization(self, organization_id: str, payload: OrganizationUpdate, owner_id: str) -> Organization:
        existing_organization = self.organization_repository.get_organization_by_id(organization_id)
        if not existing_organization:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        if existing_organization.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the organization owner can update this organization",
            )

        if payload.name is not None:
            name = (payload.name or "").strip()
            if not name:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization name is required")

            normalized_name = name.lower()
            for organization in self.organization_repository.list_organizations():
                if (
                    organization.id != organization_id
                    and organization.owner_id == owner_id
                    and (organization.name or "").lower() == normalized_name
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Organization name already exists for this owner",
                    )

        organization = Organization(
            name=payload.name if payload.name is not None else existing_organization.name,
            description=payload.description if payload.description is not None else existing_organization.description,
            owner_id=existing_organization.owner_id,
        )
        return self.organization_repository.update_organization(organization_id, organization)

    def delete_organization(self, organization_id: str, owner_id: str) -> None:
        organization = self.organization_repository.get_organization_by_id(organization_id)
        if not organization:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        if organization.owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the organization owner can delete this organization",
            )

        self.organization_repository.delete_organization(organization_id)
