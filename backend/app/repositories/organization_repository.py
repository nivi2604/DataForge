from datetime import datetime, timezone
from uuid import uuid4

from app.db.session import SessionLocal
from app.models.organization import Organization


class OrganizationRepository:
    """SQLAlchemy-backed organization repository."""

    def list_organizations(self) -> list[Organization]:
        with SessionLocal() as session:
            return list(session.query(Organization).all())

    def get_organization(self, organization_id: str) -> Organization | None:
        with SessionLocal() as session:
            return session.get(Organization, organization_id)

    def get_organization_by_id(self, organization_id: str) -> Organization | None:
        return self.get_organization(organization_id)

    def create_organization(self, organization: Organization) -> Organization:
        if not organization.id:
            organization.id = str(uuid4())
        if not organization.created_at:
            organization.created_at = datetime.now(timezone.utc).isoformat()
        with SessionLocal() as session:
            session.add(organization)
            session.commit()
            session.refresh(organization)
            return organization

    def update_organization(self, organization_id: str, organization: Organization) -> Organization:
        with SessionLocal() as session:
            existing_organization = session.get(Organization, organization_id)
            if not existing_organization:
                raise KeyError(organization_id)

            for field in ["name", "description", "owner_id"]:
                value = getattr(organization, field, None)
                if value is not None:
                    setattr(existing_organization, field, value)

            session.commit()
            session.refresh(existing_organization)
            return existing_organization

    def delete_organization(self, organization_id: str) -> None:
        with SessionLocal() as session:
            organization = session.get(Organization, organization_id)
            if not organization:
                raise KeyError(organization_id)
            session.delete(organization)
            session.commit()
