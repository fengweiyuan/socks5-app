<template>
  <div class="filters-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>URL过滤规则</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            添加规则
          </el-button>
        </div>
      </template>

      <el-table :data="filters" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="pattern" label="匹配模式" />
        <el-table-column prop="type" label="类型">
          <template #default="scope">
            <el-tag :type="scope.row.type === 'block' ? 'danger' : 'success'">
              {{ scope.row.type === 'block' ? '阻止' : '允许' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="enabled" label="状态">
          <template #default="scope">
            <el-tag :type="scope.row.enabled ? 'success' : 'info'">
              {{ scope.row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="editFilter(scope.row)">编辑</el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteFilter(scope.row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑过滤规则对话框 -->
    <el-dialog 
      v-model="showCreateDialog" 
      :title="editingFilter ? '编辑过滤规则' : '添加过滤规则'"
      width="500px"
    >
      <el-form :model="filterForm" :rules="rules" ref="filterFormRef" label-width="100px">
        <el-form-item label="匹配模式" prop="pattern">
          <el-input v-model="filterForm.pattern" placeholder="例如: *.google.com" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="filterForm.type" placeholder="选择类型">
            <el-option label="阻止" value="block" />
            <el-option label="允许" value="allow" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="filterForm.description" type="textarea" />
        </el-form-item>
        <el-form-item label="状态" prop="enabled">
          <el-switch v-model="filterForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="saveFilter">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import type { FormInstance, FormRules } from 'element-plus'

const authStore = useAuthStore()
const loading = ref(false)
const filters = ref([])
const showCreateDialog = ref(false)
const editingFilter = ref(null)
const filterFormRef = ref<FormInstance>()

const filterForm = ref({
  pattern: '',
  type: 'block',
  description: '',
  enabled: true
})

const rules: FormRules = {
  pattern: [
    { required: true, message: '请输入匹配模式', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择类型', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入描述', trigger: 'blur' }
  ]
}

const fetchFilters = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/v1/filters', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      filters.value = data.filters
    }
  } catch (error) {
    ElMessage.error('获取过滤规则失败')
  } finally {
    loading.value = false
  }
}

const editFilter = (filter: any) => {
  editingFilter.value = filter
  filterForm.value = { ...filter }
  showCreateDialog.value = true
}

const saveFilter = async () => {
  if (!filterFormRef.value) return
  
  await filterFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const url = editingFilter.value 
          ? `/api/v1/filters/${editingFilter.value.id}`
          : '/api/v1/filters'
        
        const method = editingFilter.value ? 'PUT' : 'POST'
        
        const response = await fetch(url, {
          method,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authStore.token}`
          },
          body: JSON.stringify(filterForm.value)
        })
        
        if (response.ok) {
          ElMessage.success(editingFilter.value ? '过滤规则更新成功' : '过滤规则创建成功')
          showCreateDialog.value = false
          fetchFilters()
        }
      } catch (error) {
        ElMessage.error('操作失败')
      }
    }
  })
}

const deleteFilter = async (filterId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个过滤规则吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const response = await fetch(`/api/v1/filters/${filterId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (response.ok) {
      ElMessage.success('过滤规则删除成功')
      fetchFilters()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString()
}

onMounted(() => {
  fetchFilters()
})
</script>

<style scoped>
.filters-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
