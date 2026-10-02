from datetime import datetime, timezone
from uuid import uuid4

from app.db.session import SessionLocal
from app.models.pipeline import Pipeline
from app.models.pipeline_node import PipelineNode
from app.models.pipeline_version import PipelineVersion


class PipelineRepository:
    """SQLAlchemy-backed pipeline repository."""

    def list_pipelines(self) -> list[Pipeline]:
        with SessionLocal() as session:
            return list(session.query(Pipeline).all())

    def get_pipeline(self, pipeline_id: str) -> Pipeline | None:
        with SessionLocal() as session:
            return session.get(Pipeline, pipeline_id)

    def get_pipeline_by_id(self, pipeline_id: str) -> Pipeline | None:
        return self.get_pipeline(pipeline_id)

    def get_pipelines_by_project(self, project_id: str) -> list[Pipeline]:
        with SessionLocal() as session:
            return list(
                session.query(Pipeline)
                .filter(Pipeline.project_id == project_id)
                .all()
            )

    def create_pipeline(self, pipeline: Pipeline) -> Pipeline:
        if not pipeline.id:
            pipeline.id = str(uuid4())

        if not pipeline.created_at:
            pipeline.created_at = datetime.now(timezone.utc).isoformat()

        if not pipeline.updated_at:
            pipeline.updated_at = pipeline.created_at

        with SessionLocal() as session:
            session.add(pipeline)
            session.commit()
            session.refresh(pipeline)
            return pipeline

    def update_pipeline(
        self,
        pipeline_id: str,
        pipeline: Pipeline,
    ) -> Pipeline:
        with SessionLocal() as session:
            existing_pipeline = session.get(Pipeline, pipeline_id)

            if not existing_pipeline:
                raise KeyError(pipeline_id)

            for field in [
                "project_id",
                "name",
                "description",
                "version",
                "status",
            ]:
                value = getattr(pipeline, field, None)

                if value is not None:
                    setattr(existing_pipeline, field, value)

            existing_pipeline.updated_at = datetime.now(
                timezone.utc
            ).isoformat()

            session.commit()
            session.refresh(existing_pipeline)
            return existing_pipeline

    def delete_pipeline(self, pipeline_id: str) -> None:
        with SessionLocal() as session:
            pipeline = session.get(Pipeline, pipeline_id)

            if not pipeline:
                raise KeyError(pipeline_id)

            session.delete(pipeline)
            session.commit()

    def list_pipeline_nodes(self, pipeline_id: str) -> list[PipelineNode]:
        with SessionLocal() as session:
            return list(
                session.query(PipelineNode)
                .filter(PipelineNode.pipeline_id == pipeline_id)
                .order_by(PipelineNode.sequence_index.asc())
                .all()
            )

    def get_pipeline_node(
        self,
        pipeline_id: str,
        node_id: str,
    ) -> PipelineNode | None:
        with SessionLocal() as session:
            return (
                session.query(PipelineNode)
                .filter(
                    PipelineNode.id == node_id,
                    PipelineNode.pipeline_id == pipeline_id,
                )
                .first()
            )

    def create_pipeline_node(
        self,
        pipeline_id: str,
        node: PipelineNode,
    ) -> PipelineNode:
        if not node.id:
            node.id = str(uuid4())

        node.pipeline_id = pipeline_id

        if not node.created_at:
            node.created_at = datetime.now(timezone.utc).isoformat()

        if not node.updated_at:
            node.updated_at = node.created_at

        with SessionLocal() as session:
            session.add(node)
            session.commit()
            session.refresh(node)
            return node

    def update_pipeline_node(
        self,
        pipeline_id: str,
        node_id: str,
        node: PipelineNode,
    ) -> PipelineNode:
        with SessionLocal() as session:
            existing_node = (
                session.query(PipelineNode)
                .filter(
                    PipelineNode.id == node_id,
                    PipelineNode.pipeline_id == pipeline_id,
                )
                .first()
            )

            if not existing_node:
                raise KeyError(node_id)

            for field in [
                "node_type",
                "configuration",
                "sequence_index",
                "position_x",
                "position_y",
            ]:
                value = getattr(node, field, None)

                if value is not None:
                    setattr(existing_node, field, value)

            existing_node.updated_at = datetime.now(timezone.utc).isoformat()

            session.commit()
            session.refresh(existing_node)
            return existing_node

    def delete_pipeline_node(
        self,
        pipeline_id: str,
        node_id: str,
    ) -> None:
        with SessionLocal() as session:
            node = (
                session.query(PipelineNode)
                .filter(
                    PipelineNode.id == node_id,
                    PipelineNode.pipeline_id == pipeline_id,
                )
                .first()
            )

            if not node:
                raise KeyError(node_id)

            session.delete(node)
            session.commit()

    def create_pipeline_version(self, version: PipelineVersion) -> PipelineVersion:
        if not version.id:
            version.id = str(uuid4())

        if not version.created_at:
            version.created_at = datetime.now(timezone.utc).isoformat()

        with SessionLocal() as session:
            session.add(version)
            session.commit()
            session.refresh(version)
            return version

    def list_pipeline_versions(self, pipeline_id: str) -> list[PipelineVersion]:
        with SessionLocal() as session:
            return list(
                session.query(PipelineVersion)
                .filter(PipelineVersion.pipeline_id == pipeline_id)
                .order_by(PipelineVersion.version_number.desc())
                .all()
            )

    def get_pipeline_version(self, pipeline_id: str, version_id: str) -> PipelineVersion | None:
        with SessionLocal() as session:
            return (
                session.query(PipelineVersion)
                .filter(
                    PipelineVersion.id == version_id,
                    PipelineVersion.pipeline_id == pipeline_id,
                )
                .first()
            )

    def get_latest_pipeline_version(self, pipeline_id: str) -> PipelineVersion | None:
        with SessionLocal() as session:
            return (
                session.query(PipelineVersion)
                .filter(PipelineVersion.pipeline_id == pipeline_id)
                .order_by(PipelineVersion.version_number.desc())
                .first()
            )

    def update_pipeline_version_github_info(self, version_id: str, branch: str, commit_sha: str, pr_url: str | None) -> PipelineVersion | None:
        with SessionLocal() as session:
            version = session.get(PipelineVersion, version_id)
            if version:
                version.github_branch = branch
                version.github_commit_sha = commit_sha
                if pr_url:
                    version.github_pr_url = pr_url
                session.commit()
                session.refresh(version)
                return version
            return None
