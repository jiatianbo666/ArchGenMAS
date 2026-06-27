/** 流水线执行状态管理 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { PipelineStatus } from '../types'
import { STAGE_LABELS, AGENT_LABELS } from '../types'

export const usePipelineStore = defineStore('pipeline', () => {
  const isRunning = ref(false)
  const projectId = ref('')
  const stage = ref('idle')
  const agentStatuses = ref<Record<string, string>>({})
  const logs = ref<string[]>([])
  const iteration = ref(0)
  const maxIterations = ref(3)
  const error = ref('')

  const stageLabel = computed(() => STAGE_LABELS[stage.value] || stage.value)

  const agentProgress = computed(() => {
    return Object.entries(AGENT_LABELS).map(([key, label]) => ({
      key,
      label,
      status: agentStatuses.value[key] || 'idle',
    }))
  })

  const progressPercent = computed(() => {
    const done = Object.values(agentStatuses.value).filter(s => s === 'done').length
    if (done >= 5) return 100
    if (stage.value === 'done') return 100
    if (stage.value === 'error') return 0
    // 粗略估算
    const stageMap: Record<string, number> = {
      idle: 0,
      parsing: 5,
      validating_requirement: 15,
      designing_architecture: 40,
      reviewing: 60,
      analyzing_risk: 70,
      iterating: 75,
      generating_document: 90,
      done: 100,
    }
    return stageMap[stage.value] || 0
  })

  function updateFromStatus(status: PipelineStatus) {
    projectId.value = status.project_id
    stage.value = status.stage
    agentStatuses.value = status.agent_statuses
    logs.value = status.logs
    iteration.value = status.iteration
    maxIterations.value = status.max_iterations
  }

  function start(pid: string) {
    isRunning.value = true
    projectId.value = pid
    stage.value = 'idle'
    agentStatuses.value = {}
    logs.value = []
    error.value = ''
  }

  function addLog(msg: string) {
    logs.value.push(msg)
  }

  function setStage(s: string) {
    stage.value = s
  }

  function done() {
    isRunning.value = false
    stage.value = 'done'
  }

  function setError(msg: string) {
    isRunning.value = false
    error.value = msg
    stage.value = 'error'
  }

  function reset() {
    isRunning.value = false
    projectId.value = ''
    stage.value = 'idle'
    agentStatuses.value = {}
    logs.value = []
    iteration.value = 0
    error.value = ''
  }

  return {
    isRunning,
    projectId,
    stage,
    agentStatuses,
    logs,
    iteration,
    maxIterations,
    error,
    stageLabel,
    agentProgress,
    progressPercent,
    updateFromStatus,
    start,
    addLog,
    setStage,
    done,
    setError,
    reset,
  }
})
