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
        <div v-if="activeTab === 'ontology'">
          <OntologyManager 
            ref="ontologyManagerRef"
            @open-upload="uploadDialogVisible = true"
            @view="handleView"
            @history="handleHistory"
            @subscription="handleSubscriptionStatus"
            @delete="openDeleteOntologyDialog"
          />
        </div>
        
        <!-- 订阅设置 Tab -->
        <div v-if="activeTab === 'webhook'">
          <WebhookManager @change="refreshList" />
        </div>
        
        <!-- 解析模板 Tab -->
        <div v-if="activeTab === 'templates'">
          <TemplateManager />
        </div>
      </Container>
    </main>
    
    <!-- Global Dialogs & Drawers -->
    <OntologyDetailDialog 
      v-model="detailDialogVisible" 
      :ontology-id="selectedOntologyId"
      @viewHistory="handleViewHistoryFromDetail"
      @refresh="refreshList"
    />
    
    <VersionHistoryDrawer
      v-model="historyDrawerVisible"
      :ontology-name="selectedOntologyName"
      :ontology-code="selectedOntologyCode"
      @viewDetail="handleViewDetailFromHistory"
      @compare="handleCompareFromHistory"
      @refresh="refreshList"
      @upload-success="handleVersionUploadSuccess"
    />
    
    <VersionCompareDialog
      v-model="compareDialogVisible"
      :new-version="compareVersions.new"
      :old-version="compareVersions.old"
    />
    
    <DeliveryStatusDialog
      v-model="deliveryDialogVisible"
      :package-id="selectedPackageId"
    />

    <VersionPushStatusDialog
      v-model="pushStatusDialog.visible"
      :package-id="pushStatusDialog.packageId"
      :ontology-code="pushStatusDialog.ontologyCode"
      :ontology-name="pushStatusDialog.ontologyName"
      :version="pushStatusDialog.version"
    />

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

    <!-- Refactored Dialogs -->
    <CreateOntologyDialog 
      v-model="uploadDialogVisible" 
      @success="handleCreateSuccess" 
    />

    <DeleteOntologyDialog
      v-model="deleteOntologyDialog.visible"
      :ontology-code="deleteOntologyDialog.code"
      :ontology-name="deleteOntologyDialog.name"
      @success="refreshList"
    />
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { 
  Header, Container, Button, Dialog,
  OntologyManager, CreateOntologyDialog, DeleteOntologyDialog,
  WebhookManager, TemplateManager, SubscriptionList,
  OntologyDetailDialog, VersionHistoryDrawer, VersionCompareDialog,
  DeliveryStatusDialog, VersionPushStatusDialog
} from './components/index.js'

// Tabs
const tabs = [
  { label: '本体库管理', value: 'ontology' },
  { label: '订阅设置', value: 'webhook' },
  { label: '解析模板', value: 'templates' }
]
const activeTab = ref('ontology')
const ontologyManagerRef = ref(null)

// Dialog states
const uploadDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const historyDrawerVisible = ref(false)
const compareDialogVisible = ref(false)
const deliveryDialogVisible = ref(false)
const subscriptionDialogVisible = ref(false)

const selectedOntologyId = ref(null)
const selectedOntologyName = ref('')
const selectedOntologyCode = ref('')
const selectedPackageId = ref(null)

const compareVersions = reactive({ new: null, old: null })

const pushStatusDialog = ref({
  visible: false,
  packageId: '',
  ontologyCode: '',
  ontologyName: '',
  version: ''
})

const deleteOntologyDialog = reactive({
  visible: false,
  code: '',
  name: ''
})

// Methods
const tabClasses = (value) => {
  const base = 'px-8 py-4 text-base font-bold transition-all duration-300 border-b-4 cursor-pointer'
  return value === activeTab.value
    ? `${base} border-accent text-accent scale-105`
    : `${base} border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground/30`
}

const refreshList = () => {
  ontologyManagerRef.value?.fetchOntologies()
}

const handleCreateSuccess = (data) => {
  if (data.subscriber_count > 0) {
    pushStatusDialog.value = {
      visible: true,
      packageId: data.id,
      ontologyCode: data.code,
      ontologyName: data.name,
      version: data.version
    }
  }
  refreshList()
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

const handleSubscriptionStatus = (row) => {
  selectedOntologyCode.value = row.code
  selectedOntologyName.value = row.name
  subscriptionDialogVisible.value = true
}

const openDeleteOntologyDialog = (row) => {
  deleteOntologyDialog.code = row.code
  deleteOntologyDialog.name = row.name
  deleteOntologyDialog.visible = true
}

const handleVersionUploadSuccess = (data) => {
  if ((data.autoPush || data.autoPush === undefined) && data.subscriber_count > 0) {
    pushStatusDialog.value = {
      visible: true,
      packageId: data.id,
      ontologyCode: data.code,
      ontologyName: data.name,
      version: data.version
    }
  }
}

const handleViewHistoryFromDetail = (ontology) => {
  selectedOntologyCode.value = ontology.code
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
</script>
