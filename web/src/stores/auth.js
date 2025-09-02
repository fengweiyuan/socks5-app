import { ref } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
import { authAPI } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token'))
  const user = ref(null)
  const loading = ref(false)

  const login = async (credentials) => {
    loading.value = true
    try {
      const response = await authAPI.login(credentials)
      token.value = response.token
      user.value = response.user
      localStorage.setItem('token', response.token)
      ElMessage.success('登录成功')
      return response
    } catch (error) {
      ElMessage.error(error.response?.data?.error || '登录失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    try {
      await authAPI.logout()
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      token.value = null
      user.value = null
      localStorage.removeItem('token')
      ElMessage.success('已退出登录')
    }
  }

  const clearError = () => {
    // 清除错误状态
  }

  return {
    token,
    user,
    loading,
    login,
    logout,
    clearError
  }
})
