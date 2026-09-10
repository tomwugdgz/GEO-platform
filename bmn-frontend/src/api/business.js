import axios from 'axios'
import { resolveTenantId, cleanParams, cleanUrl } from './tenant'

const api = axios.create({
  baseURL: '/api/v2'
})

/**
 * 租户上下文统一兜底：补齐 tenant_id + 清洗无效参数
 * （详见 @/api/tenant 的说明；页面无需逐个改造）
 */
api.interceptors.request.use(async (config) => {
  const method = (config.method || 'get').toLowerCase()

  config.url = cleanUrl(config.url)
  config.params = cleanParams(config.params)

  if (method === 'get' || method === 'delete') {
    const hasInUrl = typeof config.url === 'string' && config.url.includes('tenant_id=')
    const hasInParams = config.params && config.params.tenant_id
    if (!hasInUrl && !hasInParams) {
      const tid = await resolveTenantId()
      if (tid) config.params = { tenant_id: tid, ...(config.params || {}) }
    }
  }

  return config
})

// 蒸馏主词 API
export const getKeywords = (params) => api.get('/geo/distill/keywords', { params })
export const createKeyword = (data) => api.post('/geo/distill/keywords', data)
export const deleteKeyword = (id) => api.delete(`/geo/distill/keywords/${id}`)
export const updateKeyword = (id, data) => api.put(`/geo/distill/keywords/${id}`, data)

// 图库 API
export const getCategories = (params) => api.get('/geo/gallery/categories', { params })
export const createCategory = (data) => api.post('/geo/gallery/categories', data)
export const deleteCategory = (id) => api.delete(`/geo/gallery/categories/${id}`)
export const uploadImage = (formData) => api.post('/geo/gallery/images', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const getImages = (params) => api.get('/geo/gallery/images', { params })
export const deleteImage = (id) => api.delete(`/geo/gallery/images/${id}`)

// 自媒体账号 API
export const getSocialAccounts = (params) => api.get('/geo/social/accounts', { params })
export const createSocialAccount = (data) => api.post('/geo/social/accounts', data)
export const deleteSocialAccount = (id) => api.delete(`/geo/social/accounts/${id}`)
export const activateSocialAccount = (id, data) => api.post(`/geo/social/accounts/${id}/activate`, data)

// 写作任务 API
export const getWritingTasks = (params) => api.get('/geo/writing/tasks', { params })
export const createWritingTask = (data) => api.post('/geo/writing/tasks', data)
export const executeWritingTask = (id, tenantId) => api.post(`/geo/writing/tasks/${id}/run?tenant_id=${tenantId}`)
export const deleteWritingTask = (id, tenantId) => api.delete(`/geo/writing/tasks/${id}?tenant_id=${tenantId}`)
export const getTaskResults = (id, params) => api.get(`/geo/writing/tasks/${id}/results`, { params })

// 分发任务 API（后端实际路径：/geo/feed/*）
export const getDistributionTasks = (params) => api.get('/geo/feed/tasks', { params })
export const createDistributionTask = (data) => api.post('/geo/feed/tasks', data)
export const startDistributionTask = (id, tenantId) => api.post(`/geo/feed/tasks/${id}/start?tenant_id=${tenantId}`)
export const pauseDistributionTask = (id, tenantId) => api.post(`/geo/feed/tasks/${id}/pause?tenant_id=${tenantId}`)
export const deleteDistributionTask = (id, tenantId) => api.delete(`/geo/feed/tasks/${id}?tenant_id=${tenantId}`)
export const getDistributionProgress = (id, tenantId) => api.get(`/geo/feed/tasks/${id}/progress?tenant_id=${tenantId}`)

// 监测看板 API（临时 mock，后端暂无此模块）
// 注意：页面统一按 res.data 取值，这里必须返回 { data } 结构，
// 字段名也要与 Monitoring.vue 的模板保持一致（appearance_rate 等）。
export const getMonitoringOverview = (params) => Promise.resolve({
  data: {
    appearance_rate: 0,
    appearance_trend: 0,
    citation_rates: 0,
    citation_trend: 0,
    recommendation_rates: 0,
    recommendation_trend: 0,
    geo_health_score: 0,
    health_trend: 0,
    total_queries: 0,
    platform_count: 0
  }
})
export const getPlatformData = (params) => Promise.resolve({ data: [] })
export const getCompetitorData = (params) => Promise.resolve({ data: [] })
export const getPlatformDetail = (platform, params) => Promise.resolve({
  data: {
    platform,
    platform_name: platform,
    appearance_rate: 0,
    citation_rates: 0,
    recommendation_rates: 0,
    samples: []
  }
})

export default {
  // 蒸馏主词
  getKeywords,
  createKeyword,
  deleteKeyword,
  updateKeyword,
  // 图库
  getCategories,
  createCategory,
  deleteCategory,
  uploadImage,
  getImages,
  deleteImage,
  // 自媒体
  getSocialAccounts,
  createSocialAccount,
  deleteSocialAccount,
  activateSocialAccount,
  // 写作任务
  getWritingTasks,
  createWritingTask,
  executeWritingTask,
  deleteWritingTask,
  // 分发任务
  getDistributionTasks,
  createDistributionTask,
  startDistributionTask,
  pauseDistributionTask,
  deleteDistributionTask,
  getDistributionProgress,
  // 监测看板
  getMonitoringOverview,
  getPlatformData,
  getCompetitorData,
  getPlatformDetail
}
