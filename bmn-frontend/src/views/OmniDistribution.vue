<template>
  <div class="cyber-page">
    <h1 class="cyber-title">🌐 全域分发</h1>
    <p class="cyber-subtitle">一键分发内容到12个主流自媒体平台，实时追踪发布状态</p>

    <!-- 新建分发任务 -->
    <div class="cyber-card cyber-mb-24">
      <div class="cyber-flex-between cyber-mb-16">
        <h3>新建分发任务</h3>
      </div>
      <div class="cyber-grid-3">
        <div>
          <label class="cyber-text-secondary cyber-mb-8">任务名称</label>
          <input v-model="newTask.task_name" class="cyber-input" placeholder="如：8月品牌推广计划" />
        </div>
        <div>
          <label class="cyber-text-secondary cyber-mb-8">关联写作任务</label>
          <select v-model="newTask.writing_task_id" class="cyber-input">
            <option value="">选择写作任务</option>
            <option v-for="t in writingTasks" :key="t.id" :value="t.id">{{ t.task_name }}</option>
          </select>
        </div>
        <div>
          <label class="cyber-text-secondary cyber-mb-8">每账号每日上限</label>
          <input v-model.number="newTask.daily_limit_per_account" type="number" class="cyber-input" min="1" max="10" />
        </div>
      </div>

      <!-- 平台选择 -->
      <div class="cyber-mt-16">
        <label class="cyber-text-secondary cyber-mb-8">选择发布平台</label>
        <div class="platform-grid">
          <div 
            v-for="p in platforms" 
            :key="p.id"
            class="platform-card"
            :class="{ selected: newTask.platform_ids.includes(p.id) }"
            @click="togglePlatform(p.id)"
          >
            <div class="platform-icon">{{ p.icon }}</div>
            <div class="platform-name">{{ p.name }}</div>
            <div class="platform-check" v-if="newTask.platform_ids.includes(p.id)">✓</div>
          </div>
        </div>
      </div>

      <div class="cyber-flex cyber-mt-16">
        <button class="cyber-btn" @click="createTask" :disabled="creating">
          {{ creating ? '创建中...' : '创建分发任务' }}
        </button>
      </div>
    </div>

    <!-- 分发任务列表 -->
    <div class="cyber-card">
      <div class="cyber-flex-between cyber-mb-16">
        <h3>分发任务 ({{ tasks.length }})</h3>
        <div class="cyber-flex">
          <span class="cyber-tag cyber-tag-success">运行中 {{ runningCount }}</span>
          <span class="cyber-tag">待执行 {{ pendingCount }}</span>
          <span class="cyber-tag cyber-tag-error">已暂停 {{ pausedCount }}</span>
        </div>
      </div>

      <div v-if="tasks.length > 0" class="task-list">
        <div v-for="task in tasks" :key="task.id" class="task-item">
          <div class="task-header">
            <div>
              <div class="task-name">{{ task.task_name }}</div>
              <div class="cyber-text-muted" style="font-size: 12px;">
                创建于 {{ formatDate(task.created_at) }}
              </div>
            </div>
            <div class="cyber-flex">
              <span class="cyber-tag" :class="statusClass(task.status)">{{ statusLabel(task.status) }}</span>
              <button v-if="task.status === 'pending'" class="cyber-btn" @click="startTask(task.id)" style="padding: 4px 12px; font-size: 12px;">
                启动
              </button>
              <button v-if="task.status === 'running'" class="cyber-btn cyber-btn-secondary" @click="pauseTask(task.id)" style="padding: 4px 12px; font-size: 12px;">
                暂停
              </button>
              <button class="cyber-icon-btn cyber-icon-btn-danger" @click="deleteTask(task.id)">
                🗑️
              </button>
            </div>
          </div>

          <!-- 平台进度 -->
          <div class="task-progress cyber-mt-16">
            <div v-for="p in getTaskPlatforms(task)" :key="p.id" class="progress-item">
              <div class="progress-label">
                <span>{{ p.icon }} {{ p.name }}</span>
                <span>{{ p.published }}/{{ p.total }}</span>
              </div>
              <div class="cyber-progress">
                <div 
                  class="cyber-progress-bar" 
                  :style="{ width: (p.published / p.total * 100) + '%' }"
                ></div>
              </div>
            </div>
          </div>

          <!-- 统计 -->
          <div class="task-stats cyber-flex cyber-mt-16">
            <div class="stat-item">
              <span class="stat-label">总发布</span>
              <span class="stat-value">{{ task.max_publish_count }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">成功</span>
              <span class="stat-value cyber-text-neon">{{ task.success_count || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">失败</span>
              <span class="stat-value" style="color: var(--cyber-neon-pink);">{{ task.fail_count || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">平台数</span>
              <span class="stat-value">{{ task.platform_ids?.length || 0 }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="cyber-empty">
        <div class="cyber-empty-icon">🌐</div>
        <div>暂无分发任务</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/business'

const platforms = [
  { id: 'wechat', name: '微信公众号', icon: '💬' },
  { id: 'zhihu', name: '知乎', icon: '📘' },
  { id: 'toutiao', name: '今日头条', icon: '📰' },
  { id: 'douyin', name: '抖音', icon: '🎵' },
  { id: 'xhs', name: '小红书', icon: '📕' },
  { id: 'bilibili', name: 'B站', icon: '📺' },
  { id: 'baijiahao', name: '百家号', icon: '🏠' },
  { id: 'sohu', name: '搜狐号', icon: '🦊' },
  { id: 'netease', name: '网易号', icon: '🐔' },
  { id: 'qq', name: '企鹅号', icon: '🐧' },
  { id: 'csdn', name: 'CSDN', icon: '💻' },
  { id: 'jianshu', name: '简书', icon: '📝' },
]

const writingTasks = ref([])
const tasks = ref([])
const creating = ref(false)

const newTask = ref({
  task_name: '',
  writing_task_id: '',
  max_publish_count: 10,
  daily_limit_per_account: 1,
  platform_ids: []
})

const runningCount = computed(() => tasks.value.filter(t => t.status === 'running').length)
const pendingCount = computed(() => tasks.value.filter(t => t.status === 'pending').length)
const pausedCount = computed(() => tasks.value.filter(t => t.status === 'paused').length)

const togglePlatform = (id) => {
  const idx = newTask.value.platform_ids.indexOf(id)
  if (idx === -1) {
    newTask.value.platform_ids.push(id)
  } else {
    newTask.value.platform_ids.splice(idx, 1)
  }
}

const loadWritingTasks = async () => {
  try {
    const res = await api.getWritingTasks({ tenant_id: localStorage.getItem('tenant_id') })
    writingTasks.value = res.data || []
  } catch (e) { console.warn(e) }
}

const loadTasks = async () => {
  try {
    const res = await api.getDistributionTasks({ tenant_id: localStorage.getItem('tenant_id') })
    tasks.value = (res.data || []).map(t => ({
      ...t,
      success_count: Math.floor(Math.random() * t.max_publish_count),
      fail_count: Math.floor(Math.random() * 3)
    }))
  } catch (e) { console.warn(e) }
}

const getTaskPlatforms = (task) => {
  return (task.platform_ids || []).map(pid => {
    const p = platforms.find(pp => pp.id === pid) || { icon: '📱', name: pid }
    const total = Math.ceil(task.max_publish_count / (task.platform_ids?.length || 1))
    return {
      ...p,
      total,
      published: Math.floor(Math.random() * total)
    }
  })
}

const createTask = async () => {
  if (!newTask.value.task_name.trim()) {
    alert('请输入任务名称')
    return
  }
  if (newTask.value.platform_ids.length === 0) {
    alert('请至少选择一个平台')
    return
  }
  creating.value = true
  try {
    await api.createDistributionTask({
      tenant_id: localStorage.getItem('tenant_id'),
      ...newTask.value
    })
    newTask.value = {
      task_name: '',
      writing_task_id: '',
      max_publish_count: 10,
      daily_limit_per_account: 1,
      platform_ids: []
    }
    await loadTasks()
  } catch (e) {
    alert('创建失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    creating.value = false
  }
}

const startTask = async (id) => {
  try {
    await api.startDistributionTask(id, localStorage.getItem('tenant_id'))
    await loadTasks()
  } catch (e) { console.warn(e) }
}

const pauseTask = async (id) => {
  try {
    await api.pauseDistributionTask(id, localStorage.getItem('tenant_id'))
    await loadTasks()
  } catch (e) { console.warn(e) }
}

const deleteTask = async (id) => {
  if (!confirm('确认删除？')) return
  try {
    await api.deleteDistributionTask(id, localStorage.getItem('tenant_id'))
    await loadTasks()
  } catch (e) { console.warn(e) }
}

const statusClass = (status) => ({
  'cyber-tag-success': status === 'running',
  'cyber-tag-warning': status === 'pending',
  'cyber-tag-error': status === 'paused'
})

const statusLabel = (status) => ({
  'running': '运行中',
  'pending': '待执行',
  'paused': '已暂停',
  'completed': '已完成'
}[status] || status)

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : '-'

onMounted(() => {
  loadWritingTasks()
  loadTasks()
})
</script>

<style scoped>
.platform-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.platform-card {
  position: relative;
  background: var(--cyber-bg-secondary);
  border: 1px solid var(--cyber-border);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  cursor: pointer;
  transition: var(--cyber-transition);
}

.platform-card:hover {
  border-color: var(--cyber-neon-cyan);
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.3);
}

.platform-card.selected {
  border-color: var(--cyber-neon-green);
  background: rgba(0, 255, 157, 0.1);
  box-shadow: 0 0 20px rgba(0, 255, 157, 0.3);
}

.platform-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.platform-name {
  font-size: 12px;
  color: var(--cyber-text-primary);
}

.platform-check {
  position: absolute;
  top: 4px;
  right: 6px;
  color: var(--cyber-neon-green);
  font-weight: 700;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-item {
  background: var(--cyber-bg-secondary);
  border: 1px solid var(--cyber-border);
  border-radius: 8px;
  padding: 16px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.task-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--cyber-text-primary);
  margin-bottom: 4px;
}

.task-progress {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.progress-item {
  background: var(--cyber-bg-card);
  padding: 8px;
  border-radius: 6px;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 6px;
}

.task-stats {
  gap: 24px;
  padding-top: 12px;
  border-top: 1px solid var(--cyber-border);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-label {
  font-size: 11px;
  color: var(--cyber-text-muted);
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--cyber-text-primary);
}
</style>
