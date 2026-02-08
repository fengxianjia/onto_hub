<template>
  <div class="space-y-8 animate-slideUp">
    <Card class="shadow-xl" variant="elevated">
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="text-2xl font-bold text-foreground">订阅管理 (Webhooks)</h3>
          <div class="flex gap-3">
            <Button variant="ghost" size="sm" @click="fetchWebhooks">
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </Button>
            <Button variant="primary" @click="handleAdd">新增订阅</Button>
          </div>
        </div>
      </template>

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-20">
        <Loading />
      </div>

      <!-- Empty State -->
      <div v-else-if="!tableData.length" class="py-12">
        <Empty description="暂无订阅数据" />
      </div>

      <!-- Table -->
      <div v-else class="overflow-x-auto rounded-lg">
        <table class="w-full">
          <thead class="bg-gradient-to-r from-muted/80 to-muted/40">
            <tr>
              <th class="px-6 py-3 text-left text-sm font-semibold text-foreground whitespace-nowrap">名称</th>
              <th class="px-6 py-3 text-left text-sm font-semibold text-foreground whitespace-nowrap">回调地址</th>
              <th class="px-6 py-3 text-left text-sm font-semibold text-foreground whitespace-nowrap">事件类型</th>
              <th class="px-6 py-3 text-left text-sm font-semibold text-foreground whitespace-nowrap">适用本体</th>
              <th class="px-6 py-3 text-left text-sm font-semibold text-foreground whitespace-nowrap">签名加固</th>
              <th class="px-6 py-3 text-left text-sm font-semibold text-foreground whitespace-nowrap">连通性</th>
              <th class="px-6 py-3 text-left text-sm font-semibold text-foreground whitespace-nowrap">创建时间</th>
              <th class="px-6 py-3 text-right text-sm font-semibold text-foreground whitespace-nowrap">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border">
            <tr v-for="(row, index) in tableData" :key="row.id" 
                :class="['transition-all duration-200 hover:bg-accent/5 hover:shadow-md', index % 2 === 0 ? 'bg-white' : 'bg-muted/20']">
              <td class="px-6 py-4 text-sm font-medium whitespace-nowrap">{{ row.name }}</td>
              <td class="px-6 py-4 text-sm text-muted-foreground max-w-xs truncate" :title="row.target_url">{{ row.target_url }}</td>
              <td class="px-6 py-4 whitespace-nowrap">
                <Badge variant="accent" size="sm">{{ row.event_type }}</Badge>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <Badge v-if="row.ontology_filter" variant="info" outline size="sm">{{ row.ontology_filter }}</Badge>
                <Badge v-else variant="default" size="sm">全局 (All)</Badge>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <Badge v-if="row.secret_token" variant="success" size="sm">已加固</Badge>
                <Badge v-else variant="default" outline size="sm">未加固</Badge>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                 <div class="flex items-center gap-2">
                    <div :class="['w-2 h-2 rounded-full', 
                      row.ping_status === 'SUCCESS' ? 'bg-green-500' : 
                      row.ping_status === 'WARNING' ? 'bg-yellow-500' : 
                      row.ping_status === 'FAILURE' ? 'bg-red-500' : 'bg-gray-300']">
                    </div>
                    <span v-if="row.ping_code" class="text-xs font-mono text-muted-foreground">{{ row.ping_code }}</span>
                    <span v-else class="text-xs text-muted-foreground">-</span>
                 </div>
              </td>
              <td class="px-6 py-4 text-sm text-muted-foreground whitespace-nowrap">{{ formatDate(row.created_at) }}</td>
              <td class="px-6 py-4 text-right whitespace-nowrap">
                <div class="flex justify-end gap-1">
                  <button title="测试连通性" @click="handlePing(row)" class="p-1.5 rounded-lg text-muted-foreground hover:bg-accent/10 hover:text-accent transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                  </button>
                  <button title="查看日志" @click="handleLogs(row)" class="p-1.5 rounded-lg text-muted-foreground hover:bg-accent/10 hover:text-accent transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                  </button>
                  <button title="编辑" @click="handleEdit(row)" class="p-1.5 rounded-lg text-muted-foreground hover:bg-accent/10 hover:text-accent transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                  </button>
                  <button title="删除" @click="handleDelete(row)" class="p-1.5 rounded-lg text-red-600 hover:bg-red-50 hover:text-red-700 transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Pagination -->
      <div v-if="tableData.length" class="mt-4 border-t pt-4">
        <Pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :disabled="loading"
          @change="handlePageChange"
          @update:page-size="handlePageChange"
        />
      </div>
    </Card>

    <!-- Create/Edit Dialog -->
    <Dialog v-model="dialogVisible" :title="isEdit ? '编辑订阅' : '新增订阅'" width="600px">
      <div class="space-y-6">
        <Input
          v-model="form.name"
          label="名称"
          placeholder="请输入订阅名称 (例如: 生产环境)"
          required
        />
        <Input
          v-model="form.target_url"
          label="回调地址"
          placeholder="http://your-service:8080/callback"
          required
        />
        <Select
          v-model="form.event_type"
          :options="eventTypeOptions"
          label="事件类型"
          placeholder="选择事件类型"
          required
        />
        <Select
          v-model="form.ontology_filter"
          :options="ontologyFilterOptions"
          label="指定本体"
          placeholder="默认为所有 (全局)"
          filterable
        />
        <div>
          <Input
            v-model="form.secret_token"
            type="password"
            label="签名密钥"
            placeholder="HMAC SHA256 密钥 (可选)"
          />
          <p class="mt-2 text-xs text-muted-foreground">如果设置,推送时会携带 X-Hub-Signature-256 请求头。</p>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <Button variant="secondary" @click="dialogVisible = false">取消</Button>
          <Button variant="primary" @click="handleSubmit" :loading="submitting">确定</Button>
        </div>
      </template>
    </Dialog>

    <!-- Webhook Log Drawer -->
    <WebhookLogDrawer 
      v-model="logDrawerVisible" 
      :webhook-id="currentWebhookId"
      :webhook-name="currentWebhookName"
      :logs-data="logsData" 
      :loading="logsLoading"
      :total="logsPagination.total"
      :current-page="logsPagination.currentPage"
      :page-size="logsPagination.pageSize"
      @refresh="fetchLogs"
      @page-change="fetchLogs"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import axios from 'axios'
import { Card, Button, Badge, Dialog, Input, Select, Loading, Empty, Pagination } from './index.js'
import WebhookLogDrawer from './WebhookLogDrawer.vue'
import { showMessage, showConfirm } from '../utils/message.js'

const emit = defineEmits(['change'])

const tableData = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const currentId = ref(null)

const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// 日志相关
const logDrawerVisible = ref(false)
const logsData = ref([])
const logsLoading = ref(false)
const currentWebhookId = ref(null)
const currentWebhookName = ref('')
const logsPagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

const form = reactive({
  name: '',
  target_url: '',
  event_type: 'ontology.activated',
  ontology_filter: '',
  secret_token: ''
})

const ontologyOptions = ref([])

const eventTypeOptions = [
  { label: 'ontology.activated', value: 'ontology.activated' }
]

const ontologyFilterOptions = computed(() => {
  return [
    { label: '所有本体 (默认)', value: '' },
    ...ontologyOptions.value
  ]
})

const fetchOntologyOptions = async () => {
  try {
    const res = await axios.get('/api/ontologies?all_versions=false') // Ensure we get unique codes effectively by listing active/latest
    // Map to Code + Name, ensure uniqueness by Code
    const uniqueMap = new Map()
    res.data.forEach(item => {
      if (!uniqueMap.has(item.code)) {
        uniqueMap.set(item.code, `${item.name} (${item.code})`)
      }
    })
    
    ontologyOptions.value = Array.from(uniqueMap.entries()).map(([code, label]) => ({ 
      label: label, 
      value: code 
    }))
  } catch (e) {
    console.error("Failed to fetch ontologies", e)
  }
}

const fetchWebhooks = async () => {
  loading.value = true
  try {
    const skip = (pagination.currentPage - 1) * pagination.pageSize
    const res = await axios.get('/api/webhooks', {
      params: {
        skip,
        limit: pagination.pageSize
      }
    })
    // Backend now returns { items: [], total: int }
    tableData.value = res.data.items
    pagination.total = res.data.total
    emit('change')
  } catch (error) {
    showMessage('获取订阅列表失败', 'error')
  } finally {
    loading.value = false
  }
}

const handlePageChange = () => {
  fetchWebhooks()
}

const handleAdd = () => {
  fetchOntologyOptions()
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

const handleDelete = async (row) => {
  try {
    await showConfirm('确定要删除该订阅吗?', '警告')
    
    await axios.delete(`/api/webhooks/${row.id}`)
    showMessage('删除成功', 'success')
    fetchWebhooks()
  } catch (error) {
    if (error !== 'cancel') {
      showMessage('删除失败', 'error')
    }
  }
}

const handleLogs = (row) => {
  currentWebhookId.value = row.id
  currentWebhookName.value = row.name
  logDrawerVisible.value = true
  logsData.value = []
  logsPagination.currentPage = 1
  logsPagination.total = 0
  fetchLogs()
}

const fetchLogs = async (filters = {}) => {
  if (!currentWebhookId.value) return
  
  if (filters.page) {
    logsPagination.currentPage = filters.page
    logsPagination.pageSize = filters.pageSize
    delete filters.page
    delete filters.pageSize
  }

  logsLoading.value = true
  try {
    const params = {}
    if (filters.ontology) params.ontology_name = filters.ontology
    if (filters.status) params.status = filters.status
    
    params.skip = (logsPagination.currentPage - 1) * logsPagination.pageSize
    params.limit = logsPagination.pageSize

    const res = await axios.get(`/api/webhooks/${currentWebhookId.value}/logs`, { params })
    logsData.value = res.data.items
    logsPagination.total = res.data.total
  } catch (e) {
    showMessage('获取日志失败', 'error')
  } finally {
    logsLoading.value = false
  }
}

const handlePing = async (row) => {
  showMessage('正在测试连通性...', 'info')
  try {
    const res = await axios.post(`/api/webhooks/${row.id}/ping`)
    const { response_status } = res.data
    
    if (response_status) {
      if (response_status >= 200 && response_status < 400) {
        row.ping_status = 'SUCCESS'
        row.ping_code = response_status
        showMessage(`测试成功 (HTTP ${response_status})`, 'success')
      } else if (response_status >= 400 && response_status < 500) {
        row.ping_status = 'WARNING'
        row.ping_code = response_status
        showMessage(`测试警告 (HTTP ${response_status})`, 'warning')
      } else {
        row.ping_status = 'FAILURE'
        row.ping_code = response_status
        showMessage(`测试失败 (HTTP ${response_status})`, 'error')
      }
    } else {
      row.ping_status = 'FAILURE'
      row.ping_code = 'Error'
      showMessage('测试失败 (无响应)', 'error')
    }
  } catch (error) {
    row.ping_status = 'FAILURE'
    row.ping_code = 'Error'
    showMessage('测试失败', 'error')
  }
}

const handleSubmit = async () => {
  if (!form.name || !form.target_url || !form.event_type) {
    showMessage('请填写必填项', 'warning')
    return
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      await axios.put(`/api/webhooks/${currentId.value}`, form)
      showMessage('更新成功', 'success')
    } else {
      await axios.post('/api/webhooks', form)
      showMessage('创建成功', 'success')
    }
    dialogVisible.value = false
    fetchWebhooks()
  } catch (error) {
    showMessage(isEdit.value ? '更新失败' : '创建失败', 'error')
  } finally {
    submitting.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchWebhooks()
})
</script>
