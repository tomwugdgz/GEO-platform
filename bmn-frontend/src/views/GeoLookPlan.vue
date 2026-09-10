<template>
  <div class="plan-management">
    <div class="header">
      <h1>📋 工单管理</h1>
      <button @click="generatePlan" :disabled="loading" class="btn-primary">
        {{ loading ? '生成中...' : '生成工单' }}
      </button>
    </div>

    <div v-if="tasks.length > 0" class="content">
      <!-- 统计卡片 -->
      <div class="stats">
        <div class="stat-card">
          <div class="stat-value">{{ tasks.length }}</div>
          <div class="stat-label">总工单数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ completedCount }}</div>
          <div class="stat-label">已完成</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ pendingCount }}</div>
          <div class="stat-label">待处理</div>
        </div>
      </div>

      <!-- 工单列表 -->
      <div class="task-list">
        <h3>工单列表</h3>
        <div v-for="task in tasks" :key="task.id" :class="['task-item', `priority-${task.priority}`, `status-${task.status}`]">
          <div class="task-header">
            <span class="task-id">{{ task.id }}</span>
            <span :class="['task-priority', `priority-${task.priority}`]">{{ task.priority }}</span>
            <span :class="['task-status', `status-${task.status}`]">{{ task.status_label || statusLabel(task.status) }}</span>
          </div>
          <div class="task-title">{{ task.title }}</div>
          <div class="task-meta">
            <span v-if="task.package">📦 {{ task.package }}</span>
            <span v-if="task.owner">👤 {{ task.owner }}</span>
            <span v-if="task.market">🌍 {{ marketLabel(task.market) }}</span>
            <span v-if="task.effort">⏱ 工时 {{ task.effort }}</span>
            <span v-if="task.window">📅 窗口 {{ task.window }}</span>
          </div>
          <!-- 依据：GeoLook 原始字段是 why，兼容 rationale -->
          <div v-if="task.why || task.rationale" class="task-rationale">{{ task.why || task.rationale }}</div>
          <!-- 动作 -->
          <div v-if="task.action" class="task-rationale"><strong>动作：</strong>{{ task.action }}</div>
          <div v-if="task.acceptance" class="task-acceptance">
            <strong>验收标准：</strong>{{ acceptanceText(task.acceptance) }}
          </div>
          <div v-if="task.affected && task.affected.length" class="task-meta">
            <span>🎯 影响 {{ task.affected.length }} 个页面</span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <p>暂无工单，请点击"生成工单"开始</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/axios'
import { resolveGeoSlug, NO_PROJECT_HINT } from '@/composables/useGeoProject'

const route = useRoute()
// 当前项目：路由参数 → 本地记忆 → 项目列表第一个
let slug = route.params.slug || ''
const tasks = ref([])
const loading = ref(false)

const ensureSlug = async () => {
  if (!slug) slug = await resolveGeoSlug(route.params.slug)
  return slug
}

const completedCount = computed(() => tasks.value.filter(t => t.status === 'done').length)
const pendingCount = computed(() => tasks.value.filter(t => t.status !== 'done').length)

// 工单状态中文标签（与 GeoLook tasks.py 的状态机一致）
const STATUS_LABELS = {
  todo: '待办', doing: '进行中', done: '已完成',
  blocked: '受阻', wontfix: '不修复'
}
const statusLabel = (status) => STATUS_LABELS[status] || status || '-'

// 市场口径：GeoLook 里是 cn / global / both
const MARKET_LABELS = { cn: '中国', global: '国际', both: '中国+国际' }
const marketLabel = (market) => MARKET_LABELS[market] || market || '-'

// 验收标准在 tasks.json 里是对象 {type, check, desc}，需转成可读文本
const acceptanceText = (acceptance) => {
  if (!acceptance) return '-'
  if (typeof acceptance === 'string') return acceptance
  const kind = acceptance.type === 'auto' ? '自动判定' : '人工确认'
  const parts = []
  if (acceptance.desc) parts.push(acceptance.desc)
  if (acceptance.check) parts.push(`检查项：${acceptance.check}`)
  return `${parts.join('；')}（${kind}）`
}

const loadTasks = async () => {
  const s = await ensureSlug()
  if (!s) return
  try {
    const res = await api.get(`/api/v2/geolook/projects/${s}/tasks`)
    tasks.value = res.data.tasks || []
  } catch (err) {
    console.error('加载工单失败:', err)
  }
}

const generatePlan = async () => {
  const s = await ensureSlug()
  if (!s) return alert(NO_PROJECT_HINT)
  loading.value = true
  try {
    await api.post(`/api/v2/geolook/projects/${s}/plan`)
    await loadTasks()
  } catch (err) {
    console.error('生成工单失败:', err)
    alert('生成工单失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.plan-management {
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header h1 {
  margin: 0;
  font-size: 24px;
}

.btn-primary {
  padding: 10px 20px;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-card {
  background: var(--px-bg-card);
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #2196F3;
}

.stat-label {
  font-size: 14px;
  color: var(--px-text-dim);
  margin-top: 4px;
}

.task-list {
  background: var(--px-bg-card);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.task-list h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
}

.task-item {
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 12px;
  border-left: 4px solid;
}

.task-item.priority-P0 { border-left-color: #F44336; }
.task-item.priority-P1 { border-left-color: #FF9800; }
.task-item.priority-P2 { border-left-color: #2196F3; }

.task-item.status-done { opacity: 0.6; }

.task-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.task-id {
  font-weight: bold;
  color: var(--px-text-primary);
}

.task-priority, .task-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.task-priority.priority-P0 { background: rgba(255, 46, 151, 0.18); color: #FF6B9D; }
.task-priority.priority-P1 { background: rgba(255, 107, 0, 0.18); color: #FFA74D; }
.task-priority.priority-P2 { background: rgba(0, 240, 255, 0.14); color: #4DD8FF; }

/* 状态徽章：深色背景下需保证对比度 */
.task-status.status-todo { background: rgba(139, 155, 191, 0.18); color: #B7C4DC; }
.task-status.status-doing { background: rgba(0, 240, 255, 0.16); color: #4DD8FF; }
.task-status.status-done { background: rgba(57, 255, 20, 0.16); color: #7CE85F; }
.task-status.status-blocked { background: rgba(255, 46, 151, 0.18); color: #FF6B9D; }
.task-status.status-wontfix { background: rgba(139, 155, 191, 0.14); color: #8B9BBF; }

.task-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  color: var(--px-text-primary);
}

.task-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--px-text-dim);
  margin-bottom: 8px;
}

.task-rationale {
  font-size: 14px;
  color: var(--px-text-dim);
  margin-bottom: 8px;
  line-height: 1.5;
}

.task-acceptance {
  font-size: 13px;
  color: #4CAF50;
  background: rgba(57, 255, 20, 0.12);
  padding: 8px;
  border-radius: 4px;
}

.empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--px-text-muted);
}
</style>
