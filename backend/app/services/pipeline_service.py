from fastapi import HTTPException, status

import json
from app.models.pipeline import Pipeline
from app.models.pipeline_node import PipelineNode
from app.models.pipeline_version import PipelineVersion
from app.repositories.pipeline_repository import PipelineRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.pipeline import PipelineCreate, PipelineNodeCreate, PipelineUpdate


class PipelineService:
    """Pipeline service with validation and CRUD orchestration."""

    def __init__(self) -> None:
        self.pipeline_repository = PipelineRepository()
        self.project_repository = ProjectRepository()

    def list_pipelines(self, project_id: str | None = None) -> list[Pipeline]:
        if project_id:
            return self.pipeline_repository.get_pipelines_by_project(project_id)

        return self.pipeline_repository.list_pipelines()

    def get_pipeline(self, pipeline_id: str) -> Pipeline:
        pipeline = self.pipeline_repository.get_pipeline_by_id(pipeline_id)

        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )

        return pipeline

    def create_pipeline(self, payload: PipelineCreate) -> Pipeline:
        name = (payload.name or "").strip()

        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pipeline name is required",
            )

        project_id = (payload.project_id or "").strip()

        if not project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project ID is required",
            )

        project = self.project_repository.get_project_by_id(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        pipeline = Pipeline(
            project_id=project_id,
            name=name,
            description=payload.description,
            version=payload.version or "1",
            status=payload.status or "active",
        )

        return self.pipeline_repository.create_pipeline(pipeline)

    def update_pipeline(
        self,
        pipeline_id: str,
        payload: PipelineUpdate,
    ) -> Pipeline:
        existing_pipeline = self.pipeline_repository.get_pipeline_by_id(
            pipeline_id
        )

        if not existing_pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )

        if payload.name is not None:
            name = (payload.name or "").strip()

            if not name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pipeline name is required",
                )

        if payload.project_id is not None:
            project_id = (payload.project_id or "").strip()

            if not project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Project ID is required",
                )

            project = self.project_repository.get_project_by_id(project_id)

            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found",
                )

        pipeline = Pipeline(
            project_id=(
                payload.project_id
                if payload.project_id is not None
                else existing_pipeline.project_id
            ),
            name=(
                payload.name
                if payload.name is not None
                else existing_pipeline.name
            ),
            description=(
                payload.description
                if payload.description is not None
                else existing_pipeline.description
            ),
            version=(
                payload.version
                if payload.version is not None
                else existing_pipeline.version
            ),
            status=(
                payload.status
                if payload.status is not None
                else existing_pipeline.status
            ),
        )

        return self.pipeline_repository.update_pipeline(
            pipeline_id,
            pipeline,
        )

    def delete_pipeline(self, pipeline_id: str) -> None:
        pipeline = self.pipeline_repository.get_pipeline_by_id(pipeline_id)

        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )

        self.pipeline_repository.delete_pipeline(pipeline_id)

    def list_pipeline_nodes(self, pipeline_id: str) -> list[PipelineNode]:
        pipeline = self.pipeline_repository.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )
        return self.pipeline_repository.list_pipeline_nodes(pipeline_id)

    def get_pipeline_node(
        self,
        pipeline_id: str,
        node_id: str,
    ) -> PipelineNode:
        pipeline = self.pipeline_repository.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )

        node = self.pipeline_repository.get_pipeline_node(pipeline_id, node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline node not found",
            )
        return node

    def create_pipeline_node(
        self,
        pipeline_id: str,
        payload: PipelineNodeCreate,
    ) -> PipelineNode:
        pipeline = self.pipeline_repository.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )

        node_type = (payload.node_type or "").strip()
        if not node_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Node type is required",
            )

        node = PipelineNode(
            node_type=node_type,
            configuration=payload.configuration,
            sequence_index=payload.sequence_index,
            position_x=payload.position_x,
            position_y=payload.position_y,
        )

        return self.pipeline_repository.create_pipeline_node(pipeline_id, node)

    def update_pipeline_node(
        self,
        pipeline_id: str,
        node_id: str,
        payload: PipelineNodeCreate,
    ) -> PipelineNode:
        pipeline = self.pipeline_repository.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )

        existing_node = self.pipeline_repository.get_pipeline_node(pipeline_id, node_id)
        if not existing_node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline node not found",
            )

        node = PipelineNode(
            node_type=payload.node_type if payload.node_type is not None else existing_node.node_type,
            configuration=payload.configuration if payload.configuration is not None else existing_node.configuration,
            sequence_index=payload.sequence_index if payload.sequence_index is not None else existing_node.sequence_index,
            position_x=payload.position_x if payload.position_x is not None else existing_node.position_x,
            position_y=payload.position_y if payload.position_y is not None else existing_node.position_y,
        )

        try:
            return self.pipeline_repository.update_pipeline_node(pipeline_id, node_id, node)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline node not found",
            )

    def delete_pipeline_node(self, pipeline_id: str, node_id: str) -> None:
        pipeline = self.pipeline_repository.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )

        existing_node = self.pipeline_repository.get_pipeline_node(pipeline_id, node_id)
        if not existing_node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline node not found",
            )

        try:
            self.pipeline_repository.delete_pipeline_node(pipeline_id, node_id)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline node not found",
            )

    def create_pipeline_version(self, pipeline_id: str, description: str | None, user_id: str) -> PipelineVersion:
        pipeline = self.pipeline_repository.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )

        nodes = self.pipeline_repository.list_pipeline_nodes(pipeline_id)
        snapshot = []
        for node in nodes:
            snapshot.append({
                "id": node.id,
                "node_type": node.node_type,
                "configuration": node.configuration,
                "sequence_index": node.sequence_index,
                "position_x": node.position_x,
                "position_y": node.position_y,
            })

        latest = self.pipeline_repository.get_latest_pipeline_version(pipeline_id)
        next_num = 1 if not latest else (latest.version_number or 0) + 1

        version = PipelineVersion(
            pipeline_id=pipeline_id,
            version_number=next_num,
            created_by=user_id,
            description=description,
            pipeline_snapshot=json.dumps(snapshot),
        )
        return self.pipeline_repository.create_pipeline_version(version)

    def list_pipeline_versions(self, pipeline_id: str) -> list[PipelineVersion]:
        pipeline = self.pipeline_repository.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )
        return self.pipeline_repository.list_pipeline_versions(pipeline_id)

    def get_pipeline_version(self, pipeline_id: str, version_id: str) -> PipelineVersion:
        pipeline = self.pipeline_repository.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )
        version = self.pipeline_repository.get_pipeline_version(pipeline_id, version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found",
            )
        return version

    def compare_pipeline_versions(self, pipeline_id: str, v1_id: str, v2_id: str) -> list[str]:
        v1 = self.get_pipeline_version(pipeline_id, v1_id)
        v2 = self.get_pipeline_version(pipeline_id, v2_id)

        snap1 = json.loads(v1.pipeline_snapshot or "[]")
        snap2 = json.loads(v2.pipeline_snapshot or "[]")

        dict1 = {n.get("id"): n for n in snap1}
        dict2 = {n.get("id"): n for n in snap2}

        diff = []
        for nid, n2 in dict2.items():
            if nid not in dict1:
                diff.append(f"+ Added node: {n2.get('node_type')}")
            else:
                n1 = dict1[nid]
                if n1.get('configuration') != n2.get('configuration'):
                    diff.append(f"~ Changed configuration for node: {n2.get('node_type')}")
                if n1.get('sequence_index') != n2.get('sequence_index'):
                    diff.append(f"~ Changed sequence for node: {n2.get('node_type')}")

        for nid, n1 in dict1.items():
            if nid not in dict2:
                diff.append(f"- Removed node: {n1.get('node_type')}")

        return diff

    def rollback_pipeline_version(self, pipeline_id: str, version_id: str, user_id: str, rollback_message: str | None = None) -> PipelineVersion:
        version = self.get_pipeline_version(pipeline_id, version_id)

        # Delete existing nodes
        existing_nodes = self.pipeline_repository.list_pipeline_nodes(pipeline_id)
        for node in existing_nodes:
            self.pipeline_repository.delete_pipeline_node(pipeline_id, node.id)

        # Recreate nodes from snapshot
        snapshot = json.loads(version.pipeline_snapshot or "[]")
        for node_data in snapshot:
            new_node = PipelineNode(
                node_type=node_data.get("node_type"),
                configuration=node_data.get("configuration"),
                sequence_index=node_data.get("sequence_index"),
                position_x=node_data.get("position_x"),
                position_y=node_data.get("position_y"),
            )
            self.pipeline_repository.create_pipeline_node(pipeline_id, new_node)

        description = rollback_message or f"Rollback to version {version.version_number}"
        return self.create_pipeline_version(pipeline_id, description, user_id)

    def update_pipeline_version_github_info(self, pipeline_id: str, version_id: str, branch: str, commit_sha: str, pr_url: str | None = None) -> PipelineVersion:
        version = self.pipeline_repository.update_pipeline_version_github_info(version_id, branch, commit_sha, pr_url)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline version not found",
            )
        return version