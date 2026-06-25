import type { AxiosError } from 'axios'

export function getApiErrorMessage(error: unknown): string {
  if (!error || typeof error !== 'object') {
    return '操作失败'
  }

  const axiosError = error as AxiosError<{ detail?: string; error?: string }>

  if (axiosError.code === 'ECONNABORTED') {
    return '请求超时，请稍后重试'
  }

  if (!axiosError.response) {
    return '网络连接失败，请检查网络'
  }

  const status = axiosError.response.status
  const detail = axiosError.response.data?.detail || axiosError.response.data?.error

  switch (status) {
    case 400:
      return detail || '请求参数错误'
    case 401:
      return detail || '未登录或登录已过期'
    case 403:
      return detail || '权限不足，请联系管理员'
    case 404:
      return detail || '资源不存在'
    case 500:
      return detail || '服务器内部错误'
    default:
      return detail || `请求失败 (${status})`
  }
}
