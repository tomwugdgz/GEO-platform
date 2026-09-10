import axios from 'axios'
import { resolveTenantId, cleanParams, cleanUrl } from './tenant'

const http = axios.create({
  baseURL: '/api/v2',
  timeout: 30000,
})

/**
 * 租户上下文兜底
 * 部分页面调用 getBrands() 时不传租户，拼出 /tenants/undefined/brands 导致 500；
 * 这里统一清洗参数、补 tenant_id，并把路径里的 undefined/null 段换成真实租户。
 */
http.interceptors.request.use(async (config) => {
  const method = (config.method || 'get').toLowerCase()

  config.url = cleanUrl(config.url)
  config.params = cleanParams(config.params)

  const needsTenantInPath =
    typeof config.url === 'string' && /\/tenants\/(undefined|null|\s*)\//.test(config.url)

  if (needsTenantInPath) {
    const tid = await resolveTenantId()
    if (tid) config.url = config.url.replace(/\/tenants\/(undefined|null|\s*)\//, `/tenants/${tid}/`)
  }

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

// ── 租户 ──
export const getTenants = async () => {
  const { data } = await http.get('/tenants')
  return data
}

export const getBrands = async (tenantId) => {
  const { data } = await http.get(`/tenants/${tenantId}/brands`)
  return data
}

// ── 意图洞察 ──
export const getScenarios = async (tenantId, params = {}) => {
  const { data } = await http.get(`/geo/intent/scenarios`, { params: { tenant_id: tenantId, ...params } })
  return data
}

export const createScenario = async (tenantId, payload) => {
  const { data } = await http.post(`/geo/intent/scenarios`, payload, { params: { tenant_id: tenantId } })
  return data
}

export const getIntentQueries = async (tenantId, params = {}) => {
  const { data } = await http.get(`/geo/intent/queries`, { params: { tenant_id: tenantId, ...params } })
  return data
}

export const createIntentQuery = async (tenantId, payload) => {
  const { data } = await http.post(`/geo/intent/queries`, payload, { params: { tenant_id: tenantId } })
  return data
}

// ── 知识库 ──
export const getKnowledgeUnits = async (tenantId, params = {}) => {
  const { data } = await http.get(`/geo/knowledge/units`, { params: { tenant_id: tenantId, ...params } })
  return data
}

export const createKnowledgeUnit = async (tenantId, payload) => {
  const { data } = await http.post(`/geo/knowledge/units`, payload, { params: { tenant_id: tenantId } })
  return data
}

export const validateKnowledgeUnit = async (tenantId, unitId) => {
  const { data } = await http.post(`/geo/knowledge/${unitId}/validate`, null, { params: { tenant_id: tenantId } })
  return data
}

// ── 内容生产 ──
export const getContentPieces = async (tenantId, params = {}) => {
  const { data } = await http.get(`/geo/content/pieces`, { params: { tenant_id: tenantId, ...params } })
  return data
}

export const generateContent = async (tenantId, payload) => {
  const { data } = await http.post(`/geo/content/generate`, payload, { params: { tenant_id: tenantId } })
  return data
}

export const approveContent = async (tenantId, pieceId) => {
  const { data } = await http.post(`/geo/content/${pieceId}/approve`, null, { params: { tenant_id: tenantId } })
  return data
}

export const scoreContent = async (tenantId, pieceId) => {
  const { data } = await http.post(`/geo/content/${pieceId}/score`, null, { params: { tenant_id: tenantId } })
  return data
}

// ── 监测看板 ──
export const getMonitorSnapshots = async (tenantId, params = {}) => {
  const { data } = await http.get(`/geo/monitor/snapshots`, { params: { tenant_id: tenantId, ...params } })
  return data
}

export const scanMonitor = async (tenantId, payload) => {
  const { data } = await http.post(`/geo/monitor/scan`, payload, { params: { tenant_id: tenantId } })
  return data
}

export const getMonitorBoard = async (tenantId, params = {}) => {
  const { data } = await http.get(`/geo/monitor/board`, { params: { tenant_id: tenantId, ...params } })
  return data
}

export const getCompetitors = async (tenantId, params = {}) => {
  const { data } = await http.get(`/geo/monitor/competitors`, { params: { tenant_id: tenantId, ...params } })
  return data
}

export default {
  getTenants, getBrands,
  getScenarios, createScenario, getIntentQueries, createIntentQuery,
  getKnowledgeUnits, createKnowledgeUnit, validateKnowledgeUnit,
  getContentPieces, generateContent, approveContent, scoreContent,
  getMonitorSnapshots, scanMonitor, getMonitorBoard, getCompetitors,
}
