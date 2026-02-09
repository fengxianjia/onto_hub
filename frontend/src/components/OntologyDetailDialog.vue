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
        <div class="flex gap-4" style="height: 72vh;">
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

        <div class="space-y-10 py-2">
          <!-- Metadata Section -->
          <div class="space-y-4">
            <div class="flex items-center justify-between border-b pb-2">
              <h5 class="text-sm font-bold flex items-center gap-2">
                <span class="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                基本信息 (全局生效)
              </h5>
              <span class="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded uppercase tracking-wider">Affects all versions</span>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 items-end p-6 bg-muted/20 rounded-2xl border border-muted/30">
               <div class="md:col-span-1">
                 <UIInput 
                   v-model="editForm.name" 
                   label="本体显示名称" 
                   placeholder="例如：核心业务对象" 
                 />
               </div>
               <div class="md:col-span-1">
                 <UISelect 
                   v-model="editForm.templateId" 
                   label="默认解析模板"
                   :options="templateOptions"
                   placeholder="选择解析规则"
                 />
               </div>
               <div class="flex items-end h-[68px]"> <!-- Align with label-offset inputs -->
                 <Button variant="primary" class="w-full h-10 shadow-lg shadow-blue-500/20" :loading="updatingSeries" @click="handleUpdateSeries">
                   <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                   </svg>
                   保存修改
                 </Button>
               </div>
            </div>
            <p class="text-[11px] text-muted-foreground leading-relaxed italic ml-1 flex items-center gap-1">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              修改默认模板后，后续上传的新版本将自动关联此解析规则。
            </p>
          </div>

          <!-- Reparse Section -->
          <div class="space-y-4">
            <div class="flex items-center justify-between border-b pb-2">
              <h5 class="text-sm font-bold flex items-center gap-2 text-danger">
                <span class="w-1.5 h-1.5 rounded-full bg-danger"></span>
                数据重析 (仅针对当前版本 v{{ ontology.version }})
              </h5>
              <Badge variant="outline" class="text-danger border-red-200">危险操作</Badge>
            </div>
            
            <div class="bg-red-50/30 border border-red-100/50 rounded-2xl p-6 space-y-6">
              <div class="flex gap-4">
                <div class="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center shrink-0">
                  <svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <p class="text-sm text-red-700 leading-relaxed">
                  如果您认为当前版本的解析结果不准确（如：实体提取错误、关系遗漏），可以使用选定的模板强制后台重新运行提取算法。
                  <strong class="block mt-1 underline">重要提示：此操作仅会刷新版本 v{{ ontology.version }} 的数据，不会改动历史或其他版本的图谱内容。但该版本的已有图谱数据将被清空并重新提取。</strong>
                </p>
              </div>

              <div class="flex flex-col md:flex-row gap-6 items-end border-t border-red-100 pt-6">
                <div class="flex-1 w-full space-y-1.5">
                  <label class="text-xs font-semibold text-red-600/70 ml-1">指定重析模板 (可选)</label>
                  <UISelect 
                     v-model="reparseForm.templateId" 
                     :options="templateOptions"
                     placeholder="留空则使用上述默认模板"
                  />
                </div>
                <Button variant="outline" class="shrink-0 h-10 px-6 border-red-200 text-red-600 hover:bg-red-50 shadow-sm" :loading="reparsing" @click="handleReparse">
                  <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  立即重新解析
                </Button>
              </div>
            </div>
          </div>
        </div>
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
import { ref, reactive, computed, watch } from 'vue'
import axios from 'axios'
import MarkdownIt from 'markdown-it'
import 'github-markdown-css/github-markdown-light.css'
import { Dialog, Card, Badge, Button, Empty, Loading, RelationList, Select as UISelect, Input as UIInput } from './index.js'
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
  { label: '订阅服务', value: 'subscriptions' },
  { label: '管理设置', value: 'settings' }
]
const activeTab = ref('files')

const editForm = reactive({
  name: '',
  templateId: ''
})

const reparseForm = reactive({
  templateId: ''
})

const templateOptions = ref([])

const fetchTemplates = async () => {
  try {
    const res = await axios.get('/api/templates/')
    templateOptions.value = [
      { label: '不解析 (None)', value: '' },
      ...res.data.map(t => ({ label: t.name, value: t.id }))
    ]
  } catch (e) {
    console.error('Failed to fetch templates', e)
  }
}

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
    
    // 初始化编辑表单
    editForm.name = res.data.name
    editForm.templateId = res.data.template_id || ''
    reparseForm.templateId = res.data.template_id || ''

    // 获取模板列表
    fetchTemplates()

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
const updatingSeries = ref(false)
const reparsing = ref(false)

const handleUpdateSeries = async () => {
  if (!ontology.value) return
  updatingSeries.value = true
  try {
    const res = await axios.patch(`/api/ontologies/${ontology.value.code}`, {
      name: editForm.name,
      default_template_id: editForm.templateId || null
    })
    message.success('本体信息已更新')
    ontology.value = res.data // 更新本地副本
    emit('refresh')
  } catch (e) {
    message.error(e.response?.data?.detail || '更新失败')
  } finally {
    updatingSeries.value = false
  }
}

const handleReparse = async () => {
  if (!ontology.value) return
  
  try {
    await showConfirm(
      `确定要重新解析当前版本 (v${ontology.value.version}) 吗？\n\n注意：这会清除该版本已有的图谱数据并重新从源码提取，但不会影响该本体的其他版本。`,
      '重析确认',
      { confirmButtonText: '确定重析', cancelButtonText: '取消', type: 'warning' }
    )
    
    reparsing.value = true
    await axios.post(`/api/ontologies/packages/${ontology.value.id}/reparse`, {
      template_id: reparseForm.templateId || null
    })
    message.success('已触发重新解析，后台正在处理中...')
    
    // 自动切回知识图谱页签或文件树
    setTimeout(() => {
      activeTab.value = 'graph'
    }, 1000)
  } catch (e) {
    if (e !== 'cancel') {
      message.error(e.response?.data?.detail || '解析触发失败')
    }
  } finally {
    reparsing.value = false
  }
}

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
