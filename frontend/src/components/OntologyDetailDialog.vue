<template>
  <Dialog v-model="visible" title="本体详情" size="xl">
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <Loading />
    </div>

    <!-- Content -->
    <div v-else-if="ontology" class="space-y-6">
      <!-- Metadata Header -->
      <div class="mb-2">
        <div class="flex items-center gap-3 mb-2">
          <h2 class="text-2xl font-bold text-foreground">{{ ontology.name }}</h2>
          <Badge variant="outline" class="font-mono text-xs">{{ ontology.code }}</Badge>
          <Badge variant="accent">v{{ ontology.version }}</Badge>
          <Badge v-if="ontology.status !== 'READY'" :variant="getStatusVariant(ontology.status)">{{ ontology.status }}</Badge>
        </div>
        
        <div class="flex items-center gap-4 text-sm text-muted-foreground">
          <div class="flex items-center gap-1.5">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>上传于 {{ formatDate(ontology.upload_time) }}</span>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="border-b border-border mt-6">
        <div class="flex gap-6">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            @click="activeTab = tab.value"
            :class="[
              'px-4 py-3 text-sm font-medium transition-all border-b-2',
              activeTab === tab.value
                ? 'border-accent text-accent'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            ]"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>

      <!-- Tab Content: File Browser -->
      <Card v-if="activeTab === 'files'" variant="default">
        <template #header>
          <h4 class="text-lg font-bold">文件浏览器</h4>
        </template>
        <FileBrowser :ontology-id="ontology.id" :files="ontology.files" />
      </Card>

      <!-- Tab Content: Subscriptions -->
      <Card v-else-if="activeTab === 'subscriptions'" variant="default">
        <SubscriptionList 
          :ontology-code="ontology.code"
          :ontology-name="ontology.name"
          :current-version="ontology.version"
          :package-id="ontology.id"
        />
      </Card>

      <!-- Tab Content: Graph -->
      <div v-else-if="activeTab === 'graph'" class="h-[72vh] border rounded-lg bg-white overflow-hidden">
        <OntologyGraph :ontology-id="ontology.id" />
      </div>

      <!-- Tab Content: Entities -->
      <Card v-else-if="activeTab === 'entities'" variant="default">
         <EntityList :ontology-id="ontology.id" />
      </Card>

      <!-- Tab Content: Relations -->
      <Card v-else-if="activeTab === 'relations'" variant="default">
         <RelationList :ontology-id="ontology.id" />
      </Card>

      <!-- Tab Content: Settings -->
      <Card v-else-if="activeTab === 'settings'" variant="default">
        <template #header>
          <div class="flex items-center gap-2">
            <svg class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <h4 class="text-lg font-bold">配置与管理</h4>
          </div>
        </template>
        <OntologySettings :ontology="ontology" @refresh="fetchOntologyDetail" @switchToTab="t => activeTab = t" />
      </Card>
    </div>

    <template #footer>
      <div class="flex justify-end gap-3">
        <Button variant="secondary" @click="visible = false">关闭</Button>
        <Button 
          v-if="ontology && !ontology.is_active" 
          variant="primary" 
          @click="handleActivate"
          :loading="activating"
        >
          切换至此版本
        </Button>
        <Button variant="outline" @click="handleViewHistory">版本历史</Button>
      </div>
    </template>

    <DeliveryStatusDialog 
      v-model="deliveryDialogVisible" 
      :package-id="currentPackageId" 
    />
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { 
  Dialog, Badge, Button, Card, Loading, 
  RelationList, FileBrowser, OntologySettings 
} from './index.js'
import OntologyGraph from './OntologyGraph.vue'
import EntityList from './EntityList.vue'
import SubscriptionList from './SubscriptionList.vue'
import DeliveryStatusDialog from './DeliveryStatusDialog.vue'
import { message, showConfirm } from '../utils/message.js'
import { formatDate } from '../utils/format.js'
import { getStatusVariant } from '../utils/ontology.js'

const props = defineProps({
  modelValue: Boolean,
  ontologyId: [String, Number]
})

const emit = defineEmits(['update:modelValue', 'viewHistory', 'refresh'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const ontology = ref(null)
const loading = ref(false)
const deliveryDialogVisible = ref(false)
const currentPackageId = ref(null)

// Tabs
const tabs = [
  { label: '文件树', value: 'files' },
  { label: '知识图谱', value: 'graph' },
  { label: '实体列表', value: 'entities' },
  { label: '关系列表', value: 'relations' },
  { label: '订阅服务', value: 'subscriptions' },
  { label: '管理设置', value: 'settings' }
]
const activeTab = ref('files')

const fetchOntologyDetail = async () => {
  if (!props.ontologyId) return
  
  loading.value = true
  try {
    const res = await axios.get(`/api/ontologies/${props.ontologyId}`)
    ontology.value = res.data
  } catch (error) {
    message.error('获取本体详情失败')
  } finally {
    loading.value = false
  }
}

const handleViewHistory = () => {
  emit('viewHistory', ontology.value)
  visible.value = false
}

const activating = ref(false)

const handleActivate = async () => {
  if (!ontology.value) return
  
  try {
    const isRepush = ontology.value.is_active
    const title = isRepush ? '重新推送确认' : '切换版本确认'
    const confirmText = isRepush ? '确定重新推送' : '确定切换'
    
    await showConfirm(
      `确定要${isRepush ? '重新推送' : '切换到'}版本 v${ontology.value.version} 吗？\n\n${isRepush ? '重新推送' : '切换'}后，所有订阅此本体的服务均会收到${isRepush ? '当前' : '被切换'}版本（v${ontology.value.version}）的推送。`,
      title,
      { confirmButtonText: confirmText, cancelButtonText: '取消' }
    )
    
    activating.value = true
    currentPackageId.value = ontology.value.id
    
    await axios.post(`/api/ontologies/${ontology.value.id}/activate`)
    message.success(`版本 v${ontology.value.version} 已激活并触发推送`)
    
    deliveryDialogVisible.value = true
    
    await fetchOntologyDetail()
    emit('refresh')
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
      message.error(e.response?.data?.detail || '激活失败')
    }
  } finally {
    activating.value = false
  }
}

watch(() => props.modelValue, (newVal) => {
  if (newVal && props.ontologyId) {
    fetchOntologyDetail()
  } else {
    ontology.value = null
  }
})
</script>
