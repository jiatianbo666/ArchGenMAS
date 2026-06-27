/** 历史记录 API */
import client from './client'

export interface HistoryItem {
  project_id: string
  project_name: string
  filename: string
  content_preview: string
  architecture_style: string
  review_score: number | null
  risk_level: string
  iteration: number
  stage: string
  created_at: string
  updated_at: string
}

export async function getHistory(page = 1, size = 20): Promise<{ total: number; items: HistoryItem[] }> {
  const { data } = await client.get('/history', { params: { page, size } })
  return data
}

export async function deleteHistoryItem(projectId: string): Promise<void> {
  await client.delete(`/history/${projectId}`)
}
