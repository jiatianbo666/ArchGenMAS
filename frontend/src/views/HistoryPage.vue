<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getHistory, deleteHistoryItem, type HistoryItem } from '../api/history'

const router = useRouter()
const items = ref<HistoryItem[]>([])
const total = ref(0)
const loading = ref(false)

onMounted(load)
async function load() { loading.value = true; try { const d = await getHistory(1); items.value = d.items; total.value = d.total } catch { ElMessage.error('加载失败') } finally { loading.value = false } }
async function removeItem(id: string, name: string) { try { await ElMessageBox.confirm(`确定删除「${name}」？`, '确认删除', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }); await deleteHistoryItem(id); items.value = items.value.filter(i => i.project_id !== id); ElMessage.success('已删除') } catch { /* cancel */ } }
function goResult(id: string) { router.push(`/result/${id}`) }
</script>

<template>
  <div class="history-page">
    <div class="top-bar">
      <el-button text @click="router.push('/')"><el-icon><ArrowLeft /></el-icon> 返回首页</el-button>
      <span class="top-title">历史记录</span>
      <el-button type="primary" round @click="router.push('/workspace')"><el-icon><Plus /></el-icon> 新建项目</el-button>
    </div>

    <div class="panel" v-loading="loading">
      <div class="panel-hd">最近生成的项目<el-tag type="info" size="small" effect="plain" round class="count">共 {{ total }} 条</el-tag></div>
      <el-empty v-if="!items.length" description="暂无历史记录" :image-size="100"><el-button type="primary" round @click="router.push('/workspace')">开始使用</el-button></el-empty>
      <el-table v-else :data="items" stripe class="hist-table" :header-cell-style="{ background:'#f8fafc', fontWeight:600, color:'#64748b', fontSize:'11px', textTransform:'uppercase', letterSpacing:'1px' }">
        <el-table-column prop="project_id" label="ID" width="120"><template #default="{row}"><code class="pid">{{ row.project_id }}</code></template></el-table-column>
        <el-table-column prop="project_name" label="项目名称" min-width="200" show-overflow-tooltip><template #default="{row}"><el-link type="primary" underline="never" class="p-link" @click="goResult(row.project_id)">{{ row.project_name }}</el-link></template></el-table-column>
        <el-table-column prop="architecture_style" label="体系风格" width="140"><template #default="{row}"><el-tag v-if="row.architecture_style" size="small" effect="plain" round>{{ row.architecture_style }}</el-tag><span v-else class="dash">—</span></template></el-table-column>
        <el-table-column prop="review_score" label="评审" width="80" align="center"><template #default="{row}"><span v-if="row.review_score!==null" class="score" :class="row.review_score>=7?'g':row.review_score>=5?'m':'b'">{{ row.review_score }}/10</span><span v-else class="dash">—</span></template></el-table-column>
        <el-table-column prop="risk_level" label="风险" width="90" align="center"><template #default="{row}"><el-tag v-if="row.risk_level" :type="row.risk_level==='high'?'danger':row.risk_level==='medium'?'warning':'success'" size="small" effect="dark" round>{{ row.risk_level }}</el-tag><span v-else class="dash">—</span></template></el-table-column>
        <el-table-column prop="stage" label="状态" width="90" align="center"><template #default="{row}"><el-tag v-if="row.stage==='done'" type="success" size="small" effect="plain" round>完成</el-tag><el-tag v-else-if="row.stage==='running'" type="warning" size="small" effect="plain" round>运行中</el-tag><el-tag v-else type="info" size="small" round>{{ row.stage }}</el-tag></template></el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170"><template #default="{row}">{{ row.created_at?new Date(row.created_at).toLocaleString():'—' }}</template></el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center"><template #default="{row}"><el-button size="small" type="primary" link @click="goResult(row.project_id)">查看</el-button><el-button size="small" type="danger" link @click="removeItem(row.project_id,row.project_name)">删除</el-button></template></el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.history-page { max-width: 1100px; margin: 0 auto; padding: 16px 24px; }
.top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.top-title { font-size: 18px; font-weight: 700; color: #1e293b; }

.panel { background: #fff; border: 1px solid #f1f5f9; border-radius: 16px; padding: 24px; }
.panel-hd { font-size: 14px; font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 10px; margin-bottom: 20px; }
.count { margin-left: auto; }

.hist-table { border-radius: 8px; overflow: hidden; }
.pid { font-family: 'Courier New', monospace; font-size: 11px; color: #64748b; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }
.p-link { font-weight: 600; }
.dash { color: #cbd5e1; }
.score { font-weight: 700; font-size: 13px; } .score.g { color: #10b981; } .score.m { color: #f59e0b; } .score.b { color: #ef4444; }
</style>
