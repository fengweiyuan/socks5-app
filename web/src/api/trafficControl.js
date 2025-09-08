// 流量控制 API 服务
import { ElMessage } from 'element-plus'

const API_BASE = '/api/v1'

// 获取认证头
const getAuthHeaders = (token) => ({
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${token}`
})

// 处理 API 响应
const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: '请求失败' }))
    throw new Error(error.error || '请求失败')
  }
  return response.json()
}

// 流量控制 API
export const trafficControlAPI = {
  // 设置用户带宽限制
  async setBandwidthLimit(token, data) {
    try {
      const response = await fetch(`${API_BASE}/traffic/limit`, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify(data)
      })
      return await handleResponse(response)
    } catch (error) {
      ElMessage.error('设置带宽限制失败: ' + error.message)
      throw error
    }
  },

  // 获取所有用户带宽限制
  async getBandwidthLimits(token) {
    try {
      const response = await fetch(`${API_BASE}/traffic/limits`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      return await handleResponse(response)
    } catch (error) {
      ElMessage.error('获取带宽限制失败: ' + error.message)
      throw error
    }
  },

  // 更新用户带宽限制
  async updateBandwidthLimit(token, userId, data) {
    try {
      const response = await fetch(`${API_BASE}/traffic/limits/${userId}`, {
        method: 'PUT',
        headers: getAuthHeaders(token),
        body: JSON.stringify(data)
      })
      return await handleResponse(response)
    } catch (error) {
      ElMessage.error('更新带宽限制失败: ' + error.message)
      throw error
    }
  },

  // 删除用户带宽限制
  async deleteBandwidthLimit(token, userId) {
    try {
      const response = await fetch(`${API_BASE}/traffic/limits/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      return await handleResponse(response)
    } catch (error) {
      ElMessage.error('删除带宽限制失败: ' + error.message)
      throw error
    }
  },

  // 获取流量统计
  async getTrafficStats(token) {
    try {
      const response = await fetch(`${API_BASE}/traffic`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      return await handleResponse(response)
    } catch (error) {
      ElMessage.error('获取流量统计失败: ' + error.message)
      throw error
    }
  },

  // 获取实时流量数据
  async getRealtimeTraffic(token) {
    try {
      const response = await fetch(`${API_BASE}/traffic/realtime`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      return await handleResponse(response)
    } catch (error) {
      ElMessage.error('获取实时流量失败: ' + error.message)
      throw error
    }
  },

  // 获取流量日志
  async getTrafficLogs(token, params = {}) {
    try {
      const queryString = new URLSearchParams(params).toString()
      const url = `${API_BASE}/traffic/logs${queryString ? '?' + queryString : ''}`
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      return await handleResponse(response)
    } catch (error) {
      ElMessage.error('获取流量日志失败: ' + error.message)
      throw error
    }
  },

  // 导出流量日志
  async exportTrafficLogs(token) {
    try {
      const response = await fetch(`${API_BASE}/traffic/export`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (!response.ok) {
        throw new Error('导出失败')
      }
      return response.blob()
    } catch (error) {
      ElMessage.error('导出流量日志失败: ' + error.message)
      throw error
    }
  }
}

// 用户管理 API
export const userAPI = {
  // 获取用户列表
  async getUsers(token) {
    try {
      const response = await fetch(`${API_BASE}/users`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      return await handleResponse(response)
    } catch (error) {
      ElMessage.error('获取用户列表失败: ' + error.message)
      throw error
    }
  },

  // 获取用户详情
  async getUser(token, userId) {
    try {
      const response = await fetch(`${API_BASE}/users/${userId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      return await handleResponse(response)
    } catch (error) {
      ElMessage.error('获取用户详情失败: ' + error.message)
      throw error
    }
  }
}

// 系统状态 API
export const systemAPI = {
  // 获取系统状态
  async getSystemStatus(token) {
    try {
      const response = await fetch(`${API_BASE}/system/status`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      return await handleResponse(response)
    } catch (error) {
      ElMessage.error('获取系统状态失败: ' + error.message)
      throw error
    }
  },

  // 获取系统统计
  async getSystemStats(token) {
    try {
      const response = await fetch(`${API_BASE}/system/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      return await handleResponse(response)
    } catch (error) {
      ElMessage.error('获取系统统计失败: ' + error.message)
      throw error
    }
  }
}

// 工具函数
export const utils = {
  // 格式化带宽显示
  formatBandwidth(bytes) {
    if (bytes === 0) return '无限制'
    if (bytes < 1024) return bytes + ' B/s'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB/s'
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB/s'
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB/s'
  },

  // 格式化字节数
  formatBytes(bytes) {
    if (bytes === 0) return '0 B'
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
  },

  // 格式化日期时间
  formatDateTime(dateString) {
    if (!dateString) return '-'
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  },

  // 下载文件
  downloadFile(blob, filename) {
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    window.URL.revokeObjectURL(url)
  },

  // 导出 CSV
  exportToCSV(data, filename) {
    const csvContent = [
      Object.keys(data[0]),
      ...data.map(row => Object.values(row))
    ].map(row => row.join(',')).join('\n')

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
    this.downloadFile(blob, filename)
  }
}

export default {
  trafficControlAPI,
  userAPI,
  systemAPI,
  utils
}
