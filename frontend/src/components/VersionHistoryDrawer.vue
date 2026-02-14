<template>
    <Drawer v-model="visible" :title="`版本历史 - ${ontologyName}`" size="600px">
      <!-- Header Actions -->
      <div class="px-6 pb-4 border-b border-border flex justify-between items-center">
        <div class="text-sm text-muted-foreground">
          共 {{ versions.length }} 个版本
        </div>
        <div class="flex flex-col items-end gap-2">
            <div class="flex gap-2">
                <input
                  type="file"
                  ref="fileInputRef"
                  accept=".zip"
                  class="hidden"
                  @change="handleFileUpload"
                />
                <Button size="sm" variant="outline" @click="triggerUpload" :loading="uploading">
                  <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  上传新版本
                </Button>
            </div>
            <div class="flex items-center gap-2">
                <input 
                  type="checkbox" 
                  id="version-auto-push" 
                  v-model="autoPush"
                  class="w-3 h-3 text-accent border-gray-300 rounded focus:ring-accent"
                >
                <label for="version-auto-push" class="text-xs text-muted-foreground cursor-pointer">
                  上传后立即推送
                </label>
            </div>
        </div>
      </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <Loading />
    </div>

    <!-- Empty State -->
    <div v-else-if="!versions.length" class="py-12">
      <Empty description="暂无版本历史" />
    </div>

    <!-- Timeline -->
    <div v-else class="space-y-4">
      <div v-for="(version, index) in versions" :key="version.id" class="relative">
        <!-- Timeline Line -->
        <div v-if="index < versions.length - 1" class="absolute left-6 top-12 h-full w-0.5 bg-border"></div>
        
        <!-- Version Card -->
        <Card :variant="version.status === 'READY' ? 'featured' : 'default'" hoverable>
          <div class="flex items-start gap-4">
            <!-- Timeline Dot -->
            <div :class="['flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full', 
                          version.status === 'READY' ? 'bg-gradient-to-br from-accent to-accent-secondary text-white shadow-lg' : 'bg-muted text-muted-foreground']">
              <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
              </svg>
            </div>
            
            <!-- Content -->
            <div class="flex-1">
              <div class="flex items-center gap-3">
                <Badge variant="accent">v{{ version.version }}</Badge>
                <Badge v-if="version.status !== 'READY'" :variant="getStatusVariant(version.status)">{{ version.status }}</Badge>
                <Badge v-if="version.is_active" variant="success" outline>当前版本</Badge>
              </div>
              
              <div class="mt-3 space-y-2 text-sm">
                <div class="flex items-center gap-2 text-muted-foreground">
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{{ formatDate(version.upload_time) }}</span>
                </div>
                
                <div v-if="version.display_name" class="flex items-center gap-2 text-foreground">
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                  <span>{{ version.display_name }}</span>
                </div>
              </div>
              
              <!-- Actions -->
              <div class="mt-4 flex flex-wrap gap-2">
                <Button 
                  v-if="!version.is_active"
                  variant="primary" 
                  size="sm" 
                  @click="handleActivate(version)"
                  :loading="activating === version.id"
                >
                  切换至此版本
                </Button>
                <Button 
                  v-else
                  variant="outline" 
                  size="sm" 
                  @click="handleActivate(version)"
                  :loading="activating === version.id"
                >
                  重新推送 (Re-push)
                </Button>

                <Button 
                  v-if="!version.is_active" 
                  variant="ghost" 
                  size="sm" 
                  class="text-red-600 hover:text-red-700 hover:bg-red-50"
                  @click="handleDelete(version)"
                >
                  删除
                </Button>

                <Button variant="ghost" size="sm" @click="handleDownload(version)">下载源码包</Button>
                <Button variant="ghost" size="sm" @click="handleViewDetail(version)">查看详情</Button>
                <Button v-if="index < versions.length - 1" variant="ghost" size="sm" @click="handleCompare(version, versions[index + 1])">
                  对比上一版本
                </Button>
                <Button 
                  :variant="isSelected(version) ? 'primary' : 'ghost'" 
                  size="sm" 
                  @click="toggleSelectVersion(version)"
                >
                  {{ isSelected(version) ? '✓ 已选择' : '选择对比' }}
                </Button>
              </div>
            </div>
          </div>
        </Card>
      </div>
      
      <!-- Compare Selected Button (Floating) -->
      <div v-if="selectedVersions.length === 2" class="sticky bottom-4 flex justify-center">
        <Button variant="primary" size="lg" @click="handleCompareSelected" class="shadow-lg">
          对比选中的版本 (v{{ selectedVersions[0].version }} vs v{{ selectedVersions[1].version }})
        </Button>
      </div>
      <!-- Compare Selected Button (Floating) -->
      <div v-if="selectedVersions.length === 2" class="sticky bottom-4 flex justify-center">
        <Button variant="primary" size="lg" @click="handleCompareSelected" class="shadow-lg">
          对比选中的版本 (v{{ selectedVersions[0].version }} vs v{{ selectedVersions[1].version }})
        </Button>
      </div>
      
      <!-- Pagination -->
      <div v-if="versions.length" class="mt-4 flex justify-center pb-4">
        <Pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            :disabled="loading"
            @change="handlePageChange"
            @update:page-size="handlePageChange"
            layout="prev, pager, next" 
        />
      </div>
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

    <DeliveryStatusDialog 
      v-model="deliveryDialogVisible" 
      :package-id="currentPackageId" 
    />
  </Drawer>
</template>

<script setup>
import { ref, computed, watch, reactive } from 'vue'
import { getOntologyVersions, addOntologyVersion, activateOntology, deleteOntologyVersion } from '../api/ontologies.js'
import { Drawer, Card, Badge, Button, Loading, Empty, Pagination } from './index.js'
import DeliveryStatusDialog from './DeliveryStatusDialog.vue'
import { message, showConfirm } from '../utils/message.js'
import { formatDate } from '../utils/format.js'

const props = defineProps({
  modelValue: Boolean,
  ontologyName: String,
  ontologyCode: String
})

const emit = defineEmits(['update:modelValue', 'refresh', 'viewDetail', 'compare', 'upload-success'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const versions = ref([])
const loading = ref(false)
const uploading = ref(false)
const activating = ref(null)
const deliveryDialogVisible = ref(false)
const currentPackageId = ref(null)
const fileInputRef = ref(null)
const autoPush = ref(true)

const triggerUpload = () => {
  fileInputRef.value.click()
}

const handleFileUpload = async (e) => {
  const files = e.target.files
  if (!files || files.length === 0) return
  
  const file = files[0]
  // Reset input
  e.target.value = ''
  
  if (!props.ontologyCode) {
    message.error('缺少本体编码，无法上传')
    return
  }

  try {
    uploading.value = true
    const formData = new FormData()
    formData.append('file', file)
    formData.append('auto_push', autoPush.value ? 'true' : 'false')
    
    const res = await addOntologyVersion(props.ontologyCode, formData)
    message.success(`版本 v${res.data.version} 上传成功`)
    
    // Refresh list
    await fetchVersions()
    emit('refresh') // Refresh main list
    
    // Auto-activate or show delivery status? 
    // The previous logic showed push status dialog. 
    // Parent handles `pushStatusDialog`. Let's emit 'upload-success' with data and autoPush status.
    emit('upload-success', { ...res.data, autoPush: autoPush.value })
  } catch (error) {
    message.error(error.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

const handleActivate = async (version) => {
  try {
    const isRepush = version.is_active
    const title = isRepush ? '重新推送确认' : '切换版本确认'
    const confirmText = isRepush ? '确定重新推送' : '确定切换'

    await showConfirm(
      `确定要${isRepush ? '重新推送' : '切换到'}版本 v${version.version} 吗？\n\n${isRepush ? '重新推送' : '切换'}后，所有订阅此本体的服务均会收到${isRepush ? '当前' : '被切换'}版本（v${version.version}）的推送。`,
      title,
      { confirmButtonText: confirmText, cancelButtonText: '取消' }
    )
    
    activating.value = version.id
    // Set for dialog
    currentPackageId.value = version.id

    await activateOntology(version.id)
    message.success(`版本 v${version.version} 已激活并触发推送`)
    
    // Show Progress
    deliveryDialogVisible.value = true
    
    // Refresh list to update active status
    // Refresh list to update active status
    await fetchVersions()
    emit('refresh') // Notify parent to refresh main list if needed
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
      message.error(e.response?.data?.detail || '激活失败')
    }
  } finally {
    activating.value = null
  }
}

const handleDelete = async (version) => {
  try {
    await showConfirm(
      `确定要删除版本 v${version.version} 吗？\n\n此操作不可撤销。`,
      '删除确认',
      { confirmButtonText: '确定删除', type: 'error' }
    )

    await deleteOntologyVersion(version.id)
    message.success(`版本 v${version.version} 已删除`)
    
    await fetchVersions()
    emit('refresh')
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
      message.error(e.response?.data?.detail || '删除失败')
    }
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



// Version selection for comparison
const selectedVersions = ref([])

const toggleSelectVersion = (version) => {
  const index = selectedVersions.value.findIndex(v => v.id === version.id)
  if (index > -1) {
    selectedVersions.value.splice(index, 1)
  } else {
    if (selectedVersions.value.length >= 2) {
      selectedVersions.value.shift() // Remove first one
    }
    selectedVersions.value.push(version)
  }
}

const isSelected = (version) => {
  return selectedVersions.value.some(v => v.id === version.id)
}

const handleCompareSelected = () => {
  if (selectedVersions.value.length === 2) {
    const [v1, v2] = selectedVersions.value
    // Ensure newer version is first
    const newVersion = v1.version > v2.version ? v1 : v2
    const oldVersion = v1.version > v2.version ? v2 : v1
    emit('compare', { newVersion, oldVersion })
    selectedVersions.value = []
  }
}

const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

const fetchVersions = async () => {
  if (!props.ontologyCode) return
  
  loading.value = true
  try {
    const skip = (pagination.currentPage - 1) * pagination.pageSize
    const res = await getOntologyVersions(props.ontologyCode, {
      skip,
      limit: pagination.pageSize
    })
    // Sort by version descending (backend already sorts by upload_time desc, but let's trust backend or ensure sort)
    // Backend `list_versions` calls `list_packages` which orders by `upload_time` desc.
    // So items are already sorted.
    versions.value = res.data.items
    pagination.total = res.data.total
  } catch (error) {
    showMessage('获取版本历史失败', 'error')
  } finally {
    loading.value = false
  }
}

const handlePageChange = () => {
    fetchVersions()
}

const handleViewDetail = (version) => {
  emit('viewDetail', version)
}

const handleCompare = (newVersion, oldVersion) => {
  emit('compare', { newVersion, oldVersion })
}

const handleDownload = (version) => {
  const url = `/api/ontologies/${props.ontologyCode}/versions/${version.version}/download`;
  // 使用原生 a 标签触发下载
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `${props.ontologyCode}_v${version.version}.zip`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

watch(() => props.visible, (newVal) => {
  if (newVal) {
    fetchVersions()
    // 每次打开侧边栏，重置推送开关为默认开启
    autoPush.value = true
  }
})

watch(() => props.modelValue, (newVal) => {
  if (newVal && props.ontologyName) {
    fetchVersions()
  }
})
</script>
