import apiClient from './client';
import type { Pipeline, PipelineNode, PipelineVersion } from '../types';

export const getPipelines = async (projectId?: string): Promise<Pipeline[]> => {
  const params = projectId ? { project_id: projectId } : {};
  const response = await apiClient.get('/pipelines', { params });
  return response.data;
};

export const getPipeline = async (id: string): Promise<Pipeline> => {
  const response = await apiClient.get(`/pipelines/${id}`);
  return response.data;
};

export const createPipeline = async (data: { project_id: string; name: string; description?: string }): Promise<Pipeline> => {
  const response = await apiClient.post('/pipelines', data);
  return response.data;
};

export const deletePipeline = async (id: string): Promise<void> => {
  await apiClient.delete(`/pipelines/${id}`);
};

export const getPipelineNodes = async (pipelineId: string): Promise<PipelineNode[]> => {
  const response = await apiClient.get(`/pipelines/${pipelineId}/nodes`);
  return response.data;
};

export const createPipelineNode = async (pipelineId: string, data: Partial<PipelineNode>): Promise<PipelineNode> => {
  const response = await apiClient.post(`/pipelines/${pipelineId}/nodes`, data);
  return response.data;
};

export const updatePipelineNode = async (pipelineId: string, nodeId: string, data: Partial<PipelineNode>): Promise<PipelineNode> => {
  const response = await apiClient.put(`/pipelines/${pipelineId}/nodes/${nodeId}`, data);
  return response.data;
};

export const deletePipelineNode = async (pipelineId: string, nodeId: string): Promise<void> => {
  await apiClient.delete(`/pipelines/${pipelineId}/nodes/${nodeId}`);
};

export const getPipelineVersions = async (pipelineId: string): Promise<PipelineVersion[]> => {
  const response = await apiClient.get(`/pipelines/${pipelineId}/versions`);
  return response.data;
};

export const createPipelineVersion = async (pipelineId: string, data: { description?: string }): Promise<PipelineVersion> => {
  const response = await apiClient.post(`/pipelines/${pipelineId}/versions`, data);
  return response.data;
};

export const getPipelineVersionDiff = async (pipelineId: string, v1Id: string, v2Id: string): Promise<string[]> => {
  const response = await apiClient.get(`/pipelines/${pipelineId}/versions/${v1Id}/compare/${v2Id}`);
  return response.data;
};

export const rollbackPipelineVersion = async (pipelineId: string, versionId: string, data: { description?: string }): Promise<PipelineVersion> => {
  const response = await apiClient.post(`/pipelines/${pipelineId}/versions/${versionId}/rollback`, data);
  return response.data;
};

export const pushPipelineVersionToGithub = async (
  pipelineId: string, 
  versionId: string, 
  data: { 
    connection_id: string; 
    branch: string; 
    commit_message: string; 
    create_pr?: boolean; 
    pr_title?: string; 
    pr_base?: string;
  }
): Promise<PipelineVersion> => {
  const response = await apiClient.post(`/pipelines/${pipelineId}/versions/${versionId}/github-push`, data);
  return response.data;
};
