<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const features = [
  { icon: 'Document', title: '需求校验 Agent', desc: '自动检测需求完整性、识别逻辑冲突与模糊点，输出结构化需求规格', color: '#409EFF' },
  { icon: 'Cpu', title: '架构设计 Agent', desc: '智能选型体系风格，生成 C4 四层模型 + 4+1 五套视图 + 技术方案', color: '#67C23A' },
  { icon: 'Checked', title: '评审纠错 Agent', desc: 'Critic 批评者模式，检查架构一致性、耦合度、冗余，给出修改建议', color: '#E6A23C' },
  { icon: 'WarningFilled', title: '风险检测 Agent', desc: '四维度风险扫描：性能 · 安全 · 扩展性 · 并发，输出风险清单与缓解方案', color: '#F56C6C' },
  { icon: 'Tickets', title: '文档生成 Agent', desc: '一键整合所有产物，导出标准化 PDF 架构设计文档', color: '#909399' },
]

const steps = [
  { title: '上传需求', desc: '拖拽或粘贴业务需求文档' },
  { title: 'Agent 协同', desc: '5个AI专家依次协作分析' },
  { title: '迭代优化', desc: '评审+风险双重校验，自动迭代' },
  { title: '一键导出', desc: '生成C4/4+1/风险评估/PDF报告' },
]

function goWorkspace() {
  router.push('/workspace')
}
</script>

<template>
  <div class="home-page">
    <!-- Hero -->
    <header class="hero">
      <h1 class="hero-title">ArchGenMAS</h1>
      <p class="hero-subtitle">多智能体协同软件架构自动生成系统</p>
      <p class="hero-desc">
        输入自然语言业务需求，5 大 AI 专家 Agent 协同完成全流程架构设计，<br/>
        一键输出 C4 模型、4+1 视图、风险评估与标准化 PDF 文档。
      </p>
      <el-button type="primary" size="large" round @click="goWorkspace">
        <el-icon><Upload /></el-icon> 开始使用
      </el-button>
    </header>

    <!-- 功能特性 -->
    <section class="features">
      <h2 class="section-title">五大专家 Agent 协同</h2>
      <div class="feature-grid">
        <el-card
          v-for="f in features"
          :key="f.title"
          class="feature-card"
          shadow="hover"
        >
          <el-icon :size="32" :color="f.color">
            <component :is="f.icon" />
          </el-icon>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </el-card>
      </div>
    </section>

    <!-- 工作流程 -->
    <section class="workflow">
      <h2 class="section-title">工作流程</h2>
      <el-steps :active="4" align-center>
        <el-step v-for="s in steps" :key="s.title" :title="s.title" :description="s.desc" />
      </el-steps>
    </section>

    <!-- 页脚 -->
    <footer class="footer">
      <p>Architecture Generation Multi-Agent System © 2026</p>
      <p>Vue 3 + FastAPI · 软件体系结构大作业</p>
    </footer>
  </div>
</template>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.hero {
  text-align: center;
  padding: 60px 20px 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
  margin-top: 24px;
}
.hero-title {
  font-size: 48px;
  font-weight: 800;
  margin: 0 0 8px 0;
  letter-spacing: -1px;
}
.hero-subtitle {
  font-size: 22px;
  margin: 0 0 16px 0;
  opacity: 0.9;
}
.hero-desc {
  font-size: 15px;
  line-height: 1.8;
  opacity: 0.85;
  margin: 0 0 28px 0;
}

.section-title {
  text-align: center;
  font-size: 26px;
  margin: 48px 0 28px;
  color: #303133;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
}
.feature-card {
  text-align: center;
  padding: 12px 0;
}
.feature-card h3 {
  margin: 12px 0 8px;
  font-size: 16px;
}
.feature-card p {
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
}

.workflow {
  max-width: 800px;
  margin: 0 auto;
}

.footer {
  text-align: center;
  padding: 40px 0 24px;
  color: #909399;
  font-size: 13px;
}
</style>
