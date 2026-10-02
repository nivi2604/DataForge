import time
import json
import csv
from pathlib import Path
import pyarrow.parquet as pq
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timezone
from fastapi import HTTPException, status

from app.models.execution_log import ExecutionLog
from app.models.pipeline_execution import PipelineExecution
from app.models.pipeline_node import PipelineNode
from app.repositories.execution_repository import ExecutionRepository
from app.repositories.pipeline_repository import PipelineRepository
from app.repositories.data_source_repository import DataSourceRepository
from app.schemas.execution import ExecutePipelineRequest
from app.services.data_quality_service import DataQualityService
from app.services.github_service import GithubService
from app.schemas.github import GithubCommitCreate
import io


class ExecutionService:
    """Execution service."""

    def __init__(self) -> None:
        self.execution_repository = ExecutionRepository()
        self.pipeline_repository = PipelineRepository()
        self.data_source_repository = DataSourceRepository()

    def execute_pipeline(self, pipeline_id: str, payload: ExecutePipelineRequest, user_id: str = None) -> PipelineExecution:
        pipeline = self.pipeline_repository.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")

        execution = PipelineExecution(
            pipeline_id=pipeline_id,
            status="running",
            triggered_by=payload.triggered_by,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        execution = self.execution_repository.create_execution(execution)

        self._log(execution.id, None, "INFO", "Execution started")

        nodes = self.pipeline_repository.list_pipeline_nodes(pipeline_id)
        nodes = sorted(nodes, key=lambda n: n.sequence_index or 0)

        supported_types = {"extract", "transform", "load", "data_quality"}

        def with_retries(func, *args, **kwargs):
            max_attempts = 3
            last_err = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    time.sleep(1 * (attempt + 1))
            raise last_err

        try:
            data = None
            for node in nodes:
                node_type = (node.node_type or "").lower()
                self._log(execution.id, node.id, "INFO", f"Node started: {node_type}")

                if node_type not in supported_types:
                    e = ValueError(f"Unsupported node type: {node_type}")
                    e.node_id = node.id
                    raise e

                try:
                    if node_type == "extract":
                        data = with_retries(self._execute_extract, node, execution.id, user_id)
                        rows_processed = len(data) if data else 0
                        self._log(execution.id, node.id, "INFO", f"Extracted {rows_processed} rows")
                    elif node_type == "transform":
                        data = self._execute_transform(node, execution.id, data, user_id)
                        rows_processed = len(data) if data else 0
                        self._log(execution.id, node.id, "INFO", f"Transformed {rows_processed} rows")
                    elif node_type == "data_quality":
                        result = self._execute_data_quality(node, execution.id, data)
                        self._log(execution.id, node.id, "INFO", result)
                    elif node_type == "load":
                        with_retries(self._execute_load, node, execution.id, data, user_id)
                        rows_processed = len(data) if data else 0
                        self._log(execution.id, node.id, "INFO", f"Loaded {rows_processed} rows")
                except Exception as e:
                    e.node_id = node.id
                    raise e

                self._log(execution.id, node.id, "INFO", f"Node completed: {node_type}")

            execution.status = "completed"
            self._log(execution.id, None, "INFO", "Execution completed")

        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            self._log(execution.id, getattr(e, 'node_id', None), "ERROR", f"Execution failed: {str(e)}")

        execution.completed_at = datetime.now(timezone.utc).isoformat()

        started = datetime.fromisoformat(execution.started_at)
        completed = datetime.fromisoformat(execution.completed_at)
        execution.duration = int((completed - started).total_seconds())

        return self.execution_repository.update_execution(execution.id, execution)

    def list_executions(self, pipeline_id: str | None = None) -> list[PipelineExecution]:
        return self.execution_repository.list_executions(pipeline_id)

    def get_execution(self, execution_id: str) -> PipelineExecution:
        execution = self.execution_repository.get_execution(execution_id)
        if not execution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
        return execution

    def get_execution_logs(self, pipeline_id: str, execution_id: str) -> list[ExecutionLog]:
        pipeline = self.pipeline_repository.get_pipeline_by_id(pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")

        execution = self.execution_repository.get_execution(execution_id)
        if not execution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

        if execution.pipeline_id != pipeline_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Execution does not belong to this pipeline")

        return self.execution_repository.get_execution_logs(execution_id)

    def cancel_execution(self, execution_id: str) -> PipelineExecution:
        raise NotImplementedError

    def _log(self, execution_id: str, pipeline_node_id: str | None, level: str, message: str) -> None:
        log = ExecutionLog(
            execution_id=execution_id,
            pipeline_node_id=pipeline_node_id,
            level=level,
            message=message,
        )
        self.execution_repository.create_execution_log(log)

    def _execute_extract(self, node: PipelineNode, execution_id: str, user_id: str = None) -> list[dict]:
        config = json.loads(node.configuration or "{}")
        ds_id = config.get("data_source_id")
        if not ds_id:
            raise ValueError("Extract node missing data_source_id configuration")

        ds = self.data_source_repository.get_data_source_by_id(ds_id)
        if not ds:
            raise ValueError(f"Data source {ds_id} not found")

        conn_details = json.loads(ds.connection_details or "{}")

        if ds.type == "CSV":
            path = conn_details.get("path")
            if not path or not Path(path).is_file():
                raise ValueError(f"Invalid or missing CSV path in data source {ds_id}")
            with open(path, mode='r', encoding='utf-8') as f:
                return list(csv.DictReader(f))

        elif ds.type == "JSON":
            path = conn_details.get("path")
            if not path or not Path(path).is_file():
                raise ValueError(f"Invalid or missing JSON path in data source {ds_id}")
            with open(path, mode='r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("JSON data must be a list of objects")
                return data

        elif ds.type == "Parquet":
            path = conn_details.get("path")
            if not path or not Path(path).is_file():
                raise ValueError(f"Invalid or missing Parquet path in data source {ds_id}")
            df = pd.read_parquet(path)
            return df.to_dict(orient="records")

        elif ds.type == "PostgreSQL":
            host = conn_details.get("host")
            port = conn_details.get("port", 5432)
            db = conn_details.get("database")
            user = conn_details.get("username")
            pw = conn_details.get("password")
            table = conn_details.get("table")

            if not all([host, db, user, pw, table]):
                raise ValueError("Missing PostgreSQL connection details or table")

            engine = create_engine(f"postgresql://{user}:{pw}@{host}:{port}/{db}")

            query_parts = []
            params = {}

            import re

            select_cols = config.get("sql_select", "*")
            if not select_cols or not re.match(r'^[\w\s,.*()]+$', str(select_cols)):
                select_cols = "*"
            query_parts.append(f"SELECT {select_cols}")

            # Simple sanitization for table names
            if not re.match(r'^[a-zA-Z0-9_]+$', table):
                raise ValueError("Invalid table name")
            query_parts.append(f"FROM {table}")

            join_table = config.get("sql_join_table")
            if join_table and re.match(r'^[a-zA-Z0-9_]+$', str(join_table)):
                join_type = config.get("sql_join_type", "INNER")
                left_col = config.get("sql_join_left")
                right_col = config.get("sql_join_right")
                if left_col and right_col and re.match(r'^[\w.]+$', str(left_col)) and re.match(r'^[\w.]+$', str(right_col)):
                    query_parts.append(f"{join_type} JOIN {join_table} ON {left_col} = {right_col}")

            where_col = config.get("sql_where_col")
            where_op = config.get("sql_where_op")
            where_val = config.get("sql_where_val")
            if where_col and where_op and where_val is not None and str(where_val).strip() != "":
                if re.match(r'^[\w.]+$', str(where_col)) and where_op in ['=', '!=', '>', '<', '>=', '<=', 'LIKE']:
                    query_parts.append(f"WHERE {where_col} {where_op} :where_val")
                    params["where_val"] = where_val

            group_by = config.get("sql_group_by")
            if group_by and re.match(r'^[\w\s,.]+$', str(group_by)):
                query_parts.append(f"GROUP BY {group_by}")

                having_col = config.get("sql_having_col")
                having_op = config.get("sql_having_op")
                having_val = config.get("sql_having_val")
                if having_col and having_op and having_val is not None and str(having_val).strip() != "":
                    if re.match(r'^[\w.()]+$', str(having_col)) and having_op in ['=', '!=', '>', '<', '>=', '<=']:
                        query_parts.append(f"HAVING {having_col} {having_op} :having_val")
                        params["having_val"] = having_val

            order_by = config.get("sql_order_by")
            if order_by and re.match(r'^[\w\s,.]+$', str(order_by)):
                query_parts.append(f"ORDER BY {order_by}")

            limit = config.get("sql_limit")
            if limit and str(limit).isdigit():
                query_parts.append(f"LIMIT {int(limit)}")

            query_str = " ".join(query_parts)
            self._log(execution_id, node.id, "INFO", f"Executing SQL: {query_str}")

            with engine.connect() as conn:
                result = conn.execute(text(query_str), params)
                return [dict(row._mapping) for row in result]

        elif ds.type == "GitHub":
            conn_id = conn_details.get("connection_id")
            branch = conn_details.get("branch")
            file_path = conn_details.get("file_path")

            if not all([conn_id, branch, file_path]):
                raise ValueError("Missing GitHub connection details (connection_id, branch, file_path)")

            if not user_id:
                raise ValueError("User context required to access GitHub data source")

            gh_service = GithubService()
            content = gh_service.fetch_file_content(user_id, conn_id, file_path, branch)

            # parse content
            if file_path.endswith(".csv"):
                reader = csv.DictReader(io.StringIO(content))
                return list(reader)
            elif file_path.endswith(".json"):
                data = json.loads(content)
                if not isinstance(data, list):
                    raise ValueError("JSON data from GitHub must be a list of objects")
                return data
            else:
                raise ValueError("Unsupported GitHub file extension (only .csv, .json supported)")

        else:
            raise ValueError(f"Unsupported extraction source type: {ds.type}")

    def _execute_transform(self, node: PipelineNode, execution_id: str, data: list[dict] | None, user_id: str = None) -> list[dict]:
        if data is None:
            raise ValueError("No data to transform")

        config = json.loads(node.configuration or "{}")
        operation = config.get("operation")

        if not operation:
            raise ValueError("Transform node missing 'operation' in configuration")

        self._log(execution_id, node.id, "INFO",
                  f"Transform [{operation}] starting on {len(data)} rows")

        # ── Relational operations: handled in-service (need _execute_extract) ──
        if operation in ("inner_join", "left_join", "right_join", "full_join", "merge"):
            return self._execute_join(node, execution_id, data, user_id, operation, config)

        # ── All other operations: delegate to the transformation registry ──
        from app.services.transformation_registry import get_transform
        handler = get_transform(operation)
        if handler is None:
            raise ValueError(
                f"Unsupported transform operation: '{operation}'. "
                f"Run GET /transforms to see available operations."
            )

        try:
            result = handler(data, config)
        except NotImplementedError:
            # Registry stubs for relational ops should never reach here,
            # but guard defensively
            raise ValueError(f"Operation '{operation}' requires special execution context")

        self._log(execution_id, node.id, "INFO",
                  f"Transform [{operation}] produced {len(result)} rows")
        return result

    def _execute_join(
        self,
        node: PipelineNode,
        execution_id: str,
        data: list[dict],
        user_id: str | None,
        operation: str,
        config: dict,
    ) -> list[dict]:
        """Handle join/merge operations that need to fetch a second data source."""
        import pandas as pd

        right_source = config.get("right_source")
        left_key = config.get("left_key")
        right_key = config.get("right_key")

        if not all([right_source, left_key, right_key]):
            raise ValueError(
                f"[{operation}] requires 'right_source', 'left_key', and 'right_key'"
            )

        # Fetch right-hand data by re-using extract logic with a temporary node
        temp_node = PipelineNode(
            id="__temp_join__",
            pipeline_id=node.pipeline_id,
            node_type="extract",
            configuration=json.dumps({"data_source_id": right_source}),
            sequence_index=-1,
        )
        right_data = self._execute_extract(temp_node, execution_id, user_id)
        self._log(execution_id, node.id, "INFO",
                  f"[{operation}] Fetched {len(right_data)} rows from right source")

        if not right_data:
            if operation in ("left_join", "full_join"):
                return data
            return []

        left_df = pd.DataFrame(data)
        right_df = pd.DataFrame(right_data)

        # Determine pandas how parameter
        how_map = {
            "inner_join": "inner",
            "left_join": "left",
            "right_join": "right",
            "full_join": "outer",
            "merge": config.get("how", "left"),
        }
        how = how_map.get(operation, "inner")

        merged = pd.merge(left_df, right_df, left_on=left_key, right_on=right_key, how=how)
        merged = merged.where(pd.notnull(merged), None)
        result = merged.to_dict(orient="records")
        self._log(execution_id, node.id, "INFO",
                  f"[{operation}] Produced {len(result)} rows after join")
        return result

    def _execute_transform_LEGACY_UNUSED(self, node: PipelineNode, execution_id: str, data: list[dict] | None, user_id: str = None) -> list[dict]:
        """LEGACY: kept for reference only — all logic has moved to registry."""
        if data is None:
            raise ValueError("No data to transform")

        config = json.loads(node.configuration or "{}")
        operation = config.get("operation")

        if operation == "drop_nulls":
            return [row for row in data if all(v is not None and str(v).strip() != "" for v in row.values())]
        elif operation == "select_columns":
            columns = config.get("columns", [])
            if not columns:
                raise ValueError("select_columns operation requires 'columns' list")
            return [{k: row[k] for k in columns if k in row} for row in data]
        elif operation == "remove_duplicates":
            columns = config.get("columns")
            if not isinstance(columns, list) or len(columns) == 0:
                columns = None

            seen = set()
            new_data = []
            for row in data:
                if columns:
                    key = tuple(row.get(c) for c in columns)
                else:
                    # Convert to immutable tuple of items for hashing.
                    # We sort the items to ensure consistent ordering.
                    # Handle unhashable types like lists or dicts by coercing to str
                    try:
                        key = tuple(sorted((k, v if isinstance(v, (int, float, str, bool, type(None))) else str(v)) for k, v in row.items()))
                    except TypeError:
                        key = str(row)

                if key not in seen:
                    seen.add(key)
                    new_data.append(row)
            return new_data
        elif operation == "fill_missing":
            column = config.get("column")
            value = config.get("value")
            if not column:
                raise ValueError("fill_missing operation requires 'column'")

            for row in data:
                if row.get(column) is None or str(row.get(column)).strip() == "":
                    row[column] = value
            return data
        elif operation == "standardize_values":
            column = config.get("column")
            mapping = config.get("mapping")
            if not column or mapping is None:
                raise ValueError("standardize_values operation requires 'column' and 'mapping'")

            for row in data:
                val = str(row.get(column)) if row.get(column) is not None else None
                if val in mapping:
                    row[column] = mapping[val]
                elif row.get(column) in mapping:
                    row[column] = mapping[row.get(column)]
            return data
        elif operation == "filter":
            column = config.get("column")
            operator = config.get("operator")
            value = config.get("value")
            if not all([column, operator, value is not None]):
                raise ValueError("filter operation requires 'column', 'operator', and 'value'")
            new_data = []
            for row in data:
                val = row.get(column)
                if val is None:
                    continue
                match = False
                try:
                    if operator == "==": match = str(val) == str(value)
                    elif operator == "!=": match = str(val) != str(value)
                    elif operator == ">": match = float(val) > float(value)
                    elif operator == "<": match = float(val) < float(value)
                    elif operator == ">=": match = float(val) >= float(value)
                    elif operator == "<=": match = float(val) <= float(value)
                    elif operator == "contains": match = str(value) in str(val)
                except ValueError:
                    pass # ignore cast errors for numeric comparisons
                if match:
                    new_data.append(row)
            return new_data
        elif operation == "rename_column":
            old_name = config.get("old_name")
            new_name = config.get("new_name")
            if not all([old_name, new_name]):
                raise ValueError("rename_column operation requires 'old_name' and 'new_name'")
            for row in data:
                if old_name in row:
                    row[new_name] = row.pop(old_name)
            return data
        elif operation == "drop_columns":
            columns = config.get("columns", [])
            if isinstance(columns, str):
                columns = [c.strip() for c in columns.split(",") if c.strip()]
            if not columns:
                raise ValueError("drop_columns operation requires 'columns' list")
            for row in data:
                for col in columns:
                    row.pop(col, None)
            return data
        elif operation == "cast_type":
            column = config.get("column")
            target_type = config.get("target_type")
            if not all([column, target_type]):
                raise ValueError("cast_type operation requires 'column' and 'target_type'")
            for row in data:
                val = row.get(column)
                if val is not None:
                    try:
                        if target_type == "int": row[column] = int(float(val))
                        elif target_type == "float": row[column] = float(val)
                        elif target_type == "str": row[column] = str(val)
                        elif target_type == "bool": row[column] = str(val).lower() in ("true", "1", "yes", "y", "t")
                    except ValueError:
                        row[column] = None
            return data
        elif operation in ["inner_join", "left_join", "right_join"]:
            right_source = config.get("right_source")
            left_key = config.get("left_key")
            right_key = config.get("right_key")

            if not all([right_source, left_key, right_key]):
                raise ValueError(f"{operation} operation requires 'right_source', 'left_key', and 'right_key'")

            temp_node = PipelineNode(
                id="temp_merge",
                pipeline_id=node.pipeline_id,
                node_type="extract",
                configuration=json.dumps({"data_source_id": right_source}),
                sequence_index=-1
            )
            right_data = self._execute_extract(temp_node, execution_id, user_id)

            if not right_data:
                return data if operation == "left_join" else []

            left_df = pd.DataFrame(data)
            right_df = pd.DataFrame(right_data)

            how = operation.split("_")[0]
            merged_df = pd.merge(left_df, right_df, left_on=left_key, right_on=right_key, how=how)
            merged_df = merged_df.where(pd.notnull(merged_df), None)
            return merged_df.to_dict(orient="records")
        elif operation in ["group_by", "count", "sum", "avg", "min", "max"]:
            group_columns = config.get("group_columns")
            if isinstance(group_columns, str):
                group_columns = [c.strip() for c in group_columns.split(",") if c.strip()]
            agg_column = config.get("agg_column")
            if not group_columns:
                raise ValueError(f"{operation} operation requires 'group_columns'")

            df = pd.DataFrame(data)
            for col in group_columns:
                if col not in df.columns:
                    raise ValueError(f"group_column '{col}' not found")

            if operation != "group_by":
                if not agg_column:
                    raise ValueError(f"{operation} requires 'agg_column'")
                if agg_column not in df.columns:
                    raise ValueError(f"agg_column '{agg_column}' not found")

                if operation in ["sum", "avg", "min", "max"]:
                    df[agg_column] = pd.to_numeric(df[agg_column], errors='coerce')

                if operation == "count":
                    grouped = df.groupby(group_columns, as_index=False)[agg_column].count()
                elif operation == "sum":
                    grouped = df.groupby(group_columns, as_index=False)[agg_column].sum()
                elif operation == "avg":
                    grouped = df.groupby(group_columns, as_index=False)[agg_column].mean()
                elif operation == "min":
                    grouped = df.groupby(group_columns, as_index=False)[agg_column].min()
                elif operation == "max":
                    grouped = df.groupby(group_columns, as_index=False)[agg_column].max()
            else:
                df['__count'] = 1
                grouped = df.groupby(group_columns, as_index=False)['__count'].sum()

            grouped = grouped.where(pd.notnull(grouped), None)
            return grouped.to_dict(orient="records")
        elif operation == "merge":
            right_source = config.get("right_source")
            left_key = config.get("left_key")
            right_key = config.get("right_key")
            how = config.get("how", "left")

            if not all([right_source, left_key, right_key]):
                raise ValueError("merge operation requires 'right_source', 'left_key', and 'right_key'")

            # Create a temporary PipelineNode for extraction
            temp_node = PipelineNode(
                id="temp_merge",
                pipeline_id=node.pipeline_id,
                node_type="extract",
                configuration=json.dumps({"data_source_id": right_source}),
                sequence_index=-1
            )
            right_data = self._execute_extract(temp_node, execution_id, user_id)

            if not right_data:
                return data

            left_df = pd.DataFrame(data)
            right_df = pd.DataFrame(right_data)

            merged_df = pd.merge(left_df, right_df, left_on=left_key, right_on=right_key, how=how)

            # Replace NaN/NaT with None so it translates back to JSON cleanly
            merged_df = merged_df.where(pd.notnull(merged_df), None)

            return merged_df.to_dict(orient="records")
        else:
            raise ValueError(f"Unsupported transform operation: {operation}")

    def _execute_load(self, node: PipelineNode, execution_id: str, data: list[dict] | None, user_id: str = None) -> None:
        if not data:
            self._log(execution_id, node.id, "INFO", "No data to load")
            return

        config = json.loads(node.configuration or "{}")
        ds_id = config.get("data_source_id")
        if not ds_id:
            raise ValueError("Load node missing data_source_id configuration")

        ds = self.data_source_repository.get_data_source_by_id(ds_id)
        if not ds:
            raise ValueError(f"Data source {ds_id} not found")

        conn_details = json.loads(ds.connection_details or "{}")

        if ds.type == "CSV":
            path = conn_details.get("path")
            if not path:
                raise ValueError(f"Missing CSV path in target data source {ds_id}")
            with open(path, mode='w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)

        elif ds.type == "JSON":
            path = conn_details.get("path")
            if not path:
                raise ValueError(f"Missing JSON path in target data source {ds_id}")
            with open(path, mode='w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

        elif ds.type == "Parquet":
            path = conn_details.get("path")
            if not path:
                raise ValueError(f"Missing Parquet path in target data source {ds_id}")
            df = pd.DataFrame(data)
            df.to_parquet(path, index=False)

        elif ds.type == "PostgreSQL":
            host = conn_details.get("host")
            port = conn_details.get("port", 5432)
            db = conn_details.get("database")
            user = conn_details.get("username")
            pw = conn_details.get("password")
            table = conn_details.get("table")

            if not all([host, db, user, pw, table]):
                raise ValueError("Missing PostgreSQL connection details or table")

            engine = create_engine(f"postgresql://{user}:{pw}@{host}:{port}/{db}")
            df = pd.DataFrame(data)
            df.to_sql(table, engine, if_exists='replace', index=False)

        elif ds.type == "GitHub":
            conn_id = conn_details.get("connection_id")
            branch = conn_details.get("branch")
            file_path = conn_details.get("file_path")

            if not all([conn_id, branch, file_path]):
                raise ValueError("Missing GitHub connection details (connection_id, branch, file_path)")

            if not user_id:
                raise ValueError("User context required to access GitHub data source")

            gh_service = GithubService()

            if file_path.endswith(".csv"):
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
                content = output.getvalue()
            elif file_path.endswith(".json"):
                content = json.dumps(data, indent=2)
            else:
                raise ValueError("Unsupported GitHub file extension (only .csv, .json supported)")

            from app.schemas.github import GithubPullRequestCreate

            pr_branch = f"output-pr-{execution_id[:8]}"

            # 1. Create a new branch off of the specified base branch
            gh_service.create_branch(user_id, conn_id, new_branch=pr_branch, base_branch=branch)

            # 2. Push the file to the new branch
            commit_payload = GithubCommitCreate(
                branch=pr_branch,
                file_path=file_path,
                message=f"DataForge pipeline execution {execution_id}",
                content=content
            )
            gh_service.create_commit(user_id, conn_id, commit_payload)

            # 3. Create the Pull Request
            pr_payload = GithubPullRequestCreate(
                title=f"DataForge Output: {execution_id}",
                head=pr_branch,
                base=branch,
                body=f"Automated output delivery from pipeline execution `{execution_id}`."
            )
            pr = gh_service.create_pull_request(user_id, conn_id, pr_payload)
            self._log(execution_id, node.id, "INFO", f"Created PR #{pr.number}: {pr.html_url}")

        else:
            raise ValueError(f"Unsupported load destination type: {ds.type}")

    def _execute_data_quality(self, node: PipelineNode, execution_id: str, data: list[dict] | None) -> str:
        config = json.loads(node.configuration or "{}")

        required_columns = config.get("required_columns")
        email_column = config.get("email_column")
        type_validation = config.get("type_validation")

        unique_columns = config.get("unique_columns")
        range_validation = config.get("range_validation")
        allowed_values = config.get("allowed_values")
        pattern_validation = config.get("pattern_validation")
        schema = config.get("schema")

        result_dict = DataQualityService.compute_quality(
            data,
            required_columns=required_columns,
            email_column=email_column,
            type_validation=type_validation,
            unique_columns=unique_columns,
            range_validation=range_validation,
            allowed_values=allowed_values,
            pattern_validation=pattern_validation,
            schema=schema,
        )
        summary = DataQualityService.format_quality_result(result_dict)
        # Log individual check results for transparency
        for check_name, check_result in result_dict.get("checks", {}).items():
            level = "INFO" if check_result["passed"] else "WARN"
            self._log(execution_id, node.id, level,
                      f"Quality check [{check_name}]: {check_result['detail']}")
        return summary
