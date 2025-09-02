import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api/auth'

export const useUsersStore = defineStore('users', () => {
  const users = ref([])
  const loading = ref(false)

  const fetchUsers = async () => {
    loading.value = true
    try {
      const response = await api.get('/users')
      users.value = response.users
    } catch (error) {
      ElMessage.error('获取用户列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const createUser = async (userData) => {
    try {
      const response = await api.post('/users', userData)
      users.value.push(response.user)
      ElMessage.success('用户创建成功')
      return response.user
    } catch (error) {
      ElMessage.error('创建用户失败')
      throw error
    }
  }

  const updateUser = async (id, userData) => {
    try {
      const response = await api.put(`/users/${id}`, userData)
      const index = users.value.findIndex(user => user.id === id)
      if (index !== -1) {
        users.value[index] = response.user
      }
      ElMessage.success('用户更新成功')
      return response.user
    } catch (error) {
      ElMessage.error('更新用户失败')
      throw error
    }
  }

  const deleteUser = async (id) => {
    try {
      await api.delete(`/users/${id}`)
      users.value = users.value.filter(user => user.id !== id)
      ElMessage.success('用户删除成功')
    } catch (error) {
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
