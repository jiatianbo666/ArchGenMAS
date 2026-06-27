<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useResultStore } from '../stores/result'
import { getResult, getExportPdfUrl } from '../api/result'
import PlantUmlViewer from '../components/viewer/PlantUmlViewer.vue'

const route = useRoute(); const router = useRouter(); const store = useResultStore()
const projectId = route.params.id as string; const activeTab = ref('c4')

async function loadResult() { store.setLoading(true); try { store.setResult(await getResult(projectId)) } catch (e: any) { ElMessage.error(e.message) } finally { store.setLoading(false) } }
function downloadPdf() { window.open(getExportPdfUrl(projectId), '_blank') }
onMounted(loadResult)

const tagType = (l: string) => ({ high: 'danger', medium: 'warning', low: 'success' } as any)[l] || 'info'
const C4: any = { context: 'L1 系统上下文图', container: 'L2 容器图', component: 'L3 组件图', code: 'L4 代码图' }
const V41: any = { logical: '逻辑视图', development: '开发视图', process: '进程视图', physical: '物理视图', scenario: '场景视图 (+1)' }
</script>

<template>
  <div class="result-page">
    <div class="top-bar">
      <el-button text @click="router.push('/workspace')"><el-icon><ArrowLeft /></el-icon> 返回工作台</el-button>
      <span class="top-title">架构设计结果</span>
      <el-button type="primary" round @click="downloadPdf"><el-icon><Download /></el-icon> 下载 PDF</el-button>
    </div>

    <div v-if="store.loading" class="loading-wrap"><el-icon :size="40" class="is-loading"><Loading /></el-icon><p>加载结果中...</p></div>

    <template v-if="store.result">
      <el-row :gutter="16" class="overview-row">
        <el-col :span="6"><div class="stat-card"><span class="stat-val">{{ store.result.architecture?.style || '—' }}</span><span class="stat-lbl">体系风格</span></div></el-col>
        <el-col :span="6"><div class="stat-card"><span class="stat-val">{{ store.result.review?.overall_score ?? '—' }}<small>/10</small></span><span class="stat-lbl">评审评分</span></div></el-col>
        <el-col :span="6"><div class="stat-card"><span class="stat-val" :class="'risk-'+(store.result.risk?.overall_risk_level||'low')">{{ store.result.risk?.overall_risk_level || '—' }}</span><span class="stat-lbl">风险等级</span></div></el-col>
        <el-col :span="6"><div class="stat-card"><span class="stat-val">{{ store.result.logs?.length>0?'完成':'—' }}</span><span class="stat-lbl">生成状态</span></div></el-col>
      </el-row>

      <div class="tab-panel">
        <el-tabs v-model="activeTab">
          <el-tab-pane name="c4"><template #label><el-icon><Grid /></el-icon> C4 模型</template>
            <div v-if="store.result.architecture?.c4_plantuml">
              <PlantUmlViewer v-for="(code, layer) in store.result.architecture.c4_plantuml" :key="layer" :code="code" :title="C4[layer]||layer" />
            </div>
            <el-empty v-else description="暂无数据" />
          </el-tab-pane>
          <el-tab-pane name="views"><template #label><el-icon><Connection /></el-icon> 4+1 视图</template>
            <div v-if="store.result.architecture?.views_plantuml">
              <PlantUmlViewer v-for="(code, key) in store.result.architecture.views_plantuml" :key="key" :code="code" :title="V41[key]||key" />
            </div>
            <el-empty v-else description="暂无数据" />
          </el-tab-pane>
          <el-tab-pane name="tech"><template #label><el-icon><Notebook /></el-icon> 技术方案</template>
            <div v-if="store.result.architecture" class="tech-section">
              <el-alert :title="store.result.architecture.style" :description="store.result.architecture.style_rationale" type="info" show-icon :closable="false" />
              <h4 class="t-h4">技术栈</h4>
              <el-table :data="Object.entries(store.result.architecture.tech_stack||{}).map(([k,v])=>({layer:k,tech:v}))" class="tech-table" stripe><el-table-column prop="layer" label="层级" width="160" /><el-table-column prop="tech" label="技术选型" /></el-table>
              <h4 class="t-h4">方案说明</h4>
              <div class="tech-plan" v-html="(store.result.architecture.tech_plan||'').replace(/\n/g,'<br/>')" />
            </div>
            <el-empty v-else description="暂无数据" />
          </el-tab-pane>
          <el-tab-pane name="risk"><template #label><el-icon><WarningFilled /></el-icon> 风险评估</template>
            <div v-if="store.result.risk?.risk_items_display?.length">
              <el-row :gutter="12" class="r-summary">
                <el-col :span="8" v-for="(count, level) in store.result.risk.count_by_level" :key="level"><div class="mini-stat" :class="'mini-'+level"><span class="mini-num">{{ count }}</span><span class="mini-lbl">{{ level }}</span></div></el-col>
              </el-row>
              <el-table :data="store.result.risk.risk_items_display" stripe class="r-table"><el-table-column prop="id" label="#" width="90" /><el-table-column prop="dimension_label" label="维度" width="100" /><el-table-column prop="risk_level" label="等级" width="90"><template #default="{row}"><el-tag :type="tagType(row.risk_level)" size="small" effect="dark" round>{{ row.risk_level }}</el-tag></template></el-table-column><el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip /><el-table-column prop="impact" label="影响" min-width="140" show-overflow-tooltip /><el-table-column prop="mitigation" label="缓解措施" min-width="180" show-overflow-tooltip /></el-table>
              <el-alert v-if="store.result.risk.summary" :title="store.result.risk.summary" :type="store.result.risk.overall_risk_level==='high'?'error':'warning'" show-icon :closable="false" class="r-alert" />
            </div>
            <el-empty v-else description="暂无数据" />
          </el-tab-pane>
          <el-tab-pane name="review"><template #label><el-icon><Checked /></el-icon> 评审意见</template>
            <div v-if="store.result.review">
              <el-row :gutter="12" class="r-summary">
                <el-col :span="8"><div class="mini-stat mini-score"><span class="mini-num">{{ store.result.review.overall_score }}</span><span class="mini-lbl">评分 /10</span></div></el-col>
                <el-col :span="8"><div class="mini-stat"><span class="mini-num">{{ store.result.review.issues?.length||0 }}</span><span class="mini-lbl">问题数</span></div></el-col>
                <el-col :span="8" style="display:flex;align-items:center;justify-content:center"><el-tag :type="store.result.review.requires_revision?'danger':'success'" size="large" effect="dark" round>{{ store.result.review.requires_revision?'需修改':'已通过' }}</el-tag></el-col>
              </el-row>
              <el-table v-if="store.result.review.issues?.length" :data="store.result.review.issues" stripe class="r-table"><el-table-column prop="id" label="#" width="90" /><el-table-column prop="category" label="类别" width="120" /><el-table-column prop="severity" label="严重" width="100"><template #default="{row}"><el-tag :type="row.severity==='critical'?'danger':row.severity==='major'?'warning':'info'" size="small" round>{{ row.severity }}</el-tag></template></el-table-column><el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip /><el-table-column prop="suggestion" label="建议" min-width="180" show-overflow-tooltip /></el-table>
              <div v-if="store.result.review.suggestions?.length" class="suggest-list"><h4>改进建议</h4><ul><li v-for="s in store.result.review.suggestions" :key="s">{{ s }}</li></ul></div>
            </div>
            <el-empty v-else description="暂无数据" />
          </el-tab-pane>
          <el-tab-pane name="logs"><template #label><el-icon><Tickets /></el-icon> 执行日志</template>
            <div class="log-box"><p v-for="(l,i) in store.result.logs" :key="i" class="log-line">{{ l }}</p><el-empty v-if="!store.result.logs?.length" description="暂无日志" /></div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </template>
  </div>
</template>

<style scoped>
.result-page { max-width: 1200px; margin: 0 auto; padding: 16px 24px; }
.top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.top-title { font-size: 18px; font-weight: 700; color: #1e293b; }
.loading-wrap { text-align: center; padding: 80px 0; color: #64748b; }

.overview-row { margin-bottom: 20px; }
.stat-card { background: #fff; border: 1px solid #f1f5f9; border-radius: 14px; padding: 20px; text-align: center; }
.stat-val { font-size: 22px; font-weight: 700; color: #1e293b; display: block; }
.stat-val small { font-size: 12px; color: #94a3b8; font-weight: 500; }
.stat-lbl { font-size: 11px; color: #94a3b8; margin-top: 4px; display: block; text-transform: uppercase; letter-spacing: 1px; }
.risk-high { color: #ef4444; } .risk-medium { color: #f59e0b; } .risk-low { color: #10b981; }

.tab-panel { background: #fff; border: 1px solid #f1f5f9; border-radius: 16px; padding: 24px; }
.t-h4 { margin: 20px 0 10px; font-size: 14px; font-weight: 600; color: #1e293b; }
.tech-table { max-width: 520px; border-radius: 8px; overflow: hidden; }
.tech-plan { background: #f8fafc; border-radius: 10px; padding: 18px; line-height: 1.9; color: #475569; font-size: 13px; }

.r-summary { margin-bottom: 16px; }
.mini-stat { text-align: center; padding: 14px; border-radius: 10px; background: #f8fafc; }
.mini-high { background: #fef2f2; } .mini-medium { background: #fffbeb; } .mini-low { background: #f0fdf4; } .mini-score { background: #eef2ff; }
.mini-num { font-size: 24px; font-weight: 700; color: #1e293b; display: block; }
.mini-lbl { font-size: 10px; color: #94a3b8; display: block; margin-top: 2px; text-transform: uppercase; letter-spacing: 1px; }

.r-table { border-radius: 8px; overflow: hidden; }
.r-alert { margin-top: 16px; border-radius: 10px; }

.log-box { background: #0f172a; border-radius: 10px; padding: 16px; max-height: 500px; overflow-y: auto; }
.log-line { color: #86efac; font-size: 11px; font-family: 'Courier New', monospace; margin: 2px 0; }

.suggest-list { margin-top: 16px; } .suggest-list h4 { font-size: 14px; color: #1e293b; margin: 0 0 8px; } .suggest-list ul { padding-left: 20px; } .suggest-list li { font-size: 13px; color: #475569; line-height: 1.8; }
</style>
