<template>
  <el-dialog
    v-model="visible"
    title="Webhook 推送状态"
    width="600px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="3" animated />
    </div>
    
    <div v-else>
      <div v-if="deliveries.length === 0" class="empty-state">
        <el-empty description="没有配置相关的 Webhook 订阅" image-size="60" />
      </div>
      
      <el-table v-else :data="deliveries" style="width: 100%">
        <el-table-column prop="target_url" label="目标 URL" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="response_status" label="Code" width="80">
           <template #default="scope">
               <span v-if="scope.row.response_status">{{ scope.row.response_status }}</span>
               <span v-else>-</span>
           </template>
        </el-table-column>
        <el-table-column label="详情" width="80">
           <template #default="scope">
             <el-tooltip 
                v-if="scope.row.error_message" 
                class="box-item" 
                effect="dark" 
                :content="scope.row.error_message" 
                placement="top"
             >
                <el-icon color="red"><Warning /></el-icon>
             </el-tooltip>
             <span v-else>-</span>
           </template>
        </el-table-column>
      </el-table>
      
      <div class="progress-footer">
          <span v-if="isPolling">
             <el-icon class="is-loading"><Loading /></el-icon> 正在等待推送结果...
          </span>
          <span v-else-if="allFinished">
             推送完成
          </span>
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="closeConfig">关闭</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed, onUnmounted } from 'vue'
import axios from 'axios'
import { Warning, Loading } from '@element-plus/icons-vue'

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
    // If any item is PENDING, we are polling (or should be)
    return deliveries.value.some(d => d.status === 'PENDING')
})

const allFinished = computed(() => {
    return deliveries.value.length > 0 && !isPolling.value
})

const getStatusType = (status) => {
  if (status === 'SUCCESS') return 'success'
  if (status === 'FAILURE') return 'danger'
  return 'info' // PENDING
}

const getStatusText = (status) => {
  if (status === 'SUCCESS') return '成功'
  if (status === 'FAILURE') return '失败'
  return '等待中'
}

const fetchStatus = async () => {
    if (!props.packageId) return
    try {
        const res = await axios.get(`/api/ontologies/${props.packageId}/deliveries`)
        deliveries.value = res.data
        
        // Check if we should stop polling
        const hasPending = res.data.some(d => d.status === 'PENDING')
        if (!hasPending && timer.value) {
            clearInterval(timer.value)
            timer.value = null
        }
    } catch (e) {
        console.error("Failed to fetch delivery status", e)
    }
}

watch(() => props.modelValue, (val) => {
    if (val && props.packageId) {
        loading.value = true
        deliveries.value = []
        // Initial fetch
        fetchStatus().then(() => {
            loading.value = false
            // Start polling if needed
            if (isPolling.value) {
                timer.value = setInterval(fetchStatus, 2000)
            }
        })
    } else {
        if (timer.value) {
            clearInterval(timer.value)
            timer.value = null
        }
    }
})

onUnmounted(() => {
    if (timer.value) clearInterval(timer.value)
})

const closeConfig = () => {
  visible.value = false
}
</script>

<style scoped>
.loading-state {
    padding: 20px;
}
.empty-state {
    padding: 20px;
}
.progress-footer {
    margin-top: 15px;
    text-align: right;
    color: #909399;
    font-size: 13px;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 5px;
}
</style>
