<template>
  <div class="geolook-dashboard">
    <div class="header">
      <h1>🔬 GeoLook 引擎</h1>
      <p class="subtitle">基于 GeoLook 0.2.0 的 GEO 优化诊断系统</p>
    </div>

    <!-- 项目列表 -->
    <div class="section">
      <div class="section-header">
        <h2>📁 项目列表</h2>
        <button @click="refreshProjects" class="btn btn-secondary">刷新</button>
      </div>
      
      <div v-if="loading" class="loading">加载中...</div>
      
      <div v-else-if="projects.length === 0" class="empty">
        暂无项目，点击下方按钮创建新项目
      </div>
      
      <div v-else class="project-grid">
        <div v-for="project in projects" :key="project.slug" class="project-card">
          <div class="project-header">
            <h3>{{ project.brand_name }}</h3>
            <span class="market-badge">{{ project.market }}</span>
          </div>
          <div class="project-info">
            <p><strong>Slug:</strong> {{ project.slug }}</p>
            <p><strong>网站:</strong> <a :href="project.site" target="_blank">{{ project.site }}</a></p>
            <p><strong>问题数:</strong> {{ project.question_count }}</p>
            <p><strong>竞品数:</strong> {{ project.competitor_count }}</p>
            <p><strong>创建时间:</strong> {{ formatDate(project.created_at) }}</p>
          </div>
          <div class="project-actions">
            <button @click="runAudit(project.slug)" :disabled="running[project.slug]" class="btn btn-primary">
              {{ running[project.slug] ? '诊断中...' : '运行诊断' }}
            </button>
            <button @click="viewResults(project.slug)" class="btn btn-secondary">查看结果</button>
          </div>
          <!-- 直接跳转到该项目的 GeoLook 各模块（同时把它记为「当前项目」） -->
          <div class="project-modules">
            <button @click="openModule(project.slug, '/geo/siteaudit')" class="btn btn-link">站点审计</button>
            <button @click="openModule(project.slug, '/geo/gaps')" class="btn btn-link">缺口诊断</button>
            <button @click="openModule(project.slug, '/geo/plan')" class="btn btn-link">工单</button>
            <button @click="openModule(project.slug, '/geo/competitors')" class="btn btn-link">竞品</button>
            <button @click="openModule(project.slug, '/geo/channels')" class="btn btn-link">渠道</button>
            <button @click="openModule(project.slug, '/geo/verify')" class="btn btn-link">验收</button>
            <button @click="openModule(project.slug, '/settings')" class="btn btn-link">引擎配置</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建新项目 -->
    <div class="section">
      <h2>➕ 创建新项目</h2>
      <form @submit.prevent="createProject" class="create-form">
        <div class="form-group">
          <label>网站 URL *</label>
          <input v-model="newProject.url" type="url" required placeholder="https://example.com" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>品牌名称</label>
            <input v-model="newProject.name" type="text" placeholder="可选，自动从网站提取" />
          </div>
          <div class="form-group">
            <label>项目 Slug</label>
            <input v-model="newProject.slug" type="text" placeholder="可选，自动生成" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>市场</label>
            <select v-model="newProject.market">
              <option value="cn">中国 (cn)</option>
              <option value="global">全球 (global)</option>
              <option value="both">两者 (both)</option>
            </select>
          </div>
          <div class="form-group">
            <label>最大页面数</label>
            <input v-model.number="newProject.max_pages" type="number" min="1" max="100" />
          </div>
        </div>
        <button type="submit" :disabled="creating" class="btn btn-primary">
          {{ creating ? '创建中...' : '创建项目' }}
        </button>
      </form>
    </div>

    <!-- 诊断结果 -->
    <div v-if="auditResult" class="section">
      <h2>📊 诊断结果 - {{ auditResult.slug }}</h2>
      <div class="audit-summary">
        <div class="metric-card">
          <div class="metric-value">{{ auditResult.avg_score }}</div>
          <div class="metric-label">平均得分</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{{ auditResult.page_count }}</div>
          <div class="metric-label">页面数</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{{ auditResult.grade_distribution?.A || 0 }}</div>
          <div class="metric-label">A 级页面</div>
        </div>
        <div class="metric-card">
          <div class="metric-value">{{ auditResult.grade_distribution?.B || 0 }}</div>
          <div class="metric-label">B 级页面</div>
        </div>
      </div>
      
      <div v-if="auditResult.site_issues && auditResult.site_issues.length > 0" class="issues-section">
        <h3>⚠️ 站点问题</h3>
        <ul class="issue-list">
          <li v-for="(issue, idx) in auditResult.site_issues" :key="idx">{{ issue }}</li>
        </ul>
      </div>

      <div v-if="auditResult.pages && auditResult.pages.length > 0" class="pages-section">
        <h3>📄 页面详情</h3>
        <div class="page-table">
          <table>
            <thead>
              <tr>
                <th>URL</th>
                <th>得分</th>
                <th>等级</th>
                <th>字数</th>
                <th>可抽取块</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="page in auditResult.pages" :key="page.url">
                <td class="url-cell">{{ page.url }}</td>
                <td>{{ page.score }}</td>
                <td><span :class="'grade-' + page.grade">{{ page.grade }}</span></td>
                <td>{{ page.word_count }}</td>
                <td>{{ Object.values(page.blocks || {}).filter(v => v).length }}/5</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 消息提示 -->
    <div v-if="message" :class="['message', messageType]">
      {{ message }}
      <button @click="message = ''" class="close-btn">×</button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/axios'
import { setStoredSlug } from '@/composables/useGeoProject'

export default {
  name: 'GeoLookDashboard',
  setup() {
    const router = useRouter()
    const projects = ref([])
    const loading = ref(false)
    const creating = ref(false)
    const running = reactive({})
    const auditResult = ref(null)
    const message = ref('')
    const messageType = ref('success')

    const newProject = reactive({
      url: '',
      name: '',
      slug: '',
      market: 'cn',
      max_pages: 25
    })

    const refreshProjects = async () => {
      loading.value = true
      try {
        const res = await api.get('/api/v2/geolook/projects')
        projects.value = res.data
      } catch (err) {
        showMessage('加载项目失败: ' + (err.response?.data?.detail || err.message), 'error')
      } finally {
        loading.value = false
      }
    }

    const createProject = async () => {
      if (!newProject.url) {
        showMessage('请输入网站 URL', 'error')
        return
      }
      creating.value = true
      try {
        const res = await api.post('/api/v2/geolook/projects/init', newProject)
        if (res.data?.slug) setStoredSlug(res.data.slug)   // 新项目自动成为当前项目
        showMessage('项目创建成功: ' + res.data.slug, 'success')
        await refreshProjects()
        // 重置表单
        newProject.url = ''
        newProject.name = ''
        newProject.slug = ''
        newProject.market = 'cn'
        newProject.max_pages = 25
      } catch (err) {
        showMessage('创建失败: ' + (err.response?.data?.detail || err.message), 'error')
      } finally {
        creating.value = false
      }
    }

    // 维护「当前项目」：对该项目执行操作即视为选中它，供各子页面复用
    const selectProject = (slug) => {
      setStoredSlug(slug)
      return slug
    }

    const runAudit = async (slug) => {
      selectProject(slug)
      running[slug] = true
      try {
        // 先抓取
        await api.post(`/api/v2/geolook/projects/${slug}/crawl`, { max_pages: 25 })
        showMessage('抓取完成，开始诊断...', 'success')
        
        // 再诊断
        const res = await api.post(`/api/v2/geolook/projects/${slug}/audit`)
        auditResult.value = res.data.data
        showMessage('诊断完成！', 'success')
      } catch (err) {
        showMessage('诊断失败: ' + (err.response?.data?.detail || err.message), 'error')
      } finally {
        running[slug] = false
      }
    }

    // 跳转到指定模块，并把该项目记为当前项目
    const openModule = (slug, path) => {
      selectProject(slug)
      router.push(path)
    }

    const viewResults = async (slug) => {
      selectProject(slug)
      try {
        const res = await api.get(`/api/v2/geolook/projects/${slug}/audit-data`)
        auditResult.value = res.data
        showMessage('加载诊断结果成功', 'success')
      } catch (err) {
        showMessage('加载失败: ' + (err.response?.data?.detail || err.message), 'error')
      }
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return '-'
      const d = new Date(dateStr)
      return d.toLocaleString('zh-CN')
    }

    const showMessage = (msg, type = 'success') => {
      message.value = msg
      messageType.value = type
      setTimeout(() => { message.value = '' }, 5000)
    }

    onMounted(() => {
      refreshProjects()
    })

    return {
      projects,
      loading,
      creating,
      running,
      auditResult,
      message,
      messageType,
      newProject,
      refreshProjects,
      createProject,
      runAudit,
      viewResults,
      openModule,
      formatDate
    }
  }
}
</script>

<style scoped>
.geolook-dashboard {
  padding: 24px;
  max-width: 1400px;
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

.section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  margin: 0;
  font-size: 20px;
  color: #1a1a1a;
}

.loading, .empty {
  text-align: center;
  padding: 40px;
  color: #999;
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.project-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s;
}

.project-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.project-header h3 {
  margin: 0;
  font-size: 18px;
  color: #1a1a1a;
}

.market-badge {
  background: #4CAF50;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  text-transform: uppercase;
}

.project-info p {
  margin: 8px 0;
  font-size: 14px;
  color: #666;
}

.project-info a {
  color: #2196F3;
  text-decoration: none;
}

.project-info a:hover {
  text-decoration: underline;
}

.project-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

/* 跳转到该项目的各 GeoLook 模块 */
.project-modules {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e0e0e0;
}

.btn-link {
  background: transparent;
  color: #2196F3;
  padding: 2px 6px;
  font-size: 13px;
  border-radius: 4px;
}

.btn-link:hover {
  background: #E3F2FD;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-primary {
  background: #2196F3;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1976D2;
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.create-form {
  max-width: 800px;
}

.form-group {
  margin-bottom: 16px;
  flex: 1;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #2196F3;
}

.audit-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}

.metric-value {
  font-size: 32px;
  font-weight: bold;
  color: #2196F3;
  margin-bottom: 8px;
}

.metric-label {
  font-size: 14px;
  color: #666;
}

.issues-section, .pages-section {
  margin-top: 24px;
}

.issues-section h3, .pages-section h3 {
  font-size: 18px;
  margin-bottom: 12px;
  color: #1a1a1a;
}

.issue-list {
  background: #fff3cd;
  border-left: 4px solid #ffc107;
  padding: 16px;
  border-radius: 4px;
}

.issue-list li {
  margin: 8px 0;
  color: #856404;
}

.page-table {
  overflow-x: auto;
}

.page-table table {
  width: 100%;
  border-collapse: collapse;
}

.page-table th,
.page-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.page-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #333;
}

.url-cell {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.grade-A { background: #4CAF50; color: white; padding: 2px 8px; border-radius: 4px; }
.grade-B { background: #8BC34A; color: white; padding: 2px 8px; border-radius: 4px; }
.grade-C { background: #FFC107; color: white; padding: 2px 8px; border-radius: 4px; }
.grade-D { background: #F44336; color: white; padding: 2px 8px; border-radius: 4px; }

.message {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 16px 24px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 12px;
}

.message.success {
  background: #4CAF50;
  color: white;
}

.message.error {
  background: #F44336;
  color: white;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
}
</style>
