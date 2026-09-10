<template>
  <div class="competitor-analysis">
    <div class="header">
      <h1>🏆 竞品分析</h1>
      <div class="header-actions">
        <button @click="showAdd = !showAdd" class="btn-primary">
          {{ showAdd ? '收起' : '添加竞品' }}
        </button>
        <button @click="loadCompetitors" :disabled="loading" class="btn-secondary">
          刷新
        </button>
      </div>
    </div>

    <!-- 新增竞品表单：写入 work/<slug>/geo.json，GeoLook 后续命令直接读取 -->
    <div v-if="showAdd" class="add-competitor">
      <input v-model="form.name" placeholder="竞品名称 *（如 必应/Bing）" />
      <input v-model="form.site" placeholder="官网地址（可选）" />
      <input v-model="form.notes" placeholder="备注：为什么拿它做对照（可选）" />
      <button @click="addCompetitor" :disabled="saving" class="btn-primary">
        {{ saving ? '保存中...' : '保存' }}
      </button>
    </div>

    <div v-if="competitors.length > 0" class="content">
      <!-- 竞品列表 -->
      <div class="competitor-list">
        <h3>竞品列表 ({{ competitors.length }})</h3>
        <div class="competitor-grid">
          <div v-for="competitor in competitors" :key="competitor.name" class="competitor-card">
            <div class="competitor-header">
              <div class="competitor-name">{{ competitor.name }}</div>
              <div class="competitor-type">{{ competitor.type || '竞品' }}</div>
            </div>
            <div v-if="competitor.site" class="competitor-site">
              <a :href="competitor.site" target="_blank">{{ competitor.site }}</a>
            </div>
            <div v-if="competitor.aliases" class="competitor-aliases">
              <strong>别名：</strong>{{ competitor.aliases.join(', ') }}
            </div>
            <div v-if="competitor.notes" class="competitor-notes">
              {{ competitor.notes }}
            </div>
          </div>
        </div>
      </div>

      <!-- 竞品对比矩阵（仅在体检数据存在时展示） -->
      <div v-if="auditData && auditData.exists" class="comparison-matrix">
        <h3>竞品对比矩阵</h3>
        <div class="matrix-info">
          <p>基于审计数据，分析各竞品在不同维度的表现</p>
          <div class="matrix-stats">
            <div class="stat-item">
              <div class="stat-label">平均得分</div>
              <div class="stat-value">{{ auditData.avg_score }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-label">页面数量</div>
              <div class="stat-value">{{ auditData.page_count }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <p>暂无竞品数据</p>
      <p class="hint">提示：点击右上角「添加竞品」，填入对照组品牌即可（也可先跑 bootstrap 自动推导）</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/axios'
import { resolveGeoSlug, NO_PROJECT_HINT } from '@/composables/useGeoProject'

const route = useRoute()
// 当前项目：路由参数 → 本地记忆 → 项目列表第一个
let slug = route.params.slug || ''
const competitors = ref([])
const auditData = ref(null)
const loading = ref(false)

const showAdd = ref(false)
const saving = ref(false)
const form = ref({ name: '', site: '', notes: '' })

const ensureSlug = async () => {
  if (!slug) slug = await resolveGeoSlug(route.params.slug)
  return slug
}

const loadCompetitors = async () => {
  const s = await ensureSlug()
  if (!s) return
  loading.value = true
  try {
    const [compRes, auditRes] = await Promise.all([
      api.get(`/api/v2/geolook/projects/${s}/competitors`),
      api.get(`/api/v2/geolook/projects/${s}/siteaudit`).catch(() => null)
    ])
    competitors.value = compRes.data.competitors || []
    if (auditRes) {
      auditData.value = auditRes.data
    }
  } catch (err) {
    console.error('加载竞品数据失败:', err)
  } finally {
    loading.value = false
  }
}

// 追加竞品到 geo.json（GeoLook 的 plan / verify 会直接读取该字段）
const addCompetitor = async () => {
  const s = await ensureSlug()
  if (!s) return alert(NO_PROJECT_HINT)
  if (!form.value.name.trim()) return alert('请填写竞品名称')

  saving.value = true
  try {
    await api.post(`/api/v2/geolook/projects/${s}/competitors`, {
      name: form.value.name.trim(),
      site: form.value.site.trim(),
      aliases: [],
      notes: form.value.notes.trim(),
    })
    form.value = { name: '', site: '', notes: '' }
    showAdd.value = false
    await loadCompetitors()
  } catch (err) {
    console.error('添加竞品失败:', err)
    alert('添加竞品失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadCompetitors()
})
</script>

<style scoped>
.competitor-analysis {
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

.add-competitor {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--px-bg-panel);
  border: 1px solid var(--px-border);
  border-radius: 8px;
}

.add-competitor input {
  flex: 1 1 220px;
  padding: 9px 12px;
  border: 1px solid var(--px-border);
  border-radius: 6px;
  font-size: 14px;
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

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

.competitor-list {
  background: var(--px-bg-card);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.competitor-list h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
}

.competitor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.competitor-card {
  padding: 16px;
  border: 1px solid var(--px-border);
  border-radius: 8px;
  transition: all 0.2s;
}

.competitor-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.competitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.competitor-name {
  font-size: 18px;
  font-weight: bold;
  color: var(--px-text-primary);
}

.competitor-type {
  font-size: 12px;
  padding: 4px 8px;
  background: rgba(0, 240, 255, 0.12);
  color: #2196F3;
  border-radius: 4px;
}

.competitor-site {
  margin-bottom: 8px;
}

.competitor-site a {
  color: #2196F3;
  text-decoration: none;
  font-size: 14px;
}

.competitor-site a:hover {
  text-decoration: underline;
}

.competitor-aliases {
  font-size: 13px;
  color: var(--px-text-dim);
  margin-bottom: 8px;
}

.competitor-notes {
  font-size: 14px;
  color: var(--px-text-dim);
  line-height: 1.5;
}

.comparison-matrix {
  background: var(--px-bg-card);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.comparison-matrix h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
}

.matrix-info {
  color: var(--px-text-dim);
  font-size: 14px;
}

.matrix-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-top: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: var(--px-bg-elev);
  border-radius: 8px;
}

.stat-label {
  font-size: 14px;
  color: var(--px-text-dim);
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #2196F3;
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
