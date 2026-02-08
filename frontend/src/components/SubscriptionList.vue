<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-bold">订阅服务</h3>
        <p class="text-sm text-muted-foreground">
          {{ subscriptions.length }} 个服务订阅了此本体
        </p>
      </div>
      <Button variant="outline" size="sm" @click="fetchSubscriptions(true)" :disabled="refreshing">
        <svg v-if="!refreshing" class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <svg v-else class="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        {{ refreshing ? '刷新中...' : '刷新' }}
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center py-12">
      <Loading />
    </div>

    <!-- Empty State -->
    <div v-else-if="subscriptions.length === 0" class="text-center py-12">
      <Empty description="暂无订阅服务" />
    </div>

    <!-- Subscription List -->
    <div v-else class="space-y-3">
      <div
        v-for="(sub, index) in subscriptions"
        :key="index"
        class="p-4 rounded-lg border border-border hover:border-accent/50 transition-all"
      >
        <div class="flex items-start justify-between">
          <!-- Service Info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-2">
              <h4 class="font-medium truncate">{{ sub.webhook_name || '未命名服务' }}</h4>
              <Badge v-if="sub.is_global" variant="info" size="sm">全局订阅</Badge>
            </div>
            
            <p class="text-sm text-muted-foreground truncate mb-3" :title="sub.target_url">
              {{ sub.target_url }}
            </p>

            <!-- Version Info -->
            <div class="flex items-center gap-4 text-sm">
              <div v-if="sub.latest_success_version">
                <span class="text-muted-foreground">当前版本:</span>
                <Badge variant="accent" size="sm" class="ml-2">
                  v{{ sub.latest_success_version }}
                </Badge>
                <!-- Version Mismatch Warning -->
                <Badge 
                  v-if="currentVersion && sub.latest_success_version != currentVersion" 
                  variant="warning" 
                  size="sm" 
                  class="ml-2"
                >
                  非当前版本 (v{{ currentVersion }})
                </Badge>
              </div>
              <div v-else>
                <span class="text-muted-foreground">尚未推送</span>
              </div>
              
              <div v-if="sub.delivered_at" class="text-muted-foreground">
                {{ formatTime(sub.delivered_at) }}
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div v-if="!readonly" class="flex flex-col gap-2 ml-4">
            <Button
              variant="outline"
              size="sm"
              @click="manualPush(sub)"
              :disabled="pushing === sub.webhook_id"
            >
              <svg v-if="pushing === sub.webhook_id" class="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ pushing === sub.webhook_id ? '推送中...' : '手动推送' }}
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              @click="viewHistory(sub.webhook_id)"
            >
              推送历史
            </Button>
          </div>
          
          <!-- Readonly Status Actions? Or just nothing -->
           <div v-else class="flex flex-col gap-2 ml-4">
             <!-- Maybe show history button even in readonly? User said "View Subscription Status", so history might be useful. 
                  But prompt says "readonly... hide action buttons (Manual Push)". 
                  Let's keep History button if possible, or just hide all for now to be safe.
                  User said "not operable" (不可操作).
             -->
           </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { Button, Badge, Loading, Empty } from './index.js'
import { message, showConfirm } from '../utils/message.js'

const props = defineProps({
  ontologyCode: String,
  ontologyName: String,
  currentVersion: [String, Number],
  packageId: String,
  readonly: Boolean
})

const subscriptions = ref([])
const loading = ref(false)
const refreshing = ref(false)
const pushing = ref(null)

// 获取订阅列表
// 使用 /api/ontologies/{code}/subscriptions
// 该接口会查询:
// 1. 全局订阅 (ontology_filter 为空的 webhook)
// 2. 指定本体的订阅 (ontology_filter 匹配 name 或 code)
const fetchSubscriptions = async (isRefresh = false) => {
  if (!props.ontologyCode) return
  
  try {
    if (isRefresh) {
      refreshing.value = true
    } else {
      loading.value = true
    }
    const res = await axios.get(`/api/ontologies/by-code/${props.ontologyCode}/subscriptions`)
    subscriptions.value = res.data
  } catch (e) {
    console.error('获取订阅列表失败:', e)
    message.error('获取订阅列表失败')
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

// 手动推送 - 使用激活接口重新激活最新版本
const manualPush = async (sub) => {
  const webhookId = sub.webhook_id
  try {
    pushing.value = webhookId
    let targetPackageId = props.packageId
    let targetVersion = props.currentVersion

    if (!targetPackageId) {
      // 如果没有传递具体包ID，则默认获取最新版本 (兼容旧逻辑)
      const packages = await axios.get(`/api/ontologies`, {
        params: { code: props.ontologyCode, limit: 1 }
      })
      
      if (packages.data && packages.data.length > 0) {
        targetPackageId = packages.data[0].id
        targetVersion = packages.data[0].version
      }
    }
    
    if (targetPackageId) {
      // 确认对话框
      const webhookName = sub.webhook_name || '未命名服务'
      try {
        await showConfirm(
          `确定要将版本 (v${targetVersion}) 推送到 [${webhookName}] 吗？`, 
          '推送确认',
          { confirmButtonText: '确定推送' }
        )
      } catch {
        pushing.value = null
        return
      }

      // 使用新的手动推送接口, 同步等待结果
      const pushRes = await axios.post(`/api/ontologies/${targetPackageId}/push`, null, {
        params: { webhook_id: webhookId }
      })
      
      const result = pushRes.data.delivery_result
      if (result && result.status === 'SUCCESS') {
        message.success(`推送成功 (HTTP ${result.response_status})`)
      } else {
        const errorMsg = result?.error_message || '未知错误'
        message.error(`推送失败: ${errorMsg}`)
      }
      
      // 延迟刷新以更新列表状态
      setTimeout(() => fetchSubscriptions(true), 1000)
    } else {
      message.error('未找到本体版本')
    }
  } catch (e) {
    if (e === 'cancel') return
    console.error('触发推送失败:', e)
    message.error(e.response?.data?.detail || '触发推送失败')
  } finally {
    pushing.value = null
  }
}

// 查看推送历史
const viewHistory = (webhookId) => {
  // TODO: 实现推送历史查看功能
  message.info('推送历史功能开发中')
}

// 格式化时间
const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z')
  const now = new Date()
  const diff = Math.floor((now - date) / 1000)
  
  if (diff < 60) return `${diff}秒前推送`
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前推送`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前推送`
  return `${Math.floor(diff / 86400)}天前推送`
}

watch(() => props.ontologyCode, (newVal) => {
  if (newVal) {
    fetchSubscriptions()
  }
}, { immediate: true })
</script>
