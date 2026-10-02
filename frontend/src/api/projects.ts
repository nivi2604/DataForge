import apiClient from './client';
import type { Project } from '../types';

export const getProjects = async (workspaceId?: string): Promise<Project[]> => {
  const params = workspaceId ? { workspace_id: workspaceId } : {};
  const response = await apiClient.get('/projects', { params });
  return response.data;
};

export const createProject = async (data: { workspace_id: string; name: string; description?: string }): Promise<Project> => {
  const response = await apiClient.post('/projects', data);
  return response.data;
};
