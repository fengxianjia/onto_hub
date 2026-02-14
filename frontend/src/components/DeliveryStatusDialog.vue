<template>
  <Dialog 
    v-model="visible" 
    title="Webhook 推送状态" 
    width="700px"
    :close-on-click-modal="false"
  >
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <Loading />
    </div>

    <!-- Empty State -->
    <div v-else-if="!deliveries.length" class="py-12">
      <Empty description="没有配置相关的 Webhook 订阅" />
    </div>

    <!-- Table -->
    <div v-else>
      <div class="overflow-x-auto rounded-lg">
        <table class="w-full">
          <thead class="bg-gradient-to-r from-muted/80 to-muted/40">
            <tr>
              <th class="px-6 py-3 text-left text-sm font-bold text-foreground">目标 URL</th>
              <th class="px-6 py-3 text-left text-sm font-bold text-foreground">状态</th>
              <th class="px-6 py-3 text-left text-sm font-bold text-foreground">Code</th>
              <th class="px-6 py-3 text-left text-sm font-bold text-foreground">详情</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border">
            <tr v-for="(row, index) in deliveries" :key="index" 
                :class="['transition-all duration-200 hover:bg-accent/5', index % 2 === 0 ? 'bg-white' : 'bg-muted/20']">
              <td class="px-6 py-4 text-sm max-w-xs truncate">{{ row.target_url }}</td>
              <td class="px-6 py-4">
                <Badge :variant="getStatusVariant(row.status)">{{ getStatusText(row.status) }}</Badge>
              </td>
              <td class="px-6 py-4 text-sm">{{ row.response_status || '-' }}</td>
              <td class="px-6 py-4">
                <div v-if="row.error_message" class="flex items-center gap-2 text-red-500">
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span class="text-xs">{{ row.error_message }}</span>
                </div>
                <span v-else class="text-muted-foreground">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Progress Footer -->
      <div class="mt-6 flex items-center justify-center gap-2 text-sm text-muted-foreground">
        <div v-if="isPolling" class="flex items-center gap-2">
          <div class="h-4 w-4 animate-spin rounded-full border-2 border-accent border-t-transparent"></div>
          <span>正在等待推送结果...</span>
        </div>
        <div v-else-if="allFinished" class="flex items-center gap-2 text-green-600">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span class="font-medium">推送完成</span>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end">
        <Button variant="secondary" @click="closeConfig">关闭</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, watch, computed, onUnmounted } from 'vue'
import { getDeliveries } from '../api/webhooks.js'
import { Dialog, Button, Badge, Loading, Empty } from './index.js'

const props = defineProps({
  modelValue: Boolean,
  packageId: String
})

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const deliveries = ref([])
const loading = ref(false)
const timer = ref(null)

const isPolling = computed(() => {
  return deliveries.value.some(d => d.status === 'PENDING')
})

const allFinished = computed(() => {
  return deliveries.value.length > 0 && !isPolling.value
})

const getStatusVariant = (status) => {
  if (status === 'SUCCESS') return 'success'
  if (status === 'FAILURE') return 'danger'
  return 'info' // PENDING
}

const getStatusText = (status) => {
  const statusMap = {
    'SUCCESS': '成功',
    'FAILURE': '失败',
    'PENDING': '等待中'
  }
  return statusMap[status] || status
}

const fetchDeliveries = async () => {
  if (!props.packageId) return
  
  try {
    const res = await getDeliveries(props.packageId)
    deliveries.value = res.data
    
    if (isPolling.value) {
      timer.value = setTimeout(fetchDeliveries, 2000)
    }
  } catch (error) {
    console.error('Failed to fetch deliveries', error)
  }
}

const closeConfig = () => {
  if (timer.value) {
    clearTimeout(timer.value)
    timer.value = null
  }
  visible.value = false
}

watch(() => props.modelValue, (newVal) => {
  if (newVal && props.packageId) {
    loading.value = true
    deliveries.value = []
    fetchDeliveries().finally(() => {
      loading.value = false
    })
  } else {
    if (timer.value) {
      clearTimeout(timer.value)
      timer.value = null
    }
  }
})

onUnmounted(() => {
  if (timer.value) {
    clearTimeout(timer.value)
  }
})
</script>
