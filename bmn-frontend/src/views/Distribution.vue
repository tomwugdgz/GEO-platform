<template>
  <div class="distribution-page">
    <h2>分发任务</h2>
    <p class="description">
      将生成的内容自动分发到已授权的自媒体平台，支持定时发布和多平台同步。
    </p>

    <el-button type="primary" @click="showCreateDialog = true">
      <el-icon><Plus /></el-icon> 创建分发任务
    </el-button>

    <el-table :data="tasks" style="width: 100%; margin-top: 20px">
      <el-table-column prop="name" label="任务名称" />
      <el-table-column prop="content_task_id" label="内容来源" width="150">
        <template #default="{ row }">
          <el-tag>{{ getContentTaskName(row.content_task_id) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="platform_count" label="平台数量" width="100">
        <template #default="{ row }">
          {{ row.platforms?.length || 0 }} 个
        </template>
      </el-table-column>
      <el-table-column prop="daily_limit" label="每日限制" width="100">
        <template #default="{ row }">
          {{ row.daily_limit || '无限制' }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="published_count" label="已发布" width="100">
        <template #default="{ row }">
          {{ row.published_count || 0 }} / {{ row.total_count || 0 }}
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
            @click="startTask(row)"
          >
            启动
          </el-button>
          <el-button
            v-if="row.status === 'running'"
            type="warning"
            size="small"
            @click="pauseTask(row)"
          >
            暂停
          </el-button>
          <el-button type="primary" size="small" @click="viewProgress(row)">
            查看进度
          </el-button>
          <el-button type="danger" size="small" @click="deleteTask(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建任务对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建分发任务" width="600px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="任务名称">
          <el-input v-model="createForm.name" placeholder="例如：小红书内容批量分发" />
        </el-form-item>
        <el-form-item label="内容来源">
          <el-select
            v-model="createForm.content_task_id"
            placeholder="选择写作任务"
            style="width: 100%"
          >
            <el-option
              v-for="task in writingTasks"
              :key="task.id"
              :label="task.name"
              :value="task.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标平台">
          <el-checkbox-group v-model="createForm.platforms">
            <el-checkbox
              v-for="account in socialAccounts"
              :key="account.id"
              :label="account.id"
            >
              {{ account.platform_name }} - {{ account.account_name }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="每日限制">
          <el-input-number v-model="createForm.daily_limit" :min="0" :max="100" />
          <span style="margin-left: 10px; color: #999">篇/天（0 表示无限制）</span>
        </el-form-item>
        <el-form-item label="发布时间">
          <el-radio-group v-model="createForm.schedule_type">
            <el-radio label="immediate">立即发布</el-radio>
            <el-radio label="scheduled">定时发布</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="createForm.schedule_type === 'scheduled'" label="开始时间">
          <el-date-picker
            v-model="createForm.scheduled_at"
            type="datetime"
            placeholder="选择发布时间"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 进度详情对话框 -->
    <el-dialog v-model="showProgressDialog" title="分发进度" width="700px">
      <div v-if="currentTask" class="progress-detail">
        <div class="summary">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="任务名称">{{ currentTask.name }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(currentTask.status)">
                {{ getStatusText(currentTask.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="总内容数">{{ currentTask.total_count }}</el-descriptions-item>
            <el-descriptions-item label="已发布">{{ currentTask.published_count }}</el-descriptions-item>
            <el-descriptions-item label="失败数">{{ currentTask.failed_count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatDate(currentTask.created_at) }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <h4 style="margin-top: 20px">发布记录</h4>
        <el-table :data="publishRecords" style="width: 100%; margin-top: 10px">
          <el-table-column prop="content_title" label="内容标题" />
          <el-table-column prop="platform_name" label="平台" width="120" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                {{ row.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="published_at" label="发布时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.published_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="error_message" label="错误信息" width="200">
            <template #default="{ row }">
              {{ row.error_message || '-' }}
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showProgressDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getDistributionTasks,
  createDistributionTask,
  startDistributionTask,
  pauseDistributionTask,
  deleteDistributionTask,
  getDistributionProgress
} from '@/api/business'
import { getWritingTasks } from '@/api/business'
import { getSocialAccounts } from '@/api/business'

const tasks = ref([])
const writingTasks = ref([])
const socialAccounts = ref([])
const publishRecords = ref([])
const currentTask = ref(null)

const showCreateDialog = ref(false)
const showProgressDialog = ref(false)

const createForm = ref({
  name: '',
  content_task_id: null,
  platforms: [],
  daily_limit: 0,
  schedule_type: 'immediate',
  scheduled_at: null
})

const getStatusType = (status) => {
  const map = {
    pending: 'info',
    running: 'warning',
    paused: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    pending: '待启动',
    running: '运行中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN')
}

const getContentTaskName = (taskId) => {
  const task = writingTasks.value.find(t => t.id === taskId)
  return task ? task.name : '-'
}

const loadTasks = async () => {
  try {
    const res = await getDistributionTasks()
    tasks.value = res.data
  } catch (e) {
    console.error('加载任务列表失败', e)
  }
}

const loadWritingTasks = async () => {
  try {
    const res = await getWritingTasks()
    writingTasks.value = res.data.filter(t => t.status === 'completed')
  } catch (e) {
    console.error('加载写作任务失败', e)
  }
}

const loadSocialAccounts = async () => {
  try {
    const res = await getSocialAccounts()
    socialAccounts.value = res.data.filter(a => a.status === 'active')
  } catch (e) {
    console.error('加载社交账号失败', e)
  }
}

const submitCreate = async () => {
  if (!createForm.value.name || !createForm.value.content_task_id || createForm.value.platforms.length === 0) {
    ElMessage.warning('请填写完整信息')
    return
  }
  try {
    await createDistributionTask(createForm.value)
    ElMessage.success('任务创建成功')
    showCreateDialog.value = false
    createForm.value = {
      name: '',
      content_task_id: null,
      platforms: [],
      daily_limit: 0,
      schedule_type: 'immediate',
      scheduled_at: null
    }
    await loadTasks()
  } catch (e) {
    ElMessage.error('创建失败：' + (e.response?.data?.detail || e.message))
  }
}

const startTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要启动任务 "${task.name}" 吗？`,
      '确认启动',
      { type: 'warning' }
    )
    await startDistributionTask(task.id)
    ElMessage.success('任务已启动')
    await loadTasks()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('启动失败')
    }
  }
}

const pauseTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要暂停任务 "${task.name}" 吗？`,
      '确认暂停',
      { type: 'warning' }
    )
    await pauseDistributionTask(task.id)
    ElMessage.success('任务已暂停')
    await loadTasks()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('暂停失败')
    }
  }
}

const viewProgress = async (task) => {
  try {
    currentTask.value = task
    const res = await getDistributionProgress(task.id)
    publishRecords.value = res.data.records || []
    showProgressDialog.value = true
  } catch (e) {
    ElMessage.error('加载进度失败')
  }
}

const deleteTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务 "${task.name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await deleteDistributionTask(task.id)
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
  loadWritingTasks()
  loadSocialAccounts()
})
</script>

<style scoped>
.distribution-page {
  padding: 20px;
}

.description {
  color: #666;
  margin-bottom: 20px;
}

.progress-detail {
  line-height: 1.8;
}

.summary {
  margin-bottom: 20px;
}
</style>
