export interface Organization {
  id: string;
  name: string;
  description?: string;
  owner_id?: string;
  created_at?: string;
}

export interface Workspace {
  id: string;
  organization_id?: string;
  name: string;
  description?: string;
  created_at?: string;
}

export interface Project {
  id: string;
  workspace_id?: string;
  name: string;
  description?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Pipeline {
  id: string;
  project_id?: string;
  name: string;
  description?: string;
  version?: number;
  status?: string;
  created_at?: string;
  updated_at?: string;
}

export interface PipelineNode {
  id: string;
  pipeline_id?: string;
  node_type: string;
  configuration?: string;
  sequence_index?: number;
  position_x?: number;
  position_y?: number;
}

export interface ExecutionResponse {
  id: string;
  pipeline_id?: string;
  status?: string;
  started_at?: string;
  completed_at?: string;
  duration?: number;
  triggered_by?: string;
  error_message?: string;
  created_at?: string;
}

export interface ExecutionLogResponse {
  id: string;
  execution_id?: string;
  level?: string;
  message?: string;
  timestamp?: string;
}

export interface DataSource {
  id: string;
  project_id?: string;
  name: string;
  type: string;
  connection_details?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ScheduleResponse {
  id: string;
  pipeline_id?: string;
  schedule_expression?: string;
  enabled?: boolean;
  next_run_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface PipelineVersion {
  id: string;
  pipeline_id?: string;
  version_number?: number;
  created_by?: string;
  description?: string;
  pipeline_snapshot?: string;
  created_at?: string;
  github_branch?: string;
  github_commit_sha?: string;
  github_pr_url?: string;
}
