<template>
  <div class="writing-page">
    <h2>写作任务</h2>
    <p class="description">
      基于蒸馏主词和知识库，AI 自动创作高质量内容，支持多模板批量生成。
    </p>

    <el-button type="primary" @click="showCreateDialog = true">
      <el-icon><Plus /></el-icon> 创建写作任务
    </el-button>

    <el-table :data="tasks" style="width: 100%; margin-top: 20px">
      <el-table-column prop="name" label="任务名称" />
      <el-table-column prop="keyword_count" label="关键词数量" width="120">
        <template #default="{ row }">
          {{ row.keywords?.length || 0 }} 个
        </template>
      </el-table-column>
      <el-table-column prop="knowledge_unit_id" label="知识库" width="150">
        <template #default="{ row }">
          <el-tag v-if="row.knowledge_unit_id" type="success">已关联</el-tag>
          <el-tag v-else type="info">未关联</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="template" label="模板" width="100">
        <template #default="{ row }">
          {{ getTemplateName(row.template) }}
        </template>
      </el-table-column>
      <el-table-column prop="batch_size" label="生成数量" width="100" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'pending'"
            type="success"
            size="small"
            @click="executeTask(row)"
          >
            执行
          </el-button>
          <el-button
            v-if="row.status === 'completed'"
            type="primary"
            size="small"
            @click="viewResults(row)"
          >
            查看结果
          </el-button>
          <el-button type="danger" size="small" @click="deleteTask(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建任务对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建写作任务" width="600px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="任务名称">
          <el-input v-model="createForm.name" placeholder="例如：小红书种草文批量生成" />
        </el-form-item>
        <el-form-item label="关键词">
          <el-select
            v-model="createForm.keyword_ids"
            multiple
            placeholder="选择蒸馏主词"
            style="width: 100%"
          >
            <el-option
              v-for="kw in keywords"
              :key="kw.id"
              :label="kw.keyword"
              :value="kw.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="知识库">
          <el-select
            v-model="createForm.knowledge_unit_id"
            placeholder="选择知识库（可选）"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="unit in knowledgeUnits"
              :key="unit.id"
              :label="unit.name"
              :value="unit.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="内容模板">
          <el-select v-model="createForm.template" placeholder="选择模板" style="width: 100%">
            <el-option label="FAQ 问答" value="faq" />
            <el-option label="产品对比" value="comparison" />
            <el-form-item label="教程指南" value="howto" />
            <el-option label="实体介绍" value="entity" />
            <el-option label="综合指南" value="guide" />
          </el-select>
        </el-form-item>
        <el-form-item label="生成数量">
          <el-input-number v-model="createForm.batch_size" :min="1" :max="50" />
          <span style="margin-left: 10px; color: #999">篇</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 执行进度对话框 -->
    <el-dialog v-model="showProgressDialog" title="任务执行中" width="500px">
      <div class="progress-container">
        <el-progress :percentage="progress" :status="progressStatus" />
        <p class="progress-text">{{ progressText }}</p>
      </div>
      <template #footer>
        <el-button @click="showProgressDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 结果查看对话框 -->
    <el-dialog v-model="showResultsDialog" title="生成结果" width="800px">
      <div v-if="results.length === 0" class="no-results">
        暂无生成内容
      </div>
      <el-table v-else :data="results" style="width: 100%">
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="word_count" label="字数" width="80" />
        <el-table-column prop="geo_score" label="GEO 分数" width="100">
          <template #default="{ row }">
            <el-tag :type="getScoreType(row.geo_score)">
              {{ row.geo_score?.toFixed(1) || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewContent(row)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showResultsDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 内容详情对话框 -->
    <el-dialog v-model="showContentDialog" title="内容详情" width="700px">
      <div v-if="currentContent" class="content-detail">
        <h3>{{ currentContent.title }}</h3>
        <div class="meta">
          <el-tag>GEO 分数: {{ currentContent.geo_score?.toFixed(1) }}</el-tag>
          <el-tag>字数: {{ currentContent.word_count }}</el-tag>
        </div>
        <div class="body" v-html="currentContent.body_html"></div>
      </div>
      <template #footer>
        <el-button @click="showContentDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getWritingTasks,
  createWritingTask,
  executeWritingTask,
  deleteWritingTask,
  getTaskResults
} from '@/api/business'
import { getKeywords } from '@/api/business'
import { getKnowledgeUnits } from '@/api/geo'

const tasks = ref([])
const keywords = ref([])
const knowledgeUnits = ref([])
const results = ref([])
const currentContent = ref(null)

const showCreateDialog = ref(false)
const showProgressDialog = ref(false)
const showResultsDialog = ref(false)
const showContentDialog = ref(false)

const createForm = ref({
  name: '',
  keyword_ids: [],
  knowledge_unit_id: null,
  template: 'guide',
  batch_size: 10
})

const progress = ref(0)
const progressStatus = ref('')
const progressText = ref('')

const getTemplateName = (template) => {
  const map = {
    faq: 'FAQ 问答',
    comparison: '产品对比',
    howto: '教程指南',
    entity: '实体介绍',
    guide: '综合指南'
  }
  return map[template] || template
}

const getStatusType = (status) => {
  const map = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    pending: '待执行',
    running: '执行中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

const getScoreType = (score) => {
  if (!score) return 'info'
  if (score >= 8) return 'success'
  if (score >= 6) return 'warning'
  return 'danger'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN')
}

const loadTasks = async () => {
  try {
    const res = await getWritingTasks()
    tasks.value = res.data
  } catch (e) {
    console.error('加载任务列表失败', e)
  }
}

const loadKeywords = async () => {
  try {
    const res = await getKeywords()
    keywords.value = res.data
  } catch (e) {
    console.error('加载关键词失败', e)
  }
}

const loadKnowledgeUnits = async () => {
  try {
    const res = await getKnowledgeUnits()
    knowledgeUnits.value = res.data
  } catch (e) {
    console.error('加载知识库失败', e)
  }
}

const submitCreate = async () => {
  if (!createForm.value.name || createForm.value.keyword_ids.length === 0) {
    ElMessage.warning('请填写任务名称并选择关键词')
    return
  }
  try {
    await createWritingTask(createForm.value)
    ElMessage.success('任务创建成功')
    showCreateDialog.value = false
    createForm.value = {
      name: '',
      keyword_ids: [],
      knowledge_unit_id: null,
      template: 'guide',
      batch_size: 10
    }
    await loadTasks()
  } catch (e) {
    ElMessage.error('创建失败：' + (e.response?.data?.detail || e.message))
  }
}

const executeTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要执行任务 "${task.name}" 吗？这将生成 ${task.batch_size} 篇内容。`,
      '确认执行',
      { type: 'warning' }
    )

    showProgressDialog.value = true
    progress.value = 0
    progressStatus.value = ''
    progressText.value = '任务启动中...'

    // 模拟进度
    const interval = setInterval(() => {
      if (progress.value < 90) {
        progress.value += Math.random() * 15
        progressText.value = `正在生成内容... ${Math.floor(progress.value)}%`
      }
    }, 500)

    try {
      await executeWritingTask(task.id)
      clearInterval(interval)
      progress.value = 100
      progressStatus.value = 'success'
      progressText.value = '任务执行完成！'
      ElMessage.success('任务执行成功')
      await loadTasks()
    } catch (e) {
      clearInterval(interval)
      progressStatus.value = 'exception'
      progressText.value = '任务执行失败'
      ElMessage.error('执行失败：' + (e.response?.data?.detail || e.message))
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('确认失败')
    }
  }
}

const viewResults = async (task) => {
  try {
    const res = await getTaskResults(task.id)
    results.value = res.data
    showResultsDialog.value = true
  } catch (e) {
    ElMessage.error('加载结果失败')
  }
}

const viewContent = (content) => {
  currentContent.value = content
  showContentDialog.value = true
}

const deleteTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务 "${task.name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await deleteWritingTask(task.id)
    ElMessage.success('删除成功')
    await loadTasks()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadTasks()
  loadKeywords()
  loadKnowledgeUnits()
})
</script>

<style scoped>
.writing-page {
  padding: 20px;
}

.description {
  color: #666;
  margin-bottom: 20px;
}

.progress-container {
  padding: 20px 0;
  text-align: center;
}

.progress-text {
  margin-top: 15px;
  color: #666;
  font-size: 14px;
}

.no-results {
  text-align: center;
  padding: 40px;
  color: #999;
}

.content-detail {
  line-height: 1.8;
}

.content-detail h3 {
  margin-bottom: 15px;
  color: #333;
}

.content-detail .meta {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.content-detail .body {
  padding: 20px;
  background: #f5f5f5;
  border-radius: 4px;
  line-height: 1.8;
}
</style>
