<template>
  <div class="traffic-control-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>🚀 流量控制管理</h1>
      <p>为用户设置带宽限制，实现精细化的流量管理</p>
    </div>

    <!-- 设置带宽限制 -->
    <el-card class="control-card">
      <template #header>
        <div class="card-header">
          <span>📊 设置用户带宽限制</span>
          <el-button type="primary" @click="showSetLimitDialog = true">
            <el-icon><Plus /></el-icon>
            设置限制
          </el-button>
        </div>
      </template>

      <el-form :model="limitForm" :rules="limitRules" ref="limitFormRef" label-width="120px">
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
    </el-card>

    <!-- 带宽限制列表 -->
    <el-card class="control-card">
      <template #header>
        <div class="card-header">
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
      </template>

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
    </el-card>

    <!-- 实时流量监控 -->
    <el-card class="control-card">
      <template #header>
        <div class="card-header">
          <span>📈 实时流量监控</span>
          <el-button @click="loadTrafficStats" :loading="statsLoading">
            <el-icon><Refresh /></el-icon>
            刷新统计
          </el-button>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon><Upload /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatBandwidth(trafficStats.totalBytesSent) }}</div>
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
              <div class="stat-value">{{ formatBandwidth(trafficStats.totalBytesRecv) }}</div>
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

      <!-- 流量图表 -->
      <div style="margin-top: 20px;">
        <div ref="trafficChartRef" style="height: 300px;"></div>
      </div>
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
import * as echarts from 'echarts'

const authStore = useAuthStore()

// 响应式数据
const loading = ref(false)
const setting = ref(false)
const updating = ref(false)
const statsLoading = ref(false)
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
const trafficStats = ref({
  totalBytesSent: 0,
  totalBytesRecv: 0,
  activeConnections: 0,
  onlineUsers: 0
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

// 更新图表
const updateChart = () => {
  if (!trafficChart) return
  
  const option = {
    title: {
      text: '实时流量监控',
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
      data: ['发送流量', '接收流量'],
      top: 30
    },
    xAxis: {
      type: 'category',
      data: ['1分钟前', '30秒前', '现在']
    },
    yAxis: {
      type: 'value',
      name: '字节/秒',
      axisLabel: {
        formatter: function(value) {
          return formatBandwidth(value)
        }
      }
    },
    series: [
      {
        name: '发送流量',
        type: 'line',
        smooth: true,
        data: [
          trafficStats.value.totalBytesSent * 0.8,
          trafficStats.value.totalBytesSent * 0.9,
          trafficStats.value.totalBytesSent
        ],
        itemStyle: {
          color: '#409eff'
        }
      },
      {
        name: '接收流量',
        type: 'line',
        smooth: true,
        data: [
          trafficStats.value.totalBytesRecv * 0.8,
          trafficStats.value.totalBytesRecv * 0.9,
          trafficStats.value.totalBytesRecv
        ],
        itemStyle: {
          color: '#67c23a'
        }
      }
    ]
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
  
  // 初始化图表
  if (trafficChartRef.value) {
    trafficChart = echarts.init(trafficChartRef.value)
    updateChart()
  }
  
  // 定时更新数据
  intervalId = setInterval(() => {
    loadTrafficStats()
  }, 10000) // 每10秒更新一次
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
.traffic-control-container {
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

.control-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
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

/* 响应式设计 */
@media (max-width: 768px) {
  .traffic-control-container {
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
}
</style>
