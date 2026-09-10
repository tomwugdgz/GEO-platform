/**
 * GeoLook 当前项目上下文
 *
 * 背景：路由是静态路径（/geo/siteaudit 等），页面不知道要操作哪个项目。
 * 约定：以 localStorage 记住「当前项目」，未设置时自动取项目列表的第一个。
 * 用户在「GEO 诊断」页对某个项目执行操作时，会把该项目记为当前项目。
 */
import api from '@/api/axios'

const STORAGE_KEY = 'geolook:current-slug'

let projectsCache = null

export function getStoredSlug() {
  try {
    return localStorage.getItem(STORAGE_KEY) || ''
  } catch {
    return ''
  }
}

/** 当前项目变化事件：侧边栏等订阅者据此即时刷新 */
export const SLUG_CHANGED_EVENT = 'geolook:slug-changed'

export function setStoredSlug(slug) {
  if (!slug) return
  try {
    localStorage.setItem(STORAGE_KEY, slug)
  } catch {
    /* 隐私模式等场景静默降级 */
  }
  try {
    window.dispatchEvent(new CustomEvent(SLUG_CHANGED_EVENT, { detail: slug }))
  } catch {
    /* ignore */
  }
}

export function clearStoredSlug() {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* ignore */
  }
}

export async function fetchProjects(force = false) {
  if (projectsCache && !force) return projectsCache
  const res = await api.get('/api/v2/geolook/projects')
  projectsCache = res.data || []
  return projectsCache
}

export function getCachedProjects() {
  return projectsCache
}

/**
 * 解析当前应使用的项目 slug：
 * 1. 显式传入（路由参数）优先，并写入本地记忆
 * 2. 本地记忆
 * 3. 项目列表第一个（同时写入本地记忆）
 * 都没有则返回空串，由页面展示「尚未创建项目」引导。
 */
export async function resolveGeoSlug(explicitSlug) {
  if (explicitSlug) {
    setStoredSlug(explicitSlug)
    return explicitSlug
  }

  const stored = getStoredSlug()
  if (stored) return stored

  try {
    const list = await fetchProjects()
    if (list.length) {
      setStoredSlug(list[0].slug)
      return list[0].slug
    }
  } catch {
    /* 后端不可用时返回空串 */
  }
  return ''
}

/** 无项目时的统一提示文案 */
export const NO_PROJECT_HINT = '还没有 GeoLook 项目，请先到「GEO 诊断」页面创建'
