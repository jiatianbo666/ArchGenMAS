/** 流水线 API */
import client from './client'
import type { PipelineRunRequest, PipelineStatus } from '../types'

export async function runPipeline(req: PipelineRunRequest): Promise<{ project_id: string; status: string }> {
  const { data } = await client.post('/pipeline/run', req)
  return data
}

export async function getPipelineStatus(projectId: string): Promise<PipelineStatus> {
  const { data } = await client.get(`/pipeline/${projectId}/status`)
  return data
}
