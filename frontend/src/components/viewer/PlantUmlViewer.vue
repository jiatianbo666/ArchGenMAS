<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { deflate } from 'pako'

const props = defineProps<{
  code: string
  title?: string
}>()

const svgContent = ref('')
const loading = ref(false)
const error = ref('')
const showCode = ref(false)

// Kroki 编码: deflate → base64url
function encodeForKroki(plantuml: string): string {
  // 使用 pako (zlib) 压缩
  const compressed = deflate(new TextEncoder().encode(plantuml))
  // Base64 URL-safe 编码
  let binary = ''
  for (let i = 0; i < compressed.length; i++) {
    binary += String.fromCharCode(compressed[i])
  }
  return btoa(binary)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '')
}

async function renderDiagram() {
  if (!props.code?.trim()) {
    error.value = '无 PlantUML 代码'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const encoded = encodeForKroki(props.code.trim())
    const svgUrl = `https://kroki.io/plantuml/svg/${encoded}`

    const resp = await fetch(svgUrl)
    if (!resp.ok) {
      throw new Error(`Kroki 渲染失败: ${resp.status}`)
    }
    svgContent.value = await resp.text()
  } catch (e: any) {
    error.value = e.message || '渲染失败'
    svgContent.value = ''
  } finally {
    loading.value = false
  }
}

watch(() => props.code, () => {
  if (props.code) renderDiagram()
})

onMounted(() => {
  if (props.code) renderDiagram()
})
</script>

<template>
  <div class="plantuml-viewer">
    <!-- 标题栏 -->
    <div class="viewer-header" v-if="title">
      <span class="viewer-title">{{ title }}</span>
      <el-button size="small" text @click="showCode = !showCode">
        {{ showCode ? '隐藏代码' : '查看代码' }}
      </el-button>
    </div>

    <!-- 渲染的图 -->
    <div v-if="loading" class="viewer-loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>渲染中...</span>
    </div>
    <div v-else-if="svgContent" class="viewer-svg" v-html="svgContent" />
    <div v-else-if="error" class="viewer-error">
      <el-alert :title="error" type="warning" show-icon :closable="false" />
    </div>

    <!-- PlantUML 源码（可切换显示） -->
    <div v-if="showCode" class="viewer-code">
      <pre>{{ code }}</pre>
    </div>
  </div>
</template>

<style scoped>
.plantuml-viewer {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}
.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}
.viewer-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
.viewer-loading {
  text-align: center;
  padding: 40px 16px;
  color: #909399;
}
.viewer-error {
  padding: 16px;
}
.viewer-svg {
  padding: 16px;
  overflow-x: auto;
  display: flex;
  justify-content: center;
}
.viewer-svg :deep(svg) {
  max-width: 100%;
  height: auto;
}
.viewer-code {
  padding: 0;
  border-top: 1px solid #ebeef5;
}
.viewer-code pre {
  margin: 0;
  padding: 12px 16px;
  background: #1e1e1e;
  color: #8bc34a;
  font-size: 11px;
  font-family: 'Courier New', monospace;
  overflow-x: auto;
  max-height: 300px;
}
</style>
