import uuid
from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.models.github_connection import GithubConnection

class GithubConnectionRepository:
    def create_connection(self, connection: GithubConnection) -> GithubConnection:
        if not connection.id:
            connection.id = str(uuid.uuid4())
        if not connection.created_at:
            connection.created_at = datetime.now(timezone.utc).isoformat()
            
        with SessionLocal() as session:
            session.add(connection)
            session.commit()
            session.refresh(connection)
            return connection
            
    def get_connection(self, connection_id: str) -> GithubConnection | None:
        with SessionLocal() as session:
            return session.get(GithubConnection, connection_id)
            
    def get_connections_for_user(self, user_id: str) -> list[GithubConnection]:
        with SessionLocal() as session:
            return session.query(GithubConnection).filter(GithubConnection.user_id == user_id).all()
            
    def delete_connection(self, connection_id: str) -> None:
        with SessionLocal() as session:
            conn = session.get(GithubConnection, connection_id)
            if conn:
                session.delete(conn)
                session.commit()
