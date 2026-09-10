<template>
  <div class="site-audit">
    <div class="header">
      <h1>🔍 站点审计</h1>
      <button @click="runAudit" :disabled="loading" class="btn-primary">
        {{ loading ? '审计中...' : '运行审计' }}
      </button>
    </div>

    <div v-if="auditData && auditData.exists" class="content">
      <!-- 总体评分 -->
      <div class="score-card">
        <div class="score-value">{{ auditData.avg_score }}</div>
        <div class="score-label">平均得分</div>
        <div class="page-count">共 {{ auditData.page_count }} 个页面</div>
      </div>

      <!-- 等级分布 -->
      <div class="grade-distribution">
        <h3>等级分布</h3>
        <div class="grades">
          <div v-for="(count, grade) in auditData.grade_distribution" :key="grade" 
               :class="['grade-item', `grade-${grade}`]">
            <div class="grade-value">{{ count }}</div>
            <div class="grade-label">{{ grade }}</div>
          </div>
        </div>
      </div>

      <!-- 四层依赖链 -->
      <div class="layers">
        <h3>四层依赖链</h3>
        <div class="layer-list">
          <div v-for="layer in auditData.layers" :key="layer.key" 
               :class="['layer-item', `status-${layer.status}`]">
            <div class="layer-header">
              <span class="layer-name">{{ layer.name }}</span>
              <span class="layer-status">{{ layer.status }}</span>
            </div>
            <div class="layer-question">{{ layer.question }}</div>
          </div>
        </div>
      </div>

      <!-- 站点问题 -->
      <div v-if="auditData.site_issues && auditData.site_issues.length > 0" class="site-issues">
        <h3>站点问题</h3>
        <ul class="issue-list">
          <li v-for="(issue, idx) in auditData.site_issues" :key="idx">{{ issue }}</li>
        </ul>
      </div>

      <!-- 页面列表 -->
      <div class="pages">
        <h3>页面详情 ({{ auditData.pages.length }})</h3>
        <div class="page-table">
          <div v-for="page in auditData.pages" :key="page.url" class="page-row">
            <div class="page-url">{{ page.url }}</div>
            <div class="page-score">{{ page.score }}</div>
            <div :class="['page-grade', `grade-${page.grade}`]">{{ page.grade }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <p>暂无审计数据，请点击"运行审计"开始分析</p>
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
const auditData = ref(null)
const loading = ref(false)

const ensureSlug = async () => {
  if (!slug) slug = await resolveGeoSlug(route.params.slug)
  return slug
}

const loadAudit = async () => {
  const s = await ensureSlug()
  if (!s) return
  try {
    const res = await api.get(`/api/v2/geolook/projects/${s}/siteaudit`)
    auditData.value = res.data
  } catch (err) {
    console.error('加载审计数据失败:', err)
  }
}

const runAudit = async () => {
  const s = await ensureSlug()
  if (!s) return alert(NO_PROJECT_HINT)
  loading.value = true
  try {
    await api.post(`/api/v2/geolook/projects/${s}/audit`)
    await loadAudit()
  } catch (err) {
    console.error('审计失败:', err)
    alert('审计失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAudit()
})
</script>

<style scoped>
.site-audit {
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

.score-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 32px;
  border-radius: 12px;
  text-align: center;
}

.score-value {
  font-size: 64px;
  font-weight: bold;
  line-height: 1;
}

.score-label {
  font-size: 16px;
  margin-top: 8px;
  opacity: 0.9;
}

.page-count {
  font-size: 14px;
  margin-top: 4px;
  opacity: 0.8;
}

.grade-distribution {
  background: var(--px-bg-card);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.grade-distribution h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
}

.grades {
  display: flex;
  gap: 16px;
}

.grade-item {
  flex: 1;
  text-align: center;
  padding: 16px;
  border-radius: 8px;
}

.grade-A { background: #4CAF50; color: white; }
.grade-B { background: #8BC34A; color: white; }
.grade-C { background: #FFC107; color: white; }
.grade-D { background: #F44336; color: white; }

.grade-value {
  font-size: 32px;
  font-weight: bold;
}

.grade-label {
  font-size: 14px;
  margin-top: 4px;
}

.layers {
  background: var(--px-bg-card);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.layers h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
}

.layer-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.layer-item {
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid;
}

.layer-item.status-pass { border-left-color: #4CAF50; background: rgba(57, 255, 20, 0.12); }
.layer-item.status-warn { border-left-color: #FFC107; background: #FFF8E1; }
.layer-item.status-fail { border-left-color: #F44336; background: rgba(255, 46, 151, 0.14); }

.layer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.layer-name {
  font-weight: bold;
  font-size: 16px;
}

.layer-status {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  background: rgba(0,0,0,0.1);
}

.layer-question {
  font-size: 14px;
  color: var(--px-text-dim);
}

.site-issues {
  background: var(--px-bg-card);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.site-issues h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
}

.issue-list {
  margin: 0;
  padding-left: 20px;
}

.issue-list li {
  margin-bottom: 8px;
  color: var(--px-text-dim);
}

.pages {
  background: var(--px-bg-card);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.pages h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
}

.page-table {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px;
  background: var(--px-bg-elev);
  border-radius: 6px;
}

.page-url {
  flex: 1;
  font-size: 14px;
  color: var(--px-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.page-score {
  font-weight: bold;
  font-size: 16px;
  min-width: 40px;
  text-align: center;
}

.page-grade {
  padding: 4px 12px;
  border-radius: 4px;
  font-weight: bold;
  font-size: 14px;
  min-width: 30px;
  text-align: center;
}

.grade-A { background: #4CAF50; color: white; }
.grade-B { background: #8BC34A; color: white; }
.grade-C { background: #FFC107; color: white; }
.grade-D { background: #F44336; color: white; }

.empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--px-text-muted);
}
</style>
