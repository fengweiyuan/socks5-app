<template>
  <div class="logs-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>系统日志</span>
          <div>
            <el-button @click="refreshLogs">刷新</el-button>
            <el-button type="primary" @click="exportLogs">导出日志</el-button>
            <el-button type="danger" @click="clearLogs">清理日志</el-button>
          </div>
        </div>
      </template>

      <el-table :data="logs" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="user.username" label="操作用户" />
        <el-table-column label="操作类型" width="120">
          <template #default="scope">
            <el-tag :type="getOperationType(scope.row).type">
              {{ getOperationType(scope.row).text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_url" label="操作路径" />
        <el-table-column prop="method" label="方法" width="80" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'">
              {{ scope.row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作详情" show-overflow-tooltip>
          <template #default="scope">
            {{ getOperationDetails(scope.row) }}
          </template>
        </el-table-column>
        <el-table-column prop="client_ip" label="客户端IP" width="120" />
        <el-table-column prop="timestamp" label="时间" width="160">
          <template #default="scope">
            {{ formatDate(scope.row.timestamp) }}
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="js">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { formatDate } from '@/utils/formatters'

const authStore = useAuthStore()
const loading = ref(false)
const logs = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const fetchLogs = async () => {
  loading.value = true
  try {
    const response = await fetch(`/api/v1/logs?page=${currentPage.value}&size=${pageSize.value}`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      logs.value = data.logs
      total.value = data.total
    }
  } catch (error) {
    ElMessage.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

const refreshLogs = () => {
  fetchLogs()
}

const exportLogs = async () => {
  try {
    const response = await fetch('/api/v1/logs/export', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'system_logs.csv'
      a.click()
      window.URL.revokeObjectURL(url)
      ElMessage.success('日志导出成功')
    }
  } catch (error) {
    ElMessage.error('日志导出失败')
  }
}

const clearLogs = async () => {
  try {
    await ElMessageBox.confirm('确定要清理所有日志吗？此操作不可恢复！', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const response = await fetch('/api/v1/logs', {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (response.ok) {
      ElMessage.success('日志清理成功')
      fetchLogs()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('日志清理失败')
    }
  }
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  fetchLogs()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchLogs()
}

// 获取操作类型
const getOperationType = (log) => {
  const url = log.target_url || ''
  const userAgent = log.user_agent || ''
  
  // 检查是否是用户操作日志
  if (userAgent.includes('CREATE_USER')) {
    return { type: 'success', text: '创建用户' }
  } else if (userAgent.includes('UPDATE_USER')) {
    return { type: 'warning', text: '编辑用户' }
  } else if (userAgent.includes('DELETE_USER')) {
    return { type: 'danger', text: '删除用户' }
  } else if (userAgent.includes('EXPORT_LOGS')) {
    return { type: 'primary', text: '导出日志' }
  } else if (userAgent.includes('CLEAR_LOGS')) {
    return { type: 'danger', text: '清理日志' }
  } else if (url.includes('/auth/login')) {
    return { type: 'primary', text: '用户登录' }
  } else if (url.includes('/auth/logout')) {
    return { type: 'info', text: '用户登出' }
  } else if (url.includes('/users')) {
    return { type: 'warning', text: '用户管理' }
  } else if (url.includes('/logs')) {
    return { type: 'info', text: '日志管理' }
  } else {
    return { type: '', text: '其他操作' }
  }
}

// 获取操作详情
const getOperationDetails = (log) => {
  const userAgent = log.user_agent || ''
  
  // 提取操作详情（在UserAgent字段中存储的详情信息）
  const detailsMatch = userAgent.match(/\| (.+)$/)
  if (detailsMatch) {
    return detailsMatch[1]
  }
  
  // 如果没有详情信息，返回基本信息
  const url = log.target_url || ''
  if (url.includes('/auth/login')) {
    return '用户登录操作'
  } else if (url.includes('/auth/logout')) {
    return '用户登出操作'
  } else if (url.includes('/users')) {
    return '用户管理操作'
  } else if (url.includes('/logs')) {
    return '日志管理操作'
  }
  
  return userAgent
}



onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
.logs-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
