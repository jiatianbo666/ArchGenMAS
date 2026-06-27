<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getHistory, deleteHistoryItem, type HistoryItem } from '../api/history'

const router = useRouter()
const items = ref<HistoryItem[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)

onMounted(() => {
  loadHistory()
})

async function loadHistory() {
  loading.value = true
  try {
    const data = await getHistory(page.value)
    items.value = data.items
    total.value = data.total
  } catch {
    ElMessage.error('加载历史记录失败')
  } finally {
    loading.value = false
  }
}

async function removeItem(id: string, name: string) {
  try {
    await ElMessageBox.confirm(`确定删除「${name}」？`, '确认删除', { type: 'warning' })
    await deleteHistoryItem(id)
    items.value = items.value.filter(i => i.project_id !== id)
    ElMessage.success('已删除')
  } catch {
    // 取消删除
  }
}

function goResult(id: string) {
  router.push(`/result/${id}`)
}

function goWorkspace() {
  router.push('/workspace')
}
</script>

<template>
  <div class="history-page">
    <div class="top-bar">
      <el-button text @click="router.push('/')">← 返回首页</el-button>
      <span class="title">历史记录</span>
      <el-button type="primary" @click="goWorkspace">
        <el-icon><Plus /></el-icon> 新建项目
      </el-button>
    </div>

    <el-card v-loading="loading">
      <template #header>
        <span>最近生成的项目（共 {{ total }} 条，存储在 SQLite）</span>
      </template>

      <el-empty v-if="!items.length" description="暂无历史记录">
        <el-button type="primary" @click="goWorkspace">开始使用</el-button>
      </el-empty>

      <el-table v-else :data="items" stripe>
        <el-table-column prop="project_id" label="项目ID" width="130" />
        <el-table-column prop="project_name" label="项目名称" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="goResult(row.project_id)">{{ row.project_name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="architecture_style" label="体系风格" width="140">
          <template #default="{ row }">
            <el-tag v-if="row.architecture_style" size="small">{{ row.architecture_style }}</el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="review_score" label="评审" width="70">
          <template #default="{ row }">
            <span v-if="row.review_score !== null">{{ row.review_score }}/10</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险" width="80">
          <template #default="{ row }">
            <el-tag
              v-if="row.risk_level"
              :type="row.risk_level === 'high' ? 'danger' : row.risk_level === 'medium' ? 'warning' : 'success'"
              size="small"
            >{{ row.risk_level }}</el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="stage" label="状态" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.stage === 'done'" type="success" size="small">完成</el-tag>
            <el-tag v-else-if="row.stage === 'running'" type="warning" size="small">运行中</el-tag>
            <el-tag v-else type="info" size="small">{{ row.stage }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">
            {{ row.created_at ? new Date(row.created_at).toLocaleString() : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="goResult(row.project_id)">查看</el-button>
            <el-button size="small" type="danger" @click="removeItem(row.project_id, row.project_name)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.history-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 16px 20px;
}
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.top-bar .title { font-size: 18px; font-weight: 700; }
.text-muted { color: #c0c4cc; }
</style>
