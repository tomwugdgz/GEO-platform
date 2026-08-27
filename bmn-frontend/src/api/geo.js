import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v2',
  timeout: 30000,
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
