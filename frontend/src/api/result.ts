/** 结果查询 API */
import client from './client'
import type { ProjectResult, ProjectSummary } from '../types'

export async function getResult(projectId: string): Promise<ProjectResult> {
  const { data } = await client.get(`/result/${projectId}`)
  return data
}

export async function getResultSummary(projectId: string): Promise<ProjectSummary> {
  const { data } = await client.get(`/result/${projectId}/summary`)
  return data
}

export function getExportPdfUrl(projectId: string): string {
  return `/api/export/${projectId}/pdf`
}

export function getExportMdUrl(projectId: string): string {
  return `/api/export/${projectId}/markdown`
}
