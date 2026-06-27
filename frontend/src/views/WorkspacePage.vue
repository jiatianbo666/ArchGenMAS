<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useWorkspaceStore } from '../stores/workspace'
import { usePipelineStore } from '../stores/pipeline'
import { uploadFile } from '../api/upload'
import { runPipeline, getPipelineStatus } from '../api/pipeline'
import type { UploadFile } from 'element-plus'

const router = useRouter()
const workspace = useWorkspaceStore()
const pipeline = usePipelineStore()

const uploading = ref(false)
const starting = ref(false)
const pollingTimer = ref<ReturnType<typeof setInterval> | null>(null)

// 架构风格选项
const styleOptions = [
  { value: 'auto', label: '自动选择（推荐）' },
  { value: 'microservices', label: '微服务架构' },
  { value: 'monolith', label: '单体架构' },
  { value: 'layered', label: '分层架构' },
  { value: 'event_driven', label: '事件驱动架构' },
  { value: 'pipeline', label: '管道过滤器架构' },
]

// 处理文件上传
async function handleFileChange(file: UploadFile) {
  if (!file.raw) return
  uploading.value = true
  try {
    const result = await uploadFile(file.raw)
    workspace.setUploadedFile({
      name: result.filename,
      content: result.content_full,
      charCount: result.char_count,
    })
    ElMessage.success(`文件解析成功，共 ${result.char_count} 个字符`)
  } catch (e: any) {
    ElMessage.error(e.message || '文件解析失败')
  } finally {
    uploading.value = false
  }
}

// 启动生成
async function startGeneration() {
  if (!workspace.hasContent) {
    ElMessage.warning('请先上传需求文档或输入需求描述')
    return
  }
  starting.value = true
  pipeline.reset()

  try {
    const resp = await runPipeline({
      content: workspace.requirementText,
      filename: workspace.uploadedFile?.name || '',
      architecture_style: workspace.architectureStyle,
      max_iterations: workspace.maxIterations,
    })
    workspace.currentProjectId = resp.project_id
    pipeline.start(resp.project_id)

    // 写入历史记录
    saveToHistory(resp.project_id, workspace.requirementText)

    ElMessage.success('流水线已启动，正在执行...')

    // 轮询状态
    startPolling(resp.project_id)
  } catch (e: any) {
    ElMessage.error(e.message || '启动失败')
    starting.value = false
  }
}

// 轮询流水线状态
function startPolling(projectId: string) {
  pollingTimer.value = setInterval(async () => {
    try {
      const status = await getPipelineStatus(projectId)
      pipeline.updateFromStatus(status)

      if (status.stage === 'done') {
        stopPolling()
        pipeline.done()
        // 更新历史记录
        updateHistory(projectId, { stage: 'done' })
        ElMessage.success('架构生成完毕！')
        // 跳转到结果页
        setTimeout(() => {
          router.push(`/result/${projectId}`)
        }, 500)
      } else if (status.stage === 'error') {
        stopPolling()
        pipeline.setError('流水线执行出错，请查看日志')
        ElMessage.error('流水线执行出错')
      }
    } catch {
      // 静默处理轮询错误
    }
  }, 1500)
}

function stopPolling() {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
  starting.value = false
}

// 保存到历史记录（localStorage）
function saveToHistory(projectId: string, content: string) {
  try {
    const raw = localStorage.getItem('archgenmas_history')
    const items = raw ? JSON.parse(raw) : []
    const firstLine = content.trim().split('\n')[0] || '未命名项目'
    const name = firstLine.replace(/^[#\-\*【】\s]+/, '').slice(0, 50) || '未命名项目'
    if (!items.find((i: any) => i.project_id === projectId)) {
      items.unshift({
        project_id: projectId,
        project_name: name,
        architecture_style: '',
        review_score: null,
        risk_level: null,
        iteration: 0,
        stage: 'running',
        created_at: new Date().toISOString(),
      })
      if (items.length > 20) items.pop()
      localStorage.setItem('archgenmas_history', JSON.stringify(items))
    }
  } catch { /* ignore */ }
}

function updateHistory(projectId: string, updates: Record<string, any>) {
  try {
    const raw = localStorage.getItem('archgenmas_history')
    const items = raw ? JSON.parse(raw) : []
    const idx = items.findIndex((i: any) => i.project_id === projectId)
    if (idx >= 0) {
      items[idx] = { ...items[idx], ...updates }
      localStorage.setItem('archgenmas_history', JSON.stringify(items))
    }
  } catch { /* ignore */ }
}

// 跳转到结果页
function goResult() {
  if (pipeline.projectId) {
    router.push(`/result/${pipeline.projectId}`)
  }
}

// Agent 状态颜色
function statusColor(status: string) {
  return { idle: '#909399', running: '#409EFF', done: '#67C23A', error: '#F56C6C' }[status] || '#909399'
}
function statusIcon(status: string) {
  return { idle: 'Clock', running: 'Loading', done: 'CircleCheckFilled', error: 'CircleCloseFilled' }[status] || 'QuestionFilled'
}
</script>

<template>
  <div class="workspace-page">
    <!-- 顶部导航 -->
    <div class="top-bar">
      <el-button text @click="router.push('/')">← 返回首页</el-button>
      <span class="title">ArchGenMAS 工作台</span>
      <el-button text @click="router.push('/history')">历史记录</el-button>
    </div>

    <el-row :gutter="24">
      <!-- 左侧：输入区 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span><el-icon><Edit /></el-icon> 需求输入</span>
          </template>

          <!-- 文件上传 -->
          <el-upload
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :show-file-list="false"
            accept=".txt,.docx,.md"
          >
            <el-icon :size="40"><UploadFilled /></el-icon>
            <div class="upload-text">
              <p><em>点击或拖拽上传需求文档</em></p>
              <p class="hint">支持 .txt / .docx / .md 格式</p>
            </div>
          </el-upload>

          <div v-if="workspace.uploadedFile" class="file-info">
            <el-tag type="success" closable @close="workspace.uploadedFile = null">
              {{ workspace.uploadedFile.name }} ({{ workspace.uploadedFile.charCount }} 字)
            </el-tag>
          </div>

          <!-- 文本编辑器 -->
          <el-input
            v-model="workspace.requirementText"
            type="textarea"
            :rows="12"
            placeholder="或在此直接输入/粘贴需求文档内容..."
            class="text-editor"
          />

          <!-- 配置面板 -->
          <div class="config-panel">
            <el-form label-position="top" size="small">
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="体系风格偏好">
                    <el-select v-model="workspace.architectureStyle" style="width:100%">
                      <el-option v-for="s in styleOptions" :key="s.value" :label="s.label" :value="s.value" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="最大迭代次数">
                    <el-input-number v-model="workspace.maxIterations" :min="1" :max="5" style="width:100%" />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </div>

          <el-button
            type="primary"
            size="large"
            :loading="starting"
            :disabled="!workspace.hasContent"
            style="width:100%; margin-top:12px"
            @click="startGeneration"
          >
            <el-icon><Cpu /></el-icon>
            {{ starting ? '执行中...' : '开始生成架构' }}
          </el-button>
          <div v-if="!workspace.hasContent" class="empty-hint">请先输入需求内容</div>
        </el-card>
      </el-col>

      <!-- 右侧：进度区 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span><el-icon><Loading /></el-icon> 执行进度</span>
            <el-tag v-if="pipeline.isRunning" type="warning" size="small" style="margin-left:8px">运行中</el-tag>
            <el-tag v-else-if="pipeline.stage === 'done'" type="success" size="small" style="margin-left:8px">已完成</el-tag>
            <el-tag v-else type="info" size="small" style="margin-left:8px">等待中</el-tag>
          </template>

          <!-- 进度条 -->
          <div class="progress-section">
            <el-progress
              :percentage="pipeline.progressPercent"
              :status="pipeline.stage === 'error' ? 'exception' : undefined"
              :stroke-width="16"
            />
            <p class="stage-text">当前阶段：{{ pipeline.stageLabel }}</p>
            <p v-if="pipeline.iteration > 0" class="iter-text">
              迭代次数：{{ pipeline.iteration }} / {{ pipeline.maxIterations }}
            </p>
          </div>

          <!-- Agent 状态卡片 -->
          <div class="agent-statuses">
            <div
              v-for="agent in pipeline.agentProgress"
              :key="agent.key"
              class="agent-item"
            >
              <el-icon :color="statusColor(agent.status)">
                <component :is="statusIcon(agent.status)" />
              </el-icon>
              <span class="agent-label">{{ agent.label }}</span>
              <el-tag
                :type="agent.status === 'done' ? 'success' : agent.status === 'running' ? 'warning' : 'info'"
                size="small"
              >
                {{ { idle: '等待', running: '执行中', done: '完成', error: '出错' }[agent.status] || agent.status }}
              </el-tag>
            </div>
          </div>

          <!-- 完成操作 -->
          <div v-if="pipeline.stage === 'done'" class="done-actions">
            <el-button type="primary" @click="goResult">
              <el-icon><View /></el-icon> 查看结果
            </el-button>
          </div>

          <!-- 日志区 -->
          <div class="log-section">
            <h4>执行日志</h4>
            <div class="log-list">
              <p v-for="(log, i) in pipeline.logs" :key="i" class="log-line">{{ log }}</p>
              <p v-if="!pipeline.logs.length" class="log-empty">等待执行...</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.workspace-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px 20px;
}
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 0 4px;
}
.top-bar .title {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.upload-text { text-align: center; }
.upload-text .hint { color: #909399; font-size: 12px; }
.file-info { margin-top: 8px; }
.text-editor { margin-top: 12px; }
.config-panel { margin-top: 16px; }
.empty-hint { color: #909399; font-size: 12px; text-align: center; margin-top: 4px; }

.progress-section { margin-bottom: 20px; }
.stage-text { text-align: center; color: #606266; margin: 8px 0 0; font-size: 14px; }
.iter-text { text-align: center; color: #E6A23C; font-size: 13px; margin: 4px 0 0; }

.agent-statuses {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}
.agent-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 8px;
}
.agent-label { flex: 1; font-size: 13px; color: #606266; }

.done-actions { text-align: center; margin: 16px 0; }

.log-section h4 { margin: 0 0 8px; font-size: 14px; color: #303133; }
.log-list {
  max-height: 240px;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 8px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}
.log-line { color: #8bc34a; margin: 2px 0; word-break: break-all; }
.log-empty { color: #666; }
</style>
