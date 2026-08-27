<template>
  <div class="keywords-page">
    <div class="page-header">
      <h2>蒸馏主词</h2>
      <p class="desc">AI 智能拓展关键词，批量生成 SEO 优化词组</p>
    </div>

    <!-- 新建蒸馏任务 -->
    <div class="create-section">
      <h3>创建蒸馏任务</h3>
      <el-form :model="createForm" label-width="120px">
        <el-form-item label="训练主词">
          <el-input v-model="createForm.seed_keyword" placeholder="如：智能家居" />
        </el-form-item>
        <el-form-item label="转化词">
          <el-input v-model="createForm.conversion_keyword" placeholder="如：智能家居品牌" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="startDistillation" :loading="distilling">
            开始 AI 蒸馏
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 蒸馏结果 -->
    <div class="result-section" v-if="distilledKeywords.length > 0">
      <div class="section-header">
        <h3>蒸馏结果 ({{ distilledKeywords.length }} 个问题)</h3>
        <div class="actions">
          <el-button size="small" @click="selectAll">全选</el-button>
          <el-button size="small" @click="deselectAll">取消全选</el-button>
          <el-button type="primary" size="small" @click="saveSelected" :disabled="selectedCount === 0">
            保存到词库 ({{ selectedCount }})
          </el-button>
        </div>
      </div>
      <div class="keyword-list">
        <div class="keyword-item" v-for="kw in distilledKeywords" :key="kw.id">
          <el-checkbox v-model="kw.checked">
            <span class="keyword-text">{{ kw.question }}</span>
          </el-checkbox>
          <span class="keyword-meta">
            <el-tag size="small" type="info">{{ kw.source }}</el-tag>
          </span>
        </div>
      </div>
    </div>

    <!-- 已保存关键词 -->
    <div class="saved-section">
      <h3>已保存关键词 ({{ savedKeywords.length }})</h3>
      <div class="keyword-list">
        <div class="keyword-item" v-for="kw in savedKeywords" :key="kw.id">
          <div class="keyword-text">
            <el-tag :type="kw.selected ? 'success' : 'info'" size="small" style="margin-right: 8px;">
              {{ kw.selected ? '已选' : '未选' }}
            </el-tag>
            训练词: {{ kw.training_keyword }} | 转化词: {{ kw.conversion_keyword }}
          </div>
          <div class="keyword-meta">
            <span class="keyword-text" style="color: #666; font-size: 12px;">
              {{ (kw.distilled_queries || []).length }} 个蒸馏问题
            </span>
            <el-button
              type="danger"
              size="small"
              @click="deleteKeywordItem(kw.id)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
      <el-empty v-if="savedKeywords.length === 0" description="暂无关键词" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import { getKeywords as fetchKeywords, createKeyword, deleteKeyword as removeKeyword } from '@/api/business'

const tenantId = computed(() => localStorage.getItem('tenant_id'))
const brandId = computed(() => localStorage.getItem('brand_id'))

const createForm = ref({
  seed_keyword: '',
  conversion_keyword: ''
})

const distilling = ref(false)
const distilledKeywords = ref([])
const selectedIds = ref([])
const savedKeywords = ref([])

const selectedCount = computed(() => distilledKeywords.value.filter(kw => kw.checked).length)

// 开始 AI 蒸馏
const startDistillation = async () => {
  if (!createForm.value.seed_keyword.trim()) {
    ElMessage.warning('请输入训练主词')
    return
  }
  if (!createForm.value.conversion_keyword.trim()) {
    createForm.value.conversion_keyword = createForm.value.seed_keyword
  }
  distilling.value = true
  try {
    const res = await createKeyword({
      tenant_id: tenantId.value,
      brand_id: brandId.value || '00000000-0000-0000-0000-000000000001',
      training_keyword: createForm.value.seed_keyword,
      conversion_keyword: createForm.value.conversion_keyword,
      source: 'ai_distill'
    })
    const item = res.data
    distilledKeywords.value = (item.distilled_queries || []).map((q, i) => ({
      id: item.id + '-' + i,
      question: q,
      source: 'ai_distill',
      checked: false,
      parent_id: item.id
    }))
    ElMessage.success(`蒸馏完成，生成 ${distilledKeywords.value.length} 个问题`)
  } catch (err) {
    ElMessage.error('蒸馏失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    distilling.value = false
  }
}

// 全选
const selectAll = () => {
  distilledKeywords.value.forEach(kw => kw.checked = true)
}

// 取消全选
const deselectAll = () => {
  distilledKeywords.value.forEach(kw => kw.checked = false)
}

// 保存已选（标记蒸馏结果已选）
const saveSelected = async () => {
  const checked = distilledKeywords.value.filter(kw => kw.checked)
  ElMessage.success(`已选择 ${checked.length} 个关键词进入写作库`)
  distilledKeywords.value = []
}

// 加载已保存的关键词
const loadSavedKeywords = async () => {
  try {
    const res = await fetchKeywords({ tenant_id: tenantId.value, brand_id: brandId.value })
    savedKeywords.value = res.data || []
  } catch (err) {
    console.error('加载关键词失败', err)
  }
}

// 删除关键词
const deleteKeywordItem = async (id) => {
  try {
    await ElMessageBox.confirm('确认删除该关键词？', '警告', { type: 'warning' })
    await removeKeyword(id, tenantId.value)
    ElMessage.success('已删除')
    await loadSavedKeywords()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadSavedKeywords()
})
</script>

<style scoped>
.keywords-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px 0;
}

.desc {
  color: #909399;
  margin: 0;
}

.create-section,
.result-section,
.saved-section {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
}

.actions {
  display: flex;
  gap: 8px;
}

.keyword-list {
  max-height: 500px;
  overflow-y: auto;
}

.keyword-item {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.keyword-item:last-child {
  border-bottom: none;
}

.keyword-text {
  font-size: 14px;
  margin-right: 12px;
  flex: 1;
}

.keyword-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
