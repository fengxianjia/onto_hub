<template>
  <Drawer v-model="visible" title="执行日志 (Webhook Logs)" size="50%">
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
            <th class="px-6 py-3 text-left text-sm font-bold text-foreground">时间</th>
            <th class="px-6 py-3 text-left text-sm font-bold text-foreground">订阅名称</th>
            <th class="px-6 py-3 text-left text-sm font-bold text-foreground">版本</th>
            <th class="px-6 py-3 text-left text-sm font-bold text-foreground">结果</th>
            <th class="px-6 py-3 text-left text-sm font-bold text-foreground">Code</th>
            <th class="px-6 py-3 text-left text-sm font-bold text-foreground">详情</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border">
          <tr v-for="(row, index) in logsData" :key="index" 
              :class="['transition-all duration-200 hover:bg-accent/5', index % 2 === 0 ? 'bg-white' : 'bg-muted/20']">
            <td class="px-6 py-4 text-sm text-muted-foreground">{{ formatDate(row.created_at) }}</td>
            <td class="px-6 py-4 text-sm">{{ row.webhook_name }}</td>
            <td class="px-6 py-4">
              <Badge v-if="getOntologyVersion(row.payload)" variant="info" outline>v{{ getOntologyVersion(row.payload) }}</Badge>
              <span v-else class="text-muted-foreground">-</span>
            </td>
            <td class="px-6 py-4">
              <Badge :variant="row.status === 'SUCCESS' ? 'success' : 'danger'">{{ row.status }}</Badge>
            </td>
            <td class="px-6 py-4 text-sm">{{ row.response_status || '-' }}</td>
            <td class="px-6 py-4">
              <Button variant="ghost" size="sm" @click="showDetail(row)">
                {{ row.status === 'SUCCESS' ? '查看详情' : '查看错误' }}
              </Button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <template #footer>
      <div class="flex justify-center">
        <Button variant="ghost" @click="$emit('refresh')">
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </Button>
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
import { computed, ref } from 'vue'
import { Drawer, Button, Badge, Dialog, Loading, Empty } from './index.js'

const props = defineProps({
  modelValue: Boolean,
  webhookId: [String, Number],
  logsData: Array,
  loading: Boolean
})

const emit = defineEmits(['update:modelValue', 'refresh'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const detailVisible = ref(false)
const selectedLog = ref(null)

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
