<template>
  <div class="px-fade-in">
    <div class="px-page-title">
      <div class="px-page-title-icon">◈</div>
      <h1>数据驾驶舱</h1>
      <span class="sub">DATA COCKPIT // METRICS OVERVIEW</span>
    </div>

    <!-- 第一行：6 格指标 -->
    <div class="px-grid px-grid-6" style="margin-bottom:20px">
      <div class="px-stat" v-for="m in metrics" :key="m.label">
        <div class="px-stat-label">{{ m.label }}</div>
        <div class="px-stat-value" :style="{ color: m.color, fontSize: m.size || '32px' }">{{ m.value }}</div>
        <div class="px-stat-trend" :class="m.trend >= 0 ? 'up' : 'down'">
          {{ m.trend >= 0 ? '▲' : '▼' }} {{ Math.abs(m.trend) }}%
        </div>
      </div>
    </div>

    <!-- 第二行：趋势图 + 平台分布 -->
    <div class="px-grid px-grid-2" style="margin-bottom:16px">
      <div class="px-card">
        <div class="px-card-title">7日出镜率趋势</div>
        <div class="px-chart-area">
          <svg viewBox="0 0 400 160" class="px-chart-svg">
            <!-- 网格线 -->
            <line v-for="i in 4" :key="'g'+i" :x1="0" :y1="i*32" :x2="400" :y2="i*32" stroke="rgba(0,240,255,0.08)" stroke-width="1" />
            <!-- 折线 -->
            <polyline fill="none" stroke="#00f0ff" stroke-width="2"
              :points="trendPoints" />
            <!-- 面积 -->
            <polygon :points="trendArea" fill="url(#cyanGrad)" opacity="0.3" />
            <!-- 数据点 -->
            <circle v-for="(p, i) in trendData" :key="i"
              :cx="i * (400/6)" :cy="160 - p * 1.4"
              r="3" fill="#00f0ff" />
            <defs>
              <linearGradient id="cyanGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#00f0ff" stop-opacity="0.4" />
                <stop offset="100%" stop-color="#00f0ff" stop-opacity="0" />
              </linearGradient>
            </defs>
          </svg>
          <div class="px-chart-labels">
            <span v-for="d in days" :key="d">{{ d }}</span>
          </div>
        </div>
      </div>

      <div class="px-card">
        <div class="px-card-title">平台内容分布</div>
        <div v-for="ch in channels" :key="ch.name" class="px-channel-row">
          <div class="px-ch-icon" :style="{ background: ch.color, boxShadow: '0 0 8px ' + ch.color }">
            {{ ch.icon }}
          </div>
          <div class="px-ch-info">
            <div class="px-ch-name">{{ ch.name }}</div>
            <div class="px-ch-count">{{ ch.count }} 篇</div>
          </div>
          <div class="px-ch-bar">
            <div class="px-progress" style="height:4px">
              <div class="px-progress-bar" :style="{ width: ch.pct + '%', background: ch.color }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 第三行：关键词 TOP10 -->
    <div class="px-card">
      <div class="px-card-title">蒸馏关键词 TOP 10</div>
      <div class="px-grid px-grid-2">
        <div v-for="(kw, idx) in topKeywords" :key="kw.word" class="px-kw-row">
          <span class="px-kw-rank" :style="{ color: idx < 3 ? '#00f0ff' : '#5a6888' }">
            {{ String(idx + 1).padStart(2, '0') }}
          </span>
          <span class="px-kw-word">{{ kw.word }}</span>
          <span class="px-kw-score">{{ kw.score }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const metrics = ref([
  { label: '总出镜率', value: '73%', color: '#00f0ff', trend: 12 },
  { label: 'AI 搜索覆盖', value: '856', color: '#39ff14', trend: 8 },
  { label: '蒸馏关键词', value: '124', color: '#b537f2', trend: 15 },
  { label: '分发成功率', value: '94%', color: '#fff200', trend: 3 },
  { label: '活跃平台', value: '8', color: '#ff6b00', trend: 0 },
  { label: '健康评分', value: '82', color: '#ff2e97', trend: -2, size: '28px' },
])

const trendData = ref([62, 68, 65, 73, 71, 78, 73])
const days = ['D-6', 'D-5', 'D-4', 'D-3', 'D-2', 'D-1', 'TODAY']
const trendPoints = computed(() =>
  trendData.value.map((v, i) => `${i * (400/6)},${160 - v * 1.4}`).join(' ')
)
const trendArea = computed(() => {
  const pts = trendData.value.map((v, i) => `${i * (400/6)},${160 - v * 1.4}`)
  return `0,160 ${pts.join(' ')} ${6 * (400/6)},160`
})

const channels = ref([
  { name: '微信公众号', icon: '微', count: 156, pct: 92, color: '#39ff14' },
  { name: '知乎', icon: '知', count: 128, pct: 76, color: '#00f0ff' },
  { name: '小红书', icon: '红', count: 95, pct: 56, color: '#ff2e97' },
  { name: '头条号', icon: '头', count: 87, pct: 52, color: '#ff6b00' },
  { name: '百家号', icon: '百', count: 72, pct: 43, color: '#b537f2' },
  { name: '抖音', icon: '抖', count: 64, pct: 38, color: '#fff200' },
])

const topKeywords = ref([
  { word: '智能门禁系统', score: 98 },
  { word: '社区广告优化', score: 92 },
  { word: '电梯广告效果', score: 87 },
  { word: 'pDOOH投放', score: 83 },
  { word: '社区媒体矩阵', score: 79 },
  { word: '品牌出镜率提升', score: 75 },
  { word: 'AI搜索优化策略', score: 71 },
  { word: 'GEO蒸馏方法', score: 68 },
  { word: '线下流量转化', score: 64 },
  { word: '社区团购运营', score: 60 },
])
</script>

<style scoped>
.px-chart-area { position: relative; }
.px-chart-svg { width: 100%; height: 160px; }
.px-chart-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--px-text-muted);
  margin-top: 8px;
  padding: 0 4px;
}

.px-channel-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}
.px-ch-icon {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px;
  color: var(--px-bg-void);
  font-weight: 700;
  flex-shrink: 0;
  clip-path: polygon(4px 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%, 0 4px);
}
.px-ch-info { width: 100px; flex-shrink: 0; }
.px-ch-name { font-size: 12px; color: var(--px-text-primary); }
.px-ch-count { font-size: 10px; color: var(--px-text-muted); }
.px-ch-bar { flex: 1; }

.px-kw-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  border-bottom: 1px solid rgba(0, 240, 255, 0.05);
}
.px-kw-rank {
  font-family: 'VT323', monospace;
  font-size: 18px;
  width: 28px;
  text-align: right;
}
.px-kw-word { flex: 1; font-size: 12px; color: var(--px-text-primary); }
.px-kw-score {
  font-family: 'VT323', monospace;
  font-size: 16px;
  color: var(--px-neon-green);
}
</style>
