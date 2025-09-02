<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon user-icon">
              <el-icon><User /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-value">{{ stats.totalUsers }}</div>
              <div class="stats-label">总用户数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon online-icon">
              <el-icon><View /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-value">{{ stats.onlineUsers }}</div>
              <div class="stats-label">在线用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon connection-icon">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-value">{{ stats.activeConnections }}</div>
              <div class="stats-label">活跃连接</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon traffic-icon">
              <el-icon><DataLine /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-value">{{ formatBytes(stats.totalBytesSent + stats.totalBytesRecv) }}</div>
              <div class="stats-label">总流量</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <span>流量统计</span>
          </template>
          <div class="traffic-stats">
            <div class="traffic-item">
              <span class="traffic-label">发送流量:</span>
              <span class="traffic-value sent">{{ formatBytes(stats.totalBytesSent) }}</span>
            </div>
            <div class="traffic-item">
              <span class="traffic-label">接收流量:</span>
              <span class="traffic-value received">{{ formatBytes(stats.totalBytesRecv) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <span>实时流量图表</span>
          </template>
          <div class="chart-container">
            <v-chart :option="trafficChartOption" style="height: 200px" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 在线用户表格 -->
    <el-card class="online-users-card">
      <template #header>
        <span>在线用户</span>
      </template>
      
      <el-table
        :data="onlineUsers"
        style="width: 100%"
        :loading="loading"
        size="small"
      >
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="clientIP" label="客户端IP" />
        <el-table-column prop="startTime" label="连接时间">
          <template #default="{ row }">
            {{ formatTime(row.startTime) }}
          </template>
        </el-table-column>
        <el-table-column prop="bytesSent" label="发送流量">
          <template #default="{ row }">
            {{ formatBytes(row.bytesSent) }}
          </template>
        </el-table-column>
        <el-table-column prop="bytesRecv" label="接收流量">
          <template #default="{ row }">
            {{ formatBytes(row.bytesRecv) }}
          </template>
        </el-table-column>
        <el-table-column label="状态">
          <template #default>
            <el-tag type="success" size="small">在线</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="js">
import { ref, onMounted, onUnmounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { User, View, Connection, DataLine } from '@element-plus/icons-vue'
import api from '@/api/auth'
import { formatBytes, formatTime } from '@/utils/formatters'

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const stats = ref({
  totalBytesSent: 0,
  totalBytesRecv: 0,
  activeConnections: 0,
  totalUsers: 0,
  onlineUsers: 0
})

const onlineUsers = ref([])
const loading = ref(true)
let interval = null

const trafficChartOption = ref({
  title: {
    text: '实时流量监控',
    left: 'center'
  },
  tooltip: {
    trigger: 'axis'
  },
  legend: {
    data: ['发送流量', '接收流量'],
    top: 30
  },
  xAxis: {
    type: 'time',
    boundaryGap: false
  },
  yAxis: {
    type: 'value',
    name: '流量 (MB)'
  },
  series: [
    {
      name: '发送流量',
      type: 'line',
      smooth: true,
      data: []
    },
    {
      name: '接收流量',
      type: 'line',
      smooth: true,
      data: []
    }
  ]
})

const fetchDashboardData = async () => {
  try {
    const [statsRes, onlineRes] = await Promise.all([
      api.get('/traffic'),
      api.get('/online')
    ])
    
    // 确保数据存在且为有效值
    if (statsRes && statsRes.stats) {
      stats.value = {
        totalBytesSent: statsRes.stats.total_bytes_sent || 0,
        totalBytesRecv: statsRes.stats.total_bytes_recv || 0,
        activeConnections: statsRes.stats.active_connections || 0,
        totalUsers: statsRes.stats.total_users || 0,
        onlineUsers: statsRes.stats.online_users || 0
      }
    }
    
    if (onlineRes && onlineRes.online_users) {
      onlineUsers.value = onlineRes.online_users
    } else {
      onlineUsers.value = []
    }
  } catch (error) {
    console.error('获取仪表盘数据失败:', error)
    // 设置默认值避免显示 NaN
    stats.value = {
      totalBytesSent: 0,
      totalBytesRecv: 0,
      activeConnections: 0,
      totalUsers: 0,
      onlineUsers: 0
    }
    onlineUsers.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDashboardData()
  interval = window.setInterval(fetchDashboardData, 30000) // 30秒更新一次
})

onUnmounted(() => {
  if (interval) {
    clearInterval(interval)
  }
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stats-card {
  margin-bottom: 20px;
}

.stats-content {
  display: flex;
  align-items: center;
}

.stats-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
  color: white;
}

.user-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.online-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.connection-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.traffic-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stats-info {
  flex: 1;
}

.stats-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stats-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.chart-row {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.traffic-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.traffic-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.traffic-label {
  font-size: 14px;
  color: #606266;
}

.traffic-value {
  font-size: 16px;
  font-weight: bold;
}

.traffic-value.sent {
  color: #409eff;
}

.traffic-value.received {
  color: #67c23a;
}

.chart-container {
  height: 200px;
}

.online-users-card {
  margin-bottom: 20px;
}
</style>
