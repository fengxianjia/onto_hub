<template>
  <div class="min-h-screen bg-background animate-fadeIn">
    <!-- Header -->
    <Header title="OntoHub" subtitle="本体管理中心" />
    
    <!-- Main Content -->
    <main class="py-12 animate-slideUp">
      <Container max-width="full">
        <!-- Tabs -->
        <div class="mb-12 flex gap-6 border-b-2 border-border">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            @click="activeTab = tab.value"
            :class="tabClasses(tab.value)"
          >
            {{ tab.label }}
          </button>
        </div>
        
        <!-- 本体库管理 Tab -->
        <div v-if="activeTab === 'ontology'" class="space-y-8">
          <!-- Upload Card -->

          
          <!-- Ontology List Card -->
          <Card class="shadow-xl" variant="elevated">
            <template #header>
              <div class="flex items-center justify-between">
                <h3 class="text-2xl font-bold text-foreground">本体列表</h3>
                <div class="flex gap-2">
                  <Button variant="primary" size="sm" @click="uploadDialogVisible = true">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                    </svg>
                    新建本体
                  </Button>
                  <Button variant="ghost" size="sm" @click="fetchOntologies">
                    <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  </Button>
                </div>
              </div>
            </template>
            
            <div v-if="loading" class="flex justify-center py-12">
              <Loading />
            </div>
            
            <div v-else-if="tableData.length === 0" class="py-12">
              <Empty description="暂无本体数据" />
            </div>
            
            <div v-else class="overflow-x-auto rounded-lg">
              <table class="w-full">
                <thead class="bg-gradient-to-r from-muted/80 to-muted/40">
                  <tr>
                    <th class="px-8 py-4 text-left text-base font-bold text-foreground">编码</th>
                    <th class="px-8 py-4 text-left text-base font-bold text-foreground">名称</th>
                    <th class="px-8 py-4 text-left text-base font-bold text-foreground">版本</th>
                    <th class="px-8 py-4 text-left text-base font-bold text-foreground">状态</th>
                    <th class="px-8 py-4 text-left text-base font-bold text-foreground">上传时间</th>
                    <th class="px-8 py-4 text-left text-base font-bold text-foreground">操作</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-border">
                  <tr v-for="(row, index) in tableData" :key="row.id" 
                      :class="['transition-all duration-200 hover:bg-accent/5 hover:shadow-md', index % 2 === 0 ? 'bg-white' : 'bg-muted/20']">
                    <td class="px-8 py-5">
                      <Badge variant="info" outline size="lg">{{ row.code || '-' }}</Badge>
                    </td>
                    <td class="px-8 py-5 text-base font-medium">{{ row.name }}</td>
                    <td class="px-8 py-5">
                      <Badge variant="accent" size="lg">v{{ row.version }}</Badge>
                    </td>
                    <td class="px-8 py-5">
                      <Badge :variant="getStatusVariant(row.status)" size="lg">{{ row.status }}</Badge>
                    </td>
                    <td class="px-8 py-5 text-sm text-muted-foreground">{{ formatDate(row.upload_time) }}</td>
                    <td class="px-8 py-5">
                      <div class="flex gap-3">
                        <Button variant="ghost" size="sm" @click="handleView(row)">详情</Button>
                        <Button variant="ghost" size="sm" @click="handleHistory(row)">版本</Button>
                        <Button variant="ghost" size="sm" @click="handleSubscriptionStatus(row)">订阅状态</Button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>
          
          <!-- Pagination -->
          <div v-if="tableData.length" class="flex justify-center">
            <Pagination
              v-model:current-page="pagination.currentPage"
              v-model:page-size="pagination.pageSize"
              :total="pagination.total"
              :disabled="loading"
              @change="handlePageChange"
              @update:page-size="handlePageChange"
            />
          </div>
        </div>
        
        <!-- 订阅设置 Tab -->
        <div v-if="activeTab === 'webhook'">
          <WebhookManager @change="fetchOntologies" />
        </div>
      </Container>
    </main>
    
    <!-- Ontology Detail Dialog -->
    <OntologyDetailDialog 
      v-model="detailDialogVisible" 
      :ontology-id="selectedOntologyId"
      @viewHistory="handleViewHistoryFromDetail"
      @refresh="fetchOntologies"
    />
    
    <!-- Version History Drawer -->
    <VersionHistoryDrawer
      v-model="historyDrawerVisible"
      :ontology-name="selectedOntologyName"
      :ontology-code="selectedOntologyCode"
      @viewDetail="handleViewDetailFromHistory"
      @compare="handleCompareFromHistory"
      @refresh="fetchOntologies"
      @upload-success="handleVersionUploadSuccess"
    />
    
    <!-- Version Compare Dialog -->
    <VersionCompareDialog
      v-model="compareDialogVisible"
      :new-version="compareVersions.new"
      :old-version="compareVersions.old"
    />
    
    <!-- Delivery Status Dialog -->
    <DeliveryStatusDialog
      v-model="deliveryDialogVisible"
      :package-id="selectedPackageId"
    />
    <!-- Version Push Status Dialog -->
    <VersionPushStatusDialog
      v-model="pushStatusDialog.visible"
      :package-id="pushStatusDialog.packageId"
      :ontology-code="pushStatusDialog.ontologyCode"
      :ontology-name="pushStatusDialog.ontologyName"
      :version="pushStatusDialog.version"
    />

    <!-- Readonly Subscription Dialog -->
    <Dialog v-model="subscriptionDialogVisible" title="订阅状态" width="800px">
      <div v-if="selectedOntologyCode">
        <SubscriptionList 
          :ontology-code="selectedOntologyCode" 
          :ontology-name="selectedOntologyName"
          readonly 
        />
      </div>
      <template #footer>
        <div class="flex justify-end">
          <Button variant="secondary" @click="subscriptionDialogVisible = false">关闭</Button>
        </div>
      </template>
    </Dialog>

    <!-- Upload Dialog -->
    <Dialog v-model="uploadDialogVisible" title="新建本体" width="600px">
      <div class="space-y-6">
        
        <!-- 新建本体表单 -->
        <div class="space-y-4">
          <Input
            v-model="newOntologyForm.code"
            label="本体编码"
            placeholder="全局唯一标识 (e.g. auth-module)"
            required
          />
          <Input
            v-model="newOntologyForm.name"
            label="显示名称"
            placeholder="人类可读名称 (e.g. 认证模块)"
          />
          <Upload
            ref="newUploadRef"
            label="文件"
            accept=".zip"
            required
            @change="handleNewFileChange"
          />
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <Button variant="secondary" @click="uploadDialogVisible = false">取消</Button>
          <Button
            variant="primary"
            :disabled="!newOntologyForm.code || !newFileSelected"
            :loading="uploading"
            @click="submitNewOntology"
          >
            创建并上传
          </Button>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { Header, Container } from './components/index.js'
import { Button, Card, Input, Select, Upload, Badge, Empty, Loading, Dialog, Pagination } from './components/index.js'
import WebhookManager from './components/WebhookManager.vue'
import OntologyDetailDialog from './components/OntologyDetailDialog.vue'
import SubscriptionList from './components/SubscriptionList.vue'
import VersionHistoryDrawer from './components/VersionHistoryDrawer.vue'
import VersionCompareDialog from './components/VersionCompareDialog.vue'
import DeliveryStatusDialog from './components/DeliveryStatusDialog.vue'
import VersionPushStatusDialog from './components/VersionPushStatusDialog.vue'
import { showMessage } from './utils/message.js'

// Tabs
const tabs = [
  { label: '本体库管理', value: 'ontology' },
  { label: '订阅设置', value: 'webhook' }
]
const activeTab = ref('ontology')

// Upload - New Ontology
const uploading = ref(false)
const uploadDialogVisible = ref(false)
const newFileSelected = ref(false)

// Forms
const newOntologyForm = ref({
  code: '',
  name: ''
})

// Refs
const newUploadRef = ref(null)

// Table Data
const tableData = ref([])
const loading = ref(false)
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// Dialog and Drawer states
const pushStatusDialog = ref({
  visible: false,
  packageId: '',
  ontologyCode: '',
  ontologyName: '',
  version: ''
})
const detailDialogVisible = ref(false)
const historyDrawerVisible = ref(false)
const compareDialogVisible = ref(false)
const deliveryDialogVisible = ref(false)
const selectedOntologyId = ref(null)
const selectedOntologyName = ref('')
const selectedPackageId = ref(null)
const compareVersions = reactive({ new: null, old: null })

// Computed
const ontologyOptions = computed(() => {
  const map = new Map()
  tableData.value.forEach(item => {
    if (item.code && !map.has(item.code)) {
      map.set(item.code, {
        label: item.name ? `${item.name} (${item.code})` : item.code,
        value: item.code
      })
    }
  })
  return Array.from(map.values())
})

// Methods
const tabClasses = (value) => {
  const base = 'px-8 py-4 text-base font-bold transition-all duration-300 border-b-4 cursor-pointer'
  return value === activeTab.value
    ? `${base} border-accent text-accent scale-105`
    : `${base} border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground/30`
}



const getStatusVariant = (status) => {
  if (status === 'READY') return 'success'
  if (status === 'ERROR') return 'danger'
  return 'warning'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z')
  return date.toLocaleString()
}

const handleNewFileChange = (files) => {
  newFileSelected.value = files.length > 0
}



const submitNewOntology = async () => {
  if (!newOntologyForm.value.code) {
    showMessage('请输入本体编码', 'warning')
    return
  }
  
  const files = newUploadRef.value?.getFiles()
  if (!files || files.length === 0) {
    showMessage.warning('请选择文件')
    return
  }
  
  uploading.value = true
  const formData = new FormData()
  formData.append('file', files[0])
  formData.append('code', newOntologyForm.value.code)
  if (newOntologyForm.value.name) {
    formData.append('name', newOntologyForm.value.name)
  }
  
  try {
    const res = await axios.post('/api/ontologies', formData)
    showMessage(`上传成功: ${res.data.code} v${res.data.version}`, 'success')
    
    // 打开推送状态对话框
    pushStatusDialog.value = {
      visible: true,
      packageId: res.data.id,
      ontologyCode: res.data.code,
      ontologyName: res.data.name,
      version: res.data.version
    }
    
    // Reset form
    newOntologyForm.value = { code: '', name: '' }
    newUploadRef.value?.clearFiles()
    newFileSelected.value = false
    uploadDialogVisible.value = false
    
    fetchOntologies()
  } catch (e) {
    showMessage('上传失败', 'error')
  } finally {
    uploading.value = false
  }
}



const fetchOntologies = async () => {
  loading.value = true
  try {
    const skip = (pagination.currentPage - 1) * pagination.pageSize
    const res = await axios.get('/api/ontologies', {
        params: {
            skip,
            limit: pagination.pageSize
        }
    })
    tableData.value = res.data.items
    pagination.total = res.data.total
  } catch (error) {
    showMessage('获取列表失败', 'error')
  } finally {
    loading.value = false
  }
}

const handlePageChange = () => {
    fetchOntologies()
}

const handleView = (row) => {
  selectedOntologyId.value = row.id
  detailDialogVisible.value = true
}

const handleHistory = (row) => {
  selectedOntologyCode.value = row.code
  selectedOntologyName.value = row.name
  historyDrawerVisible.value = true
}

const handleVersionUploadSuccess = (data) => {
  // Show push status dialog
  pushStatusDialog.value = {
    visible: true,
    packageId: data.id,
    ontologyCode: data.code,
    ontologyName: data.name,
    version: data.version
  }
}

const handleViewHistoryFromDetail = (ontology) => {
  selectedOntologyName.value = ontology.name
  detailDialogVisible.value = false
  historyDrawerVisible.value = true
}

const handleViewDetailFromHistory = (version) => {
  selectedOntologyId.value = version.id
  historyDrawerVisible.value = false
  detailDialogVisible.value = true
}

const handleCompareFromHistory = ({ newVersion, oldVersion }) => {
  compareVersions.new = newVersion
  compareVersions.old = oldVersion
  compareDialogVisible.value = true
}

// Subscription Status View
const subscriptionDialogVisible = ref(false)
const selectedOntologyCode = ref('')

const handleSubscriptionStatus = (row) => {
  selectedOntologyCode.value = row.code
  selectedOntologyName.value = row.name
  subscriptionDialogVisible.value = true
}

// Lifecycle
onMounted(() => {
  fetchOntologies()
})
</script>
