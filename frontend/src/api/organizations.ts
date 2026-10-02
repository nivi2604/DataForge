import apiClient from './client';
import type { Organization } from '../types';

export const getOrganizations = async (): Promise<Organization[]> => {
  const response = await apiClient.get('/organizations');
  return response.data;
};

export const getOrganization = async (id: string): Promise<Organization> => {
  const response = await apiClient.get(`/organizations/${id}`);
  return response.data;
};

export const createOrganization = async (data: { name: string; description?: string }): Promise<Organization> => {
  const response = await apiClient.post('/organizations', data);
  return response.data;
};
