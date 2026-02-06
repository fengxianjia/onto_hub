<template>
  <el-card class="box-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span>订阅管理 (Webhooks)</span>
        <div class="header-actions">
           <el-button type="primary" @click="fetchWebhooks" circle><el-icon><refresh /></el-icon></el-button>
           <el-button type="success" @click="handleAdd">新增订阅</el-button>
        </div>
      </div>
    </template>
    
    <el-table ref="webhookTable" :data="tableData" style="width: 100%" v-loading="loading">
      <el-table-column prop="name" label="名称" width="150" show-overflow-tooltip />
      <el-table-column prop="target_url" label="回调地址 (Target URL)" min-width="300" />
      <el-table-column prop="event_type" label="事件类型" width="180">
         <template #default="scope">
            <el-tag>{{ scope.row.event_type }}</el-tag>
         </template>
      </el-table-column>
      <el-table-column prop="ontology_filter" label="适用本体 (Scope)" width="200">
         <template #default="scope">
            <el-tag v-if="scope.row.ontology_filter" type="primary" effect="plain">{{ scope.row.ontology_filter }}</el-tag>
            <el-tag v-else type="info" effect="plain">全局 (All)</el-tag>
         </template>
      </el-table-column>
      <el-table-column label="签名加固" width="120" align="center">
         <template #default="scope">
            <el-tag v-if="scope.row.secret_token" type="success" effect="dark" size="small">已加固</el-tag>
            <el-tag v-else type="info" effect="plain" size="small">未加固</el-tag>
         </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="220">
         <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
         </template>
      </el-table-column>
      <el-table-column label="连通性 (Status)" width="180" align="center">
        <template #default="scope">
           <span v-if="scope.row.ping_status === 'SUCCESS'" style="color: #67C23A; font-weight: bold;">
             HTTP {{ scope.row.ping_code }}
           </span>
           <span v-else-if="scope.row.ping_status === 'WARNING'" style="color: #E6A23C; font-weight: bold;">
              HTTP {{ scope.row.ping_code }}
           </span>
           <span v-else-if="scope.row.ping_status === 'FAILURE'" style="color: #F56C6C; font-weight: bold;">
              {{ scope.row.ping_code || 'Error' }}
           </span>
           <span v-else style="color: #999;">-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280">
        <template #default="scope">
          <el-button size="small" type="warning" plain @click="handlePing(scope.row)">测试</el-button>
          <el-button size="small" @click="handleLogs(scope.row)">日志</el-button>
          <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 编辑/新增 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑订阅' : '新增订阅'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称" required>
            <el-input v-model="form.name" placeholder="请输入订阅名称 (例如: 生产环境)" />
        </el-form-item>
        <el-form-item label="回调地址" required>
          <el-input v-model="form.target_url" placeholder="http://your-service:8080/callback" />
        </el-form-item>
        <el-form-item label="事件类型" required>
          <el-select v-model="form.event_type" placeholder="选择事件类型">
            <el-option label="ontology.activated" value="ontology.activated" />
          </el-select>
        </el-form-item>
        <el-form-item label="指定本体">
            <el-select v-model="form.ontology_filter" placeholder="默认为所有 (全局)" clearable filterable>
                <el-option label="所有本体 (默认)" value="" />
                <el-option 
                    v-for="opt in ontologyOptions" 
                    :key="opt.value" 
                    :label="opt.label" 
                    :value="opt.value" 
                />
            </el-select>
        </el-form-item>
        <el-form-item label="签名密钥">
            <el-input v-model="form.secret_token" type="password" show-password placeholder="HMAC SHA256 密钥 (可选)" />
            <div style="font-size: 11px; color: #999; margin-top: 4px; line-height: 1.2;">
              如果设置，推送时会携带 X-Hub-Signature-256 请求头。
            </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Webhook Log Drawer (Shared Component) -->
    <webhook-log-drawer 
        v-model="logDrawerVisible" 
        title="执行日志 (Webhook Logs)" 
        :logs-data="logsData" 
        :loading="logsLoading" 
        @refresh="fetchLogs"
    />
  </el-card>
</template>

<script setup>
import { ref, onMounted, reactive, nextTick } from 'vue'
import { Refresh, Document, Check, Warning, Close } from '@element-plus/icons-vue' // Icons updated
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import WebhookLogDrawer from './WebhookLogDrawer.vue'

const emit = defineEmits(['change'])

const tableData = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const currentId = ref(null)

// 日志相关
const logDrawerVisible = ref(false)
const logsData = ref([])
const logsLoading = ref(false)
const currentWebhookId = ref(null)

const form = reactive({
  name: '',
  target_url: '',
  event_type: 'ontology.activated',
  ontology_filter: '',
  secret_token: ''
})

const ontologyOptions = ref([])

const fetchOntologyOptions = async () => {
  try {
    const res = await axios.get('/api/ontologies')
    // We only need names for the dropdown
    // Use Set to avoid duplicates if API returns multiple versions (though default API is active only)
    const names = new Set(res.data.map(item => item.name))
    ontologyOptions.value = Array.from(names).map(name => ({ label: name, value: name }))
  } catch (e) {
    console.error("Failed to fetch ontologies", e)
  }
}

// Duplicate import removed
const webhookTable = ref(null)

const fetchWebhooks = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/webhooks')
    tableData.value = res.data
    // Fix layout misalignment by re-calculating layout after DOM update
    nextTick(() => {
        if (webhookTable.value) {
            webhookTable.value.doLayout()
        }
    })
    emit('change')
  } catch (error) {
    ElMessage.error('获取订阅列表失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  fetchOntologyOptions() // Refresh options when opening dialog
  isEdit.value = false
  currentId.value = null
  form.name = ''
  form.target_url = ''
  form.event_type = 'ontology.activated'
  form.ontology_filter = ''
  form.secret_token = ''
  dialogVisible.value = true
}

const handleEdit = (row) => {
  fetchOntologyOptions()
  isEdit.value = true
  currentId.value = row.id
  form.name = row.name || 'Webhook'
  form.target_url = row.target_url
  form.event_type = row.event_type
  form.ontology_filter = row.ontology_filter || ''
  form.secret_token = row.secret_token || ''
  dialogVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该订阅吗?', '警告', {
    type: 'warning'
  }).then(async () => {
    try {
      await axios.delete(`/api/webhooks/${row.id}`)
      ElMessage.success('删除成功')
      fetchWebhooks()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

const handleLogs = (row) => {
    currentWebhookId.value = row.id
    logDrawerVisible.value = true
    logsData.value = []
    fetchLogs()
}

const fetchLogs = async () => {
    if (!currentWebhookId.value) return
    logsLoading.value = true
    try {
        const res = await axios.get(`/api/webhooks/${currentWebhookId.value}/logs`)
        logsData.value = res.data
    } catch (e) {
        ElMessage.error('获取日志失败')
    } finally {
        logsLoading.value = false
    }
}

const handlePing = async (row) => {
    const loading = ElMessage.info({ message: '正在测试连通性...', duration: 0 })
    try {
        const res = await axios.post(`/api/webhooks/${row.id}/ping`)
        loading.close()
        
        const { response_status } = res.data
        
        if (response_status) {
             if (response_status >= 200 && response_status < 400) {
                 // 2xx, 3xx -> Success
                 row.ping_status = 'SUCCESS'
                 row.ping_code = response_status
                 ElMessage.success(`测试成功 (HTTP ${response_status})`)
             } else if (response_status === 404 || response_status === 405) {
                 // 404, 405 -> Treat as Configuration Error (Failure)
                 row.ping_status = 'FAILURE'
                 row.ping_code = response_status
                 ElMessage.error(`连接失败: 目标地址不可用 (HTTP ${response_status})`)
             } else {
                 // 422, 5xx -> Connected but App Error (Treat as Warning/Connected)
                 row.ping_status = 'WARNING'
                 row.ping_code = response_status
                 ElMessage.warning(`连通正常，但返回错误 (HTTP ${response_status})`)
             }
        } else {
             // Network Error (No response status from server)
             row.ping_status = 'FAILURE'
             row.ping_code = 'Network Error'
             ElMessage.error(`连接失败: 无法访问目标地址`)
        }
        
    } catch (e) {
        loading.close()
        row.ping_status = 'FAILURE'
        
        // Handle case where axio error has response (e.g. 500) if not caught above
        if (e.response && e.response.status) {
             const s = e.response.status
             if (s === 404 || s === 405) {
                  row.ping_code = s
                  ElMessage.error(`连接失败: 目标地址不可用 (HTTP ${s})`)
             } else {
                  // Treat others as connected
                  row.ping_status = 'WARNING'
                  row.ping_code = s
                  ElMessage.warning(`连通正常，但返回错误 (HTTP ${s})`)
             }
        } else {
             row.ping_code = 'Network Error'
             ElMessage.error(`测试请求失败: ${e.message}`)
        }
    }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  // Backend returns naive UTC (no Z). Append Z to ensure it's treated as UTC.
  const date = new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z')
  return date.toLocaleString()
}

const handleSubmit = async () => {
  if (!form.name) {
    ElMessage.warning('请输入订阅名称')
    return
  }
  if (!form.target_url) {
    ElMessage.warning('请输入回调地址')
    return
  }
  
  submitting.value = true
  try {
    if (isEdit.value) {
      await axios.put(`/api/webhooks/${currentId.value}`, form)
      ElMessage.success('更新成功')
    } else {
      await axios.post('/api/webhooks', form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchWebhooks()
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchWebhooks()
})
</script>

<style scoped>
.header-actions {
  display: flex;
  gap: 10px;
}
</style>
