<template>
  <div class="traffic-management-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>📊 流量管理</h1>
      <p>实时流量监控与带宽控制管理</p>
    </div>

    <!-- 流量统计概览 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Upload /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatBytes(trafficStats.totalBytesSent) }}</div>
            <div class="stat-label">总发送流量</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Download /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatBytes(trafficStats.totalBytesRecv) }}</div>
            <div class="stat-label">总接收流量</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Connection /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ trafficStats.activeConnections }}</div>
            <div class="stat-label">活跃连接</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ trafficStats.onlineUsers }}</div>
            <div class="stat-label">在线用户</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 实时流量监控图表 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>📈 实时流量监控</span>
          <div>
            <el-button 
              @click="toggleAutoRefresh" 
              :loading="statsLoading"
              :type="isAutoRefresh ? 'success' : 'primary'"
            >
              <el-icon><Refresh /></el-icon>
              {{ isAutoRefresh ? '停止自动刷新' : '开启自动刷新' }}
            </el-button>
          </div>
        </div>
      </template>
      <div ref="trafficChartRef" style="height: 400px;"></div>
    </el-card>

    <!-- 流量控制管理 -->
    <el-card class="control-card">
      <template #header>
        <div class="card-header">
          <span>🚀 流量控制管理</span>
          <el-button type="primary" @click="showSetLimitDialog = true">
            <el-icon><Plus /></el-icon>
            设置带宽限制
          </el-button>
        </div>
      </template>

      <!-- 设置带宽限制表单 -->
      <el-form :model="limitForm" :rules="limitRules" ref="limitFormRef" label-width="120px" class="limit-form">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="用户ID" prop="user_id">
              <el-input-number
                v-model="limitForm.user_id"
                :min="1"
                placeholder="请输入用户ID"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="带宽限制" prop="limit">
              <el-input-number
                v-model="limitForm.limit"
                :min="0"
                placeholder="字节/秒"
                style="width: 100%"
              />
              <div class="form-tip">
                0 表示无限制，例如：1048576 (1MB/s)
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="限制周期" prop="period">
              <el-select v-model="limitForm.period" placeholder="选择周期" style="width: 100%">
                <el-option label="日限制" value="daily" />
                <el-option label="月限制" value="monthly" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" @click="setBandwidthLimit" :loading="setting">
            设置带宽限制
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 带宽限制列表 -->
      <div class="limits-section">
        <div class="section-header">
          <span>📋 用户带宽限制列表</span>
          <div>
            <el-button @click="loadBandwidthLimits" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button type="success" @click="exportLimits">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
          </div>
        </div>

        <el-table :data="bandwidthLimits" v-loading="loading" style="width: 100%">
          <el-table-column prop="user_id" label="用户ID" width="80" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="limit" label="带宽限制" width="150">
            <template #default="scope">
              <el-tag :type="scope.row.limit > 0 ? 'success' : 'info'">
                {{ formatBandwidth(scope.row.limit) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="period" label="周期" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.period === 'daily' ? 'primary' : 'warning'">
                {{ scope.row.period === 'daily' ? '日限制' : '月限制' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="enabled" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.enabled ? 'success' : 'danger'">
                {{ scope.row.enabled ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" width="180" />
          <el-table-column label="操作" width="200">
            <template #default="scope">
              <el-button size="small" @click="editLimit(scope.row)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button size="small" type="danger" @click="deleteLimit(scope.row)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 历史流量查询 -->
    <el-card class="historical-card">
      <template #header>
        <div class="card-header">
          <span>🔍 历史流量查询</span>
        </div>
      </template>
      
      <!-- 查询条件 -->
      <el-form :model="queryForm" :inline="true" class="query-form">
        <el-form-item label="用户名">
          <el-input v-model="queryForm.username" placeholder="请输入用户名" clearable />
        </el-form-item>
        <el-form-item label="目标IP">
          <el-input v-model="queryForm.targetIP" placeholder="请输入目标IP" clearable />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="queryForm.startDate"
            type="datetime"
            placeholder="选择开始时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="queryForm.endDate"
            type="datetime"
            placeholder="选择结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="排序方式">
          <el-select v-model="queryForm.sortBy" placeholder="选择排序字段">
            <el-option label="时间" value="timestamp" />
            <el-option label="发送字节" value="bytes_sent" />
            <el-option label="接收字节" value="bytes_recv" />
            <el-option label="目标IP" value="target_ip" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序顺序">
          <el-select v-model="queryForm.sortOrder" placeholder="选择排序顺序">
            <el-option label="降序" value="desc" />
            <el-option label="升序" value="asc" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchHistoricalTraffic" :loading="historicalLoading">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetQuery">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 统计信息 -->
      <div v-if="historicalStats" class="stats-summary">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic title="总发送流量" :value="historicalStats.total_sent" suffix="字节" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="总接收流量" :value="historicalStats.total_recv" suffix="字节" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="平均发送" :value="historicalStats.avg_sent" suffix="字节" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="平均接收" :value="historicalStats.avg_recv" suffix="字节" />
          </el-col>
        </el-row>
      </div>

      <!-- 历史流量表格 -->
      <el-table :data="historicalLogs" v-loading="historicalLoading" stripe>
        <el-table-column prop="timestamp" label="时间" width="180" />
        <el-table-column prop="user.username" label="用户" width="120" />
        <el-table-column prop="target_ip" label="目标IP" width="150" />
        <el-table-column prop="bytes_sent" label="发送字节" width="120">
          <template #default="{ row }">
            {{ formatBandwidth(row.bytes_sent) }}
          </template>
        </el-table-column>
        <el-table-column prop="bytes_recv" label="接收字节" width="120">
          <template #default="{ row }">
            {{ formatBandwidth(row.bytes_recv) }}
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="持续时间" width="100">
          <template #default="{ row }">
            {{ row.duration || 0 }}ms
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-if="historicalTotal > 0"
        v-model:current-page="queryForm.page"
        v-model:page-size="queryForm.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="historicalTotal"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="searchHistoricalTraffic"
        @current-change="searchHistoricalTraffic"
        class="pagination"
      />
    </el-card>

    <!-- 流量日志 -->
    <el-card class="logs-card">
      <template #header>
        <div class="card-header">
          <span>📝 流量日志</span>
          <div>
            <el-button type="primary" @click="fetchTrafficLogs" :loading="logsLoading">
              <el-icon><Refresh /></el-icon>
              刷新日志
            </el-button>
            <el-button type="success" @click="exportLogs">
              <el-icon><Download /></el-icon>
              导出日志
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="trafficLogs" v-loading="logsLoading" style="width: 100%">
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

    <!-- 编辑限制对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑带宽限制" width="500px">
      <el-form :model="editForm" :rules="limitRules" ref="editFormRef" label-width="120px">
        <el-form-item label="用户ID" prop="user_id">
          <el-input-number v-model="editForm.user_id" :min="1" disabled style="width: 100%" />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="带宽限制" prop="limit">
          <el-input-number
            v-model="editForm.limit"
            :min="0"
            placeholder="字节/秒"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="限制周期" prop="period">
          <el-select v-model="editForm.period" placeholder="选择周期" style="width: 100%">
            <el-option label="日限制" value="daily" />
            <el-option label="月限制" value="monthly" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="updateBandwidthLimit" :loading="updating">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Refresh,
  Download,
  Edit,
  Delete,
  Upload,
  Connection,
  User
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { trafficControlAPI, utils } from '@/api/trafficControl'
import { formatBytes, formatDate } from '@/utils/formatters'
import * as echarts from 'echarts'

const authStore = useAuthStore()

// 响应式数据
const loading = ref(false)
const setting = ref(false)
const updating = ref(false)
const statsLoading = ref(false)
const logsLoading = ref(false)
const showEditDialog = ref(false)

// 表单数据
const limitForm = reactive({
  user_id: null,
  limit: null,
  period: 'daily'
})

const editForm = reactive({
  user_id: null,
  username: '',
  limit: null,
  period: 'daily'
})

// 数据列表
const bandwidthLimits = ref([])
const trafficLogs = ref([])
const trafficStats = ref({
  totalBytesSent: 0,
  totalBytesRecv: 0,
  activeConnections: 0,
  onlineUsers: 0
})
const realtimeTraffic = ref([])
const userTraffic = ref([])
const isAutoRefresh = ref(false)

// 历史流量查询相关
const historicalLogs = ref([])
const historicalStats = ref(null)
const historicalTotal = ref(0)
const historicalLoading = ref(false)
const queryForm = ref({
  username: '',
  targetIP: '',
  startDate: '',
  endDate: '',
  sortBy: 'timestamp',
  sortOrder: 'desc',
  page: 1,
  pageSize: 20
})

// 表单验证规则
const limitRules = {
  user_id: [
    { required: true, message: '请输入用户ID', trigger: 'blur' }
  ],
  limit: [
    { required: true, message: '请输入带宽限制', trigger: 'blur' }
  ],
  period: [
    { required: true, message: '请选择限制周期', trigger: 'change' }
  ]
}

// 图表相关
const trafficChartRef = ref()
let trafficChart = null
let intervalId = null

// 使用工具函数
const formatBandwidth = utils.formatBandwidth

// 设置带宽限制
const setBandwidthLimit = async () => {
  try {
    await limitFormRef.value.validate()
    setting.value = true

    const result = await trafficControlAPI.setBandwidthLimit(authStore.token, limitForm)
    ElMessage.success(result.message || '带宽限制设置成功')
    resetForm()
    loadBandwidthLimits()
  } catch (error) {
    // 错误已在 API 服务中处理
  } finally {
    setting.value = false
  }
}

// 加载带宽限制列表
const loadBandwidthLimits = async () => {
  loading.value = true
  try {
    const result = await trafficControlAPI.getBandwidthLimits(authStore.token)
    bandwidthLimits.value = result.data || []
  } catch (error) {
    // 错误已在 API 服务中处理
  } finally {
    loading.value = false
  }
}

// 编辑限制
const editLimit = (row) => {
  editForm.user_id = row.user_id
  editForm.username = row.username
  editForm.limit = row.limit
  editForm.period = row.period
  showEditDialog.value = true
}

// 更新带宽限制
const updateBandwidthLimit = async () => {
  try {
    await editFormRef.value.validate()
    updating.value = true

    const result = await trafficControlAPI.updateBandwidthLimit(
      authStore.token, 
      editForm.user_id, 
      {
        limit: editForm.limit,
        period: editForm.period
      }
    )
    ElMessage.success(result.message || '更新成功')
    showEditDialog.value = false
    loadBandwidthLimits()
  } catch (error) {
    // 错误已在 API 服务中处理
  } finally {
    updating.value = false
  }
}

// 删除限制
const deleteLimit = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 ${row.username} 的带宽限制吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const result = await trafficControlAPI.deleteBandwidthLimit(authStore.token, row.user_id)
    ElMessage.success(result.message || '删除成功')
    loadBandwidthLimits()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已在 API 服务中处理
    }
  }
}

// 加载流量统计
const loadTrafficStats = async () => {
  statsLoading.value = true
  try {
    const result = await trafficControlAPI.getTrafficStats(authStore.token)
    trafficStats.value = result
    updateChart()
  } catch (error) {
    // 错误已在 API 服务中处理
  } finally {
    statsLoading.value = false
  }
}

// 获取实时流量数据
const loadRealtimeTraffic = async () => {
  try {
    const response = await fetch('/api/v1/traffic/realtime', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      realtimeTraffic.value = data.realtime_traffic || []
      userTraffic.value = data.user_traffic || []
      updateChart()
    }
  } catch (error) {
    console.error('获取实时流量数据失败:', error)
  }
}

// 获取流量日志
const fetchTrafficLogs = async () => {
  logsLoading.value = true
  try {
    const response = await fetch('/api/v1/logs?type=traffic', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      trafficLogs.value = data.logs || []
    }
  } catch (error) {
    ElMessage.error('获取流量日志失败')
  } finally {
    logsLoading.value = false
  }
}

// 切换自动刷新状态
const toggleAutoRefresh = () => {
  isAutoRefresh.value = !isAutoRefresh.value
  
  if (isAutoRefresh.value) {
    // 开始自动刷新
    intervalId = setInterval(() => {
      loadTrafficStats()
      loadRealtimeTraffic()
    }, 10000) // 每10秒更新一次
    ElMessage.success('已开启自动刷新')
  } else {
    // 停止自动刷新
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
    ElMessage.info('已关闭自动刷新')
  }
}

// 搜索历史流量
const searchHistoricalTraffic = async () => {
  historicalLoading.value = true
  try {
    const params = new URLSearchParams()
    params.append('page', queryForm.value.page)
    params.append('pageSize', queryForm.value.pageSize)
    params.append('sortBy', queryForm.value.sortBy)
    params.append('sortOrder', queryForm.value.sortOrder)
    
    if (queryForm.value.username) {
      params.append('username', queryForm.value.username)
    }
    if (queryForm.value.targetIP) {
      params.append('targetIP', queryForm.value.targetIP)
    }
    if (queryForm.value.startDate) {
      params.append('startDate', queryForm.value.startDate)
    }
    if (queryForm.value.endDate) {
      params.append('endDate', queryForm.value.endDate)
    }

    const response = await fetch(`/api/v1/traffic/historical?${params}`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      historicalLogs.value = data.logs || []
      historicalStats.value = data.stats
      historicalTotal.value = data.total || 0
    } else {
      ElMessage.error('查询历史流量失败')
    }
  } catch (error) {
    console.error('查询历史流量失败:', error)
    ElMessage.error('查询历史流量失败')
  } finally {
    historicalLoading.value = false
  }
}

// 重置查询条件
const resetQuery = () => {
  queryForm.value = {
    username: '',
    targetIP: '',
    startDate: '',
    endDate: '',
    sortBy: 'timestamp',
    sortOrder: 'desc',
    page: 1,
    pageSize: 20
  }
  historicalLogs.value = []
  historicalStats.value = null
  historicalTotal.value = 0
}

// 更新图表
const updateChart = () => {
  if (!trafficChart) return
  
  // 处理用户流量数据
  const timeLabels = []
  const series = []
  const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#c71585', '#ff6347', '#32cd32', '#ffd700', '#ff69b4']
  
  if (userTraffic.value && userTraffic.value.length > 0) {
    // 收集所有时间点
    const allTimes = new Set()
    userTraffic.value.forEach(user => {
      user.traffic.forEach(traffic => {
        const time = new Date(traffic.timestamp).toLocaleTimeString()
        allTimes.add(time)
      })
    })
    
    // 排序时间点
    timeLabels.push(...Array.from(allTimes).sort())
    
    // 为每个用户创建数据系列
    userTraffic.value.forEach((user, index) => {
      const sentData = new Array(timeLabels.length).fill(0)
      const recvData = new Array(timeLabels.length).fill(0)
      
      user.traffic.forEach(traffic => {
        const time = new Date(traffic.timestamp).toLocaleTimeString()
        const timeIndex = timeLabels.indexOf(time)
        if (timeIndex !== -1) {
          sentData[timeIndex] = traffic.bytes_sent || 0
          recvData[timeIndex] = traffic.bytes_recv || 0
        }
      })
      
      const color = colors[index % colors.length]
      
      // 发送流量系列
      series.push({
        name: `${user.username} - 发送`,
        type: 'line',
        smooth: true,
        data: sentData,
        itemStyle: { color },
        lineStyle: { color }
      })
      
      // 接收流量系列
      series.push({
        name: `${user.username} - 接收`,
        type: 'line',
        smooth: true,
        data: recvData,
        itemStyle: { color: color + '80' }, // 半透明
        lineStyle: { color: color + '80', type: 'dashed' }
      })
    })
  } else {
    // 如果没有用户数据，显示总体数据
    if (realtimeTraffic.value && realtimeTraffic.value.length > 0) {
      const sortedData = realtimeTraffic.value
        .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
        .slice(-10)
      
      sortedData.forEach(item => {
        const time = new Date(item.timestamp)
        timeLabels.push(time.toLocaleTimeString())
      })
      
      const sentData = sortedData.map(item => item.bytes_sent || 0)
      const recvData = sortedData.map(item => item.bytes_recv || 0)
      
      series.push(
        {
          name: '总发送流量',
          type: 'line',
          smooth: true,
          data: sentData,
          itemStyle: { color: '#409eff' }
        },
        {
          name: '总接收流量',
          type: 'line',
          smooth: true,
          data: recvData,
          itemStyle: { color: '#67c23a' }
        }
      )
    } else {
      timeLabels.push('暂无数据')
      series.push({
        name: '暂无数据',
        type: 'line',
        data: [0],
        itemStyle: { color: '#909399' }
      })
    }
  }
  
  const option = {
    title: {
      text: '实时流量监控 (按用户)',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        let result = params[0].name + '<br/>'
        params.forEach(param => {
          result += param.marker + param.seriesName + ': ' + formatBandwidth(param.value) + '<br/>'
        })
        return result
      }
    },
    legend: {
      data: series.map(s => s.name),
      top: 30,
      type: 'scroll'
    },
    xAxis: {
      type: 'category',
      data: timeLabels,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '字节',
      axisLabel: {
        formatter: function(value) {
          return formatBandwidth(value)
        }
      }
    },
    series: series
  }
  
  trafficChart.setOption(option)
}

// 导出限制
const exportLimits = () => {
  const data = bandwidthLimits.value.map(limit => ({
    '用户ID': limit.user_id,
    '用户名': limit.username,
    '带宽限制': limit.limit,
    '周期': limit.period === 'daily' ? '日限制' : '月限制',
    '状态': limit.enabled ? '启用' : '禁用',
    '更新时间': limit.updated_at
  }))
  
  utils.exportToCSV(data, 'bandwidth_limits.csv')
  ElMessage.success('导出成功')
}

// 导出流量数据
const exportTrafficData = () => {
  const data = [{
    '总发送流量': trafficStats.value.totalBytesSent,
    '总接收流量': trafficStats.value.totalBytesRecv,
    '活跃连接': trafficStats.value.activeConnections,
    '在线用户': trafficStats.value.onlineUsers
  }]
  
  utils.exportToCSV(data, 'traffic_stats.csv')
  ElMessage.success('导出成功')
}

// 导出日志
const exportLogs = () => {
  const data = trafficLogs.value.map(log => ({
    'ID': log.id,
    '用户名': log.username,
    '客户端IP': log.client_ip,
    '目标IP': log.target_ip,
    '目标端口': log.target_port,
    '协议': log.protocol,
    '发送字节': log.bytes_sent,
    '接收字节': log.bytes_recv,
    '时间': log.timestamp
  }))
  
  utils.exportToCSV(data, 'traffic_logs.csv')
  ElMessage.success('导出成功')
}

// 重置表单
const resetForm = () => {
  limitForm.user_id = null
  limitForm.limit = null
  limitForm.period = 'daily'
}

// 表单引用
const limitFormRef = ref()
const editFormRef = ref()

// 生命周期
onMounted(() => {
  loadBandwidthLimits()
  loadTrafficStats()
  loadRealtimeTraffic()
  fetchTrafficLogs()
  
  // 初始化图表
  if (trafficChartRef.value) {
    trafficChart = echarts.init(trafficChartRef.value)
    updateChart()
  }
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
.traffic-management-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 30px;
  text-align: center;
}

.page-header h1 {
  color: #303133;
  margin: 0 0 10px 0;
  font-size: 28px;
}

.page-header p {
  color: #606266;
  margin: 0;
  font-size: 16px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  font-size: 32px;
  margin-right: 16px;
  opacity: 0.8;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.chart-card,
.control-card,
.logs-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.limit-form {
  margin-bottom: 30px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.limits-section {
  margin-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-weight: 500;
  color: #303133;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .traffic-management-container {
    padding: 10px;
  }
  
  .page-header h1 {
    font-size: 24px;
  }
  
  .stat-card {
    padding: 15px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}

.query-form {
  margin-bottom: 20px;
}

.stats-summary {
  margin-bottom: 20px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}
</style>
