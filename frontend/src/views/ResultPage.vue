<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useResultStore } from '../stores/result'
import { getResult, getExportPdfUrl } from '../api/result'
import PlantUmlViewer from '../components/viewer/PlantUmlViewer.vue'

const route = useRoute()
const router = useRouter()
const store = useResultStore()

const projectId = route.params.id as string
const activeTab = ref('c4')

async function loadResult() {
  store.setLoading(true)
  try {
    const data = await getResult(projectId)
    store.setResult(data)
    updateHistoryFromResult(projectId, data)
  } catch (e: any) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    store.setLoading(false)
  }
}

function updateHistoryFromResult(projectId: string, data: any) {
  try {
    const raw = localStorage.getItem('archgenmas_history')
    const items = raw ? JSON.parse(raw) : []
    const idx = items.findIndex((i: any) => i.project_id === projectId)
    if (idx >= 0) {
      items[idx] = {
        ...items[idx],
        architecture_style: data?.architecture?.style || items[idx].architecture_style,
        review_score: data?.review?.overall_score ?? items[idx].review_score,
        risk_level: data?.risk?.overall_risk_level ?? items[idx].risk_level,
        stage: 'done',
      }
      localStorage.setItem('archgenmas_history', JSON.stringify(items))
    }
  } catch { /* ignore */ }
}

function downloadPdf() {
  window.open(getExportPdfUrl(projectId), '_blank')
}

function getRiskTagType(level: string) {
  return { high: 'danger', medium: 'warning', low: 'success' }[level] || 'info'
}

onMounted(() => { loadResult() })
</script>

<template>
  <div class="result-page">
    <!-- 顶部导航 -->
    <div class="top-bar">
      <el-button text @click="router.push('/workspace')">← 返回工作台</el-button>
      <span class="title">架构设计结果</span>
      <el-button type="primary" @click="downloadPdf">
        <el-icon><Download /></el-icon> 下载 PDF
      </el-button>
    </div>

    <!-- 加载中 -->
    <div v-if="store.loading" class="loading-wrap">
      <el-icon :size="48" class="is-loading"><Loading /></el-icon>
      <p>加载结果中...</p>
    </div>

    <!-- 结果内容 -->
    <template v-if="store.result">
      <!-- 概览卡片 -->
      <el-row :gutter="16" class="overview-row">
        <el-col :span="6">
          <el-card shadow="hover">
            <el-statistic title="体系风格" :value="store.result.architecture?.style || '-'" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <el-statistic title="评审评分" :value="store.result.review?.overall_score || '-'">
              <template #suffix>/10</template>
            </el-statistic>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <el-statistic title="风险等级" :value="store.result.risk?.overall_risk_level || '-'" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <el-statistic title="迭代次数" :value="store.result.logs?.length > 0 ? '完成' : '-'" />
          </el-card>
        </el-col>
      </el-row>

      <!-- Tab 切换 -->
      <el-card style="margin-top:20px">
        <el-tabs v-model="activeTab" type="border-card">
          <!-- C4 渲染 -->
          <el-tab-pane label="C4 模型" name="c4">
            <div v-if="store.result.architecture?.c4_plantuml">
              <PlantUmlViewer
                v-for="(code, layer) in store.result.architecture.c4_plantuml"
                :key="layer"
                :code="code"
                :title="(
                  { context: 'L1 系统上下文图 (Context)',
                    container: 'L2 容器图 (Container)',
                    component: 'L3 组件图 (Component)',
                    code: 'L4 代码图 (Code)' } as Record<string,string>
                )[layer] || layer"
              />
            </div>
            <el-empty v-else description="暂无C4模型数据" />
          </el-tab-pane>

          <!-- 4+1 视图 -->
          <el-tab-pane label="4+1 视图" name="views">
            <div v-if="store.result.architecture?.views_plantuml">
              <PlantUmlViewer
                v-for="(code, key) in store.result.architecture.views_plantuml"
                :key="key"
                :code="code"
                :title="(
                  { logical: '逻辑视图 (Logical View)',
                    development: '开发视图 (Development View)',
                    process: '进程视图 (Process View)',
                    physical: '物理视图 (Physical View)',
                    scenario: '场景视图 (Scenario View)' } as Record<string,string>
                )[key] || key"
              />
            </div>
            <el-empty v-else description="暂无4+1视图数据" />
          </el-tab-pane>

          <!-- 技术方案 -->
          <el-tab-pane label="技术方案" name="tech">
            <div v-if="store.result.architecture" class="tech-section">
              <h3>体系风格选型</h3>
              <el-alert
                :title="store.result.architecture.style"
                :description="store.result.architecture.style_rationale"
                type="info" show-icon :closable="false"
              />

              <h3 style="margin-top:20px">技术栈</h3>
              <el-table
                :data="Object.entries(store.result.architecture.tech_stack || {}).map(([k, v]) => ({ layer: k, tech: v }))"
                style="max-width:500px"
              >
                <el-table-column prop="layer" label="层级" />
                <el-table-column prop="tech" label="技术选型" />
              </el-table>

              <h3 style="margin-top:20px">技术方案说明</h3>
              <div class="tech-plan" v-html="(store.result.architecture.tech_plan || '').replace(/\n/g, '<br/>')" />
            </div>
            <el-empty v-else description="暂无技术方案数据" />
          </el-tab-pane>

          <!-- 风险评估 -->
          <el-tab-pane label="风险评估" name="risk">
            <div v-if="store.result.risk?.risk_items_display?.length">
              <el-row :gutter="12" style="margin-bottom:16px">
                <el-col :span="6" v-for="(count, level) in store.result.risk.count_by_level" :key="level">
                  <el-statistic :title="level" :value="count">
                    <template #suffix>项</template>
                  </el-statistic>
                </el-col>
              </el-row>

              <el-table :data="store.result.risk.risk_items_display" stripe>
                <el-table-column prop="id" label="编号" width="100" />
                <el-table-column prop="dimension_label" label="维度" width="100" />
                <el-table-column prop="risk_level" label="等级" width="80">
                  <template #default="{ row }">
                    <el-tag :type="getRiskTagType(row.risk_level)">{{ row.risk_level }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="description" label="描述" min-width="200" />
                <el-table-column prop="impact" label="影响" min-width="150" />
                <el-table-column prop="mitigation" label="缓解措施" min-width="200" />
              </el-table>

              <el-alert
                v-if="store.result.risk.summary"
                :title="store.result.risk.summary"
                :type="store.result.risk.overall_risk_level === 'high' ? 'error' : store.result.risk.overall_risk_level === 'medium' ? 'warning' : 'success'"
                show-icon :closable="false"
                style="margin-top:16px"
              />
            </div>
            <el-empty v-else description="暂无风险数据" />
          </el-tab-pane>

          <!-- 评审意见 -->
          <el-tab-pane label="评审意见" name="review">
            <div v-if="store.result.review">
              <el-row :gutter="12" style="margin-bottom:16px">
                <el-col :span="6">
                  <el-statistic title="总评分" :value="store.result.review.overall_score">
                    <template #suffix>/10</template>
                  </el-statistic>
                </el-col>
                <el-col :span="6">
                  <el-statistic title="问题数" :value="store.result.review.issues?.length || 0" />
                </el-col>
                <el-col :span="6">
                  <el-tag :type="store.result.review.requires_revision ? 'danger' : 'success'">
                    {{ store.result.review.requires_revision ? '需要修改' : '评审通过' }}
                  </el-tag>
                </el-col>
              </el-row>

              <el-table v-if="store.result.review.issues?.length" :data="store.result.review.issues" stripe>
                <el-table-column prop="id" label="编号" width="100" />
                <el-table-column prop="category" label="类别" width="120" />
                <el-table-column prop="severity" label="严重程度" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.severity === 'critical' ? 'danger' : row.severity === 'major' ? 'warning' : 'info'">
                      {{ row.severity }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="description" label="描述" min-width="200" />
                <el-table-column prop="suggestion" label="建议" min-width="200" />
              </el-table>

              <div v-if="store.result.review.suggestions?.length" style="margin-top:16px">
                <h4>改进建议</h4>
                <ul><li v-for="s in store.result.review.suggestions" :key="s">{{ s }}</li></ul>
              </div>
            </div>
            <el-empty v-else description="暂无评审数据" />
          </el-tab-pane>

          <!-- 执行日志 -->
          <el-tab-pane label="执行日志" name="logs">
            <div class="log-section">
              <p v-for="(log, i) in store.result.logs" :key="i" class="log-line">{{ log }}</p>
              <el-empty v-if="!store.result.logs?.length" description="暂无日志" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </template>
  </div>
</template>

<style scoped>
.result-page { max-width: 1200px; margin: 0 auto; padding: 16px 20px; }
.top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.top-bar .title { font-size: 18px; font-weight: 700; }
.loading-wrap { text-align: center; padding: 80px 0; }
.overview-row { margin-bottom: 0; }

.tech-section h3 { margin: 16px 0 12px; color: #303133; }
.tech-plan { background: #f5f7fa; padding: 16px; border-radius: 8px; line-height: 1.8; color: #606266; }

.log-section { background: #1e1e1e; border-radius: 8px; padding: 16px; max-height: 500px; overflow-y: auto; }
.log-line { color: #8bc34a; font-size: 12px; font-family: 'Courier New', monospace; margin: 2px 0; }
</style>
