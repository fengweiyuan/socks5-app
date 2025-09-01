import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api/auth'

interface User {
  id: number
  username: string
  email: string
  role: string
  status: string
  bandwidthLimit: number
  createdAt: string
}

export const useUsersStore = defineStore('users', () => {
  const users = ref<User[]>([])
  const loading = ref(false)

  const fetchUsers = async () => {
    loading.value = true
    try {
      const response = await api.get('/users')
      users.value = response.users
    } catch (error: any) {
      ElMessage.error('获取用户列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const createUser = async (userData: {
    username: string
    password: string
    email?: string
    role?: string
    bandwidthLimit?: number
  }) => {
    try {
      const response = await api.post('/users', userData)
      users.value.push(response.user)
      ElMessage.success('用户创建成功')
      return response.user
    } catch (error: any) {
      ElMessage.error('创建用户失败')
      throw error
    }
  }

  const updateUser = async (id: number, userData: Partial<User>) => {
    try {
      const response = await api.put(`/users/${id}`, userData)
      const index = users.value.findIndex(user => user.id === id)
      if (index !== -1) {
        users.value[index] = response.user
      }
      ElMessage.success('用户更新成功')
      return response.user
    } catch (error: any) {
      ElMessage.error('更新用户失败')
      throw error
    }
  }

  const deleteUser = async (id: number) => {
    try {
      await api.delete(`/users/${id}`)
      users.value = users.value.filter(user => user.id !== id)
      ElMessage.success('用户删除成功')
    } catch (error: any) {
      ElMessage.error('删除用户失败')
      throw error
    }
  }

  return {
    users,
    loading,
    fetchUsers,
    createUser,
    updateUser,
    deleteUser
  }
})
