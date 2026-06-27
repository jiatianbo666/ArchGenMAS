/** 结果展示状态管理 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ProjectResult } from '../types'

export const useResultStore = defineStore('result', () => {
  const result = ref<ProjectResult | null>(null)
  const loading = ref(false)
  const activeTab = ref('c4')

  function setResult(data: ProjectResult) {
    result.value = data
  }

  function setLoading(val: boolean) {
    loading.value = val
  }

  function setActiveTab(tab: string) {
    activeTab.value = tab
  }

  function reset() {
    result.value = null
    loading.value = false
    activeTab.value = 'c4'
  }

  return {
    result,
    loading,
    activeTab,
    setResult,
    setLoading,
    setActiveTab,
    reset,
  }
})
