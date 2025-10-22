<template>
  <div class="ip-control-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>IP访问控制</span>
        </div>
      </template>

      <el-tabs v-model="activeTab" type="border-card">
        <!-- IP黑名单标签页 -->
        <el-tab-pane label="IP黑名单" name="blacklist">
          <div class="tab-header">
            <div class="tab-description">
              <el-icon><WarningFilled /></el-icon>
              <span>阻止指定的IP地址或网段访问。支持单个IP（如 192.168.1.1）或CIDR格式（如 192.168.10.0/24）</span>
            </div>
            <el-button type="danger" @click="showBlacklistDialog = true">
              <el-icon><Plus /></el-icon>
              添加黑名单
            </el-button>
          </div>

          <el-table :data="blacklist" v-loading="blacklistLoading" style="width: 100%; margin-top: 20px">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="cidr" label="IP/CIDR" min-width="180">
              <template #default="scope">
                <el-tag type="info">{{ scope.row.cidr }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="200" />
            <el-table-column prop="enabled" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.enabled ? 'success' : 'info'">
                  {{ scope.row.enabled ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="scope">
                {{ formatDate(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="scope">
                <el-button size="small" @click="editBlacklistEntry(scope.row)">编辑</el-button>
                <el-button 
                  size="small" 
                  type="danger" 
                  @click="deleteBlacklistEntry(scope.row.id)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- IP白名单标签页 -->
        <el-tab-pane label="IP白名单" name="whitelist">
          <div class="tab-header">
            <div class="tab-description">
              <el-icon><CircleCheck /></el-icon>
              <span>只允许白名单中的IP地址访问。如果白名单不为空，则只有白名单中的IP才能通过</span>
            </div>
            <el-button type="success" @click="showWhitelistDialog = true">
              <el-icon><Plus /></el-icon>
              添加白名单
            </el-button>
          </div>

          <el-table :data="whitelist" v-loading="whitelistLoading" style="width: 100%; margin-top: 20px">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="ip" label="IP地址" min-width="180">
              <template #default="scope">
                <el-tag type="success">{{ scope.row.ip }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="200" />
            <el-table-column prop="enabled" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.enabled ? 'success' : 'info'">
                  {{ scope.row.enabled ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="scope">
                {{ formatDate(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="scope">
                <el-button size="small" @click="editWhitelistEntry(scope.row)">编辑</el-button>
                <el-button 
                  size="small" 
                  type="danger" 
                  @click="deleteWhitelistEntry(scope.row.id)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 黑名单对话框 -->
    <el-dialog 
      v-model="showBlacklistDialog" 
      :title="editingBlacklist ? '编辑黑名单' : '添加黑名单'"
      width="500px"
    >
      <el-form :model="blacklistForm" :rules="blacklistRules" ref="blacklistFormRef" label-width="100px">
        <el-form-item label="IP/CIDR" prop="cidr">
          <el-input 
            v-model="blacklistForm.cidr" 
            placeholder="例如: 192.168.10.0/24 或 192.168.1.1" 
          />
          <div class="form-tip">支持单个IP或CIDR网段格式</div>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="blacklistForm.description" type="textarea" />
        </el-form-item>
        <el-form-item label="状态" prop="enabled">
          <el-switch v-model="blacklistForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showBlacklistDialog = false">取消</el-button>
          <el-button type="primary" @click="saveBlacklist">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 白名单对话框 -->
    <el-dialog 
      v-model="showWhitelistDialog" 
      :title="editingWhitelist ? '编辑白名单' : '添加白名单'"
      width="500px"
    >
      <el-form :model="whitelistForm" :rules="whitelistRules" ref="whitelistFormRef" label-width="100px">
        <el-form-item label="IP地址" prop="ip">
          <el-input 
            v-model="whitelistForm.ip" 
            placeholder="例如: 192.168.1.1" 
          />
          <div class="form-tip">仅支持单个IP地址</div>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="whitelistForm.description" type="textarea" />
        </el-form-item>
        <el-form-item label="状态" prop="enabled">
          <el-switch v-model="whitelistForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showWhitelistDialog = false">取消</el-button>
          <el-button type="primary" @click="saveWhitelist">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="js">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, WarningFilled, CircleCheck } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { formatDate } from '@/utils/formatters'

const authStore = useAuthStore()
const activeTab = ref('blacklist')

// 黑名单相关
const blacklistLoading = ref(false)
const blacklist = ref([])
const showBlacklistDialog = ref(false)
const editingBlacklist = ref(null)
const blacklistFormRef = ref()

const blacklistForm = ref({
  cidr: '',
  description: '',
  enabled: true
})

const blacklistRules = {
  cidr: [
    { required: true, message: '请输入IP地址或CIDR网段', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入描述', trigger: 'blur' }
  ]
}

// 白名单相关
const whitelistLoading = ref(false)
const whitelist = ref([])
const showWhitelistDialog = ref(false)
const editingWhitelist = ref(null)
const whitelistFormRef = ref()

const whitelistForm = ref({
  ip: '',
  description: '',
  enabled: true
})

const whitelistRules = {
  ip: [
    { required: true, message: '请输入IP地址', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入描述', trigger: 'blur' }
  ]
}

// ==================== 黑名单操作 ====================

const fetchBlacklist = async () => {
  blacklistLoading.value = true
  try {
    const response = await fetch('/api/v1/ip-blacklist', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      blacklist.value = data.blacklist || []
    }
  } catch (error) {
    ElMessage.error('获取IP黑名单失败')
  } finally {
    blacklistLoading.value = false
  }
}

const editBlacklistEntry = (entry) => {
  editingBlacklist.value = entry
  blacklistForm.value = { ...entry }
  showBlacklistDialog.value = true
}

const saveBlacklist = async () => {
  if (!blacklistFormRef.value) return
  
  await blacklistFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const url = editingBlacklist.value 
          ? `/api/v1/ip-blacklist/${editingBlacklist.value.id}`
          : '/api/v1/ip-blacklist'
        
        const method = editingBlacklist.value ? 'PUT' : 'POST'
        
        const response = await fetch(url, {
          method,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authStore.token}`
          },
          body: JSON.stringify(blacklistForm.value)
        })
        
        if (response.ok) {
          ElMessage.success(editingBlacklist.value ? 'IP黑名单更新成功' : 'IP黑名单创建成功')
          showBlacklistDialog.value = false
          editingBlacklist.value = null
          blacklistForm.value = { cidr: '', description: '', enabled: true }
          fetchBlacklist()
        } else {
          const data = await response.json()
          ElMessage.error(data.error || '操作失败')
        }
      } catch (error) {
        ElMessage.error('操作失败')
      }
    }
  })
}

const deleteBlacklistEntry = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这条IP黑名单规则吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const response = await fetch(`/api/v1/ip-blacklist/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (response.ok) {
      ElMessage.success('IP黑名单规则删除成功')
      fetchBlacklist()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// ==================== 白名单操作 ====================

const fetchWhitelist = async () => {
  whitelistLoading.value = true
  try {
    const response = await fetch('/api/v1/ip-whitelist', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      whitelist.value = data.whitelist || []
    }
  } catch (error) {
    ElMessage.error('获取IP白名单失败')
  } finally {
    whitelistLoading.value = false
  }
}

const editWhitelistEntry = (entry) => {
  editingWhitelist.value = entry
  whitelistForm.value = { ...entry }
  showWhitelistDialog.value = true
}

const saveWhitelist = async () => {
  if (!whitelistFormRef.value) return
  
  await whitelistFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const url = editingWhitelist.value 
          ? `/api/v1/ip-whitelist/${editingWhitelist.value.id}`
          : '/api/v1/ip-whitelist'
        
        const method = editingWhitelist.value ? 'PUT' : 'POST'
        
        const response = await fetch(url, {
          method,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authStore.token}`
          },
          body: JSON.stringify(whitelistForm.value)
        })
        
        if (response.ok) {
          ElMessage.success(editingWhitelist.value ? 'IP白名单更新成功' : 'IP白名单创建成功')
          showWhitelistDialog.value = false
          editingWhitelist.value = null
          whitelistForm.value = { ip: '', description: '', enabled: true }
          fetchWhitelist()
        } else {
          const data = await response.json()
          ElMessage.error(data.error || '操作失败')
        }
      } catch (error) {
        ElMessage.error('操作失败')
      }
    }
  })
}

const deleteWhitelistEntry = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这条IP白名单规则吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const response = await fetch(`/api/v1/ip-whitelist/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (response.ok) {
      ElMessage.success('IP白名单规则删除成功')
      fetchWhitelist()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// ==================== 初始化 ====================

onMounted(() => {
  fetchBlacklist()
  fetchWhitelist()
})
</script>

<style scoped>
.ip-control-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.tab-description {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
  font-size: 14px;
}

.tab-description .el-icon {
  font-size: 18px;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-tabs--border-card) {
  box-shadow: none;
  border: 1px solid #dcdfe6;
}

:deep(.el-tabs__header) {
  background-color: #f5f7fa;
}
</style>

