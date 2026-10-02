import apiClient from './client';
import type { ExecutionResponse, ExecutionLogResponse } from '../types';

export const executePipeline = async (pipelineId: string, triggeredBy: string = 'user'): Promise<ExecutionResponse> => {
  const response = await apiClient.post(`/pipelines/${pipelineId}/executions`, { triggered_by: triggeredBy });
  return response.data;
};

export const getExecutionLogs = async (pipelineId: string, executionId: string): Promise<ExecutionLogResponse[]> => {
  const response = await apiClient.get(`/pipelines/${pipelineId}/executions/${executionId}/logs`);
  return response.data;
};

export const listExecutions = async (pipelineId: string): Promise<ExecutionResponse[]> => {
  const response = await apiClient.get(`/pipelines/${pipelineId}/executions`);
  return response.data;
};
