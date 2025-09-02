<template>
  <div class="proxy-health">
    <div class="header">
      <h2>代理服务器健康状态</h2>
      <div class="actions">
        <el-button 
          :type="autoRefresh ? 'primary' : 'default'"
          @click="toggleAutoRefresh"
          :icon="Clock"
        >
          {{ autoRefresh ? '停止自动刷新' : '开启自动刷新' }}
        </el-button>
        <el-button 
          @click="fetchHealthData"
          :loading="loading"
          :icon="Refresh"
        >
          手动刷新
        </el-button>
        <el-button 
          @click="cleanupHeartbeats"
          :loading="cleanupLoading"
          :icon="Delete"
          type="warning"
        >
          清理过期心跳
        </el-button>
      </div>
    </div>

    <!-- 整体状态提示 -->
    <el-alert
      v-if="healthData"
      :title="`代理服务状态: ${healthData.status.toUpperCase()}`"
      :description="healthData.message"
      :type="getAlertType(healthData.status)"
      show-icon
      style="margin-bottom: 16px"
    />

    <!-- 心跳超时说明 -->
    <el-alert
      v-if="healthData"
      title="心跳监控说明"
      description="系统每5秒检查一次代理服务器心跳，超过15秒未收到心跳的服务器将被标记为离线状态"
      type="info"
      show-icon
      style="margin-bottom: 16px"
    />

    <!-- 错误提示 -->
    <el-alert
      v-if="error"
      title="获取健康状态失败"
      :description="error"
      type="error"
      show-icon
      style="margin-bottom: 16px"
    >
      <template #default>
        <el-button size="small" @click="fetchHealthData">重试</el-button>
      </template>
    </el-alert>

    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-bottom: 16px" v-if="healthData">
      <el-col :span="6">
        <el-card>
          <el-statistic
            title="服务器总数"
            :value="healthData.summary.total_servers"
          >
            <template #prefix>
              <el-icon><Monitor /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic
            title="在线服务器"
            :value="healthData.summary.online_servers"
            value-style="color: #67c23a"
          >
            <template #prefix>
              <el-icon color="#67c23a"><SuccessFilled /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic
            title="离线服务器"
            :value="healthData.summary.offline_servers"
            :value-style="healthData.summary.offline_servers > 0 ? 'color: #f56c6c' : 'color: #67c23a'"
          >
            <template #prefix>
              <el-icon :color="healthData.summary.offline_servers > 0 ? '#f56c6c' : '#67c23a'">
                <CircleCloseFilled />
              </el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic
            title="活跃连接总数"
            :value="healthData.summary.total_active_conns"
          >
            <template #prefix>
              <el-icon><Connection /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- 服务器详情表格 -->
    <el-card title="代理服务器详情" v-if="healthData">
      <el-table
        :data="healthData.proxy_servers"
        v-loading="loading"
        size="small"
        style="width: 100%"
      >
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tooltip :content="row.health_message">
              <el-icon 
                :color="getStatusColor(row.status, row.is_healthy)"
                :size="16"
              >
                <component :is="getStatusIcon(row.status, row.is_healthy)" />
              </el-icon>
            </el-tooltip>
          </template>
        </el-table-column>
        
        <el-table-column label="代理ID" prop="proxy_id">
          <template #default="{ row }">
            <code>{{ row.proxy_id }}</code>
          </template>
        </el-table-column>
        
        <el-table-column label="地址">
          <template #default="{ row }">
            {{ row.proxy_host }}:{{ row.proxy_port }}
          </template>
        </el-table-column>
        
        <el-table-column label="状态标签">
          <template #default="{ row }">
            <el-tag :type="getTagType(row.status, row.is_healthy)">
              {{ getStatusText(row.status, row.is_healthy) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="活跃连接" prop="active_conns">
          <template #default="{ row }">
            <el-icon><Connection /></el-icon> {{ row.active_conns }}
          </template>
        </el-table-column>
        
        <el-table-column label="总连接数" prop="total_conns" />
        
        <el-table-column label="最后心跳">
          <template #default="{ row }">
            <el-tooltip :content="formatDateTime(row.last_heartbeat)">
              {{ formatDateTime(row.last_heartbeat) }}
            </el-tooltip>
          </template>
        </el-table-column>
        
        <el-table-column label="健康状态" prop="health_message">
          <template #default="{ row }">
            <el-tooltip :content="getHealthTooltip(row)">
              <span :class="{ 'text-warning': !row.is_healthy }">
                {{ row.health_message }}
              </span>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { 
  Clock, 
  Refresh, 
  Monitor, 
  SuccessFilled, 
  CircleCloseFilled, 
  Connection,
  CircleCheckFilled,
  WarningFilled,
  Delete
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { formatTime, formatDateTime } from '@/utils/formatters'
import api from '@/api/auth'

const healthData = ref(null)
const loading = ref(true)
const error = ref(null)
const autoRefresh = ref(true)
const cleanupLoading = ref(false)
let refreshInterval = null

const fetchHealthData = async () => {
  try {
    loading.value = true
    const response = await api.get('/proxy/health')
    healthData.value = response
    error.value = null
  } catch (err) {
    error.value = err.response?.data?.error || '获取健康状态失败'
  } finally {
    loading.value = false
  }
}

const cleanupHeartbeats = async () => {
  try {
    cleanupLoading.value = true
    await api.post('/proxy/cleanup')
    ElMessage.success('过期心跳记录清理完成')
    // 清理完成后刷新数据
    await fetchHealthData()
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '清理心跳记录失败')
  } finally {
    cleanupLoading.value = false
  }
}

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const startAutoRefresh = () => {
  if (refreshInterval) return
  refreshInterval = setInterval(fetchHealthData, 5000)
}

const stopAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

const getAlertType = (status) => {
  switch (status) {
    case 'online': return 'success'
    case 'degraded': return 'warning'
    case 'offline': return 'error'
    default: return 'info'
  }
}

const getStatusIcon = (status, isHealthy) => {
  if (status === 'online' && isHealthy) {
    return CircleCheckFilled
  } else if (status === 'online' && !isHealthy) {
    return WarningFilled
  } else {
    return CircleCloseFilled
  }
}

const getStatusColor = (status, isHealthy) => {
  if (status === 'online' && isHealthy) {
    return '#67c23a'
  } else if (status === 'online' && !isHealthy) {
    return '#e6a23c'
  } else {
    return '#f56c6c'
  }
}

const getTagType = (status, isHealthy) => {
  if (status === 'online' && isHealthy) {
    return 'success'
  } else if (status === 'online' && !isHealthy) {
    return 'warning'
  } else {
    return 'danger'
  }
}

const getStatusText = (status, isHealthy) => {
  if (status === 'online' && isHealthy) {
    return '在线'
  } else if (status === 'online' && !isHealthy) {
    return '异常'
  } else {
    return '离线'
  }
}

const getHealthTooltip = (row) => {
  if (row.is_healthy) {
    return `最后心跳时间: ${formatDateTime(row.last_heartbeat)}`
  } else {
    const now = new Date()
    const lastHeartbeat = new Date(row.last_heartbeat)
    const diffSeconds = Math.floor((now - lastHeartbeat) / 1000)
    return `最后心跳时间: ${formatDateTime(row.last_heartbeat)}\n已超时: ${diffSeconds} 秒`
  }
}

onMounted(() => {
  fetchHealthData()
  if (autoRefresh.value) {
    startAutoRefresh()
  }
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.proxy-health {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.actions {
  display: flex;
  gap: 8px;
}

code {
  background-color: #f5f5f5;
  padding: 2px 4px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
}

.text-warning {
  color: #e6a23c;
  font-weight: 500;
}

.proxy-health .el-table .el-table__row:hover {
  background-color: #f5f7fa;
}

.proxy-health .el-table .el-table__row.offline {
  background-color: #fef0f0;
}

.proxy-health .el-table .el-table__row.healthy {
  background-color: #f0f9ff;
}
</style>
