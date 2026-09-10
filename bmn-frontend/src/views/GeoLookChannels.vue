<template>
  <div class="channels-map">
    <div class="header">
      <h1>🗺️ 渠道地图</h1>
      <div class="header-actions">
        <button @click="generateBlueprint" :disabled="loading" class="btn-primary">
          {{ loading ? '生成中...' : '生成蓝图' }}
        </button>
        <button @click="loadChannels" :disabled="loading" class="btn-secondary">
          刷新
        </button>
      </div>
    </div>

    <div v-if="channels.length > 0" class="content">
      <!-- 渠道统计 -->
      <div class="stats">
        <div class="stat-card">
          <div class="stat-value">{{ channels.length }}</div>
          <div class="stat-label">总渠道数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ coveredCount }}</div>
          <div class="stat-label">已覆盖</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ coverageRate }}%</div>
          <div class="stat-label">覆盖率</div>
        </div>
      </div>

      <!-- 渠道列表 -->
      <div class="channel-list">
        <h3>渠道详情</h3>
        <div class="channel-grid">
          <div v-for="channel in channels" :key="channel.name" 
               :class="['channel-card', { covered: channel.covered }]">
            <div class="channel-header">
              <div class="channel-name">{{ channel.name }}</div>
              <div :class="['channel-status', channel.covered ? 'covered' : 'uncovered']">
                {{ channel.covered ? '已覆盖' : '未覆盖' }}
              </div>
            </div>
            <div class="channel-meta">
              <div v-if="channel.weight" class="channel-weight">
                <strong>权重：</strong>{{ channel.weight }}
              </div>
              <div v-if="channel.priority" class="channel-priority">
                <strong>优先级：</strong>{{ channel.priority }}
              </div>
            </div>
            <div v-if="channel.description" class="channel-description">
              {{ channel.description }}
            </div>
            <div v-if="channel.notes" class="channel-notes">
              {{ channel.notes }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <p>暂无渠道数据</p>
      <p class="hint">提示：点击右上角「生成蓝图」按钮，GeoLook 会算出该在哪些阵地建设、优先级如何</p>
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
const channels = ref([])
const loading = ref(false)

const ensureSlug = async () => {
  if (!slug) slug = await resolveGeoSlug(route.params.slug)
  return slug
}

const coveredCount = computed(() => channels.value.filter(c => c.covered).length)
const coverageRate = computed(() => {
  if (channels.value.length === 0) return 0
  return Math.round((coveredCount.value / channels.value.length) * 100)
})

const loadChannels = async () => {
  const s = await ensureSlug()
  if (!s) return
  loading.value = true
  try {
    const res = await api.get(`/api/v2/geolook/projects/${s}/channels`)
    channels.value = res.data.channels || []
  } catch (err) {
    console.error('加载渠道数据失败:', err)
  } finally {
    loading.value = false
  }
}

// 渠道数据来自 blueprint.json，需要先跑 GeoLook 的 blueprint 命令
const generateBlueprint = async () => {
  const s = await ensureSlug()
  if (!s) return alert(NO_PROJECT_HINT)
  loading.value = true
  try {
    await api.post(`/api/v2/geolook/projects/${s}/blueprint`)
    await loadChannels()
  } catch (err) {
    console.error('生成蓝图失败:', err)
    alert('生成蓝图失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadChannels()
})
</script>

<style scoped>
.channels-map {
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
  gap: 10px;
}

.btn-primary {
  padding: 10px 20px;
  background: #FF5C1A;
  color: #fff;
  border: 1px solid #FF5C1A;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary:hover {
  background: #E8500F;
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

.btn-primary:disabled,
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

.channel-list {
  background: var(--px-bg-card);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.channel-list h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
}

.channel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.channel-card {
  padding: 16px;
  border: 2px solid var(--px-border);
  border-radius: 8px;
  transition: all 0.2s;
}

.channel-card.covered {
  border-color: #4CAF50;
  background: #F1F8F4;
}

.channel-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.channel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.channel-name {
  font-size: 16px;
  font-weight: bold;
  color: var(--px-text-primary);
}

.channel-status {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
}

.channel-status.covered {
  background: #4CAF50;
  color: white;
}

.channel-status.uncovered {
  background: var(--px-bg-elev);
  color: var(--px-text-muted);
}

.channel-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--px-text-dim);
  margin-bottom: 8px;
}

.channel-description {
  font-size: 14px;
  color: var(--px-text-dim);
  line-height: 1.5;
  margin-bottom: 8px;
}

.channel-notes {
  font-size: 13px;
  color: var(--px-text-muted);
  font-style: italic;
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
