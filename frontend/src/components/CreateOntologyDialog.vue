<template>
  <Dialog v-model="visible" title="新建本体" size="md">
    <div class="space-y-6">
      <div class="space-y-4">
        <Input
          v-model="form.code"
          label="本体编码"
          placeholder="全局唯一标识 (e.g. auth-module)"
          required
        />
        <Input
          v-model="form.name"
          label="显示名称"
          placeholder="本体名称 (选填，不填默认使用本体编码)"
        />
        <Select
          v-model="form.templateId"
          label="解析模板"
          :options="templateOptions"
          placeholder="选择解析模板 (可选)"
        />
        <Upload
          ref="uploadRef"
          label="文件"
          accept=".zip"
          required
          @change="handleFileChange"
        />
        <div class="flex items-center gap-2 py-2">
          <input 
            type="checkbox" 
            id="create-auto-push" 
            v-model="form.autoPush"
            class="w-4 h-4 text-accent border-gray-300 rounded focus:ring-accent"
          >
          <label for="create-auto-push" class="text-sm font-medium text-foreground cursor-pointer">
            创建后立即推送给订阅者
          </label>
        </div>
      </div>
    </div>
    <template #footer>
      <div class="flex justify-end gap-3">
        <Button variant="secondary" @click="visible = false">取消</Button>
        <Button
          variant="primary"
          :disabled="!form.code || !fileSelected"
          :loading="uploading"
          @click="submit"
        >
          创建并上传
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import { Button, Input, Select, Upload, Dialog } from './index.js'
import { showMessage, message } from '../utils/message.js'

const props = defineProps({
  modelValue: Boolean
})
const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const uploading = ref(false)
const fileSelected = ref(false)
const uploadRef = ref(null)
const templates = ref([])

const form = ref({
  code: '',
  name: '',
  templateId: '',
  autoPush: true
})

const templateOptions = computed(() => [
  { label: '不解析 (仅上传)', value: '' },
  ...templates.value.map(t => ({ label: t.name, value: t.id }))
])

const handleFileChange = (files) => {
  fileSelected.value = files.length > 0
}

const fetchTemplates = async () => {
  try {
    const res = await axios.get('/api/templates/')
    templates.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const submit = async () => {
  const files = uploadRef.value?.getFiles()
  if (!files || files.length === 0) {
    showMessage.warning('请选择文件')
    return
  }
  
  uploading.value = true
  const formData = new FormData()
  formData.append('file', files[0])
  formData.append('code', form.value.code)
  if (form.value.name) formData.append('name', form.value.name)
  if (form.value.templateId) formData.append('template_id', form.value.templateId)
  formData.append('auto_push', form.value.autoPush ? 'true' : 'false')
  
  try {
    const res = await axios.post('/api/ontologies', formData)
    showMessage(`上传成功: ${res.data.code} v${res.data.version}`, 'success')
    emit('success', res.data)
    visible.value = false
    // Reset form
    form.value = { code: '', name: '', templateId: '', autoPush: true }
    uploadRef.value?.clearFiles()
    fileSelected.value = false
  } catch (e) {
    showMessage(message.getErrorMessage(e, '上传失败'), 'error')
  } finally {
    uploading.value = false
  }
}

onMounted(fetchTemplates)

// Reset form when opening
watch(visible, (newVal) => {
  if (newVal) {
    fetchTemplates()
  }
})
</script>
