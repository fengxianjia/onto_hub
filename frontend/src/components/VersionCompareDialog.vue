<template>
  <Dialog v-model="visible" title="版本对比" size="xl" :close-on-click-outside="false">
    <!-- Loading State -->
    <div v-if="loadingDiff" class="flex items-center justify-center py-12">
      <Loading />
    </div>

    <!-- Main Content: Left-Right Layout -->
    <div v-else class="flex h-[82vh] gap-4">
      <!-- Left Sidebar: File List -->
      <div class="w-80 flex-shrink-0 border-r border-border pr-4 flex flex-col">
        <!-- Statistics -->
        <div class="mb-4 pb-4 border-b border-border">
          <h3 class="text-lg font-bold mb-3">文件变更</h3>
          <div class="flex flex-wrap gap-2">
            <Badge variant="success" size="sm">{{ addedCount }} 新增</Badge>
            <Badge variant="danger" size="sm">{{ deletedCount }} 删除</Badge>
            <Badge variant="info" size="sm">{{ modifiedCount }} 修改</Badge>
            <Badge variant="default" size="sm">{{ unchangedCount }} 未变更</Badge>
          </div>
        </div>

        <!-- Search and Filter -->
        <div class="mb-4 space-y-3">
          <!-- Search Input -->
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索文件路径..."
              class="w-full px-3 py-2 text-sm border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            />
            <svg v-if="searchQuery" 
                 @click="searchQuery = ''"
                 class="absolute right-3 top-2.5 w-4 h-4 text-muted-foreground cursor-pointer hover:text-foreground"
                 fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>

          <!-- Status Filter Buttons -->
          <div class="flex flex-wrap gap-2">
            <button
              v-for="status in statusFilters"
              :key="status.value"
              @click="toggleStatusFilter(status.value)"
              :class="[
                'px-3 py-1 text-xs rounded-lg border transition-all',
                activeFilters.includes(status.value)
                  ? 'border-accent bg-accent text-accent-foreground'
                  : 'border-border hover:border-accent/50'
              ]"
            >
              {{ status.label }}
            </button>
            <button
              v-if="activeFilters.length > 0"
              @click="activeFilters = []"
              class="px-3 py-1 text-xs rounded-lg border border-border hover:border-danger text-muted-foreground hover:text-danger"
            >
              清除
            </button>
          </div>
        </div>

        <!-- File List -->
        <div class="flex-1 overflow-y-auto space-y-2">
          <div v-if="!filteredFiles || !filteredFiles.length" class="text-center py-8">
            <Empty :description="searchQuery || activeFilters.length > 0 ? '无匹配的文件' : '无文件变更'" />
          </div>
          <div v-else>
            <p class="text-xs text-muted-foreground mb-2">
              显示 {{ filteredFiles.length }} / {{ fileDiff.length }} 个文件
            </p>
            <div v-for="(change, index) in filteredFiles" :key="index"
               :class="['p-3 rounded-lg border cursor-pointer transition-all',
                        selectedFileDiff?.path === change.file_path 
                          ? 'border-accent bg-accent/10 shadow-sm' 
                          : 'border-border hover:bg-muted hover:border-accent/50']"
               @click="viewFileDiff(change)">
            <div class="flex items-start gap-2">
              <!-- Status Badge -->
              <Badge v-if="change.status === 'added'" variant="success" size="sm">+</Badge>
              <Badge v-else-if="change.status === 'deleted'" variant="danger" size="sm">-</Badge>
              <Badge v-else-if="change.status === 'modified'" variant="info" size="sm">M</Badge>
              <Badge v-else variant="default" size="sm">=</Badge>
              
              <!-- File Path -->
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium truncate" :title="change.file_path">
                  {{ change.file_path }}
                </p>
                <p class="text-xs text-muted-foreground mt-1">
                  <span v-if="change.status === 'added'">新增文件</span>
                  <span v-else-if="change.status === 'deleted'">删除文件</span>
                  <span v-else-if="change.status === 'modified'">已修改</span>
                  <span v-else>未变更</span>
                </p>
              </div>
            </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Panel: File Comparison -->
      <div class="flex-1 overflow-hidden flex flex-col">
        <!-- Empty State -->
        <div v-if="!selectedFileDiff" class="flex items-center justify-center h-full">
          <Empty description="请从左侧选择文件查看对比" />
        </div>

        <!-- File Comparison Content -->
        <div v-else class="h-full flex flex-col">
          <!-- File Header -->
          <div class="mb-4 pb-4 border-b border-border flex-shrink-0">
            <div class="flex items-center justify-between">
              <div>
                <h4 class="text-lg font-bold">{{ selectedFileDiff.path }}</h4>
                <div class="flex gap-2 mt-2">
                  <Badge variant="accent">v{{ oldVersion.version }} → v{{ newVersion.version }}</Badge>
                  <Badge v-if="selectedFileDiff.status === 'added'" variant="success">新增</Badge>
                  <Badge v-else-if="selectedFileDiff.status === 'deleted'" variant="danger">删除</Badge>
                  <Badge v-else-if="selectedFileDiff.status === 'modified'" variant="info">修改</Badge>
                  <Badge v-else variant="default">未变更</Badge>
                </div>
              </div>
              <Button variant="ghost" size="sm" @click="selectedFileDiff = null">关闭</Button>
            </div>
          </div>

          <!-- v-code-diff Component -->
          <div class="flex-1 overflow-hidden" style="min-height: 0;">
            <CodeDiff
              :old-string="selectedFileDiff.oldContent || ''"
              :new-string="selectedFileDiff.newContent || ''"
              output-format="side-by-side"
              :context="10"
              :render-nothings="true"
              theme="light"
              style="height: 100%;"
            />
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end">
        <Button variant="secondary" @click="visible = false">关闭</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { CodeDiff } from 'v-code-diff'
import { Dialog, Card, Badge, Button, Loading, Empty } from './index.js'
import { showMessage } from '../utils/message.js'

const props = defineProps({
  modelValue: Boolean,
  newVersion: Object,
  oldVersion: Object
})

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const fileDiff = ref([])
const loadingDiff = ref(false)
const selectedFileDiff = ref(null)

// Statistics
const addedCount = computed(() => fileDiff.value.filter(f => f.status === 'added').length)
const deletedCount = computed(() => fileDiff.value.filter(f => f.status === 'deleted').length)
const modifiedCount = computed(() => fileDiff.value.filter(f => f.status === 'modified').length)
const unchangedCount = computed(() => fileDiff.value.filter(f => f.status === 'unchanged').length)

// Search and Filter
const searchQuery = ref('')
const activeFilters = ref(['added', 'deleted', 'modified'])

const statusFilters = [
  { value: 'added', label: '新增' },
  { value: 'deleted', label: '删除' },
  { value: 'modified', label: '修改' },
  { value: 'unchanged', label: '未变更' }
]

const toggleStatusFilter = (status) => {
  const index = activeFilters.value.indexOf(status)
  if (index > -1) {
    activeFilters.value.splice(index, 1)
  } else {
    activeFilters.value.push(status)
  }
}

const filteredFiles = computed(() => {
  let files = fileDiff.value

  // Apply status filter
  if (activeFilters.value.length > 0) {
    files = files.filter(f => activeFilters.value.includes(f.status))
  }

  // Apply search filter
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    files = files.filter(f => f.file_path.toLowerCase().includes(query))
  }

  return files
})

const fetchVersionDiff = async () => {
  if (!props.newVersion || !props.oldVersion) return
  
  loadingDiff.value = true
  selectedFileDiff.value = null
  try {
    const res = await axios.get(`/api/ontologies/compare`, {
      params: {
        base_id: props.oldVersion.id,
        target_id: props.newVersion.id
      }
    })
    fileDiff.value = res.data.files || []
    
    // Auto-select first modified/added/deleted file
    const firstChange = fileDiff.value.find(f => f.status !== 'unchanged')
    if (firstChange) {
      viewFileDiff(firstChange)
    }
  } catch (error) {
    showMessage('获取版本差异失败', 'error')
  } finally {
    loadingDiff.value = false
  }
}

const viewFileDiff = (change) => {
  // Directly use the content returned from the compare API
  selectedFileDiff.value = {
    path: change.file_path,
    status: change.status,
    oldContent: change.base_content || '',
    newContent: change.target_content || ''
  }
}

watch(() => props.modelValue, (newVal) => {
  if (newVal && props.newVersion && props.oldVersion) {
    fetchVersionDiff()
  }
})
</script>
