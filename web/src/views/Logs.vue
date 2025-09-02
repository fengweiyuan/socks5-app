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
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="client_ip" label="客户端IP" />
        <el-table-column prop="target_url" label="目标URL" />
        <el-table-column prop="method" label="方法" width="80" />
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'">
              {{ scope.row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="user_agent" label="User Agent" show-overflow-tooltip />
        <el-table-column prop="timestamp" label="时间">
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
