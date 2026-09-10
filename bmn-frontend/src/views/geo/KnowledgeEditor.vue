<template>
  <div class="knowledge-editor">
    <div class="header">
      <div>
        <h2>知识库管理</h2>
        <p class="description">
          管理品牌知识资产（GeoLook 事实库），构建 AI 可理解的知识体系
        </p>
      </div>
      <div class="header-actions">
        <span class="slug-chip" :title="'当前项目：' + (slug || '未选择')">
          {{ slug || '未选择项目' }}
        </span>
        <button @click="loadFacts" :disabled="loading" class="btn-secondary">
          {{ loading ? '加载中...' : '重新加载' }}
        </button>
        <button @click="saveFacts" :disabled="saving || !slug" class="btn-primary">
          {{ saving ? '保存中...' : '保存事实库' }}
        </button>
      </div>
    </div>

    <!-- 无项目引导 -->
    <div v-if="!slug" class="empty">
      <p>还没有可编辑的项目</p>
      <p class="hint">请先到「GEO 诊断」页面创建项目，或在该页面点击某个项目的模块入口</p>
    </div>

    <template v-else>
      <div class="meta-bar">
        <span>文件：work/{{ slug }}/content/facts.md</span>
        <span :class="['status', { ok: exists, warn: !exists }]">
          {{ exists ? '已存在' : '尚未生成（保存后将创建）' }}
        </span>
      </div>

      <div class="editor-layout">
        <textarea
          v-model="facts"
          class="facts-input"
          spellcheck="false"
          placeholder="# 品牌事实库&#10;&#10;## 一句话定义&#10;...&#10;&#10;## 关键数字&#10;...&#10;&#10;> 提示：GeoLook 会把这些事实用于生成 llms.txt、JSON-LD 与内容片段，写清证据等级更有用。"
        ></textarea>

        <aside class="tips">
          <h4>填写建议</h4>
          <ul>
            <li>一句话定义要<strong>逐字统一</strong>，与官网首屏/关于页保持一致</li>
            <li>数字类事实标注来源与时间，避免 AI 引用过期数据</li>
            <li>区分「已证实」与「待核实」，降低编造风险</li>
            <li>保存后可直接运行「验收闭环」复核达标情况</li>
          </ul>
          <p v-if="message" :class="['msg', messageType]">{{ message }}</p>
        </aside>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/axios'
import { resolveGeoSlug, NO_PROJECT_HINT } from '@/composables/useGeoProject'

const route = useRoute()
let slug = route.params.slug || ''

const facts = ref('')
const exists = ref(false)
const loading = ref(false)
const saving = ref(false)
const message = ref('')
const messageType = ref('success')

const ensureSlug = async () => {
  if (!slug) slug = await resolveGeoSlug(route.params.slug)
  return slug
}

const loadFacts = async () => {
  const s = await ensureSlug()
  if (!s) return
  loading.value = true
  try {
    const res = await api.get(`/api/v2/geolook/projects/${s}/facts`)
    facts.value = res.data.facts || ''
    exists.value = !!res.data.exists
  } catch (err) {
    message.value = '加载失败：' + (err.response?.data?.detail || err.message)
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}

const saveFacts = async () => {
  const s = await ensureSlug()
  if (!s) return alert(NO_PROJECT_HINT)
  saving.value = true
  try {
    await api.put(`/api/v2/geolook/projects/${s}/facts`, { facts: facts.value })
    exists.value = true
    message.value = '已保存到 facts.md'
    messageType.value = 'success'
  } catch (err) {
    message.value = '保存失败：' + (err.response?.data?.detail || err.message)
    messageType.value = 'error'
  } finally {
    saving.value = false
  }
}

onMounted(loadFacts)
</script>

<style scoped>
.knowledge-editor {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.header h2 {
  margin: 0 0 6px;
}

.description {
  color: var(--px-text-dim);
  margin: 0;
  font-size: 14px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.slug-chip {
  padding: 6px 10px;
  border-radius: 6px;
  background: rgba(255, 92, 26, 0.08);
  border: 1px solid rgba(255, 92, 26, 0.22);
  color: #FF5C1A;
  font-size: 12px;
}

.btn-primary,
.btn-secondary {
  padding: 9px 16px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  border: 1px solid transparent;
}

.btn-primary {
  background: #FF5C1A;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #E8500F;
}

.btn-secondary {
  background: var(--px-bg-elev);
  border-color: #ddd;
  color: var(--px-text-primary);
}

.btn-secondary:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.08);
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.meta-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 18px 0 10px;
  font-size: 12px;
  color: var(--px-text-muted);
}

.status.ok {
  color: #2E7D32;
}

.status.warn {
  color: #EF6C00;
}

.editor-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 18px;
  align-items: start;
}

.facts-input {
  width: 100%;
  min-height: 460px;
  padding: 16px;
  border: 1px solid var(--px-border);
  border-radius: 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
  line-height: 1.7;
  resize: vertical;
  background: var(--px-bg-card);
}

.facts-input:focus {
  outline: none;
  border-color: #FF5C1A;
}

.tips {
  background: var(--px-bg-panel);
  border: 1px solid var(--px-border);
  border-radius: 10px;
  padding: 16px;
  font-size: 13px;
  color: var(--px-text-dim);
}

.tips h4 {
  margin: 0 0 10px;
  font-size: 13px;
  color: var(--px-text-primary);
}

.tips ul {
  margin: 0;
  padding-left: 18px;
  line-height: 1.8;
}

.msg {
  margin: 12px 0 0;
  font-size: 12px;
}

.msg.success {
  color: #2E7D32;
}

.msg.error {
  color: #C62828;
}

.empty {
  text-align: center;
  padding: 50px 20px;
  background: var(--px-bg-card);
  border-radius: 12px;
  margin-top: 20px;
}

.hint {
  color: var(--px-text-muted);
  font-size: 13px;
}

@media (max-width: 1024px) {
  .editor-layout {
    grid-template-columns: 1fr;
  }
}
</style>
