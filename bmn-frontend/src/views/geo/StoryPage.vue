<template>
  <div class="px-fade-in">
    <div class="px-page-title">
      <div class="px-page-title-icon">⌂</div>
      <h1>品牌首页</h1>
      <span class="sub">BRAND OVERVIEW // REAL-TIME</span>
    </div>

    <!-- 核心指标 -->
    <div class="px-grid px-grid-4" style="margin-bottom:20px">
      <div class="px-stat" v-for="s in stats" :key="s.label">
        <div class="px-stat-label">{{ s.label }}</div>
        <div class="px-stat-value" :style="{ color: s.color }">{{ s.value }}</div>
        <div class="px-stat-trend" :class="s.trend > 0 ? 'up' : 'down'">
          {{ s.trend > 0 ? '▲' : '▼' }} {{ Math.abs(s.trend) }}% vs 上周
        </div>
      </div>
    </div>

    <!-- 两栏布局 -->
    <div class="px-grid px-grid-2">
      <!-- 左：工作流进度 -->
      <div class="px-card">
        <div class="px-card-title">SOP 工作流进度</div>
        <div v-for="step in workflowSteps" :key="step.id" class="px-workflow-row">
          <div class="px-wf-status">
            <span :class="'px-dot-' + step.status"></span>
          </div>
          <div class="px-wf-info">
            <div class="px-wf-name">{{ step.id }}. {{ step.name }}</div>
            <div class="px-wf-desc">{{ step.desc }}</div>
          </div>
          <div class="px-wf-tag">
            <span :class="'px-tag px-tag-' + step.tagType">{{ step.tag }}</span>
          </div>
        </div>
      </div>

      <!-- 右：平台出镜率 -->
      <div class="px-card">
        <div class="px-card-title">AI 平台出镜率</div>
        <div v-for="p in platforms" :key="p.name" class="px-platform-row">
          <div class="px-plat-name">{{ p.icon }} {{ p.name }}</div>
          <div class="px-plat-bar-wrap">
            <div class="px-progress">
              <div class="px-progress-bar" :style="{ width: p.rate + '%', background: p.color }"></div>
            </div>
          </div>
          <div class="px-plat-rate" :style="{ color: p.color }">{{ p.rate }}%</div>
        </div>
      </div>
    </div>

    <!-- 底部：最近活动 -->
    <div class="px-card" style="margin-top:16px">
      <div class="px-card-title">最近活动日志</div>
      <table class="px-table">
        <thead>
          <tr>
            <th>时间</th>
            <th>模块</th>
            <th>事件</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in recentLogs" :key="log.id">
            <td style="color:var(--px-text-muted)">{{ log.time }}</td>
            <td>{{ log.module }}</td>
            <td>{{ log.event }}</td>
            <td><span :class="'px-tag px-tag-' + log.statusType">{{ log.status }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const stats = ref([
  { label: 'AI 出镜率', value: '73%', color: '#00f0ff', trend: 12 },
  { label: '内容覆盖度', value: '856', color: '#39ff14', trend: 8 },
  { label: '分发成功率', value: '94%', color: '#fff200', trend: 3 },
  { label: 'GEO 健康度', value: '82', color: '#b537f2', trend: -2 },
])

const workflowSteps = ref([
  { id: 1, name: '提供资料', desc: '品牌基础信息录入', tag: '已完成', tagType: 'success', status: 'done' },
  { id: 2, name: '蒸馏主词', desc: 'AI 扩展 12 个关联问题', tag: '已完成', tagType: 'success', status: 'done' },
  { id: 3, name: '自媒体授权', desc: '8/12 平台已连接', tag: '进行中', tagType: '', status: 'active' },
  { id: 4, name: '写作任务', desc: '待生成 24 篇内容', tag: '待启动', tagType: 'warn', status: 'pending' },
  { id: 5, name: '分发任务', desc: '多平台发布配置', tag: '待启动', tagType: 'warn', status: 'pending' },
  { id: 6, name: '数据报表', desc: 'AI 追踪 & 出镜分析', tag: '待启动', tagType: 'warn', status: 'pending' },
])

const platforms = ref([
  { name: '豆包', icon: '◈', rate: 87, color: '#00f0ff' },
  { name: 'DeepSeek', icon: '◇', rate: 72, color: '#39ff14' },
  { name: 'Kimi', icon: '○', rate: 65, color: '#b537f2' },
  { name: 'ChatGPT', icon: '◎', rate: 58, color: '#fff200' },
  { name: '百度', icon: '□', rate: 43, color: '#ff6b00' },
  { name: 'Google', icon: '△', rate: 31, color: '#ff2e97' },
])

const recentLogs = ref([
  { id: 1, time: '12:45', module: '蒸馏主词', event: '社区门禁 → 生成 8 个蒸馏问题', status: '完成', statusType: 'success' },
  { id: 2, time: '12:30', module: 'AI 写作', event: '批量生成 5 篇 SEO 文章', status: '完成', statusType: 'success' },
  { id: 3, time: '11:55', module: '全域分发', event: '知乎 + 小红书 发布中', status: '进行中', statusType: '' },
  { id: 4, time: '11:20', module: '品牌诊断', event: '品牌健康度扫描完成', status: '完成', statusType: 'success' },
  { id: 5, time: '10:40', module: 'AI 追踪', event: '豆包平台出镜率 +5%', status: '完成', statusType: 'success' },
])
</script>

<style scoped>
.px-workflow-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(0, 240, 255, 0.06);
}
.px-workflow-row:last-child { border-bottom: none; }
.px-wf-status { width: 20px; flex-shrink: 0; }
.px-dot-done { width: 10px; height: 10px; background: var(--px-neon-green); box-shadow: 0 0 6px var(--px-neon-green); border-radius: 50%; display: inline-block; }
.px-dot-active { width: 10px; height: 10px; background: var(--px-neon-cyan); box-shadow: 0 0 6px var(--px-neon-cyan); border-radius: 50%; display: inline-block; animation: blink 1.5s infinite; }
.px-dot-pending { width: 10px; height: 10px; border: 1px solid var(--px-text-muted); border-radius: 50%; display: inline-block; }
.px-wf-info { flex: 1; }
.px-wf-name { font-size: 12px; color: var(--px-text-primary); margin-bottom: 2px; }
.px-wf-desc { font-size: 10px; color: var(--px-text-muted); }
.px-wf-tag { flex-shrink: 0; }

.px-platform-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}
.px-plat-name { width: 100px; font-size: 12px; color: var(--px-text-primary); flex-shrink: 0; }
.px-plat-bar-wrap { flex: 1; }
.px-plat-rate { width: 50px; text-align: right; font-family: 'VT323', monospace; font-size: 18px; flex-shrink: 0; }
</style>
