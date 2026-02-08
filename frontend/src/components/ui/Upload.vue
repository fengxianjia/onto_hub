<template>
  <div class="w-full">
    <label v-if="label" class="mb-2 block text-sm font-medium text-foreground">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    <div :class="uploadAreaClasses" @click="triggerFileInput" @dragover.prevent="isDragging = true" @dragleave.prevent="isDragging = false" @drop.prevent="handleDrop">
      <input ref="fileInput" type="file" :accept="accept" :multiple="multiple" class="hidden" @change="handleFileChange" />
      <div v-if="!fileList.length" class="flex flex-col items-center gap-3">
        <svg class="h-12 w-12 text-muted-foreground/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <div class="text-center">
          <p class="text-sm font-medium text-foreground">点击或拖拽文件到此处上传</p>
          <p class="mt-1 text-xs text-muted-foreground">{{ accept || '支持任意格式' }}</p>
        </div>
      </div>
      <div v-else class="space-y-2">
        <div v-for="(file, index) in fileList" :key="index" class="flex items-center justify-between rounded-lg border border-border bg-muted/30 px-4 py-3">
          <div class="flex items-center gap-3">
            <svg class="h-5 w-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div>
              <p class="text-sm font-medium text-foreground">{{ file.name }}</p>
              <p class="text-xs text-muted-foreground">{{ formatFileSize(file.size) }}</p>
            </div>
          </div>
          <button @click.stop="removeFile(index)" class="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-red-500">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { cn } from '../../utils/cn.js'

const props = defineProps({
  label: String,
  accept: String,
  multiple: Boolean,
  required: Boolean
})

const emit = defineEmits(['change', 'remove'])

const fileInput = ref(null)
const fileList = ref([])
const isDragging = ref(false)

const uploadAreaClasses = computed(() => {
  const base = 'relative cursor-pointer rounded-xl border-2 border-dashed p-8 transition-all duration-200'
  const drag = isDragging.value ? 'border-accent bg-accent/5' : 'border-border hover:border-accent/50 hover:bg-muted/30'
  return cn(base, drag)
})

const triggerFileInput = () => fileInput.value?.click()

const handleFileChange = (e) => {
  const files = Array.from(e.target.files || [])
  addFiles(files)
}

const handleDrop = (e) => {
  isDragging.value = false
  const files = Array.from(e.dataTransfer.files || [])
  addFiles(files)
}

const addFiles = (files) => {
  fileList.value = props.multiple ? [...fileList.value, ...files] : files.slice(0, 1)
  emit('change', fileList.value)
}

const removeFile = (index) => {
  fileList.value.splice(index, 1)
  emit('remove', index)
  emit('change', fileList.value)
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

defineExpose({
  clearFiles: () => {
    fileList.value = []
    if (fileInput.value) fileInput.value.value = ''
  },
  getFiles: () => fileList.value
})
</script>
