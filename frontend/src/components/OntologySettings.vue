<template>
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
         <div class="flex items-end h-[68px]">
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
            如果您认为当前版本的解析结果不准确，可以使用选定的模板强制后台重新运行提取算法。
            <strong class="block mt-1 underline">重要提示：此操作仅会刷新当前版本的数据。</strong>
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
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { getTemplates } from '../api/templates.js'
import { updateOntologySeries, reparseOntology } from '../api/ontologies.js'
import { Badge, Button, Select as UISelect, Input as UIInput } from './index.js'
import { message, showConfirm } from '../utils/message.js'

const props = defineProps({
  ontology: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['refresh', 'switchToTab'])

const updatingSeries = ref(false)
const reparsing = ref(false)
const templateOptions = ref([])

const editForm = reactive({
  name: props.ontology.name,
  templateId: props.ontology.template_id || ''
})

const reparseForm = reactive({
  templateId: props.ontology.template_id || ''
})

const fetchTemplates = async () => {
  try {
    const res = await getTemplates()
    templateOptions.value = [
      { label: '不解析 (None)', value: '' },
      ...res.data.map(t => ({ label: t.name, value: t.id }))
    ]
  } catch (e) {
    console.error('Failed to fetch templates', e)
  }
}

const handleUpdateSeries = async () => {
  updatingSeries.value = true
  try {
    await updateOntologySeries(props.ontology.code, {
      name: editForm.name,
      default_template_id: editForm.templateId || null
    })
    message.success('本体信息已更新')
    emit('refresh')
  } catch (e) {
    message.error(e.response?.data?.detail || '更新失败')
  } finally {
    updatingSeries.value = false
  }
}

const handleReparse = async () => {
  try {
    await showConfirm(
      `确定要重新解析当前版本 (v${props.ontology.version}) 吗？`,
      '重析确认',
      { confirmButtonText: '确定重析', cancelButtonText: '取消', type: 'warning' }
    )
    
    reparsing.value = true
    await reparseOntology(props.ontology.id, {
      template_id: reparseForm.templateId || null
    })
    message.success('已触发重新解析，后台正在处理中...')
    emit('switchToTab', 'graph')
  } catch (e) {
    if (e !== 'cancel') {
      message.error(e.response?.data?.detail || '解析触发失败')
    }
  } finally {
    reparsing.value = false
  }
}

onMounted(fetchTemplates)
</script>
