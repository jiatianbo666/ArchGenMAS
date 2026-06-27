<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const features = [
  { title: '需求校验 Agent', desc: '自动检测需求完整性、识别逻辑冲突与模糊点，输出结构化需求规格', color: '#6366f1' },
  { title: '架构设计 Agent', desc: '智能选型体系风格，生成 C4 四层模型 + 4+1 五套视图 + 技术方案', color: '#10b981' },
  { title: '评审纠错 Agent', desc: 'Critic 批评者模式，检查架构一致性、耦合度、冗余，给出修改建议', color: '#f59e0b' },
  { title: '风险检测 Agent', desc: '四维度风险扫描：性能 · 安全 · 扩展性 · 并发，输出风险清单与缓解方案', color: '#ef4444' },
  { title: '文档生成 Agent', desc: '一键整合所有产物，导出标准化 PDF 架构设计文档', color: '#8b5cf6' },
]

const steps = [
  { title: '上传需求', desc: '拖拽或粘贴业务需求文档' },
  { title: 'Agent 协同', desc: '5个AI专家依次协作分析' },
  { title: '迭代优化', desc: '评审+风险双重校验，自动迭代' },
  { title: '一键导出', desc: '生成C4/4+1/风险评估/PDF报告' },
]

function goWorkspace() { router.push('/workspace') }
</script>

<template>
  <div class="home-page">
    <header class="hero">
      <h1 class="hero-title">ArchGenMAS</h1>
      <p class="hero-subtitle">多智能体协同软件架构自动生成系统</p>
      <p class="hero-desc">输入自然语言业务需求，5 大 AI 专家 Agent 协同完成全流程架构设计，一键输出 C4 模型、4+1 视图、风险评估与标准化 PDF 文档。</p>
      <el-button type="primary" size="large" round class="hero-btn" @click="goWorkspace"><el-icon><Upload /></el-icon> 开始使用</el-button>
    </header>

    <section class="features">
      <h2 class="section-title">五大专家 Agent 协同</h2>
      <div class="feature-grid">
        <div v-for="f in features" :key="f.title" class="feature-card" :style="{ borderTopColor: f.color }">
          <div class="feature-dot" :style="{ background: f.color }"></div>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </div>
      </div>
    </section>

    <section class="workflow">
      <h2 class="section-title">工作流程</h2>
      <el-steps :active="4" align-center finish-status="success">
        <el-step v-for="s in steps" :key="s.title" :title="s.title" :description="s.desc" />
      </el-steps>
    </section>

    <footer class="footer">
      <p>ArchGenMAS · Vue 3 + FastAPI · 软件体系结构课程大作业 © 2026</p>
    </footer>
  </div>
</template>

<style scoped>
.home-page { max-width: 1200px; margin: 0 auto; padding: 0 24px 48px; }

/* Hero */
.hero {
  margin-top: 28px; padding: 64px 40px 56px; border-radius: 20px; text-align: center;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 30%, #eef2ff 70%, #e0e7ff 100%);
  border: 1px solid #e2e8f0;
}
.hero-title { font-size: 48px; font-weight: 800; margin: 0; letter-spacing: -1.5px; color: #0f172a; }
.hero-subtitle { font-size: 20px; margin: 12px 0 20px; color: #475569; font-weight: 400; }
.hero-desc { font-size: 14px; line-height: 1.8; color: #64748b; max-width: 620px; margin: 0 auto 32px; }
.hero-btn { padding: 14px 36px; font-size: 15px; font-weight: 600; }

/* Section Title */
.section-title { text-align: center; font-size: 26px; font-weight: 700; color: #1e293b; margin: 56px 0 32px; }

/* Features */
.feature-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 18px; }
.feature-card {
  background: #fff; border: 1px solid #f1f5f9; border-top: 3px solid #f1f5f9; border-radius: 14px;
  padding: 28px 20px 24px; text-align: left; transition: all 0.25s;
}
.feature-card:hover { border-color: #e2e8f0; box-shadow: 0 4px 20px rgba(0,0,0,0.06); transform: translateY(-2px); }
.feature-dot { width: 8px; height: 8px; border-radius: 50%; margin-bottom: 16px; }
.feature-card h3 { font-size: 15px; font-weight: 700; color: #1e293b; margin: 0 0 8px; }
.feature-card p { font-size: 13px; color: #64748b; line-height: 1.7; margin: 0; }

/* Workflow */
.workflow { max-width: 760px; margin: 0 auto; }
.workflow :deep(.el-step__title) { font-weight: 600; }
.workflow :deep(.el-step__description) { color: #64748b; }

/* Footer */
.footer { text-align: center; margin-top: 56px; padding-top: 24px; border-top: 1px solid #f1f5f9; color: #94a3b8; font-size: 13px; }
</style>
