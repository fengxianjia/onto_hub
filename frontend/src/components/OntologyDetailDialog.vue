<template>
  <Dialog v-model="visible" title="本体详情" width="90%">
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
        <div class="flex gap-4" style="height: 600px;">
          <!-- Left: File Tree -->
          <div class="w-1/3 border-r border-border pr-4 overflow-y-auto">
            <div v-if="loadingFiles" class="flex items-center justify-center py-8">
              <Loading />
            </div>
            <div v-else-if="fileTree">
              <FileTree :tree="fileTree" @select="handleFileSelect" />
            </div>
            <Empty v-else description="无文件数据" />
          </div>

          <!-- Right: File Content Preview -->
          <div class="flex-1 overflow-y-auto">
            <div v-if="!selectedFile" class="flex h-full items-center justify-center">
              <Empty description="请选择文件查看内容" />
            </div>
            <div v-else>
              <div class="mb-4 flex items-center justify-between border-b border-border pb-3">
                <h5 class="font-mono text-sm font-semibold">{{ selectedFile.name }}</h5>
                <Badge variant="default" size="sm">{{ (selectedFile.size / 1024).toFixed(2) }} KB</Badge>
              </div>

              <!-- Loading State -->
              <div v-if="loadingContent" class="flex items-center justify-center py-12">
                <Loading />
              </div>

              <!-- Markdown Rendering -->
              <div
                v-else-if="renderedMarkdown"
                class="markdown-body overflow-auto rounded-lg border border-border bg-white p-6"
                v-html="renderedMarkdown"
              ></div>

              <!-- Plain Text -->
              <pre
                v-else-if="fileContent"
                class="overflow-auto rounded-lg bg-muted p-4 text-xs"
              >{{ fileContent }}</pre>

              <!-- Error State -->
              <Empty v-else description="无法加载文件内容" />
            </div>
          </div>
        </div>
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
      <div v-else-if="activeTab === 'graph'" class="h-[600px] border rounded-lg bg-white overflow-hidden">
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
import MarkdownIt from 'markdown-it'
import 'github-markdown-css/github-markdown-light.css'
import { Dialog, Card, Badge, Button, Empty, Loading, RelationList } from './index.js'
import OntologyGraph from './OntologyGraph.vue'
import EntityList from './EntityList.vue'
import FileTree from './FileTree.vue'
import SubscriptionList from './SubscriptionList.vue'
import DeliveryStatusDialog from './DeliveryStatusDialog.vue'
import { message, showConfirm } from '../utils/message.js'

// Initialize Markdown renderer
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

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
const fileTree = ref(null)
const loadingFiles = ref(false)
const selectedFile = ref(null)
const fileContent = ref('')
const loadingContent = ref(false)
const deliveryDialogVisible = ref(false)
const currentPackageId = ref(null)

// Tabs
const tabs = [
  { label: '文件树', value: 'files' },
  { label: '知识图谱', value: 'graph' },
  { label: '实体列表', value: 'entities' },
  { label: '关系列表', value: 'relations' },
  { label: '订阅服务', value: 'subscriptions' }
]
const activeTab = ref('files')

const getStatusVariant = (status) => {
  const map = {
    'READY': 'success',
    'PENDING': 'warning',
    'PROCESSING': 'info',
    'ERROR': 'danger'
  }
  return map[status] || 'default'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Check if file is Markdown
const isMarkdownFile = (filename) => {
  return filename && filename.toLowerCase().endsWith('.md')
}

// Render Markdown content
const renderedMarkdown = computed(() => {
  if (!fileContent.value || !selectedFile.value) return ''
  if (!isMarkdownFile(selectedFile.value.name)) return ''
  return md.render(fileContent.value)
})

const fetchOntologyDetail = async () => {
  if (!props.ontologyId) return
  
  loading.value = true
  try {
    const res = await axios.get(`/api/ontologies/${props.ontologyId}`)
    ontology.value = res.data
    
    // 直接从 ontology.files 构建文件树
    if (res.data.files && res.data.files.length > 0) {
      fileTree.value = buildFileTreeFromList(res.data.files)
    } else {
      fileTree.value = null
    }
  } catch (error) {
    message.error('获取本体详情失败')
  } finally {
    loading.value = false
  }
}

// 从文件列表构建树结构
const buildFileTreeFromList = (files) => {
  const root = {}
  
  files.forEach(file => {
    const pathParts = file.file_path.split('/')
    let current = root
    
    pathParts.forEach((part, i) => {
      if (i === pathParts.length - 1) {
        // 这是文件
        if (!current._files) current._files = []
        current._files.push({
          name: part,
          path: file.file_path,
          type: 'file',
          size: file.file_size
        })
      } else {
        // 这是目录
        if (!current[part]) current[part] = {}
        current = current[part]
      }
    })
  })
  
  // 将字典转换为列表
  const dictToList = (node, path = '') => {
    const result = []
    
    Object.keys(node).forEach(key => {
      if (key === '_files') return
      
      const dirPath = path ? `${path}/${key}` : key
      result.push({
        name: key,
        path: dirPath,
        type: 'directory',
        children: dictToList(node[key], dirPath)
      })
    })
    
    if (node._files) {
      result.push(...node._files)
    }
    
    return result.sort((a, b) => {
      if (a.type !== b.type) return a.type === 'file' ? 1 : -1
      return a.name.localeCompare(b.name)
    })
  }
  
  return dictToList(root)
}

const handleFileSelect = async (file) => {
  if (file.type === 'directory') return
  
  selectedFile.value = file
  loadingContent.value = true
  fileContent.value = ''
  
  try {
    const res = await axios.get(`/api/ontologies/${props.ontologyId}/files`, {
      params: { path: file.path }
    })
    fileContent.value = res.data.content || '(无内容)'
  } catch (error) {
    fileContent.value = '加载失败'
    message.error('加载文件内容失败')
  } finally {
    loadingContent.value = false
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
    // Set package ID for dialog and show it immediately (or after success?)
    // User said: "clicking OK, it needs to pop up the push box to view progress"
    // So we show it here.
    currentPackageId.value = ontology.value.id
    
    await axios.post(`/api/ontologies/${ontology.value.id}/activate`)
    message.success(`版本 v${ontology.value.version} 已激活并触发推送`)
    
    // Show Progress Dialog
    deliveryDialogVisible.value = true
    
    // 刷新详情
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
    fileTree.value = null
    selectedFile.value = null
    fileContent.value = ''
  }
})
</script>
