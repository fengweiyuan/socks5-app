<template>
  <div class="traffic-container">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>实时流量监控</span>
          </template>
          <div ref="trafficChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>流量统计</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="总发送流量">
              {{ formatBytes(trafficStats.totalBytesSent) }}
            </el-descriptions-item>
            <el-descriptions-item label="总接收流量">
              {{ formatBytes(trafficStats.totalBytesRecv) }}
            </el-descriptions-item>
            <el-descriptions-item label="活跃连接数">
              {{ trafficStats.activeConnections }}
            </el-descriptions-item>
            <el-descriptions-item label="总会话数">
              {{ trafficStats.totalSessions }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>流量日志</span>
          <el-button type="primary" @click="exportLogs">导出日志</el-button>
        </div>
      </template>

      <el-table :data="trafficLogs" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="client_ip" label="客户端IP" />
        <el-table-column prop="target_ip" label="目标IP" />
        <el-table-column prop="target_port" label="目标端口" />
        <el-table-column prop="protocol" label="协议" />
        <el-table-column prop="bytes_sent" label="发送字节">
          <template #default="scope">
            {{ formatBytes(scope.row.bytes_sent) }}
          </template>
        </el-table-column>
        <el-table-column prop="bytes_recv" label="接收字节">
          <template #default="scope">
            {{ formatBytes(scope.row.bytes_recv) }}
          </template>
        </el-table-column>
        <el-table-column prop="timestamp" label="时间">
          <template #default="scope">
            {{ formatDate(scope.row.timestamp) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import * as echarts from 'echarts'

const authStore = useAuthStore()
const loading = ref(false)
const trafficLogs = ref([])
const trafficStats = ref({
  totalBytesSent: 0,
  totalBytesRecv: 0,
  activeConnections: 0,
  totalSessions: 0
})

const trafficChartRef = ref()
let trafficChart: echarts.ECharts | null = null
let intervalId: number | null = null

const fetchTrafficStats = async () => {
  try {
    const response = await fetch('/api/v1/traffic', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      trafficStats.value = data.stats
      updateChart()
    }
  } catch (error) {
    ElMessage.error('获取流量统计失败')
  }
}

const fetchTrafficLogs = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/v1/traffic/logs', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      trafficLogs.value = data.logs
    }
  } catch (error) {
    ElMessage.error('获取流量日志失败')
  } finally {
    loading.value = false
  }
}

const updateChart = () => {
  if (!trafficChart) return
  
  const option = {
    title: {
      text: '实时流量监控'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['发送流量', '接收流量']
    },
    xAxis: {
      type: 'category',
      data: ['1分钟前', '30秒前', '现在']
    },
    yAxis: {
      type: 'value',
      name: '字节'
    },
    series: [
      {
        name: '发送流量',
        type: 'line',
        data: [
          trafficStats.value.totalBytesSent * 0.8,
          trafficStats.value.totalBytesSent * 0.9,
          trafficStats.value.totalBytesSent
        ]
      },
      {
        name: '接收流量',
        type: 'line',
        data: [
          trafficStats.value.totalBytesRecv * 0.8,
          trafficStats.value.totalBytesRecv * 0.9,
          trafficStats.value.totalBytesRecv
        ]
      }
    ]
  }
  
  trafficChart.setOption(option)
}

const exportLogs = async () => {
  try {
    const response = await fetch('/api/v1/traffic/export', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'traffic_logs.csv'
      a.click()
      window.URL.revokeObjectURL(url)
      ElMessage.success('日志导出成功')
    }
  } catch (error) {
    ElMessage.error('日志导出失败')
  }
}

const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString()
}

onMounted(() => {
  fetchTrafficStats()
  fetchTrafficLogs()
  
  // 初始化图表
  if (trafficChartRef.value) {
    trafficChart = echarts.init(trafficChartRef.value)
    updateChart()
  }
  
  // 定时更新数据
  intervalId = window.setInterval(() => {
    fetchTrafficStats()
  }, 5000)
})

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
  if (trafficChart) {
    trafficChart.dispose()
  }
})
</script>

<style scoped>
.traffic-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
