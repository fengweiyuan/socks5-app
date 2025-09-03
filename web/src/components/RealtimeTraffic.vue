<template>
  <div class="realtime-traffic">
    <el-card class="traffic-card">
      <template #header>
        <div class="card-header">
          <span>实时流量监控</span>
          <div class="header-controls">
            <el-tag :type="wsStatus.type" size="small">
              {{ wsStatus.text }}
            </el-tag>
            <el-button 
              size="small" 
              :type="wsStatus.type === 'success' ? 'danger' : 'primary'"
              @click="toggleConnection"
            >
              {{ wsStatus.type === 'success' ? '断开' : '连接' }}
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="traffic-content">
        <!-- 连接状态 -->
        <div class="connection-status">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="status-item">
                <div class="status-label">连接状态</div>
                <div class="status-value">
                  <el-tag :type="wsStatus.type" size="large">
                    {{ wsStatus.text }}
                  </el-tag>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="status-item">
                <div class="status-label">重连次数</div>
                <div class="status-value">{{ connectionStats.reconnectAttempts }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="status-item">
                <div class="status-label">订阅主题</div>
                <div class="status-value">{{ connectionStats.subscriptions.length }}</div>
              </div>
            </el-col>
          </el-row>
        </div>
        
        <!-- 实时流量图表 -->
        <div class="traffic-charts">
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="chart-container">
                <h4>上传速度</h4>
                <div class="speed-chart">
                  <div class="speed-value">{{ formatSpeed(uploadSpeed) }}</div>
                  <div class="speed-bar">
                    <div 
                      class="speed-fill upload-fill" 
                      :style="{ width: uploadSpeedPercent + '%' }"
                    ></div>
                  </div>
                </div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="chart-container">
                <h4>下载速度</h4>
                <div class="speed-chart">
                  <div class="speed-value">{{ formatSpeed(downloadSpeed) }}</div>
                  <div class="speed-bar">
                    <div 
                      class="speed-fill download-fill" 
                      :style="{ width: downloadSpeedPercent + '%' }"
                    ></div>
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
        
        <!-- 流量统计 -->
        <div class="traffic-stats">
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-icon upload-icon">
                  <i class="el-icon-upload"></i>
                </div>
                <div class="stat-content">
                  <div class="stat-value">{{ formatBytes(totalUpload) }}</div>
                  <div class="stat-label">总上传</div>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-icon download-icon">
                  <i class="el-icon-download"></i>
                </div>
                <div class="stat-content">
                  <div class="stat-value">{{ formatBytes(totalDownload) }}</div>
                  <div class="stat-label">总下载</div>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-icon connection-icon">
                  <i class="el-icon-connection"></i>
                </div>
                <div class="stat-content">
                  <div class="stat-value">{{ activeConnections }}</div>
                  <div class="stat-label">活跃连接</div>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-icon bandwidth-icon">
                  <i class="el-icon-data-analysis"></i>
                </div>
                <div class="stat-content">
                  <div class="stat-value">{{ bandwidthUsage.toFixed(1) }}%</div>
                  <div class="stat-label">带宽使用率</div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
        
        <!-- 实时数据列表 -->
        <div class="realtime-data">
          <h4>实时数据流</h4>
          <el-table :data="realtimeData" size="small" max-height="300">
            <el-table-column prop="timestamp" label="时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column prop="clientIP" label="客户端IP" width="140" />
            <el-table-column prop="uploadSpeed" label="上传速度" width="120">
              <template #default="{ row }">
                {{ formatSpeed(row.uploadSpeed) }}
              </template>
            </el-table-column>
            <el-table-column prop="downloadSpeed" label="下载速度" width="120">
              <template #default="{ row }">
                {{ formatSpeed(row.downloadSpeed) }}
              </template>
            </el-table-column>
            <el-table-column prop="bandwidth" label="带宽使用率" width="120">
              <template #default="{ row }">
                {{ row.bandwidth.toFixed(1) }}%
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import WebSocketClient from '@/utils/websocket'
import { formatBytes, formatSpeed, formatTime } from '@/utils/formatters'

export default {
  name: 'RealtimeTraffic',
  setup() {
    // 响应式数据
    const wsClient = ref(null)
    const isConnected = ref(false)
    const reconnectAttempts = ref(0)
    const subscriptions = ref([])
    
    // 流量数据
    const uploadSpeed = ref(0)
    const downloadSpeed = ref(0)
    const totalUpload = ref(0)
    const totalDownload = ref(0)
    const activeConnections = ref(0)
    const bandwidthUsage = ref(0)
    
    // 实时数据列表
    const realtimeData = ref([])
    
    // 计算属性
    const wsStatus = computed(() => {
      if (isConnected.value) {
        return { type: 'success', text: '已连接' }
      } else if (reconnectAttempts.value > 0) {
        return { type: 'warning', text: '重连中...' }
      } else {
        return { type: 'danger', text: '未连接' }
      }
    })
    
    const connectionStats = computed(() => ({
      reconnectAttempts: reconnectAttempts.value,
      subscriptions: subscriptions.value
    }))
    
    const uploadSpeedPercent = computed(() => {
      const maxSpeed = 100 * 1024 * 1024 // 100MB/s
      return Math.min((uploadSpeed.value / maxSpeed) * 100, 100)
    })
    
    const downloadSpeedPercent = computed(() => {
      const maxSpeed = 100 * 1024 * 1024 // 100MB/s
      return Math.min((downloadSpeed.value / maxSpeed) * 100, 100)
    })
    
    // 初始化WebSocket连接
    const initWebSocket = () => {
      const wsUrl = `ws://${window.location.host}/ws`
      wsClient.value = new WebSocketClient(wsUrl, {
        autoConnect: true,
        reconnectInterval: 3000,
        maxReconnectAttempts: 5
      })
      
      // 监听事件
      wsClient.value.on('open', handleOpen)
      wsClient.value.on('close', handleClose)
      wsClient.value.on('message', handleMessage)
      wsClient.value.on('error', handleError)
      wsClient.value.on('reconnect', handleReconnect)
    }
    
    // 事件处理器
    const handleOpen = (event) => {
      console.log('WebSocket连接已建立')
      isConnected.value = true
      reconnectAttempts.value = 0
      
      // 订阅主题
      wsClient.value.subscribe('traffic_data')
      wsClient.value.subscribe('proxy_health')
      wsClient.value.subscribe('system_performance')
    }
    
    const handleClose = (event) => {
      console.log('WebSocket连接已关闭')
      isConnected.value = false
    }
    
    const handleMessage = (data) => {
      switch (data.type) {
        case 'traffic_data':
          handleTrafficData(data.data)
          break
        case 'proxy_health':
          handleProxyHealth(data.data)
          break
        case 'system_performance':
          handleSystemPerformance(data.data)
          break
      }
    }
    
    const handleError = (error) => {
      console.error('WebSocket错误:', error)
    }
    
    const handleReconnect = (data) => {
      reconnectAttempts.value = data.attempt
    }
    
    // 处理流量数据
    const handleTrafficData = (data) => {
      // 更新实时数据
      uploadSpeed.value = data.uploadSpeed || 0
      downloadSpeed.value = data.downloadSpeed || 0
      totalUpload.value = data.totalUpload || 0
      totalDownload.value = data.totalDownload || 0
      activeConnections.value = data.activeConnections || 0
      bandwidthUsage.value = data.bandwidthUsage || 0
      
      // 添加到实时数据列表
      const newData = {
        timestamp: Date.now(),
        clientIP: data.clientIP || 'N/A',
        uploadSpeed: data.uploadSpeed || 0,
        downloadSpeed: data.downloadSpeed || 0,
        bandwidth: data.bandwidthUsage || 0
      }
      
      realtimeData.value.unshift(newData)
      
      // 保持最多100条记录
      if (realtimeData.value.length > 100) {
        realtimeData.value = realtimeData.value.slice(0, 100)
      }
    }
    
    // 处理代理健康数据
    const handleProxyHealth = (data) => {
      // 这里可以添加代理健康数据的处理逻辑
      console.log('代理健康数据:', data)
    }
    
    // 处理系统性能数据
    const handleSystemPerformance = (data) => {
      // 这里可以添加系统性能数据的处理逻辑
      console.log('系统性能数据:', data)
    }
    
    // 切换连接状态
    const toggleConnection = () => {
      if (isConnected.value) {
        wsClient.value.disconnect()
      } else {
        wsClient.value.connect()
      }
    }
    
    // 格式化工具函数
    const formatBytesLocal = (bytes) => formatBytes(bytes)
    const formatSpeedLocal = (bytesPerSecond) => formatSpeed(bytesPerSecond)
    const formatTimeLocal = (timestamp) => formatTime(new Date(timestamp))
    
    // 生命周期
    onMounted(() => {
      initWebSocket()
    })
    
    onUnmounted(() => {
      if (wsClient.value) {
        wsClient.value.disconnect()
      }
    })
    
    return {
      // 状态
      wsStatus,
      connectionStats,
      
      // 流量数据
      uploadSpeed,
      downloadSpeed,
      totalUpload,
      totalDownload,
      activeConnections,
      bandwidthUsage,
      
      // 实时数据
      realtimeData,
      
      // 计算属性
      uploadSpeedPercent,
      downloadSpeedPercent,
      
      // 方法
      toggleConnection,
      formatBytes: formatBytesLocal,
      formatSpeed: formatSpeedLocal,
      formatTime: formatTimeLocal
    }
  }
}
</script>

<style scoped>
.realtime-traffic {
  padding: 20px;
}

.traffic-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.traffic-content {
  padding: 20px 0;
}

.connection-status {
  margin-bottom: 30px;
}

.status-item {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.status-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
}

.status-value {
  font-size: 18px;
  font-weight: bold;
}

.traffic-charts {
  margin-bottom: 30px;
}

.chart-container {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.chart-container h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.speed-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.speed-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.speed-bar {
  width: 100%;
  height: 20px;
  background: #e4e7ed;
  border-radius: 10px;
  overflow: hidden;
}

.speed-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.upload-fill {
  background: linear-gradient(90deg, #67c23a, #85ce61);
}

.download-fill {
  background: linear-gradient(90deg, #409eff, #66b1ff);
}

.traffic-stats {
  margin-bottom: 30px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: center;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
  color: white;
}

.upload-icon {
  background: #67c23a;
}

.download-icon {
  background: #409eff;
}

.connection-icon {
  background: #e6a23c;
}

.bandwidth-icon {
  background: #f56c6c;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.realtime-data {
  margin-top: 30px;
}

.realtime-data h4 {
  margin: 0 0 15px 0;
  color: #333;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .realtime-traffic {
    padding: 10px;
  }
  
  .traffic-content {
    padding: 10px 0;
  }
  
  .status-item,
  .chart-container,
  .stat-card {
    padding: 15px;
  }
  
  .speed-value {
    font-size: 20px;
  }
  
  .stat-value {
    font-size: 18px;
  }
}
</style>
