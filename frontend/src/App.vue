<template>
  <el-container class="layout-container">
    <el-header style="text-align: left; font-size: 20px; font-weight: bold; line-height: 60px; background-color: #f5f7fa;">
      📦 OntoHub - 本体管理中心
    </el-header>
    
    <el-main>
      <el-tabs type="border-card">
        <el-tab-pane label="本体库管理">
          <!-- 上传区域 -->
          <el-card class="box-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>上传本体 (ZIP)</span>
              </div>
            </template>
            
            <el-tabs v-model="uploadTab" type="card">
                <!-- Tab 1: 新建本体 -->
                <el-tab-pane label="新建本体" name="new">
                    <el-form :model="newOntologyForm" label-width="100px">
                        <el-form-item label="本体编码" required>
                            <el-input v-model="newOntologyForm.code" placeholder="全局唯一标识 (e.g. auth-module)" />
                        </el-form-item>
                        <el-form-item label="显示名称">
                            <el-input v-model="newOntologyForm.name" placeholder="人类可读名称 (e.g. 认证模块)" />
                        </el-form-item>
                        <el-form-item label="文件" required>
                             <el-upload
                                class="upload-demo"
                                ref="newUploadRef"
                                action="/api/ontologies"
                                :data="{ 
                                    code: newOntologyForm.code, 
                                    name: newOntologyForm.name
                                }"
                                :show-file-list="true"
                                :auto-upload="false"
                                :on-success="handleUploadSuccess"
                                :on-error="handleUploadError"
                                accept=".zip"
                                :limit="1"
                                :on-exceed="handleExceedNew"
                                :on-change="(file) => handleFileChange(file, 'new')"
                            >
                                <template #trigger>
                                    <el-button type="primary">选择 ZIP 文件</el-button>
                                </template>
                            </el-upload>
                        </el-form-item>
                        <div style="margin-top: 20px;">
                            <el-button type="success" @click="submitNewOntology" :disabled="!newOntologyForm.code || !newFileSelected" style="width: 100%;">
                                <el-icon style="margin-right: 5px"><upload-filled /></el-icon> 创建并上传
                            </el-button>
                        </div>
                    </el-form>
                </el-tab-pane>

                <!-- Tab 2: 新增版本 -->
                <el-tab-pane label="新增版本" name="version">
                     <el-form :model="newVersionForm" label-width="100px">
                        <el-form-item label="选择本体" required>
                            <el-select v-model="newVersionForm.code" placeholder="请选择本体" filterable style="width: 100%">
                                <el-option
                                    v-for="item in uniqueOntologyCodes"
                                    :key="item.code"
                                    :label="item.name ? `${item.name} (${item.code})` : item.code"
                                    :value="item.code"
                                />
                            </el-select>
                        </el-form-item>
                        <el-form-item label="文件" required>
                             <el-upload
                                class="upload-demo"
                                ref="versionUploadRef"
                                :action="`/api/ontologies/${newVersionForm.code}/versions`"
                                :data="{}"
                                :show-file-list="true"
                                :auto-upload="false"
                                :on-success="handleUploadSuccess"
                                :on-error="handleUploadError"
                                accept=".zip"
                                :limit="1"
                                :on-exceed="handleExceedVersion"
                                :on-change="(file) => handleFileChange(file, 'version')"
                            >
                                <template #trigger>
                                    <el-button type="primary">选择 ZIP 文件</el-button>
                                </template>
                            </el-upload>
                        </el-form-item>
                        <div style="margin-top: 20px;">
                             <el-button 
                                type="success" 
                                @click="submitNewVersion" 
                                :disabled="!newVersionForm.code || !versionFileSelected"
                                style="width: 100%;"
                            >
                                <el-icon style="margin-right: 5px"><upload-filled /></el-icon> 上传新版本
                            </el-button>
                        </div>
                    </el-form>
                </el-tab-pane>
            </el-tabs>
          </el-card>

          <!-- 列表区域 -->
          <el-card class="box-card" style="margin-top: 20px;" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>已上传本体</span>
                <el-button type="primary" @click="fetchOntologies" circle><el-icon><refresh /></el-icon></el-button>
              </div>
            </template>
            <el-table :data="tableData" style="width: 100%" v-loading="loading">
              <el-table-column prop="code" label="编码" width="180">
                  <template #default="scope">
                      <el-tag type="info" effect="plain">{{ scope.row.code || '-' }}</el-tag>
                  </template>
              </el-table-column>
              <el-table-column prop="name" label="名称" width="200" />
              <el-table-column label="版本" width="100">
                  <template #default="scope">
                      <el-tag effect="dark" size="small">v{{ scope.row.version }}</el-tag>
                      <el-tooltip content="新增版本" placement="top">
                        <el-button 
                            type="primary" 
                            link 
                            :icon="Plus" 
                            size="small" 
                            style="margin-left: 5px"
                            @click="openAddVersion(scope.row)"
                        />
                    </el-tooltip>
                  </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="100">
                 <template #default="scope">
                    <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
                 </template>
              </el-table-column>
              <el-table-column label="生效订阅" min-width="150">
                <template #default="scope">
                  <el-popover 
                    placement="top" 
                    trigger="click" 
                    :width="300"
                    @show="fetchSubscriptionStatus(scope.row)"
                  >
                    <template #reference>
                      <el-button link type="primary">
                        查看订阅 ({{ getEffectiveWebhooksCount(scope.row) }})
                      </el-button>
                    </template>
                    
                    <el-table :data="subscriptionStatus[scope.row.code || scope.row.name] || []" size="small" v-loading="!subscriptionStatus[scope.row.code || scope.row.name]">
                       <el-table-column prop="webhook_name" label="订阅名称" show-overflow-tooltip></el-table-column>
                       <el-table-column label="生效版本" width="100">
                          <template #default="subScope">
                            <el-tag :type="subScope.row.latest_success_version ? 'success' : 'info'" size="small">
                              {{ subScope.row.latest_success_version ? 'v' + subScope.row.latest_success_version : '未送达' }}
                            </el-tag>
                          </template>
                       </el-table-column>
                    </el-table>
                  </el-popover>
                </template>
              </el-table-column>
              <el-table-column prop="upload_time" label="上传时间" width="180">
                 <template #default="scope">
                    {{ formatDate(scope.row.upload_time) }}
                 </template>
              </el-table-column>
              <!-- <el-table-column prop="id" label="ID" width="300" /> -->
              <el-table-column label="操作" fixed="right" min-width="320">
                <template #default="scope">
                  <el-button size="small" @click="handleView(scope.row)">详情</el-button>
                  <el-button size="small" @click="handleHistory(scope.row)">版本</el-button>
                  <el-button size="small" type="info" plain @click="handleOntologyLogs(scope.row)">日志</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="订阅设置">
          <webhook-manager @change="fetchAllWebhooks" />
        </el-tab-pane>
      </el-tabs>
    </el-main>
    
    <!-- 隐形的文件上传 input 用于更新操作 -->
    <input type="file" ref="updateInput" style="display: none" accept=".zip" @change="handleUpdateFileChange">

    <!-- 详情弹窗 -->
    <el-dialog v-model="dialogVisible" title="本体详情" width="80%" destroy-on-close>
      <div class="detail-container">
        <!-- 左侧文件树 -->
        <div class="file-tree">
           <h3>文件列表</h3>
           <el-tree 
              :data="fileTreeData" 
              :props="defaultProps" 
              @node-click="handleNodeClick" 
              default-expand-all
              highlight-current
           />
        </div>
        <!-- 右侧内容预览 -->
        <div class="file-content" v-loading="contentLoading">
            <h3>{{ currentFileName || '请选择文件' }}</h3>
            <div 
                v-if="fileContent" 
                class="markdown-body" 
                v-html="renderMarkdown(fileContent)"
            ></div>
            <el-empty v-else description="暂无内容或未选择文件" />
        </div>
      </div>
    </el-dialog>
    
    <!-- Version Diff Dialog -->
    <el-dialog 
        v-model="diffVisible" 
        title="版本差异对比" 
        width="95%" 
        top="5vh"
        destroy-on-close
    >
        <div v-if="diffLoading" style="padding: 40px; text-align: center;">
            <el-skeleton :rows="10" animated />
        </div>
        <div v-else-if="diffResult" class="diff-wrapper">
            <div class="diff-sidebar">
                <div class="sidebar-header">
                    <span>文件变更 ({{ diffResult.files.filter(f => f.status !== 'unchanged').length }})</span>
                </div>
                <div class="diff-file-list">
                    <div v-for="file in diffResult.files" :key="file.file_path" 
                         class="diff-file-item"
                         :class="[file.status, selectedDiffFile?.file_path === file.file_path ? 'is-active' : '']"
                         @click="selectedDiffFile = file"
                    >
                        <span class="status-dot"></span>
                        <span class="file-path">{{ file.file_path }}</span>
                    </div>
                </div>
            </div>
            <div class="diff-main">
                <template v-if="selectedDiffFile">
                    <div class="diff-main-header">
                        <el-tag size="small" :type="getDiffTagType(selectedDiffFile.status)">{{ selectedDiffFile.status.toUpperCase() }}</el-tag>
                        <span class="current-path">{{ selectedDiffFile.file_path }}</span>
                    </div>
                    <div class="diff-viewer-area">
                        <code-diff
                            v-if="selectedDiffFile.base_content !== null || selectedDiffFile.target_content !== null"
                            :old-string="selectedDiffFile.base_content || ''"
                            :new-string="selectedDiffFile.target_content || ''"
                            output-format="side-by-side"
                            style="height: 60vh"
                        />
                        <div v-else class="empty-diff">
                            <el-empty :description="selectedDiffFile.status === 'unchanged' ? '该文件内容未发生变化' : '该文件类型暂不支持内容级对比'" />
                        </div>
                    </div>
                </template>
                <div v-else class="empty-diff">
                    <el-empty description="请选择左侧文件查看详细差异" />
                </div>
            </div>
        </div>
    </el-dialog>

    <!-- Delivery Status Dialog -->
    <delivery-status-dialog 
        v-model="deliveryDialogVisible" 
        :package-id="lastUploadedPackageId"
    />

    <!-- History Drawer -->
    <el-drawer v-model="historyDrawerVisible" title="版本历史" direction="rtl" size="50%">
        <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%">
                <h4 style="margin: 0">{{ historyDrawerTitle }}</h4>
                <el-button circle size="small" @click="refreshHistory">
                    <el-icon><Refresh /></el-icon>
                </el-button>
                <el-button 
                    type="primary" 
                    size="small" 
                    :disabled="selectedVersions.length !== 2" 
                    @click="handleCompare"
                >
                    对比选中 ({{ selectedVersions.length }}/2)
                </el-button>
            </div>
        </template>
        
        <el-table 
            :data="historyData" 
            style="width: 100%" 
            v-loading="historyLoading"
            @selection-change="handleSelectionChange"
            ref="historyTableRef"
        >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="version" label="版本" width="80">
                <template #default="scope">v{{ scope.row.version }}</template>
            </el-table-column>
            <el-table-column prop="upload_time" label="上传时间" width="180">
                 <template #default="scope">
                    {{ formatDate(scope.row.upload_time) }}
                 </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
                <template #default="scope">
                    <el-tag size="small" :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
                </template>
            </el-table-column>
            <el-table-column label="已送达订阅" min-width="150">
                <template #default="scope">
                    <div v-if="scope.row.delivered_webhooks && scope.row.delivered_webhooks.length">
                        <el-tag 
                            v-for="name in scope.row.delivered_webhooks" 
                            :key="name" 
                            size="small" 
                            effect="plain" 
                            style="margin-right: 4px; margin-bottom: 4px;"
                        >
                            {{ name }}
                        </el-tag>
                    </div>
                    <span v-else style="color: #909399; font-size: 12px;">-</span>
                </template>
            </el-table-column>
            <el-table-column label="操作" min-width="280">
                <template #default="scope">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <template v-if="scope.row.is_active">
                            <el-tag type="success" effect="dark">启用中</el-tag>
                            <el-button 
                                size="small" 
                                type="warning" 
                                plain 
                                @click="handleActivate(scope.row)"
                                title="重新触发 Webhook 推送"
                            >
                                重新推送
                            </el-button>
                        </template>
                        <el-button 
                            v-else 
                            size="small" 
                            type="primary" 
                            plain 
                            @click="handleActivate(scope.row)"
                        >
                            启用
                        </el-button>
                        
                        <el-divider direction="vertical" />
                        <el-button size="small" link @click="handleView(scope.row)">详情</el-button>
                        
                        <!-- 删除按钮带约束 -->
                        <el-tooltip
                            v-if="scope.row.is_deletable === false"
                            :content="scope.row.deletable_reason || '不可删除'"
                            placement="top"
                        >
                            <div style="display: inline-block; cursor: not-allowed;"> <!-- 使用 div 并强制 cursor 确保交互 -->
                                <el-button size="small" link type="danger" disabled style="pointer-events: none;">删除</el-button>
                            </div>
                        </el-tooltip>
                        <el-button 
                            v-else 
                            size="small" 
                            link 
                            type="danger" 
                            @click="handleDelete(scope.row)"
                        >
                            删除
                        </el-button>
                    </div>
                </template>
            </el-table-column>
        </el-table>
    </el-drawer>

    <!-- Ontology Contextual Log Drawer (Shared Component) -->
    <webhook-log-drawer 
        v-model="ontologyLogDrawerVisible" 
        :title="ontologyLogDrawerTitle" 
        :logs-data="ontologyLogsData" 
        :loading="ontologyLogsLoading" 
        @refresh="fetchOntologyLogs"
    />
  </el-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { UploadFilled, Refresh, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import MarkdownIt from 'markdown-it'
import 'github-markdown-css'

import WebhookManager from './components/WebhookManager.vue'
import DeliveryStatusDialog from './components/DeliveryStatusDialog.vue'
import WebhookLogDrawer from './components/WebhookLogDrawer.vue'
import { CodeDiff } from 'v-code-diff'

const md = new MarkdownIt({
    html: true,
    linkify: true,
    typographer: true
})

const renderMarkdown = (content) => {
    return md.render(content)
}

const tableData = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const deliveryDialogVisible = ref(false)
const lastUploadedPackageId = ref('')
const currentIds = ref(null)

// History Drawer
const historyDrawerVisible = ref(false)
const historyLoading = ref(false)
const historyData = ref([])
const historyDrawerTitle = ref('')
const currentHistoryRow = ref(null)

// Upload Logic
const uploadTab = ref('new')
const newUploadRef = ref(null)
const versionUploadRef = ref(null)
const newFileSelected = ref(false)
const versionFileSelected = ref(false)
const selectedVersions = ref([])
const historyTableRef = ref(null)

const diffVisible = ref(false)
const diffLoading = ref(false)
const diffResult = ref(null)
const selectedDiffFile = ref(null)

const getDiffTagType = (status) => {
    if (status === 'added') return 'success'
    if (status === 'deleted') return 'danger'
    if (status === 'modified') return 'warning'
    return 'info'
}

const newOntologyForm = ref({
    code: '',
    name: ''
})

const newVersionForm = ref({
    code: ''
})

const uniqueOntologyCodes = computed(() => {
    // Extract unique codes from tableData to populate dropdown
    // Note: tableData might contain multiple versions if we were listing all, 
    // but default list is latest active? Actually list endpoint returns "OntologyPackage".
    // We should probably rely on a computed property that groups by code or just distinct codes.
    const map = new Map()
    tableData.value.forEach(item => {
        if (item.code && !map.has(item.code)) {
             map.set(item.code, item)
        }
    })
    return Array.from(map.values())
})

const handleExceedNew = (files) => {
    newUploadRef.value.clearFiles()
    const file = files[0]
    newUploadRef.value.handleStart(file)
}

const handleExceedVersion = (files) => {
    versionUploadRef.value.clearFiles()
    const file = files[0]
    versionUploadRef.value.handleStart(file)
}

const handleFileChange = (file, type) => {
    if (type === 'new') {
        newFileSelected.value = true
    } else {
        versionFileSelected.value = true
    }
}

const submitNewOntology = () => {
    newUploadRef.value.submit()
}

const submitNewVersion = () => {
    versionUploadRef.value.submit()
}

// 更新相关
const updateInput = ref(null)
const currentUpdateRow = ref(null)

// 订阅相关
const webhooks = ref([])
const fetchAllWebhooks = async () => {
    try {
        const res = await axios.get('/api/webhooks')
        webhooks.value = res.data
    } catch (e) {
        console.error("Failed to fetch webhooks", e)
    }
}

const webhookCount = computed(() => webhooks.value.length)

// 订阅状态返回 (name-> status list)
const subscriptionStatus = ref({})

const fetchSubscriptionStatus = async (row) => {
  // Use code primarily if available
  const params = {}
  if (row.code) params.code = row.code
  if (row.name) params.name = row.name

  try {
    const res = await axios.get('/api/subscriptions/ontologies/status', {
      params: params
    })
    // Key by code if available, else name
    const key = row.code || row.name
    subscriptionStatus.value[key] = res.data
  } catch (error) {
    console.error('获取订阅状态失败', error)
  }
}

const getEffectiveWebhooksCount = (row) => {
  const name = row.name
  const code = row.code
  return webhooks.value.filter(wh => {
      if (!wh.ontology_filter) return true
      return wh.ontology_filter === name || (code && wh.ontology_filter === code)
  }).length
}

const getEffectiveWebhooks = (row) => {
    const name = row.name
    const code = row.code
    return webhooks.value.filter(wh => {
         if (!wh.ontology_filter) return true
         return wh.ontology_filter === name || (code && wh.ontology_filter === code)
    })
}

// 详情相关
const fileTreeData = ref([])
const defaultProps = {
  children: 'children',
  label: 'label',
}
const fileContent = ref('')
const currentFileName = ref('')
const contentLoading = ref(false)
const currentPackageId = ref('')

// Ontology Logs related
const ontologyLogDrawerVisible = ref(false)
const ontologyLogDrawerTitle = ref('')
const ontologyLogsData = ref([])
const ontologyLogsLoading = ref(false)
const currentOntologyNameForLogs = ref('')

const handleOntologyLogs = (row) => {
    currentOntologyNameForLogs.value = row.name
    ontologyLogDrawerTitle.value = `"${row.name}" 推送日志 (跨版本)`
    ontologyLogDrawerVisible.value = true
    fetchOntologyLogs()
}

const fetchOntologyLogs = async () => {
    if (!currentOntologyNameForLogs.value) return
    ontologyLogsLoading.value = true
    try {
        const res = await axios.get('/api/logs/ontologies', {
            params: { name: currentOntologyNameForLogs.value } // Logs still use name? Ideally verify backend
        })
        ontologyLogsData.value = res.data
    } catch (e) {
        ElMessage.error('获取日志失败')
    } finally {
        ontologyLogsLoading.value = false
    }
}

const openAddVersion = (row) => {
    uploadTab.value = 'version'
    newVersionForm.value.code = row.code
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' })
}



const fetchOntologies = async () => {
  loading.value = true
  try {
    const [ontRes, whRes] = await Promise.all([
        axios.get('/api/ontologies'),
        axios.get('/api/webhooks')
    ])
    tableData.value = ontRes.data
    webhooks.value = whRes.data
  } catch (error) {
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

const handleHistory = async (row) => {
    currentHistoryRow.value = row
    historyDrawerVisible.value = true
    historyDrawerTitle.value = `"${row.name}" 版本历史`
    refreshHistory()
}

const refreshHistory = async () => {
    if (!currentHistoryRow.value) return
    historyLoading.value = true
    historyData.value = [] // Optional: clear or keep old while loading
    
    try {
        const res = await axios.get('/api/ontologies', {
            params: { code: currentHistoryRow.value.code, all_versions: true }
        })
        historyData.value = res.data
    } catch (e) {
        ElMessage.error("获取历史版本失败")
    } finally {
        historyLoading.value = false
    }
}

const handleActivate = async (row) => {
    try {
        await ElMessageBox.confirm(
            `确认启用版本 v${row.version} 吗？\n该操作会触发 Webhook 推送。`,
            '启用版本',
            { type: 'warning' }
        )
        
        await axios.post(`/api/ontologies/${row.id}/activate`)
        ElMessage.success(`版本 v${row.version} 已启用`)
        
        // Refresh main list
        fetchOntologies()

        // Refresh history list with a slight delay to allow webhooks to process
        setTimeout(() => {
            if (historyDrawerVisible.value) {
                refreshHistory()
            } else {
                 handleHistory(row)
            }
        }, 1000)
        
        // Show delivery status (reuse dialog)
        lastUploadedPackageId.value = row.id
        deliveryDialogVisible.value = true
        
    } catch (e) {
        if (e !== 'cancel') ElMessage.error("启用失败")
    }
}

const handleSelectionChange = (selection) => {
    if (selection.length > 2) {
        // Keep only last 2
        const lastTwo = selection.slice(-2)
        historyTableRef.value.clearSelection()
        lastTwo.forEach(row => {
            historyTableRef.value.toggleRowSelection(row, true)
        })
        selectedVersions.value = lastTwo
    } else {
        selectedVersions.value = selection
    }
}

const handleCompare = async () => {
    if (selectedVersions.value.length !== 2) return
    
    // Sort by version descending to find base/target
    const sorted = [...selectedVersions.value].sort((a, b) => a.version - b.version)
    const base = sorted[0]
    const target = sorted[1]
    
    selectedDiffFile.value = null // Reset selected file state
    diffLoading.value = true
    diffVisible.value = true
    diffResult.value = null
    
    try {
        const res = await axios.get('/api/ontologies/compare', {
            params: {
                base_id: base.id,
                target_id: target.id
            }
        })
        diffResult.value = res.data
    } catch (e) {
        ElMessage.error('对比失败')
        diffVisible.value = false
    } finally {
        diffLoading.value = false
    }
}

// Removed: handleBeforeUpload is no longer needed as we use manual submit
// const handleBeforeUpload = async (file) => ...

const handleUploadSuccess = (response) => {
  ElMessage.success(`上传成功: ${response.code} v${response.version}`)
  fetchOntologies()
  
  // Clear forms
  if (uploadTab.value === 'new') {
      newOntologyForm.value = { code: '', name: '' }
      newUploadRef.value.clearFiles()
      newFileSelected.value = false
  } else {
      newVersionForm.value = { code: '' }
      versionUploadRef.value.clearFiles()
      versionFileSelected.value = false
  }
  
  // Show delivery status (reuse dialog? Wait, response might be bare list or single obj)
  if (response.id) {
    lastUploadedPackageId.value = response.id
    deliveryDialogVisible.value = true
  }
}

const handleUploadError = () => {
  ElMessage.error('上传失败')
}

const getStatusType = (status) => {
  if (status === 'READY') return 'success'
  if (status === 'UPLOADING' || status === 'PROCESSING') return 'warning'
  if (status === 'ERROR') return 'danger'
  return 'info'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  // Backend returns naive UTC (no Z). Append Z to ensure it's treated as UTC.
  const date = new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z')
  return date.toLocaleString()
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    '确定要长期删除该本体包吗?',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await axios.delete(`/api/ontologies/${row.id}`)
      ElMessage.success('删除成功')
      fetchOntologies()
      
      // Refresh history if drawer is open
      if (historyDrawerVisible.value) {
           const res = await axios.get('/api/ontologies', {
                params: { code: row.code, all_versions: true }
           })
           historyData.value = res.data
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

// 点击更新按钮
const handleUpdate = (row) => {
    currentUpdateRow.value = row
    if (updateInput.value) {
        updateInput.value.value = '' // 清空以便重复选择
        updateInput.value.click()
    }
}

// 处理文件选择 (用于更新)
const handleUpdateFileChange = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    // 如果文件名不一致，提示用户
    if (currentUpdateRow.value && file.name !== currentUpdateRow.value.name) {
        try {
            await ElMessageBox.confirm(
                `您选择的文件 "${file.name}" 与当前本体 "${currentUpdateRow.value.name}" 名称不一致。\n\n这将创建一个新的本体记录(v1)，而不是当前本体的新版本。是否继续?`,
                '文件名不匹配',
                {
                    confirmButtonText: '继续 (新建)',
                    cancelButtonText: '取消',
                    type: 'info'
                }
            )
        } catch (e) {
            ElMessage.info('操作已取消')
            return
        }
    } 
    // 不需要覆盖确认了，因为现在是自动增加版本

    // 手动上传
    const formData = new FormData()
    formData.append('file', file)

    const loadingInstance = ElMessage.info({ message: '正在上传...', duration: 0 })
    
    try {
        const res = await axios.post('/api/ontologies', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
        loadingInstance.close()
        handleUploadSuccess(res.data)
    } catch (e) {
        loadingInstance.close()
        handleUploadError()
    }
}

// 将扁平的文件路径列表转换为树结构
const buildFileTree = (files) => {
    if (!files || files.length === 0) return []
    
    const root = []
    
    files.forEach(file => {
        const parts = file.file_path.split('/') // 假设 file_path 使用 / 分隔
        let currentLevel = root
        
        parts.forEach((part, index) => {
            let existingNode = currentLevel.find(n => n.label === part)
            if (!existingNode) {
                existingNode = {
                    label: part,
                    children: [],
                    isFile: index === parts.length - 1, // 最后一层是文件
                    fullPath: file.file_path // 只有文件节点需要完整路径
                }
                currentLevel.push(existingNode)
            }
            currentLevel = existingNode.children
        })
    })
    return root
}

const handleView = async (row) => {
  currentPackageId.value = row.id
  dialogVisible.value = true
  // Reset
  fileContent.value = ''
  currentFileName.value = ''
  
  try {
     const res = await axios.get(`/api/ontologies/${row.id}`)
     fileTreeData.value = buildFileTree(res.data.files)
  } catch (e) {
     ElMessage.error('获取详情失败')
  }
}

const handleNodeClick = async (data) => {
    if (!data.isFile) return
    currentFileName.value = data.label
    contentLoading.value = true
    try {
        const res = await axios.get(`/api/ontologies/${currentPackageId.value}/files`, {
            params: { path: data.fullPath }
        })
        fileContent.value = res.data.content
    } catch (e) {
        ElMessage.error('读取文件内容失败')
        fileContent.value = "读取失败"
    } finally {
        contentLoading.value = false
    }
}

onMounted(() => {
  fetchOntologies()
  fetchAllWebhooks()
})
</script>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background-color: #f0f2f5;
}
.diff-wrapper {
  display: flex;
  height: 75vh;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.diff-sidebar {
  width: 280px;
  border-right: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 12px;
  background: #f8f9fa;
  font-weight: bold;
  font-size: 13px;
  border-bottom: 1px solid #ebeef5;
}

.diff-file-list {
  flex: 1;
  overflow-y: auto;
}

.diff-file-item {
  padding: 10px 15px;
  cursor: pointer;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.diff-file-item:hover {
  background: #f0f2f5;
}

.diff-file-item.is-active {
  background: #ecf5ff;
  color: #409eff;
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  background: #909399;
}

.added .status-dot { background: #67c23a; }
.deleted .status-dot { background: #f56c6c; }
.modified .status-dot { background: #e6a23c; }

.diff-file-item .file-path {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.diff-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.diff-main-header {
  padding: 10px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  gap: 12px;
}

.diff-viewer-area {
  flex: 1;
  overflow: auto;
}

.empty-diff {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.layout-container {
  height: 100vh;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.detail-container {
   display: flex;
   height: 60vh;
   border: 1px solid #dcdfe6;
}
.file-tree {
   width: 300px;
   border-right: 1px solid #dcdfe6;
   padding: 10px;
   overflow-y: auto;
}
.file-content {
   flex: 1;
   padding: 20px;
   overflow-y: auto;
   background-color: #fafafa;
}
.code-block {
    background-color: #fff;
    padding: 15px;
    border: 1px solid #eaeaea;
    border-radius: 4px;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
}
</style>
