import apiClient from './client';
import type { ScheduleResponse } from '../types';

export const getSchedules = async (pipelineId: string): Promise<ScheduleResponse[]> => {
  const response = await apiClient.get(`/pipelines/${pipelineId}/schedules`);
  return response.data;
};

export const createSchedule = async (pipelineId: string, data: { schedule_expression: string; enabled: boolean }): Promise<ScheduleResponse> => {
  const response = await apiClient.post(`/pipelines/${pipelineId}/schedules`, data);
  return response.data;
};

export const updateSchedule = async (pipelineId: string, scheduleId: string, data: { schedule_expression?: string; enabled?: boolean }): Promise<ScheduleResponse> => {
  const response = await apiClient.put(`/pipelines/${pipelineId}/schedules/${scheduleId}`, data);
  return response.data;
};

export const deleteSchedule = async (pipelineId: string, scheduleId: string): Promise<void> => {
  await apiClient.delete(`/pipelines/${pipelineId}/schedules/${scheduleId}`);
};
