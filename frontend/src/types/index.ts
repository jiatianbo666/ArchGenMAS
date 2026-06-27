/** 全局 TypeScript 类型定义 */

export interface UploadResult {
  file_id: string
  filename: string
  content_preview: string
  content_full: string
  char_count: number
  status: string
}

export interface PipelineRunRequest {
  content: string
  filename: string
  architecture_style: string
  max_iterations: number
}

export interface PipelineStatus {
  project_id: string
  stage: string
  agent_statuses: Record<string, string>
  iteration: number
  max_iterations: number
  logs: string[]
  created_at: string
  updated_at: string
}

export interface C4PlantUML {
  context: string
  container: string
  component: string
  code?: string
}

export interface ViewsPlantUML {
  logical: string
  development: string
  process: string
  physical: string
  scenario: string
}

export interface ViewSummary {
  title: string
  description: string
  diagram_type: string
  element_count: number
  plantuml: string
}

export interface RiskDisplayItem {
  id: string
  dimension: string
  dimension_label: string
  risk_level: string
  risk_color: string
  description: string
  impact: string
  mitigation: string
}

export interface ProjectResult {
  project_id: string
  stage: string
  created_at: string
  updated_at: string
  validation?: any
  architecture?: {
    style: string
    style_rationale: string
    tech_stack: Record<string, string>
    tech_plan: string
    c4_plantuml: C4PlantUML
    views_plantuml: ViewsPlantUML
    views_summary: Record<string, ViewSummary>
  }
  review?: {
    overall_score: number
    issues: any[]
    suggestions: string[]
    requires_revision: boolean
  }
  risk?: {
    overall_risk_level: string
    risks: any[]
    summary: string
    risk_items_display: RiskDisplayItem[]
    count_by_level: Record<string, number>
    count_by_dimension: Record<string, number>
  }
  logs: string[]
}

export interface ProjectSummary {
  project_id: string
  stage: string
  project_name: string
  architecture_style: string
  review_score: number | null
  risk_level: string | null
  iteration: number
  created_at: string
}

export interface HistoryItem {
  project_id: string
  project_name: string
  created_at: string
  status: string
}

// Agent 名称映射
export const AGENT_LABELS: Record<string, string> = {
  requirement: '需求校验 Agent',
  architecture: '架构设计 Agent',
  review: '评审纠错 Agent',
  risk: '风险检测 Agent',
  document: '文档生成 Agent',
}

export const STAGE_LABELS: Record<string, string> = {
  idle: '空闲',
  parsing: '解析文档',
  validating_requirement: '校验需求',
  designing_architecture: '设计架构',
  reviewing: '评审中',
  analyzing_risk: '风险检测',
  iterating: '迭代优化',
  generating_document: '生成文档',
  done: '完成',
  error: '出错',
}
