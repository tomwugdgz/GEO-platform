<template>
  <div class="gaps-diagnosis">
    <div class="header">
      <h1>🎯 缺口诊断</h1>
      <button @click="loadGaps" :disabled="loading" class="btn-secondary">
        刷新
      </button>
    </div>

    <div v-if="hasData" class="content">
      <!-- 缺口统计 -->
      <div class="stats">
        <div class="stat-card">
          <div class="stat-value">{{ gaps.length }}</div>
          <div class="stat-label">内容缺口</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ blockGaps.length }}</div>
          <div class="stat-label">模块缺口</div>
        </div>
      </div>

      <!-- 内容缺口 -->
      <div v-if="gaps.length > 0" class="gap-section">
        <h3>内容缺口</h3>
        <div class="gap-list">
          <div v-for="(gap, idx) in gaps" :key="idx" class="gap-item">
            <div class="gap-title">{{ gap.title || gap.topic || `缺口 ${idx + 1}` }}</div>
            <div v-if="gap.description" class="gap-description">{{ gap.description }}</div>
            <div v-if="gap.priority" class="gap-priority">
              <strong>优先级：</strong>{{ gap.priority }}
            </div>
            <div v-if="gap.suggestion" class="gap-suggestion">
              <strong>建议：</strong>{{ gap.suggestion }}
            </div>
          </div>
        </div>
      </div>

      <!-- 模块缺口 -->
      <div v-if="blockGaps.length > 0" class="gap-section">
        <h3>模块缺口</h3>
        <div class="block-gap-list">
          <div v-for="(block, idx) in blockGaps" :key="idx" class="block-gap-item">
            <div class="block-name">{{ block.block || block.name || `模块 ${idx + 1}` }}</div>
            <div v-if="block.missing_pages" class="missing-pages">
              <strong>缺失页面：</strong>{{ block.missing_pages }}
            </div>
            <div v-if="block.total" class="total-pages">
              <strong>总页面数：</strong>{{ block.total }}
            </div>
            <div v-if="block.coverage" class="coverage">
              <strong>覆盖率：</strong>{{ block.coverage }}%
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <p>暂无缺口数据</p>
      <p class="hint">提示：先执行站点审计以获取缺口诊断数据</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/axios'
import { resolveGeoSlug } from '@/composables/useGeoProject'

const route = useRoute()
// 当前项目：路由参数 → 本地记忆 → 项目列表第一个
let slug = route.params.slug || ''
const gaps = ref([])
const blockGaps = ref([])
const loading = ref(false)

const ensureSlug = async () => {
  if (!slug) slug = await resolveGeoSlug(route.params.slug)
  return slug
}

const hasData = computed(() => gaps.value.length > 0 || blockGaps.value.length > 0)

const loadGaps = async () => {
  const s = await ensureSlug()
  if (!s) return
  loading.value = true
  try {
    const res = await api.get(`/api/v2/geolook/projects/${s}/gaps`)
    gaps.value = res.data.gaps || []
    blockGaps.value = res.data.block_gap || []
  } catch (err) {
    console.error('加载缺口数据失败:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadGaps()
})
</script>

<style scoped>
.gaps-diagnosis {
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

.btn-secondary {
  padding: 10px 20px;
  background: var(--px-bg-elev);
  color: var(--px-text-primary);
  border: 1px solid var(--px-border);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.08);
}

.btn-secondary:disabled {
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
  grid-template-columns: repeat(2, 1fr);
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
  color: #FF9800;
}

.stat-label {
  font-size: 14px;
  color: var(--px-text-dim);
  margin-top: 4px;
}

.gap-section {
  background: var(--px-bg-card);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.gap-section h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
}

.gap-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.gap-item {
  padding: 16px;
  border: 1px solid var(--px-border);
  border-radius: 8px;
  border-left: 4px solid #FF9800;
}

.gap-title {
  font-size: 16px;
  font-weight: bold;
  color: var(--px-text-primary);
  margin-bottom: 8px;
}

.gap-description {
  font-size: 14px;
  color: var(--px-text-dim);
  line-height: 1.5;
  margin-bottom: 8px;
}

.gap-priority, .gap-suggestion {
  font-size: 13px;
  color: var(--px-text-dim);
  margin-bottom: 4px;
}

.block-gap-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.block-gap-item {
  padding: 16px;
  border: 1px solid var(--px-border);
  border-radius: 8px;
  border-left: 4px solid #2196F3;
}

.block-name {
  font-size: 16px;
  font-weight: bold;
  color: var(--px-text-primary);
  margin-bottom: 12px;
}

.missing-pages, .total-pages, .coverage {
  font-size: 13px;
  color: var(--px-text-dim);
  margin-bottom: 4px;
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
