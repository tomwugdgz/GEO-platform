<template>
  <div class="cyber-page">
    <h1 class="cyber-title">🎯 AI追踪</h1>
    <p class="cyber-subtitle">监测品牌在主流AI平台的回答出镜、引用与推荐表现</p>

    <!-- 核心指标卡片 -->
    <div class="metrics-grid cyber-grid-4 cyber-mb-24">
      <div class="metric-card">
        <div class="metric-icon">📊</div>
        <div class="metric-body">
          <div class="metric-label">总出镜率</div>
          <div class="metric-value cyber-text-neon">{{ metrics.appearanceRate }}%</div>
          <div class="metric-trend up">↑ {{ metrics.appearanceTrend }}%</div>
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-icon">🔗</div>
        <div class="metric-body">
          <div class="metric-label">引用次数</div>
          <div class="metric-value" style="color: var(--cyber-neon-cyan);">{{ metrics.citations }}</div>
          <div class="metric-trend up">↑ {{ metrics.citationTrend }}%</div>
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-icon">⭐</div>
        <div class="metric-body">
          <div class="metric-label">推荐排名</div>
          <div class="metric-value" style="color: var(--cyber-neon-yellow);">TOP {{ metrics.rank }}</div>
          <div class="metric-trend down">↓ {{ metrics.rankTrend }}</div>
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-icon">📈</div>
        <div class="metric-body">
          <div class="metric-label">监测问答数</div>
          <div class="metric-value" style="color: var(--cyber-neon-purple);">{{ metrics.totalQueries }}</div>
          <div class="metric-trend up">+{{ metrics.queryTrend }}/今日</div>
        </div>
      </div>
    </div>

    <!-- 平台监控 -->
    <div class="cyber-card cyber-mb-24">
      <div class="cyber-flex-between cyber-mb-16">
        <h3>平台监测矩阵</h3>
        <div class="cyber-flex">
          <select v-model="timeRange" class="cyber-selector">
            <option value="7d">近7天</option>
            <option value="30d">近30天</option>
            <option value="90d">近90天</option>
          </select>
          <button class="cyber-btn" @click="refreshData">🔄 刷新数据</button>
        </div>
      </div>

      <div class="platform-matrix">
        <div v-for="p in platforms" :key="p.id" class="matrix-row">
          <div class="matrix-platform">
            <span class="platform-icon">{{ p.icon }}</span>
            <div>
              <div class="platform-name">{{ p.name }}</div>
              <div class="cyber-text-muted" style="font-size: 11px;">{{ p.status }}</div>
            </div>
          </div>
          <div class="matrix-metrics">
            <div class="matrix-item">
              <div class="matrix-label">出镜</div>
              <div class="matrix-value" :style="{ color: getScoreColor(p.appearance) }">{{ p.appearance }}%</div>
            </div>
            <div class="matrix-item">
              <div class="matrix-label">引用</div>
              <div class="matrix-value" :style="{ color: getScoreColor(p.citation) }">{{ p.citation }}%</div>
            </div>
            <div class="matrix-item">
              <div class="matrix-label">推荐</div>
              <div class="matrix-value" :style="{ color: getScoreColor(p.recommend) }">{{ p.recommend }}%</div>
            </div>
            <div class="matrix-item">
              <div class="matrix-label">排名</div>
              <div class="matrix-value cyber-text-neon">#{{ p.rank }}</div>
            </div>
          </div>
          <div class="matrix-trend">
            <div class="trend-bars">
              <div 
                v-for="(v, i) in p.trend" 
                :key="i" 
                class="trend-bar"
                :style="{ height: v + '%', background: `linear-gradient(180deg, var(--cyber-neon-green), transparent)` }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 实时问答追踪 -->
    <div class="cyber-card">
      <div class="cyber-flex-between cyber-mb-16">
        <h3>实时问答追踪</h3>
        <div class="cyber-flex">
          <input 
            v-model="querySearch"
            class="cyber-input"
            style="width: 240px;"
            placeholder="搜索监测的问答..."
          />
          <button class="cyber-btn cyber-btn-secondary">添加监测</button>
        </div>
      </div>

      <table class="cyber-table">
        <thead>
          <tr>
            <th>问题</th>
            <th>平台</th>
            <th>出镜状态</th>
            <th>排名</th>
            <th>引用方式</th>
            <th>监测时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(q, idx) in filteredQueries" :key="idx">
            <td class="query-text">{{ q.question }}</td>
            <td>
              <span class="cyber-tag">{{ q.platform }}</span>
            </td>
            <td>
              <span class="cyber-tag" :class="statusClass(q.status)">
                {{ statusLabel(q.status) }}
              </span>
            </td>
            <td>
              <span class="rank-badge" :class="rankClass(q.rank)">#{{ q.rank }}</span>
            </td>
            <td>{{ q.citationType }}</td>
            <td class="cyber-text-muted">{{ q.time }}</td>
            <td>
              <button class="cyber-icon-btn" @click="viewDetail(q)">👁️</button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="filteredQueries.length === 0" class="cyber-empty">
        <div class="cyber-empty-icon">📭</div>
        <div>暂无监测数据</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const timeRange = ref('7d')
const querySearch = ref('')

const metrics = ref({
  appearanceRate: 78.5,
  appearanceTrend: 12.3,
  citations: 342,
  citationTrend: 8.7,
  rank: 3,
  rankTrend: 2,
  totalQueries: 1247,
  queryTrend: 56
})

const platforms = ref([
  { id: 'doubao', name: '豆包', icon: '🫘', status: '监测中', appearance: 85, citation: 72, recommend: 68, rank: 2, trend: [60, 65, 70, 68, 75, 80, 85] },
  { id: 'deepseek', name: 'DeepSeek', icon: '🔮', status: '监测中', appearance: 78, citation: 80, recommend: 75, rank: 3, trend: [70, 72, 75, 78, 76, 80, 78] },
  { id: 'kimi', name: 'Kimi', icon: '🌙', status: '监测中', appearance: 72, citation: 68, recommend: 65, rank: 4, trend: [65, 68, 70, 72, 74, 72, 72] },
  { id: 'chatgpt', name: 'ChatGPT', icon: '🤖', status: '监测中', appearance: 65, citation: 60, recommend: 58, rank: 5, trend: [55, 58, 60, 62, 65, 63, 65] },
  { id: 'google', name: 'Google AI', icon: '🔍', status: '监测中', appearance: 58, citation: 55, recommend: 52, rank: 6, trend: [50, 52, 55, 58, 56, 58, 58] },
  { id: 'baidu', name: '文心一言', icon: '🐾', status: '监测中', appearance: 90, citation: 88, recommend: 85, rank: 1, trend: [80, 82, 85, 87, 88, 90, 90] },
  { id: 'tongyi', name: '通义千问', icon: '☁️', status: '监测中', appearance: 70, citation: 65, recommend: 62, rank: 4, trend: [60, 63, 65, 68, 70, 72, 70] },
  { id: 'yuanbao', name: '腾讯元宝', icon: '🪙', status: '监测中', appearance: 75, citation: 72, recommend: 70, rank: 3, trend: [65, 68, 70, 73, 75, 74, 75] },
])

const queries = ref([
  { question: '社区门禁系统哪家靠谱？', platform: '豆包', status: 'top3', rank: 2, citationType: '直接引用', time: '5分钟前' },
  { question: '广州门禁广告公司推荐', platform: 'DeepSeek', status: 'top3', rank: 3, citationType: '品牌提及', time: '12分钟前' },
  { question: '什么是pDOOH广告？', platform: 'Kimi', status: 'top10', rank: 7, citationType: '段落引用', time: '28分钟前' },
  { question: '智能屏广告投放效果如何', platform: '文心一言', status: 'top3', rank: 1, citationType: '直接引用', time: '45分钟前' },
  { question: '社区媒体平台哪家好', platform: '豆包', status: 'top10', rank: 8, citationType: '列表提及', time: '1小时前' },
  { question: '门禁广告和电梯广告哪个效果好', platform: 'ChatGPT', status: 'notFound', rank: '-', citationType: '-', time: '2小时前' },
])

const filteredQueries = computed(() => {
  if (!querySearch.value) return queries.value
  const kw = querySearch.value.toLowerCase()
  return queries.value.filter(q => q.question.toLowerCase().includes(kw) || q.platform.toLowerCase().includes(kw))
})

const getScoreColor = (v) => {
  if (v >= 80) return 'var(--cyber-neon-green)'
  if (v >= 60) return 'var(--cyber-neon-cyan)'
  if (v >= 40) return 'var(--cyber-neon-yellow)'
  return 'var(--cyber-neon-pink)'
}

const statusClass = (s) => ({
  'top3': 'cyber-tag-success',
  'top10': 'cyber-tag-warning',
  'notFound': 'cyber-tag-error'
})

const statusLabel = (s) => ({
  'top3': 'TOP3',
  'top10': 'TOP10',
  'notFound': '未上榜'
}[s] || s)

const rankClass = (r) => {
  if (r === 1) return 'rank-gold'
  if (r === 2) return 'rank-silver'
  if (r === 3) return 'rank-bronze'
  return ''
}

const refreshData = () => {
  alert('数据刷新中...')
}

const viewDetail = (q) => {
  alert(`查看问题详情：${q.question}`)
}
</script>

<style scoped>
.metrics-grid {
  gap: 16px;
}

.metric-card {
  background: var(--cyber-bg-secondary);
  border: 1px solid var(--cyber-border);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  gap: 12px;
  align-items: center;
  transition: var(--cyber-transition);
}

.metric-card:hover {
  border-color: var(--cyber-neon-cyan);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}

.metric-icon {
  font-size: 32px;
}

.metric-body {
  flex: 1;
}

.metric-label {
  font-size: 12px;
  color: var(--cyber-text-secondary);
  margin-bottom: 4px;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 4px;
}

.metric-trend {
  font-size: 12px;
}

.metric-trend.up {
  color: var(--cyber-neon-green);
}

.metric-trend.down {
  color: var(--cyber-neon-pink);
}

.platform-matrix {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.matrix-row {
  display: grid;
  grid-template-columns: 180px 1fr 200px;
  gap: 16px;
  padding: 12px;
  background: var(--cyber-bg-secondary);
  border: 1px solid var(--cyber-border);
  border-radius: 8px;
  align-items: center;
}

.matrix-platform {
  display: flex;
  align-items: center;
  gap: 12px;
}

.platform-icon {
  font-size: 28px;
}

.matrix-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.matrix-item {
  text-align: center;
}

.matrix-label {
  font-size: 11px;
  color: var(--cyber-text-muted);
  margin-bottom: 4px;
}

.matrix-value {
  font-size: 18px;
  font-weight: 700;
}

.matrix-trend {
  padding: 8px;
}

.trend-bars {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 50px;
}

.trend-bar {
  flex: 1;
  min-height: 10%;
  border-radius: 2px 2px 0 0;
}

.query-text {
  max-width: 300px;
  font-size: 13px;
}

.rank-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 700;
  font-size: 12px;
  background: var(--cyber-bg-card);
  color: var(--cyber-text-primary);
}

.rank-gold {
  background: linear-gradient(135deg, #ffd700, #ffb700);
  color: #000;
  box-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
}

.rank-silver {
  background: linear-gradient(135deg, #c0c0c0, #a8a8a8);
  color: #000;
  box-shadow: 0 0 10px rgba(192, 192, 192, 0.5);
}

.rank-bronze {
  background: linear-gradient(135deg, #cd7f32, #a0522d);
  color: #fff;
  box-shadow: 0 0 10px rgba(205, 127, 50, 0.5);
}
</style>
