<template>
  <div class="cyber-page">
    <h1 class="cyber-title">👥 团队协作</h1>
    <p class="cyber-subtitle">多角色协同工作，任务分配与进度追踪</p>

    <!-- 团队概览 -->
    <div class="team-overview cyber-grid-4 cyber-mb-24">
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-body">
          <div class="stat-value">{{ teamStats.totalMembers }}</div>
          <div class="stat-label">团队成员</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-body">
          <div class="stat-value">{{ teamStats.completedTasks }}</div>
          <div class="stat-label">已完成任务</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⏳</div>
        <div class="stat-body">
          <div class="stat-value">{{ teamStats.pendingTasks }}</div>
          <div class="stat-label">进行中任务</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-body">
          <div class="stat-value">{{ teamStats.completionRate }}%</div>
          <div class="stat-label">完成率</div>
        </div>
      </div>
    </div>

    <!-- 团队成员 -->
    <div class="cyber-card cyber-mb-24">
      <div class="card-header">
        <h3>团队成员</h3>
        <button class="cyber-btn" @click="showInviteDialog = true">邀请成员</button>
      </div>

      <div class="member-list">
        <div v-for="member in members" :key="member.id" class="member-item">
          <div class="member-avatar" :style="{ background: member.color }">
            {{ member.name[0] }}
          </div>
          <div class="member-info">
            <div class="member-name">{{ member.name }}</div>
            <div class="member-role">{{ member.role }}</div>
          </div>
          <div class="member-stats">
            <div class="member-stat">
              <div class="stat-num">{{ member.completedTasks }}</div>
              <div class="stat-text">已完成</div>
            </div>
            <div class="member-stat">
              <div class="stat-num">{{ member.pendingTasks }}</div>
              <div class="stat-text">进行中</div>
            </div>
          </div>
          <div class="member-actions">
            <button class="cyber-icon-btn" @click="viewMember(member)">👁️</button>
            <button class="cyber-icon-btn" @click="editMember(member)">✏️</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 任务看板 -->
    <div class="cyber-card">
      <div class="card-header">
        <h3>任务看板</h3>
        <div class="card-actions">
          <select v-model="taskFilter" class="cyber-input" style="width: 150px;">
            <option value="all">全部任务</option>
            <option value="todo">待处理</option>
            <option value="doing">进行中</option>
            <option value="done">已完成</option>
          </select>
          <button class="cyber-btn" @click="showCreateTask = true">创建任务</button>
        </div>
      </div>

      <div class="kanban-board">
        <!-- 待处理 -->
        <div class="kanban-column">
          <div class="column-header">
            <span class="column-icon">📋</span>
            <span>待处理</span>
            <span class="column-count">{{ todoTasks.length }}</span>
          </div>
          <div class="column-body">
            <div v-for="task in todoTasks" :key="task.id" class="task-card">
              <div class="task-header">
                <span class="task-priority" :class="task.priority">{{ priorityLabel(task.priority) }}</span>
                <span class="task-title">{{ task.title }}</span>
              </div>
              <div class="task-desc">{{ task.description }}</div>
              <div class="task-footer">
                <div class="task-assignee">
                  <div class="assignee-avatar" :style="{ background: getMemberColor(task.assigneeId) }">
                    {{ getMemberName(task.assigneeId)[0] }}
                  </div>
                  <span>{{ getMemberName(task.assigneeId) }}</span>
                </div>
                <div class="task-deadline">{{ task.deadline }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 进行中 -->
        <div class="kanban-column">
          <div class="column-header">
            <span class="column-icon">⏳</span>
            <span>进行中</span>
            <span class="column-count">{{ doingTasks.length }}</span>
          </div>
          <div class="column-body">
            <div v-for="task in doingTasks" :key="task.id" class="task-card">
              <div class="task-header">
                <span class="task-priority" :class="task.priority">{{ priorityLabel(task.priority) }}</span>
                <span class="task-title">{{ task.title }}</span>
              </div>
              <div class="task-desc">{{ task.description }}</div>
              <div class="task-progress">
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: task.progress + '%' }"></div>
                </div>
                <span class="progress-text">{{ task.progress }}%</span>
              </div>
              <div class="task-footer">
                <div class="task-assignee">
                  <div class="assignee-avatar" :style="{ background: getMemberColor(task.assigneeId) }">
                    {{ getMemberName(task.assigneeId)[0] }}
                  </div>
                  <span>{{ getMemberName(task.assigneeId) }}</span>
                </div>
                <div class="task-deadline">{{ task.deadline }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 已完成 -->
        <div class="kanban-column">
          <div class="column-header">
            <span class="column-icon">✅</span>
            <span>已完成</span>
            <span class="column-count">{{ doneTasks.length }}</span>
          </div>
          <div class="column-body">
            <div v-for="task in doneTasks" :key="task.id" class="task-card task-done">
              <div class="task-header">
                <span class="task-priority" :class="task.priority">{{ priorityLabel(task.priority) }}</span>
                <span class="task-title">{{ task.title }}</span>
              </div>
              <div class="task-desc">{{ task.description }}</div>
              <div class="task-footer">
                <div class="task-assignee">
                  <div class="assignee-avatar" :style="{ background: getMemberColor(task.assigneeId) }">
                    {{ getMemberName(task.assigneeId)[0] }}
                  </div>
                  <span>{{ getMemberName(task.assigneeId) }}</span>
                </div>
                <div class="task-completed">完成于 {{ task.completedAt }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 邀请成员对话框 -->
    <div v-if="showInviteDialog" class="dialog-overlay" @click.self="showInviteDialog = false">
      <div class="dialog-box">
        <div class="dialog-header">
          <h3>邀请团队成员</h3>
          <button class="cyber-icon-btn" @click="showInviteDialog = false">✖</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>成员姓名</label>
            <input v-model="newMember.name" class="cyber-input" placeholder="输入姓名" />
          </div>
          <div class="form-group">
            <label>角色</label>
            <select v-model="newMember.role" class="cyber-input">
              <option value="管理员">管理员</option>
              <option value="编辑">编辑</option>
              <option value="运营">运营</option>
              <option value="分析师">分析师</option>
            </select>
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input v-model="newMember.email" type="email" class="cyber-input" placeholder="输入邮箱" />
          </div>
        </div>
        <div class="dialog-footer">
          <button class="cyber-btn cyber-btn-secondary" @click="showInviteDialog = false">取消</button>
          <button class="cyber-btn" @click="inviteMember">发送邀请</button>
        </div>
      </div>
    </div>

    <!-- 创建任务对话框 -->
    <div v-if="showCreateTask" class="dialog-overlay" @click.self="showCreateTask = false">
      <div class="dialog-box">
        <div class="dialog-header">
          <h3>创建新任务</h3>
          <button class="cyber-icon-btn" @click="showCreateTask = false">✖</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>任务标题</label>
            <input v-model="newTask.title" class="cyber-input" placeholder="输入任务标题" />
          </div>
          <div class="form-group">
            <label>任务描述</label>
            <textarea v-model="newTask.description" class="cyber-input" rows="3" placeholder="输入任务描述"></textarea>
          </div>
          <div class="form-group">
            <label>优先级</label>
            <select v-model="newTask.priority" class="cyber-input">
              <option value="high">高</option>
              <option value="medium">中</option>
              <option value="low">低</option>
            </select>
          </div>
          <div class="form-group">
            <label>指派给</label>
            <select v-model="newTask.assigneeId" class="cyber-input">
              <option value="">选择成员</option>
              <option v-for="m in members" :key="m.id" :value="m.id">{{ m.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>截止日期</label>
            <input v-model="newTask.deadline" type="date" class="cyber-input" />
          </div>
        </div>
        <div class="dialog-footer">
          <button class="cyber-btn cyber-btn-secondary" @click="showCreateTask = false">取消</button>
          <button class="cyber-btn" @click="createTask">创建任务</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const taskFilter = ref('all')
const showInviteDialog = ref(false)
const showCreateTask = ref(false)

const teamStats = ref({
  totalMembers: 8,
  completedTasks: 47,
  pendingTasks: 12,
  completionRate: 79
})

const members = ref([
  { id: 1, name: '张三', role: '管理员', color: '#00ff9d', completedTasks: 18, pendingTasks: 3 },
  { id: 2, name: '李四', role: '编辑', color: '#00d4ff', completedTasks: 15, pendingTasks: 5 },
  { id: 3, name: '王五', role: '运营', color: '#8338ec', completedTasks: 12, pendingTasks: 2 },
  { id: 4, name: '赵六', role: '分析师', color: '#ffbe0b', completedTasks: 8, pendingTasks: 4 }
])

const newMember = ref({
  name: '',
  role: '编辑',
  email: ''
})

const tasks = ref([
  { id: 1, title: '品牌诊断报告', description: '完成Q4品牌AI出镜率诊断', priority: 'high', status: 'done', assigneeId: 1, deadline: '2026-08-20', completedAt: '08-20', progress: 100 },
  { id: 2, title: '蒸馏关键词优化', description: '优化社区门禁相关蒸馏词', priority: 'medium', status: 'done', assigneeId: 2, deadline: '2026-08-22', completedAt: '08-22', progress: 100 },
  { id: 3, title: '内容生产计划', description: '制定9月内容生产排期', priority: 'high', status: 'doing', assigneeId: 2, deadline: '2026-08-30', progress: 65 },
  { id: 4, title: '多平台分发配置', description: '配置12个平台的分发策略', priority: 'medium', status: 'doing', assigneeId: 3, deadline: '2026-08-28', progress: 40 },
  { id: 5, title: 'AI追踪报告', description: '生成8月AI平台追踪报告', priority: 'low', status: 'todo', assigneeId: 4, deadline: '2026-09-05', progress: 0 },
  { id: 6, title: '竞品分析', description: '分析TOP5竞品的AI出镜策略', priority: 'medium', status: 'todo', assigneeId: 4, deadline: '2026-09-03', progress: 0 }
])

const newTask = ref({
  title: '',
  description: '',
  priority: 'medium',
  assigneeId: '',
  deadline: ''
})

const todoTasks = computed(() => {
  const filtered = taskFilter.value === 'all' || taskFilter.value === 'todo'
  return filtered ? tasks.value.filter(t => t.status === 'todo') : []
})

const doingTasks = computed(() => {
  const filtered = taskFilter.value === 'all' || taskFilter.value === 'doing'
  return filtered ? tasks.value.filter(t => t.status === 'doing') : []
})

const doneTasks = computed(() => {
  const filtered = taskFilter.value === 'all' || taskFilter.value === 'done'
  return filtered ? tasks.value.filter(t => t.status === 'done') : []
})

const priorityLabel = (p) => ({
  'high': '高',
  'medium': '中',
  'low': '低'
}[p] || p)

const getMemberName = (id) => {
  const member = members.value.find(m => m.id === id)
  return member ? member.name : '未分配'
}

const getMemberColor = (id) => {
  const member = members.value.find(m => m.id === id)
  return member ? member.color : '#666'
}

const inviteMember = () => {
  if (!newMember.value.name || !newMember.value.email) {
    alert('请填写完整信息')
    return
  }
  const colors = ['#00ff9d', '#00d4ff', '#8338ec', '#ffbe0b', '#ff006e']
  members.value.push({
    id: members.value.length + 1,
    name: newMember.value.name,
    role: newMember.value.role,
    color: colors[Math.floor(Math.random() * colors.length)],
    completedTasks: 0,
    pendingTasks: 0
  })
  newMember.value = { name: '', role: '编辑', email: '' }
  showInviteDialog.value = false
  teamStats.value.totalMembers++
}

const createTask = () => {
  if (!newTask.value.title || !newTask.value.assigneeId) {
    alert('请填写任务标题和指派成员')
    return
  }
  tasks.value.push({
    id: tasks.value.length + 1,
    ...newTask.value,
    status: 'todo',
    progress: 0,
    deadline: newTask.value.deadline || '2026-09-30'
  })
  newTask.value = { title: '', description: '', priority: 'medium', assigneeId: '', deadline: '' }
  showCreateTask.value = false
  teamStats.value.pendingTasks++
}

const viewMember = (member) => {
  alert(`查看成员详情：${member.name} (${member.role})`)
}

const editMember = (member) => {
  alert(`编辑成员：${member.name}`)
}
</script>

<style scoped>
.team-overview {
  gap: 16px;
}

.stat-card {
  background: var(--cyber-bg-secondary);
  border: 1px solid var(--cyber-border);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: var(--cyber-transition);
}

.stat-card:hover {
  border-color: var(--cyber-neon-cyan);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}

.stat-icon {
  font-size: 36px;
}

.stat-body {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--cyber-neon-green);
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: var(--cyber-text-secondary);
  margin-top: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-actions {
  display: flex;
  gap: 12px;
}

.member-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--cyber-bg-secondary);
  border: 1px solid var(--cyber-border);
  border-radius: 8px;
  transition: var(--cyber-transition);
}

.member-item:hover {
  border-color: var(--cyber-neon-cyan);
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
}

.member-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  color: #000;
}

.member-info {
  flex: 1;
}

.member-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--cyber-text-primary);
}

.member-role {
  font-size: 13px;
  color: var(--cyber-text-secondary);
  margin-top: 2px;
}

.member-stats {
  display: flex;
  gap: 24px;
}

.member-stat {
  text-align: center;
}

.member-stat .stat-num {
  font-size: 20px;
  font-weight: 700;
  color: var(--cyber-neon-green);
}

.member-stat .stat-text {
  font-size: 11px;
  color: var(--cyber-text-muted);
  margin-top: 2px;
}

.member-actions {
  display: flex;
  gap: 8px;
}

.kanban-board {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.kanban-column {
  background: var(--cyber-bg-secondary);
  border: 1px solid var(--cyber-border);
  border-radius: 8px;
  min-height: 400px;
}

.column-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border-bottom: 1px solid var(--cyber-border);
  font-weight: 600;
}

.column-icon {
  font-size: 20px;
}

.column-count {
  margin-left: auto;
  background: var(--cyber-bg-card);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  color: var(--cyber-text-secondary);
}

.column-body {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-card {
  background: var(--cyber-bg-card);
  border: 1px solid var(--cyber-border);
  border-radius: 8px;
  padding: 12px;
  transition: var(--cyber-transition);
}

.task-card:hover {
  border-color: var(--cyber-neon-cyan);
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
}

.task-done {
  opacity: 0.7;
}

.task-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.task-priority {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.task-priority.high {
  background: rgba(255, 0, 110, 0.2);
  color: var(--cyber-neon-pink);
}

.task-priority.medium {
  background: rgba(255, 190, 11, 0.2);
  color: var(--cyber-neon-yellow);
}

.task-priority.low {
  background: rgba(0, 212, 255, 0.2);
  color: var(--cyber-neon-cyan);
}

.task-title {
  font-weight: 600;
  color: var(--cyber-text-primary);
}

.task-desc {
  font-size: 13px;
  color: var(--cyber-text-secondary);
  margin-bottom: 12px;
  line-height: 1.4;
}

.task-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: var(--cyber-bg-secondary);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--cyber-neon-green), var(--cyber-neon-cyan));
  transition: width 0.3s;
}

.progress-text {
  font-size: 12px;
  color: var(--cyber-text-secondary);
  min-width: 35px;
}

.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.task-assignee {
  display: flex;
  align-items: center;
  gap: 6px;
}

.assignee-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #000;
}

.task-deadline,
.task-completed {
  color: var(--cyber-text-muted);
}

/* Dialog */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-box {
  background: var(--cyber-bg-card);
  border: 1px solid var(--cyber-neon-cyan);
  border-radius: 12px;
  width: 500px;
  max-width: 90vw;
  box-shadow: 0 0 40px rgba(0, 212, 255, 0.3);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--cyber-border);
}

.dialog-header h3 {
  margin: 0;
  color: var(--cyber-text-primary);
}

.dialog-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--cyber-text-secondary);
  font-size: 13px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--cyber-border);
}
</style>
