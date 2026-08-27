<template>
  <div class="monitoring-page">
    <h2>AI 监测看板</h2>
    <p class="description">
      实时监控品牌在各大 AI 平台的出镜率、引用率和推荐指数，掌握 GEO 优化效果。
    </p>

    <!-- 筛选条件 -->
    <div class="filter-bar">
      <el-select v-model="selectedBrand" placeholder="选择品牌" style="width: 200px">
        <el-option label="全部品牌" value="" />
        <el-option
          v-for="brand in brands"
          :key="brand.id"
          :label="brand.name"
          :value="brand.id"
        />
      </el-select>
      <el-select v-model="selectedPlatform" placeholder="选择平台" style="width: 200px; margin-left: 10px">
        <el-option label="全部平台" value="" />
        <el-option
          v-for="platform in platforms"
          :key="platform.value"
          :label="platform.label"
          :value="platform.value"
        />
      </el-select>
      <el-button type="primary" @click="refreshData" style="margin-left: 10px">
        <el-icon><Refresh /></el-icon> 刷新数据
      </el-button>
    </div>

    <!-- 数据概览卡片 -->
    <div class="overview-cards">
      <div class="card">
        <div class="card-title">平均出镜率</div>
        <div class="card-value">{{ overview.appearance_rate?.toFixed(1) || '0.0' }}%</div>
        <div class="card-trend" :class="overview.appearance_trend > 0 ? 'up' : 'down'">
          {{ overview.appearance_trend > 0 ? '↑' : '↓' }}
          {{ Math.abs(overview.appearance_trend || 0).toFixed(1) }}%
        </div>
      </div>
      <div class="card">
        <div class="card-title">平均引用率</div>
        <div class="card-value">{{ overview.citation_rates?.toFixed(1) || '0.0' }}%</div>
        <div class="card-trend" :class="overview.citation_trend > 0 ? 'up' : 'down'">
          {{ overview.citation_trend > 0 ? '↑' : '↓' }}
          {{ Math.abs(overview.citation_trend || 0).toFixed(1) }}%
        </div>
      </div>
      <div class="card">
        <div class="card-title">平均推荐率</div>
        <div class="card-value">{{ overview.recommendation_rates?.toFixed(1) || '0.0' }}%</div>
        <div class="card-trend" :class="overview.recommendation_trend > 0 ? 'up' : 'down'">
          {{ overview.recommendation_trend > 0 ? '↑' : '↓' }}
          {{ Math.abs(overview.recommendation_trend || 0).toFixed(1) }}%
        </div>
      </div>
      <div class="card">
        <div class="card-title">GEO 健康度</div>
        <div class="card-value">{{ overview.geo_health_score?.toFixed(0) || '0' }}</div>
        <div class="card-trend" :class="overview.health_trend > 0 ? 'up' : 'down'">
          {{ overview.health_trend > 0 ? '↑' : '↓' }}
          {{ Math.abs(overview.health_trend || 0).toFixed(0) }}
        </div>
      </div>
    </div>

    <!-- 平台数据表格 -->
    <div class="section-title">平台数据明细</div>
    <el-table :data="platformData" style="width: 100%">
      <el-table-column prop="platform_name" label="平台" width="150">
        <template #default="{ row }">
          <el-tag>{{ row.platform_name }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="appearance_rate" label="出镜率" width="120">
        <template #default="{ row }">
          {{ row.appearance_rate?.toFixed(1) || '0.0' }}%
        </template>
      </el-table-column>
      <el-table-column prop="citation_rate" label="引用率" width="120">
        <template #default="{ row }">
          {{ row.citation_rate?.toFixed(1) || '0.0' }}%
        </template>
      </el-table-column>
      <el-table-column prop="recommendation_rate" label="推荐率" width="120">
        <template #default="{ row }">
          {{ row.recommendation_rate?.toFixed(1) || '0.0' }}%
        </template>
      </el-table-column>
      <el-table-column prop="geo_score" label="GEO 分数" width="120">
        <template #default="{ row }">
          <el-progress
            :percentage="row.geo_score || 0"
            :color="getScoreColor(row.geo_score)"
            :stroke-width="8"
            style="width: 80px"
          />
        </template>
      </el-table-column>
      <el-table-column prop="last_updated" label="最后更新" width="180">
        <template #default="{ row }">
          {{ formatDate(row.last_updated) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="viewDetail(row)">
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 竞品对比 -->
    <div class="section-title" style="margin-top: 30px">竞品对比</div>
    <el-table :data="competitorData" style="width: 100%">
      <el-table-column prop="brand_name" label="品牌" width="200" />
      <el-table-column prop="appearance_rate" label="出镜率" width="120">
        <template #default="{ row }">
          {{ row.appearance_rate?.toFixed(1) || '0.0' }}%
        </template>
      </el-table-column>
      <el-table-column prop="citation_rate" label="引用率" width="120">
        <template #default="{ row }">
          {{ row.citation_rate?.toFixed(1) || '0.0' }}%
        </template>
      </el-table-column>
      <el-table-column prop="recommendation_rate" label="推荐率" width="120">
        <template #default="{ row }">
          {{ row.recommendation_rate?.toFixed(1) || '0.0' }}%
        </template>
      </el-table-column>
      <el-table-column prop="geo_score" label="GEO 分数" width="120">
        <template #default="{ row }">
          <span :style="{ color: getScoreColor(row.geo_score), fontWeight: 'bold' }">
            {{ row.geo_score?.toFixed(0) || '0' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="rank" label="排名" width="100">
        <template #default="{ row }">
          <el-tag :type="getRankType(row.rank)" size="small">
            #{{ row.rank }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>

    <!-- 平台详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="平台详情" width="700px">
      <div v-if="currentPlatform" class="platform-detail">
        <h3>{{ currentPlatform.platform_name }}</h3>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="出镜率">
            {{ currentPlatform.appearance_rate?.toFixed(1) || '0.0' }}%
          </el-descriptions-item>
          <el-descriptions-item label="引用率">
            {{ currentPlatform.citation_rate?.toFixed(1) || '0.0' }}%
          </el-descriptions-item>
          <el-descriptions-item label="推荐率">
            {{ currentPlatform.recommendation_rate?.toFixed(1) || '0.0' }}%
          </el-descriptions-item>
          <el-descriptions-item label="GEO 分数">
            {{ currentPlatform.geo_score?.toFixed(1) || '0.0' }}
          </el-descriptions-item>
          <el-descriptions-item label="最后更新">
            {{ formatDate(currentPlatform.last_updated) }}
          </el-descriptions-item>
        </el-descriptions>

        <h4 style="margin-top: 20px">热门问题 TOP 10</h4>
        <el-table :data="currentPlatform.top_questions || []" style="width: 100%; margin-top: 10px">
          <el-table-column prop="question" label="问题" />
          <el-table-column prop="search_count" label="搜索次数" width="100" />
          <el-table-column prop="rank" label="排名" width="80" />
        </el-table>

        <h4 style="margin-top: 20px">引用来源分析</h4>
        <el-table :data="currentPlatform.citation_sources || []" style="width: 100%; margin-top: 10px">
          <el-table-column prop="source_name" label="来源" />
          <el-table-column prop="citation_count" label="引用次数" width="100" />
          <el-table-column prop="percentage" label="占比" width="100">
            <template #default="{ row }">
              {{ (row.percentage * 100).toFixed(1) }}%
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getMonitoringOverview, getPlatformData, getCompetitorData, getPlatformDetail } from '@/api/business'
import { getBrands } from '@/api/geo'

const brands = ref([])
const platforms = ref([
  { value: 'chatgpt', label: 'ChatGPT' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'kimi', label: 'Kimi' },
  { value: 'doubao', label: '豆包' },
  { value: 'wenxin', label: '文心一言' },
  { value: 'tongyi', label: '通义千问' },
  { value: 'zhipu', label: '智谱清言' },
  { value: 'tian', label: '天工 AI' }
])

const selectedBrand = ref('')
const selectedPlatform = ref('')
const overview = ref({})
const platformData = ref([])
const competitorData = ref([])
const currentPlatform = ref(null)
const showDetailDialog = ref(false)

const getScoreColor = (score) => {
  if (!score) return '#909399'
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

const getRankType = (rank) => {
  if (rank === 1) return 'danger'
  if (rank === 2) return 'warning'
  if (rank === 3) return 'success'
  return 'info'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN')
}

const loadBrands = async () => {
  try {
    const res = await getBrands()
    brands.value = res.data
  } catch (e) {
    console.error('加载品牌失败', e)
  }
}

const loadOverview = async () => {
  try {
    const res = await getMonitoringOverview({
      brand_id: selectedBrand.value || undefined,
      platform: selectedPlatform.value || undefined
    })
    overview.value = res.data
  } catch (e) {
    console.error('加载概览数据失败', e)
  }
}

const loadPlatformData = async () => {
  try {
    const res = await getPlatformData({
      brand_id: selectedBrand.value || undefined,
      platform: selectedPlatform.value || undefined
    })
    platformData.value = res.data
  } catch (e) {
    console.error('加载平台数据失败', e)
  }
}

const loadCompetitorData = async () => {
  try {
    const res = await getCompetitorData({
      brand_id: selectedBrand.value || undefined
    })
    competitorData.value = res.data
  } catch (e) {
    console.error('加载竞品数据失败', e)
  }
}

const refreshData = async () => {
  await Promise.all([
    loadOverview(),
    loadPlatformData(),
    loadCompetitorData()
  ])
}

const viewDetail = async (platform) => {
  try {
    const res = await getPlatformDetail(platform.platform)
    currentPlatform.value = res.data
    showDetailDialog.value = true
  } catch (e) {
    console.error('加载平台详情失败', e)
  }
}

watch([selectedBrand, selectedPlatform], () => {
  refreshData()
})

onMounted(() => {
  loadBrands()
  refreshData()
})
</script>

<style scoped>
.monitoring-page {
  padding: 20px;
}

.description {
  color: #666;
  margin-bottom: 20px;
}

.filter-bar {
  margin-bottom: 20px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.card-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 10px;
}

.card-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.card-trend {
  font-size: 14px;
}

.card-trend.up {
  color: #67c23a;
}

.card-trend.down {
  color: #f56c6c;
}

.section-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 15px;
  color: #303133;
}

.platform-detail {
  line-height: 1.8;
}

.platform-detail h3 {
  margin-bottom: 20px;
  color: #303133;
}

.platform-detail h4 {
  margin-top: 20px;
  margin-bottom: 10px;
  color: #606266;
}
</style>
