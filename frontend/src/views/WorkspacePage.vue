<script setup lang="ts">
import { ref } from 'vue'
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

const styleOptions = [
  { value: 'auto', label: '自动选择（推荐）' },
  { value: 'microservices', label: '微服务架构' },
  { value: 'monolith', label: '单体架构' },
  { value: 'layered', label: '分层架构' },
  { value: 'event_driven', label: '事件驱动架构' },
  { value: 'pipeline', label: '管道过滤器架构' },
]

async function handleFileChange(file: UploadFile) {
  if (!file.raw) return; uploading.value = true
  try {
    const result = await uploadFile(file.raw)
    workspace.setUploadedFile({ name: result.filename, content: result.content_full, charCount: result.char_count })
    ElMessage.success(`文件解析成功，共 ${result.char_count} 个字符`)
  } catch (e: any) { ElMessage.error(e.message || '文件解析失败') }
  finally { uploading.value = false }
}

async function startGeneration() {
  if (!workspace.hasContent) { ElMessage.warning('请先上传需求文档或输入需求描述'); return }
  starting.value = true; pipeline.reset()
  try {
    const resp = await runPipeline({ content: workspace.requirementText, filename: workspace.uploadedFile?.name || '', architecture_style: workspace.architectureStyle, max_iterations: workspace.maxIterations })
    workspace.currentProjectId = resp.project_id; pipeline.start(resp.project_id)
    saveToHistory(resp.project_id, workspace.requirementText)
    ElMessage.success('流水线已启动')
    startPolling(resp.project_id)
  } catch (e: any) { ElMessage.error(e.message || '启动失败'); starting.value = false }
}

function startPolling(pid: string) {
  pollingTimer.value = setInterval(async () => {
    try {
      const s = await getPipelineStatus(pid); pipeline.updateFromStatus(s)
      if (s.stage === 'done') { stopPolling(); pipeline.done(); updateHistory(pid, { stage: 'done' }); setTimeout(() => router.push(`/result/${pid}`), 500) }
      else if (s.stage === 'error') { stopPolling(); pipeline.setError('流水线出错'); ElMessage.error('流水线出错') }
    } catch { /* ignore */ }
  }, 1500)
}
function stopPolling() { if (pollingTimer.value) { clearInterval(pollingTimer.value); pollingTimer.value = null }; starting.value = false }

function saveToHistory(pid: string, c: string) { try { const raw = localStorage.getItem('archgenmas_history'); const items = raw ? JSON.parse(raw) : []; const n = (c.trim().split('\n')[0] || '').replace(/^[#\-*【】\s]+/, '').slice(0, 50) || '未命名'; if (!items.find((i: any) => i.project_id === pid)) { items.unshift({ project_id: pid, project_name: n, architecture_style: '', review_score: null, risk_level: null, iteration: 0, stage: 'running', created_at: new Date().toISOString() }); if (items.length > 20) items.pop(); localStorage.setItem('archgenmas_history', JSON.stringify(items)) } } catch { /* ignore */ } }
function updateHistory(pid: string, u: Record<string, any>) { try { const raw = localStorage.getItem('archgenmas_history'); const items = raw ? JSON.parse(raw) : []; const i = items.findIndex((x: any) => x.project_id === pid); if (i >= 0) { items[i] = { ...items[i], ...u }; localStorage.setItem('archgenmas_history', JSON.stringify(items)) } } catch { /* ignore */ } }
function goResult() { if (pipeline.projectId) router.push(`/result/${pipeline.projectId}`) }

const statusDot = (s: string) => ({ idle: '#cbd5e1', running: '#6366f1', done: '#10b981', error: '#ef4444' } as any)[s] || '#cbd5e1'
const statusLabel = (s: string) => ({ idle: '等待', running: '执行中', done: '完成', error: '出错' } as any)[s] || s
</script>

<template>
  <div class="workspace-page">
    <div class="top-bar">
      <el-button text @click="router.push('/')"><el-icon><ArrowLeft /></el-icon> 返回首页</el-button>
      <span class="top-title">ArchGenMAS 工作台</span>
      <el-button text @click="router.push('/history')"><el-icon><Clock /></el-icon> 历史记录</el-button>
    </div>

    <el-row :gutter="24">
      <el-col :span="12">
        <div class="panel">
          <div class="panel-hd"><span class="dot" style="background:#6366f1"></span> 需求输入</div>

          <el-upload drag :auto-upload="false" :on-change="handleFileChange" :show-file-list="false" accept=".txt,.docx,.md">
            <el-icon :size="32" color="#6366f1"><UploadFilled /></el-icon>
            <div class="upload-text"><p>点击或拖拽上传需求文档</p><p class="hint">支持 .txt / .docx / .md</p></div>
          </el-upload>

          <div v-if="workspace.uploadedFile" class="file-tag">
            <el-tag type="success" closable @close="workspace.uploadedFile = null" effect="plain" round>{{ workspace.uploadedFile.name }} · {{ workspace.uploadedFile.charCount }} 字</el-tag>
          </div>

          <el-input v-model="workspace.requirementText" type="textarea" :rows="10" placeholder="或在此直接输入 / 粘贴需求文档内容..." class="text-editor" />

          <div class="config-row">
            <div class="config-item"><label>体系风格</label><el-select v-model="workspace.architectureStyle"><el-option v-for="s in styleOptions" :key="s.value" :label="s.label" :value="s.value" /></el-select></div>
            <div class="config-item"><label>最大迭代</label><el-input-number v-model="workspace.maxIterations" :min="1" :max="5" /></div>
          </div>

          <el-button type="primary" size="large" :loading="starting" :disabled="!workspace.hasContent" class="run-btn" @click="startGeneration"><el-icon><Cpu /></el-icon> {{ starting ? '执行中...' : '开始生成架构' }}</el-button>
          <p v-if="!workspace.hasContent" class="empty-hint">请先输入需求内容</p>
        </div>
      </el-col>

      <el-col :span="12">
        <div class="panel">
          <div class="panel-hd">
            <span class="dot" :style="{ background: pipeline.isRunning ? '#f59e0b' : pipeline.stage === 'done' ? '#10b981' : '#cbd5e1' }" :class="{ pulse: pipeline.isRunning }"></span>
            执行进度
            <el-tag v-if="pipeline.isRunning" type="warning" size="small" effect="plain" round class="pill">运行中</el-tag>
            <el-tag v-else-if="pipeline.stage==='done'" type="success" size="small" effect="plain" round class="pill">已完成</el-tag>
            <el-tag v-else type="info" size="small" effect="plain" round class="pill">等待中</el-tag>
          </div>

          <div class="progress-block">
            <el-progress :percentage="pipeline.progressPercent" :stroke-width="10" :color="pipeline.stage==='error'?'#ef4444':'#6366f1'" :define-back-color="'#f1f5f9'" />
            <p class="stage-label">{{ pipeline.stageLabel }}</p>
            <p v-if="pipeline.iteration>0" class="iter-label">{{ pipeline.iteration }} / {{ pipeline.maxIterations }} 次迭代</p>
          </div>

          <div class="agent-list">
            <div v-for="a in pipeline.agentProgress" :key="a.key" class="agent-row">
              <span class="a-dot" :style="{ background: statusDot(a.status) }"></span>
              <span class="a-name">{{ a.label }}</span>
              <span class="a-status" :style="{ color: statusDot(a.status) }">{{ statusLabel(a.status) }}</span>
            </div>
          </div>

          <div v-if="pipeline.stage==='done'" style="text-align:center;margin-bottom:16px">
            <el-button type="primary" round @click="goResult"><el-icon><View /></el-icon> 查看结果</el-button>
          </div>

          <div class="log-box">
            <div class="log-hd">执行日志 <span>{{ pipeline.logs.length }}</span></div>
            <div class="log-list"><p v-for="(l,i) in pipeline.logs" :key="i" class="log-line">{{ l }}</p><p v-if="!pipeline.logs.length" class="log-empty">等待任务启动...</p></div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.workspace-page { max-width: 1200px; margin: 0 auto; padding: 16px 24px; }
.top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.top-title { font-size: 18px; font-weight: 700; color: #1e293b; }

.panel { background: #fff; border: 1px solid #f1f5f9; border-radius: 16px; padding: 24px; }
.panel-hd { font-size: 14px; font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 10px; margin-bottom: 20px; }
.dot { width: 9px; height: 9px; border-radius: 50%; background: #cbd5e1; }
.pulse { animation: pulse 1.2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
.pill { margin-left: auto; }

.upload-text p { margin: 8px 0 0; font-size: 14px; color: #475569; font-weight: 500; }
.upload-text .hint { color: #94a3b8; font-size: 12px; }
.file-tag { margin: 10px 0; }
.text-editor { margin-bottom: 16px; }

.config-row { display: flex; gap: 16px; margin-bottom: 16px; }
.config-item { flex: 1; }
.config-item label { display: block; font-size: 11px; color: #94a3b8; margin-bottom: 6px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
.config-item :deep(.el-select), .config-item :deep(.el-input-number) { width: 100%; }

.run-btn { width: 100%; padding: 14px; font-size: 15px; font-weight: 600; }
.empty-hint { text-align: center; color: #cbd5e1; font-size: 12px; margin: 6px 0 0; }

.progress-block { text-align: center; margin-bottom: 20px; }
.stage-label { font-size: 14px; font-weight: 600; color: #1e293b; margin: 8px 0 0; }
.iter-label { font-size: 12px; color: #f59e0b; margin: 4px 0 0; font-weight: 500; }

.agent-list { display: flex; flex-direction: column; gap: 4px; margin-bottom: 16px; }
.agent-row { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 10px; background: #f8fafc; }
.a-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.a-name { flex: 1; font-size: 13px; font-weight: 500; color: #334155; }
.a-status { font-size: 12px; font-weight: 600; }

.log-box { border: 1px solid #f1f5f9; border-radius: 10px; overflow: hidden; }
.log-hd { display: flex; justify-content: space-between; padding: 8px 14px; background: #f8fafc; font-size: 12px; font-weight: 600; color: #475569; }
.log-hd span { font-size: 11px; color: #94a3b8; }
.log-list { max-height: 180px; overflow-y: auto; background: #0f172a; padding: 10px 14px; font-family: 'Courier New', monospace; font-size: 11px; }
.log-line { color: #86efac; margin: 2px 0; line-height: 1.5; }
.log-empty { color: #475569; text-align: center; }

@media (max-width: 768px) { .workspace-page :deep(.el-col) { flex: 0 0 100%; max-width: 100%; margin-bottom: 16px; } }
</style>
