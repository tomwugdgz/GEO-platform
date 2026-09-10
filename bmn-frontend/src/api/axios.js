/**
 * 通用 HTTP 客户端（GeoLook 模块及各业务页面共用）
 *
 * - baseURL 为空：调用方使用 /api/... 完整路径，开发环境由 vite 代理到后端 5006
 * - 统一超时与错误信息，避免页面直接弹出 [object Object]
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// 统一错误提示文案：优先取后端 detail，其次 message
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err?.response?.data?.detail
    if (detail) {
      err.message = typeof detail === 'string' ? detail : JSON.stringify(detail)
    } else if (err?.code === 'ECONNABORTED') {
      err.message = '请求超时：GeoLook 引擎可能仍在执行，请稍后刷新'
    } else if (!err?.response) {
      err.message = '无法连接后端服务，请确认 5006 端口已启动'
    }
    return Promise.reject(err)
  }
)

export default api
