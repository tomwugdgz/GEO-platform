<template>
  <div class="engine-settings">
    <div class="header">
      <h1>⚙️ 引擎配置</h1>
      <button @click="loadSettings" :disabled="loading" class="btn-secondary">
        刷新
      </button>
    </div>

    <div v-if="settings || engines.length" class="content">
      <!-- 项目基本信息（仅在有当前项目时展示） -->
      <div v-if="settings" class="section">
        <h3>项目信息</h3>
        <div class="info-grid">
          <div class="info-item">
            <label>项目标识</label>
            <div class="value">{{ settings.slug }}</div>
          </div>
          <div class="info-item">
            <label>目标市场</label>
            <div class="value">{{ marketLabel(settings.market) }}</div>
          </div>
          <div class="info-item">
            <label>品牌名称</label>
            <div class="value">{{ settings.brand?.name || '-' }}</div>
          </div>
          <div class="info-item">
            <label>品牌网站</label>
            <div class="value">
              <a v-if="settings.brand?.site" :href="settings.brand.site" target="_blank">
                {{ settings.brand.site }}
              </a>
              <span v-else>-</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 引擎配置 -->
      <div class="section">
        <h3>引擎配置</h3>
        <div class="engine-list">
          <div v-for="engine in engines" :key="engine.code" class="engine-item">
            <div class="engine-header">
              <div class="engine-info">
                <div class="engine-name">{{ engine.name }}</div>
                <div class="engine-code">{{ engine.code }}</div>
              </div>
              <div :class="['engine-status', engine.configured ? 'configured' : 'not-configured']">
                {{ engine.configured ? '已配置' : '未配置' }}
              </div>
            </div>
            <div class="engine-meta">
              <div class="meta-item">
                <strong>市场：</strong>{{ engine.market === 'cn' ? '中国' : '国际' }}
              </div>
              <div v-if="engine.model" class="meta-item">
                <strong>模型：</strong>{{ engine.model }}
              </div>
            </div>
            <div v-if="!engine.configured" class="engine-hint">
              未配置 API Key —— 该引擎将走<strong>人工采样表</strong>，不影响整体流程跑通
            </div>
          </div>
        </div>
      </div>

      <!-- 目标设置 -->
      <div v-if="settings.targets" class="section">
        <h3>目标设置</h3>
        <div class="targets-grid">
          <div class="target-item">
            <label>提及率目标</label>
            <div class="target-value">{{ (settings.targets.mention_rate * 100).toFixed(0) }}%</div>
          </div>
          <div class="target-item">
            <label>Top3 率目标</label>
            <div class="target-value">{{ (settings.targets.top3_rate * 100).toFixed(0) }}%</div>
          </div>
          <div class="target-item">
            <label>平均页面分数目标</label>
            <div class="target-value">{{ settings.targets.avg_page_score }}</div>
          </div>
        </div>
      </div>

      <!-- 平台列表 -->
      <div v-if="settings.platforms && settings.platforms.length > 0" class="section">
        <h3>启用的平台</h3>
        <div class="platform-tags">
          <span v-for="platform in settings.platforms" :key="platform" class="platform-tag">
            {{ platform }}
          </span>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <p>暂无配置数据</p>
      <p class="hint">提示：请先创建项目</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/axios'
import { resolveGeoSlug } from '@/composables/useGeoProject'

const route = useRoute()
// 当前项目：路由参数 → 本地记忆 → 项目列表第一个
let slug = route.params.slug || ''

const ensureSlug = async () => {
  if (!slug) slug = await resolveGeoSlug(route.params.slug)
  return slug
}
const settings = ref(null)
const engines = ref([])
const loading = ref(false)

const marketLabel = (market) => {
  const labels = {
    cn: '中国',
    global: '国际',
    both: '中国+国际'
  }
  return labels[market] || market
}

const loadSettings = async () => {
  loading.value = true
  const s = await ensureSlug()
  try {
    // 引擎清单与项目无关，始终加载；项目配置仅在有项目时加载
    const tasks = [api.get(`/api/v2/geolook/projects/${s || 'default'}/engines`)]
    if (s) tasks.push(api.get(`/api/v2/geolook/projects/${s}/settings`))

    const [enginesRes, settingsRes] = await Promise.all(tasks)
    engines.value = enginesRes.data.engines || []
    if (settingsRes) settings.value = settingsRes.data
  } catch (err) {
    console.error('加载配置数据失败:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.engine-settings {
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

.section {
  background: var(--px-bg-card);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.section h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: var(--px-text-primary);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.info-item {
  padding: 12px;
  background: var(--px-bg-panel);
  border-radius: 6px;
}

.info-item label {
  display: block;
  font-size: 13px;
  color: var(--px-text-dim);
  margin-bottom: 4px;
}

.info-item .value {
  font-size: 15px;
  color: var(--px-text-primary);
  font-weight: 500;
}

.info-item .value a {
  color: #2196F3;
  text-decoration: none;
}

.info-item .value a:hover {
  text-decoration: underline;
}

.engine-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.engine-item {
  padding: 16px;
  border: 1px solid var(--px-border);
  border-radius: 8px;
  transition: all 0.2s;
}

.engine-item:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.engine-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.engine-info {
  flex: 1;
}

.engine-name {
  font-size: 16px;
  font-weight: bold;
  color: var(--px-text-primary);
  margin-bottom: 4px;
}

.engine-code {
  font-size: 13px;
  color: var(--px-text-muted);
  font-family: monospace;
}

.engine-status {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.engine-status.configured {
  background: #4CAF50;
  color: white;
}

.engine-status.not-configured {
  background: var(--px-bg-elev);
  color: var(--px-text-muted);
}

.engine-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

.meta-item {
  font-size: 13px;
  color: var(--px-text-dim);
}

.engine-hint {
  font-size: 12px;
  color: #FFB74D;
  font-style: italic;
  padding: 8px;
  background: rgba(255, 107, 0, 0.12);
  border-radius: 4px;
}

.targets-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.target-item {
  padding: 16px;
  background: var(--px-bg-panel);
  border-radius: 6px;
  text-align: center;
}

.target-item label {
  display: block;
  font-size: 13px;
  color: var(--px-text-dim);
  margin-bottom: 8px;
}

.target-value {
  font-size: 24px;
  font-weight: bold;
  color: #2196F3;
}

.platform-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.platform-tag {
  padding: 6px 12px;
  background: rgba(0, 240, 255, 0.12);
  color: #2196F3;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
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
