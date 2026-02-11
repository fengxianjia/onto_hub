<template>
  <Dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" size="lg">
    <template #header>
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-success/10 flex items-center justify-center">
          <svg class="w-6 h-6 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <div>
          <h3 class="text-xl font-bold">版本推送状态</h3>
          <p class="text-sm text-muted-foreground">{{ ontologyName }} v{{ version }}</p>
        </div>
      </div>
    </template>

    <div class="space-y-6">
      <!-- 推送进度概览 -->
      <div class="p-4 rounded-lg bg-muted/30 border border-border">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium">推送进度</span>
          <span class="text-sm text-muted-foreground">
            {{ completedCount }} / {{ totalCount }} 完成
          </span>
        </div>
        <div class="w-full bg-muted rounded-full h-2">
          <div 
            class="bg-accent h-2 rounded-full transition-all duration-300"
            :style="{ width: `${progressPercentage}%` }"
          ></div>
        </div>
        <div class="flex gap-4 mt-3 text-xs">
          <span class="text-success">✓ {{ successCount }} 成功</span>
          <span class="text-danger">✗ {{ failureCount }} 失败</span>
          <span class="text-muted-foreground">⟳ {{ pendingCount }} 进行中</span>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="flex justify-center py-8">
        <Loading />
      </div>

      <!-- 推送状态列表 -->
      <div v-else-if="pushStatus.length > 0" class="space-y-3 max-h-96 overflow-y-auto">
        <div
          v-for="(item, index) in pushStatus"
          :key="index"
          class="p-4 rounded-lg border transition-all"
          :class="getStatusBorderClass(item.status)"
        >
          <div class="flex items-start gap-3">
            <!-- 状态图标 -->
            <div class="flex-shrink-0 mt-1">
              <div v-if="item.status === 'SUCCESS'" 
                   class="w-6 h-6 rounded-full bg-success/10 flex items-center justify-center">
                <svg class="w-4 h-4 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div v-else-if="item.status === 'FAILURE'" 
                   class="w-6 h-6 rounded-full bg-danger/10 flex items-center justify-center">
                <svg class="w-4 h-4 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <div v-else 
                   class="w-6 h-6 rounded-full bg-muted flex items-center justify-center">
                <svg class="w-4 h-4 text-muted-foreground animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
            </div>

            <!-- 服务信息 -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between mb-1">
                <h4 class="font-medium truncate">{{ item.webhook_name || '未命名服务' }}</h4>
                <Badge 
                  :variant="getStatusVariant(item.status)" 
                  size="sm"
                >
                  {{ getStatusText(item.status) }}
                </Badge>
              </div>
              
              <p class="text-sm text-muted-foreground truncate mb-2" :title="item.target_url">
                {{ item.target_url }}
              </p>

              <!-- 成功信息 -->
              <div v-if="item.status === 'SUCCESS'" class="text-xs text-success">
                <span v-if="item.delivered_at">
                  推送成功 • {{ formatTime(item.delivered_at) }}
                </span>
                <span v-if="item.response_status">
                  • HTTP {{ item.response_status }}
                </span>
              </div>

              <!-- 失败信息 -->
              <div v-else-if="item.status === 'FAILURE'" class="space-y-2">
                <p class="text-xs text-danger">
                  {{ item.error_message || '推送失败' }}
                </p>
                <Button 
                  variant="outline" 
                  size="sm"
                  @click="retryPush(item.webhook_id)"
                >
                  重试推送
                </Button>
              </div>

              <!-- 进行中 -->
              <div v-else class="text-xs text-muted-foreground">
                正在推送...
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="text-center py-8">
        <Empty description="暂无订阅服务" />
      </div>
    </div>

    <template #footer>
      <div class="flex justify-between items-center">
        <span class="text-sm text-muted-foreground">
          {{ isPolling ? '自动刷新中...' : '推送已完成' }}
        </span>
        <div class="flex gap-2">
          <Button variant="outline" @click="fetchPushStatus">刷新</Button>
          <Button variant="primary" @click="$emit('update:modelValue', false)">关闭</Button>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import axios from 'axios'
import { Dialog, Badge, Button, Loading, Empty } from './index.js'
import { showMessage } from '../utils/message.js'

const props = defineProps({
  modelValue: Boolean,
  packageId: String,
  ontologyCode: String,
  ontologyName: String,
  version: String
})

const emit = defineEmits(['update:modelValue'])

// 状态管理
const pushStatus = ref([])
const loading = ref(false)
const isPolling = ref(false)
let pollingInterval = null

// 统计数据
const totalCount = computed(() => pushStatus.value.length)
const successCount = computed(() => pushStatus.value.filter(s => s.status === 'SUCCESS').length)
const failureCount = computed(() => pushStatus.value.filter(s => s.status === 'FAILURE').length)
const pendingCount = computed(() => pushStatus.value.filter(s => s.status === 'PENDING').length)
const completedCount = computed(() => successCount.value + failureCount.value)
const progressPercentage = computed(() => 
  totalCount.value > 0 ? (completedCount.value / totalCount.value) * 100 : 0
)

// 获取推送状态
const fetchPushStatus = async (isInitial = false) => {
  if (!props.packageId) return
  
  try {
    // 只在首次加载时显示 loading
    if (isInitial) {
      loading.value = true
    }
    // 使用后端已有的 API: /api/webhooks/deliveries/{id}
    const res = await axios.get(`/api/webhooks/deliveries/${props.packageId}`)
    pushStatus.value = res.data
  } catch (e) {
    console.error('获取推送状态失败:', e)
    if (isInitial) {
      showMessage.error('获取推送状态失败')
    }
  } finally {
    if (isInitial) {
      loading.value = false
    }
  }
}

// 开始轮询
const startPolling = () => {
  if (isPolling.value) return
  
  isPolling.value = true
  fetchPushStatus(true) // 首次加载显示 loading
  
  pollingInterval = setInterval(() => {
    fetchPushStatus(false) // 轮询时不显示 loading
  }, 2000) // 每2秒刷新一次
}

// 停止轮询
const stopPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
  isPolling.value = false
}

// 重试推送 - 使用激活接口
const retryPush = async (webhookId) => {
  try {
    // 重新激活当前版本,会自动触发推送
    await axios.post(`/api/ontologies/${props.packageId}/activate`)
    showMessage.success('重新推送已触发')
    fetchPushStatus()
  } catch (e) {
    showMessage.error('触发推送失败')
  }
}

// 格式化时间
const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z')
  const now = new Date()
  const diff = Math.floor((now - date) / 1000)
  
  if (diff < 60) return `${diff}秒前`
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  return `${Math.floor(diff / 86400)}天前`
}

// 获取状态样式
const getStatusBorderClass = (status) => {
  switch (status) {
    case 'SUCCESS': return 'border-success/30 bg-success/5'
    case 'FAILURE': return 'border-danger/30 bg-danger/5'
    default: return 'border-border'
  }
}

const getStatusVariant = (status) => {
  switch (status) {
    case 'SUCCESS': return 'success'
    case 'FAILURE': return 'danger'
    default: return 'default'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'SUCCESS': return '成功'
    case 'FAILURE': return '失败'
    default: return '推送中'
  }
}

// 监听对话框打开
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    startPolling()
  } else {
    stopPolling()
  }
})

// 监听推送状态,所有完成后停止轮询
watch(pushStatus, (status) => {
  if (status.length === 0) return
  
  const allCompleted = status.every(s => 
    s.status === 'SUCCESS' || s.status === 'FAILURE'
  )
  
  if (allCompleted && isPolling.value) {
    stopPolling()
  }
}, { deep: true })

// 组件卸载时清理
onUnmounted(() => {
  stopPolling()
})
</script>
