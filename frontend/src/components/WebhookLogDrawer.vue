<template>
  <Drawer v-model="visible" :title="drawerTitle" size="50%">
    <!-- Filters & Actions Toolbar -->
    <div class="mb-4 flex items-center justify-between gap-4">
      <div class="flex flex-1 items-center gap-4">
        <div v-if="showOntologyFilter" class="w-64">
          <Input 
            v-model="filters.ontology" 
            placeholder="搜索本体编码 (例如: eco)" 
            @keyup.enter="handleRefresh"
          >
            <template #prefix>
              <svg class="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            </template>
          </Input>
        </div>
        <div class="w-40">
          <Select 
            v-model="filters.status" 
            :options="statusOptions" 
            placeholder="状态筛选" 
            allow-clear
            @update:modelValue="handleRefresh"
          />
        </div>
      </div>
      
      <div class="flex items-center">
        <Button variant="ghost" size="sm" @click="handleRefresh" title="刷新列表">
          <svg class="h-5 w-5 text-muted-foreground hover:text-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </Button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <Loading />
    </div>

    <!-- Empty State -->
    <div v-else-if="!logsData.length" class="py-12">
      <Empty description="暂无日志数据" />
    </div>

    <!-- Table -->
    <div v-else class="overflow-x-auto rounded-lg">
      <table class="w-full">
        <thead class="bg-gradient-to-r from-muted/80 to-muted/40">
          <tr>
            <th class="px-6 py-3 text-left text-sm font-bold text-foreground whitespace-nowrap">时间</th>
            <!-- Subscription Name column removed -->
            <th class="px-6 py-3 text-left text-sm font-bold text-foreground whitespace-nowrap">本体</th>
            <th class="px-6 py-3 text-left text-sm font-bold text-foreground whitespace-nowrap">版本</th>
            <th class="px-6 py-3 text-left text-sm font-bold text-foreground whitespace-nowrap">结果</th>
            <th class="px-6 py-3 text-left text-sm font-bold text-foreground whitespace-nowrap">Code</th>
            <th class="px-6 py-3 text-left text-sm font-bold text-foreground whitespace-nowrap">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border">
          <tr v-for="(row, index) in logsData" :key="index" 
              :class="['transition-all duration-200 hover:bg-accent/5', index % 2 === 0 ? 'bg-white' : 'bg-muted/20']">
            <td class="px-6 py-4 text-sm text-muted-foreground whitespace-nowrap">{{ formatDate(row.created_at) }}</td>
            <!-- Subscription Name cell removed -->
            <td class="px-6 py-4 text-sm font-medium whitespace-nowrap">
              <div v-if="row.ontology_name" class="flex flex-col">
                <span>{{ row.ontology_name }}</span>
                <span class="text-[10px] text-muted-foreground font-mono opacity-60">{{ row.ontology_code }}</span>
              </div>
              <span v-else class="font-mono text-muted-foreground">{{ row.ontology_code || '-' }}</span>
            </td>
            <td class="px-6 py-4">
              <Badge v-if="getOntologyVersion(row.payload)" variant="info" outline>v{{ getOntologyVersion(row.payload) }}</Badge>
              <span v-else class="text-muted-foreground">-</span>
            </td>
            <td class="px-6 py-4">
              <Badge :variant="row.status === 'SUCCESS' ? 'success' : 'danger'">{{ row.status }}</Badge>
            </td>
            <td class="px-6 py-4 text-sm">{{ row.response_status || '-' }}</td>
            <td class="px-6 py-4">
              <Button variant="link" size="sm" @click="showDetail(row)" class="h-auto p-0 text-accent hover:underline">
                查看
              </Button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <template #footer>
      <div class="flex justify-center w-full">
        <Pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          :disabled="loading"
          @change="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </div>
    </template>

    <!-- Detail Dialog -->
    <Dialog v-model="detailVisible" title="日志详情" width="600px">
      <div class="space-y-4">
        <div v-if="selectedLog?.error_message" class="rounded-lg bg-red-50 p-4">
          <p class="text-sm font-bold text-red-700">错误信息:</p>
          <p class="mt-2 text-sm text-red-600">{{ selectedLog.error_message }}</p>
        </div>
        <div v-if="selectedLog?.payload">
          <p class="text-sm font-bold text-foreground">推送内容 (Payload):</p>
          <pre class="mt-2 max-h-96 overflow-auto rounded-lg bg-muted p-4 text-xs">{{ formatJson(selectedLog.payload) }}</pre>
        </div>
      </div>
    </Dialog>
  </Drawer>
</template>

<script setup>
import { computed, ref, reactive, watch } from 'vue'
import { Drawer, Button, Badge, Dialog, Loading, Empty, Input, Select, Pagination } from './index.js'

const props = defineProps({
  modelValue: Boolean,
  webhookId: [String, Number],
  webhookName: String,
  logsData: Array,
  loading: Boolean,
  showOntologyFilter: {
    type: Boolean,
    default: true
  },
  total: {
    type: Number,
    default: 0
  },
  currentPage: {
    type: Number,
    default: 1
  },
  pageSize: {
    type: Number,
    default: 10
  }
})

const emit = defineEmits(['update:modelValue', 'refresh', 'page-change'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const drawerTitle = computed(() => {
  if (props.webhookName) {
    return `执行日志 - ${props.webhookName}`
  }
  return '执行日志 (Webhook Logs)'
})

const detailVisible = ref(false)
const selectedLog = ref(null)

const filters = reactive({
  ontology: '',
  status: ''
})

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '成功 (SUCCESS)', value: 'SUCCESS' },
  { label: '失败 (FAILURE)', value: 'FAILURE' }
]

const handleRefresh = () => {
  emit('refresh', { ...filters })
}

const handlePageChange = (page) => {
  emit('page-change', { page, pageSize: props.pageSize })
}

const handlePageSizeChange = (size) => {
    emit('page-change', { page: 1, pageSize: size })
}

// Reset filters when drawer closes or webhookId changes
watch(() => props.modelValue, (val) => {
  if (val) {
    filters.ontology = ''
    filters.status = ''
  }
})

const showDetail = (log) => {
  selectedLog.value = log
  detailVisible.value = true
}

const getOntologyVersion = (payloadStr) => {
  if (!payloadStr) return null
  try {
    const data = JSON.parse(payloadStr)
    return data.version || null
  } catch (e) {
    return null
  }
}

const formatJson = (jsonStr) => {
  if (!jsonStr) return ''
  try {
    const obj = JSON.parse(jsonStr)
    return JSON.stringify(obj, null, 2)
  } catch (e) {
    return jsonStr
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z')
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
</script>
