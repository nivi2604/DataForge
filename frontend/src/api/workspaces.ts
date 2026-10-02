import apiClient from './client';
import type { Workspace } from '../types';

export const getWorkspaces = async (organizationId?: string): Promise<Workspace[]> => {
  const params = organizationId ? { organization_id: organizationId } : {};
  const response = await apiClient.get('/workspaces', { params });
  return response.data;
};

export const createWorkspace = async (data: { organization_id: string; name: string; description?: string }): Promise<Workspace> => {
  const response = await apiClient.post('/workspaces', data);
  return response.data;
};
