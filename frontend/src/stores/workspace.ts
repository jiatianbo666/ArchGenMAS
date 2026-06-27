/** 工作台状态管理 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useWorkspaceStore = defineStore('workspace', () => {
  // 上传的文件信息
  const uploadedFile = ref<{ name: string; content: string; charCount: number } | null>(null)
  // 用户编辑的需求文本
  const requirementText = ref('')
  // 架构风格选择
  const architectureStyle = ref('auto')
  // 最大迭代次数
  const maxIterations = ref(3)
  // 当前项目ID
  const currentProjectId = ref('')

  const hasContent = computed(() => requirementText.value.trim().length > 0)

  function setUploadedFile(file: { name: string; content: string; charCount: number }) {
    uploadedFile.value = file
    requirementText.value = file.content
  }

  function setRequirementText(text: string) {
    requirementText.value = text
    uploadedFile.value = null
  }

  function reset() {
    uploadedFile.value = null
    requirementText.value = ''
    architectureStyle.value = 'auto'
    maxIterations.value = 3
    currentProjectId.value = ''
  }

  return {
    uploadedFile,
    requirementText,
    architectureStyle,
    maxIterations,
    currentProjectId,
    hasContent,
    setUploadedFile,
    setRequirementText,
    reset,
  }
})
