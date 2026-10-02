import apiClient from './client';
import type { DataSource } from '../types';

export const getDataSources = async (projectId?: string): Promise<DataSource[]> => {
  const params = projectId ? { project_id: projectId } : {};
  const response = await apiClient.get('/data-sources', { params });
  return response.data;
};

export const createDataSource = async (data: any): Promise<DataSource> => {
  const response = await apiClient.post('/data-sources', data);
  return response.data;
};

export const updateDataSource = async (id: string, data: any): Promise<DataSource> => {
  const response = await apiClient.put(`/data-sources/${id}`, data);
  return response.data;
};

export const deleteDataSource = async (id: string): Promise<void> => {
  await apiClient.delete(`/data-sources/${id}`);
};

export const testConnection = async (id: string, connectionDetails?: string): Promise<{ success: boolean; message: string }> => {
  const payload = connectionDetails ? { connection_details: connectionDetails } : {};
  const response = await apiClient.post(`/data-sources/${id}/test-connection`, payload);
  return response.data;
};

export const uploadDataSourceFile = async (id: string, file: File): Promise<DataSource> => {
  const formData = new FormData();
  formData.append('file', file);
  // Do not set Content-Type header manually, let Axios set it with the correct boundary
  const response = await apiClient.post(`/data-sources/${id}/upload`, formData);
  return response.data;
};
