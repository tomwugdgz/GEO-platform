<template>
  <div class="verify-closure">
    <div class="header">
      <h1>✅ 验收闭环</h1>
      <div class="header-actions">
        <!-- 完整验收会重抓官网并重跑体检，耗时较长；勾选则基于现有数据判定 -->
        <label class="recheck-toggle">
          <input type="checkbox" v-model="noRecrawl" />
          跳过重抓（用现有数据判定，更快）
        </label>
        <button @click="runVerify" :disabled="loading" class="btn-primary">
          {{ loading ? '验收中...' : '运行验收' }}
        </button>
      </div>
    </div>

    <div v-if="verifyResult && verifyResult.exists" class="content">
      <!-- 验收统计 -->
      <div class="stats">
        <div class="stat-card">
          <div class="stat-value">{{ verifyResult.total_tasks || 0 }}</div>
          <div class="stat-label">总任务数</div>
        </div>
        <div class="stat-card success">
          <div class="stat-value">{{ verifyResult.passed_tasks || 0 }}</div>
          <div class="stat-label">通过验收</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-value">{{ verifyResult.failed_tasks || 0 }}</div>
          <div class="stat-label">未通过</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ passRate }}%</div>
          <div class="stat-label">通过率</div>
        </div>
      </div>

      <!-- 验收详情 -->
      <div v-if="verifyResult.details && verifyResult.details.length > 0" class="verify-details">
        <h3>验收详情</h3>
        <div class="detail-list">
          <div v-for="(detail, idx) in verifyResult.details" :key="idx" 
               :class="['detail-item', detail.status]">
            <div class="detail-header">
              <span class="task-id">{{ detail.task_id }}</span>
              <span :class="['status-badge', detail.status]">{{ statusLabel(detail.status) }}</span>
            </div>
            <div class="task-title">{{ detail.title }}</div>
            <div v-if="detail.reason" class="verify-reason">
              <strong>{{ detail.status === 'passed' ? '验证依据' : '失败原因' }}：</strong>
              {{ detail.reason }}
            </div>
            <div v-if="detail.evidence" class="verify-evidence">
              <strong>证据：</strong>{{ detail.evidence }}
            </div>
          </div>
        </div>
      </div>

      <!-- 验收总结 -->
      <div class="summary">
        <h3>验收总结</h3>
        <div class="summary-content">
          <p><strong>验收时间：</strong>{{ formatTime(verifyResult.verify_time) }}</p>
          <p v-if="verifyResult.recheck"><strong>重新检查：</strong>{{ verifyResult.recheck ? '是' : '否' }}</p>
          <p v-if="verifyResult.notes"><strong>备注：</strong>{{ verifyResult.notes }}</p>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <p>暂无验收数据</p>
      <p class="hint">提示：点击"运行验收"开始验收流程</p>
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
const verifyResult = ref(null)
const loading = ref(false)
// 是否跳过重抓：完整验收含爬取 + 体检，耗时可达数分钟
const noRecrawl = ref(true)

const ensureSlug = async () => {
  if (!slug) slug = await resolveGeoSlug(route.params.slug)
  return slug
}

const passRate = computed(() => {
  if (!verifyResult.value || !verifyResult.value.total_tasks) return 0
  return Math.round((verifyResult.value.passed_tasks / verifyResult.value.total_tasks) * 100)
})

const statusLabel = (status) => {
  const labels = {
    passed: '通过',
    failed: '未通过',
    pending: '待验收'
  }
  return labels[status] || status
}

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}

const runVerify = async () => {
  const s = await ensureSlug()
  if (!s) return alert(NO_PROJECT_HINT)
  loading.value = true
  try {
    const res = await api.post(
      `/api/v2/geolook/projects/${s}/verify`,
      null,
      { params: { no_recrawl: noRecrawl.value }, timeout: 900000 }
    )
    verifyResult.value = res.data
  } catch (err) {
    console.error('验收失败:', err)
    alert('验收失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

const loadVerifyResult = async () => {
  const s = await ensureSlug()
  if (!s) return
  try {
    const res = await api.get(`/api/v2/geolook/projects/${s}/verify`)
    verifyResult.value = res.data
  } catch (err) {
    console.error('加载验收数据失败:', err)
  }
}

onMounted(() => {
  loadVerifyResult()
})
</script>

<style scoped>
.verify-closure {
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 14px;
}

.recheck-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--px-text-dim);
  cursor: pointer;
  user-select: none;
}

.btn-primary {
  padding: 10px 20px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary:hover {
  background: #45a049;
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
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: var(--px-bg-card);
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.stat-card.success {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-card.warning {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
}

.stat-label {
  font-size: 14px;
  margin-top: 4px;
  opacity: 0.9;
}

.verify-details {
  background: var(--px-bg-card);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.verify-details h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
}

.detail-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-item {
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid;
}

.detail-item.passed {
  border-left-color: #4CAF50;
  background: #f1f8f4;
}

.detail-item.failed {
  border-left-color: #f44336;
  background: #fef1f1;
}

.detail-item.pending {
  border-left-color: #ff9800;
  background: #fff8f1;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-id {
  font-weight: bold;
  color: var(--px-text-primary);
}

.status-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.passed {
  background: #4CAF50;
  color: white;
}

.status-badge.failed {
  background: #f44336;
  color: white;
}

.status-badge.pending {
  background: #ff9800;
  color: white;
}

.task-title {
  font-size: 15px;
  color: var(--px-text-primary);
  margin-bottom: 8px;
}

.verify-reason, .verify-evidence {
  font-size: 13px;
  color: var(--px-text-dim);
  margin-top: 8px;
  line-height: 1.5;
}

.summary {
  background: var(--px-bg-card);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.summary h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
}

.summary-content p {
  margin: 8px 0;
  font-size: 14px;
  color: var(--px-text-dim);
  line-height: 1.6;
}

.empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--px-text-muted);
}

.hint {
  font-size: 14px;
  color: #bbb;
  margin-top: 8px;
}
</style>
