<template>
  <div class="web-publishing-optimizer">
    <div class="header">
      <h1>🌐 网站优化助手</h1>
      <p class="subtitle">基于 GEO 规范分析页面并提供优化建议</p>
    </div>

    <!-- URL 输入区 -->
    <div class="input-section">
      <div class="input-group">
        <input
          v-model="targetUrl"
          type="url"
          placeholder="输入要分析的页面 URL（如 https://example.com）"
          class="url-input"
          @keyup.enter="analyzePage"
        />
        <select v-model="checkType" class="check-type-select">
          <option value="full">完整分析</option>
          <option value="metadata">仅元数据</option>
          <option value="content">仅内容结构</option>
          <option value="technical">仅技术问题</option>
        </select>
        <button @click="analyzePage" :disabled="analyzing" class="analyze-btn">
          {{ analyzing ? '分析中...' : '开始分析' }}
        </button>
      </div>
    </div>

    <!-- 分析结果 -->
    <div v-if="analysisResult" class="results-section">
      <!-- 总体评分 -->
      <div class="score-card">
        <div class="score-circle" :class="scoreClass">
          <div class="score-value">{{ analysisResult.score.toFixed(0) }}</div>
          <div class="score-label">综合得分</div>
        </div>
        <div class="score-details">
          <div class="detail-item">
            <span class="detail-label">页面标题</span>
            <span class="detail-value">{{ analysisResult.title || '未设置' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">页面描述</span>
            <span class="detail-value">{{ analysisResult.description || '未设置' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">语言</span>
            <span class="detail-value">{{ analysisResult.language || '未设置' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Canonical</span>
            <span class="detail-value">{{ analysisResult.canonical || '未设置' }}</span>
          </div>
        </div>
      </div>

      <!-- 问题统计 -->
      <div class="issues-summary">
        <div class="stat-item critical">
          <div class="stat-value">{{ issueCounts.critical }}</div>
          <div class="stat-label">严重问题</div>
        </div>
        <div class="stat-item warning">
          <div class="stat-value">{{ issueCounts.warning }}</div>
          <div class="stat-label">警告</div>
        </div>
        <div class="stat-item info">
          <div class="stat-value">{{ issueCounts.info }}</div>
          <div class="stat-label">提示</div>
        </div>
        <div class="stat-item suggestion">
          <div class="stat-value">{{ issueCounts.suggestion }}</div>
          <div class="stat-label">建议</div>
        </div>
      </div>

      <!-- 问题列表 -->
      <div class="issues-section">
        <h2>发现的问题</h2>
        <div class="issues-list">
          <div
            v-for="(issue, index) in analysisResult.issues"
            :key="index"
            class="issue-item"
            :class="issue.severity"
          >
            <div class="issue-header">
              <span class="severity-badge" :class="issue.severity">
                {{ severityLabels[issue.severity] }}
              </span>
              <span class="issue-category">{{ issue.category }}</span>
              <h3 class="issue-title">{{ issue.title }}</h3>
            </div>
            <p class="issue-description">{{ issue.description }}</p>
            <div class="issue-recommendation">
              <strong>优化建议：</strong>{{ issue.recommendation }}
            </div>
            <div v-if="issue.affected_elements && issue.affected_elements.length > 0" class="affected-elements">
              <strong>受影响元素：</strong>
              <ul>
                <li v-for="(elem, idx) in issue.affected_elements" :key="idx">
                  <code>{{ elem }}</code>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- 优化建议汇总 -->
      <div class="recommendations-section">
        <h2>优化建议清单</h2>
        <div class="recommendations-list">
          <div
            v-for="(rec, index) in analysisResult.recommendations"
            :key="index"
            class="recommendation-item"
          >
            {{ index + 1 }}. {{ rec }}
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!analyzing" class="empty-state">
      <div class="empty-icon">🔍</div>
      <h3>输入 URL 开始分析</h3>
      <p>我们将检查页面的元数据、内容结构、技术实现和链接质量</p>
      <div class="features">
        <div class="feature-item">
          <span class="feature-icon">📋</span>
          <span>元数据检查</span>
        </div>
        <div class="feature-item">
          <span class="feature-icon">📝</span>
          <span>内容结构</span>
        </div>
        <div class="feature-item">
          <span class="feature-icon">⚙️</span>
          <span>技术问题</span>
        </div>
        <div class="feature-item">
          <span class="feature-icon">🔗</span>
          <span>链接质量</span>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMessage" class="error-message">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '@/api/axios'

const targetUrl = ref('')
const checkType = ref('full')
const analyzing = ref(false)
const analysisResult = ref(null)
const errorMessage = ref('')

const severityLabels = {
  critical: '严重',
  warning: '警告',
  info: '提示',
  suggestion: '建议'
}

const scoreClass = computed(() => {
  if (!analysisResult.value) return ''
  const score = analysisResult.value.score
  if (score >= 80) return 'excellent'
  if (score >= 60) return 'good'
  if (score >= 40) return 'fair'
  return 'poor'
})

const issueCounts = computed(() => {
  if (!analysisResult.value) return { critical: 0, warning: 0, info: 0, suggestion: 0 }
  
  const counts = { critical: 0, warning: 0, info: 0, suggestion: 0 }
  analysisResult.value.issues.forEach(issue => {
    counts[issue.severity] = (counts[issue.severity] || 0) + 1
  })
  return counts
})

const analyzePage = async () => {
  if (!targetUrl.value) {
    errorMessage.value = '请输入 URL'
    return
  }

  analyzing.value = true
  errorMessage.value = ''
  analysisResult.value = null

  try {
    const response = await api.post('/api/v2/web-publishing/analyze', {
      url: targetUrl.value,
      check_type: checkType.value
    })
    analysisResult.value = response.data
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || '分析失败，请检查 URL 是否正确'
  } finally {
    analyzing.value = false
  }
}
</script>

<style scoped>
.web-publishing-optimizer {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  margin-bottom: 32px;
}

.header h1 {
  font-size: 28px;
  color: #1a1a1a;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.input-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.input-group {
  display: flex;
  gap: 12px;
}

.url-input {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.url-input:focus {
  outline: none;
  border-color: #2196F3;
}

.check-type-select {
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  cursor: pointer;
}

.analyze-btn {
  padding: 12px 24px;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.analyze-btn:hover:not(:disabled) {
  background: #1976D2;
}

.analyze-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.results-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.score-card {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  display: flex;
  gap: 32px;
  align-items: center;
}

.score-circle {
  width: 140px;
  height: 140px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.score-circle.excellent {
  background: linear-gradient(135deg, #4CAF50 0%, #81C784 100%);
  color: white;
}

.score-circle.good {
  background: linear-gradient(135deg, #8BC34A 0%, #AED581 100%);
  color: white;
}

.score-circle.fair {
  background: linear-gradient(135deg, #FFC107 0%, #FFD54F 100%);
  color: white;
}

.score-circle.poor {
  background: linear-gradient(135deg, #F44336 0%, #E57373 100%);
  color: white;
}

.score-value {
  font-size: 48px;
  font-weight: bold;
  line-height: 1;
}

.score-label {
  font-size: 14px;
  margin-top: 8px;
}

.score-details {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  font-size: 12px;
  color: #999;
  text-transform: uppercase;
}

.detail-value {
  font-size: 14px;
  color: #333;
  word-break: break-word;
}

.issues-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-item {
  background: white;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  border-left: 4px solid;
}

.stat-item.critical {
  border-left-color: #F44336;
}

.stat-item.warning {
  border-left-color: #FF9800;
}

.stat-item.info {
  border-left-color: #2196F3;
}

.stat-item.suggestion {
  border-left-color: #9E9E9E;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #1a1a1a;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

.issues-section, .recommendations-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.issues-section h2, .recommendations-section h2 {
  margin: 0 0 20px 0;
  font-size: 20px;
  color: #1a1a1a;
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.issue-item {
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid;
  background: #f8f9fa;
}

.issue-item.critical {
  border-left-color: #F44336;
  background: #ffebee;
}

.issue-item.warning {
  border-left-color: #FF9800;
  background: #fff3e0;
}

.issue-item.info {
  border-left-color: #2196F3;
  background: #e3f2fd;
}

.issue-item.suggestion {
  border-left-color: #9E9E9E;
  background: #f5f5f5;
}

.issue-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.severity-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: white;
}

.severity-badge.critical {
  background: #F44336;
}

.severity-badge.warning {
  background: #FF9800;
}

.severity-badge.info {
  background: #2196F3;
}

.severity-badge.suggestion {
  background: #9E9E9E;
}

.issue-category {
  font-size: 12px;
  color: #666;
  text-transform: uppercase;
}

.issue-title {
  margin: 0;
  font-size: 16px;
  color: #1a1a1a;
}

.issue-description {
  margin: 8px 0;
  color: #555;
  line-height: 1.6;
}

.issue-recommendation {
  margin-top: 12px;
  padding: 12px;
  background: rgba(255,255,255,0.6);
  border-radius: 6px;
  color: #333;
  line-height: 1.6;
}

.affected-elements {
  margin-top: 12px;
  padding: 12px;
  background: rgba(255,255,255,0.6);
  border-radius: 6px;
}

.affected-elements ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.affected-elements code {
  background: rgba(0,0,0,0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommendation-item {
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  color: #333;
  line-height: 1.6;
}

.empty-state {
  text-align: center;
  padding: 80px 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: #1a1a1a;
}

.empty-state p {
  margin: 0 0 32px 0;
  color: #666;
}

.features {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  max-width: 600px;
  margin: 0 auto;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.feature-icon {
  font-size: 32px;
}

.error-message {
  background: #ffebee;
  color: #c62828;
  padding: 16px;
  border-radius: 8px;
  margin-top: 16px;
  border-left: 4px solid #f44336;
}
</style>
