/**
 * 租户上下文解析（API 层共用）
 *
 * 后端把 tenant_id 声明为必填，缺失时返回 422；
 * 部分页面还会把 undefined / null 拼进 URL 或参数，导致 500。
 * 这里提供统一的解析与参数清洗，页面无需逐个改造。
 */
import axios from 'axios'

const readStored = (key) => {
  try { return localStorage.getItem(key) || '' } catch { return '' }
}

let tenantIdPromise = null

/** 解析当前租户 id：localStorage 优先，其次取租户列表第一个（结果缓存复用） */
export function resolveTenantId() {
  const stored = readStored('tenant_id')
  if (stored) return Promise.resolve(stored)

  if (!tenantIdPromise) {
    tenantIdPromise = axios
      .get('/api/v2/tenants')
      .then((r) => {
        const first = Array.isArray(r.data) && r.data[0] ? r.data[0].id : ''
        if (first) {
          try { localStorage.setItem('tenant_id', first) } catch { /* ignore */ }
        }
        return first
      })
      .catch(() => '')
      .finally(() => { tenantIdPromise = null })
  }
  return tenantIdPromise
}

/** 无效值判定：axios 不会自动剔除字符串 "null" / "undefined" */
export function isBadParam(value) {
  return (
    value === null ||
    value === undefined ||
    value === '' ||
    value === 'null' ||
    value === 'undefined'
  )
}

/** 清洗 params 对象中的无效项 */
export function cleanParams(params) {
  if (!params || typeof params !== 'object') return params
  const out = {}
  for (const [k, v] of Object.entries(params)) {
    if (!isBadParam(v)) out[k] = v
  }
  return out
}

/** 清洗 URL 查询串中的空值参数，并替换路径里的 undefined / null 段 */
export function cleanUrl(url) {
  if (typeof url !== 'string' || !url) return url

  // 路径段：/tenants/undefined/brands → 交由调用方替换为真实租户
  let cleaned = url

  const [path, query] = cleaned.split('?')
  if (!query) return path

  const kept = query.split('&').filter((kv) => {
    const parts = kv.split('=')
    const v = parts.length > 1 ? parts.slice(1).join('=') : ''
    return !isBadParam(v)
  })
  cleaned = kept.length ? `${path}?${kept.join('&')}` : path
  return cleaned
}
