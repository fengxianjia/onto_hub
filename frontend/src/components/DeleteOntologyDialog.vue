<template>
  <Dialog v-model="visible" title="高危操作：删除本体" width="500px">
    <div class="space-y-4">
      <div class="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
        <p class="font-bold mb-1">警告：此操作不可逆！</p>
        <p>您正在尝试删除本体 <strong>{{ ontologyName }} ({{ ontologyCode }})</strong>。</p>
        <ul class="list-disc list-inside mt-2 space-y-1">
          <li>该本体下的所有<strong>历史版本</strong>将被物理删除。</li>
          <li>所有关联的<strong>文件、实体、关系数据</strong>将全部丢失。</li>
          <li>相关的 Webhook 订阅可能会受到影响。</li>
        </ul>
      </div>
      
      <div class="space-y-2">
        <p class="text-sm font-medium text-foreground">请输入本体编码 <span class="select-all font-mono bg-muted px-1 rounded">{{ ontologyCode }}</span> 以确认删除：</p>
        <Input 
          v-model="confirmCode" 
          placeholder="在此输入编码"
          autocomplete="off"
        />
      </div>
    </div>
    <template #footer>
      <div class="flex justify-end gap-3">
        <Button variant="secondary" @click="visible = false">取消</Button>
        <Button 
          variant="primary" 
          class="bg-red-600 hover:bg-red-700 border-red-600"
          :disabled="confirmCode !== ontologyCode"
          :loading="loading"
          @click="confirmDelete"
        >
          确认彻底删除
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { Button, Input, Dialog } from './index.js'
import { showMessage } from '../utils/message.js'

const props = defineProps({
  modelValue: Boolean,
  ontologyCode: String,
  ontologyName: String
})
const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const confirmCode = ref('')

const confirmDelete = async () => {
  if (confirmCode.value !== props.ontologyCode) return
  
  loading.value = true
  try {
    await axios.delete(`/api/ontologies/by-code/${props.ontologyCode}`)
    showMessage(`本体 ${props.ontologyCode} 已彻底删除`, 'success')
    emit('success')
    visible.value = false
  } catch (error) {
    showMessage(error.response?.data?.detail || '删除失败', 'error')
  } finally {
    loading.value = false
  }
}

watch(visible, (val) => {
  if (val) confirmCode.value = ''
})
</script>
