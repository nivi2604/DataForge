import apiClient from './client';

export interface GithubConnectionCreate {
  repository_name: string;
  token: string;
}

export interface GithubConnectionResponse {
  id: string;
  repository_name: string;
  created_at?: string;
}

export interface GithubBranch {
  name: string;
}

export interface GithubPullRequest {
  number: number;
  title: string;
  state: string;
  html_url: string;
  head_branch: string;
  base_branch: string;
  author?: string;
}

export interface PRValidationRecord {
  id: string;
  repository_name?: string;
  pr_number?: string;
  head_branch?: string;
  base_branch?: string;
  commit_sha?: string;
  pr_html_url?: string;
  pipeline_file_path?: string;
  status?: string;
  result_summary?: string;
  failure_reason?: string;
  execution_id?: string;
  created_at?: string;
  updated_at?: string;
}

export const createConnection = async (payload: GithubConnectionCreate): Promise<GithubConnectionResponse> => {
  const response = await apiClient.post('/github/connections', payload);
  return response.data;
};

export const listConnections = async (): Promise<GithubConnectionResponse[]> => {
  const response = await apiClient.get('/github/connections');
  return response.data;
};

export const deleteConnection = async (id: string): Promise<void> => {
  await apiClient.delete(`/github/connections/${id}`);
};

export const listBranches = async (id: string): Promise<GithubBranch[]> => {
  const response = await apiClient.get(`/github/connections/${id}/branches`);
  return response.data;
};

export const listPullRequests = async (id: string): Promise<GithubPullRequest[]> => {
  const response = await apiClient.get(`/github/connections/${id}/pulls`);
  return response.data;
};

export const mergePullRequest = async (id: string, prNumber: number): Promise<void> => {
  await apiClient.post(`/github/connections/${id}/pulls/${prNumber}/merge`);
};

export const closePullRequest = async (id: string, prNumber: number): Promise<void> => {
  await apiClient.post(`/github/connections/${id}/pulls/${prNumber}/close`);
};

export const listPRValidations = async (repositoryName?: string): Promise<PRValidationRecord[]> => {
  const params = repositoryName ? { repository_name: repositoryName } : {};
  const response = await apiClient.get('/github/pr-validations', { params });
  return response.data;
};
