<template>
  <div class="flex items-center justify-between px-2">
    <div class="flex-1 text-sm text-muted-foreground">
      共 {{ total }} 条记录
    </div>
    <div class="flex items-center space-x-2">
      <div class="flex items-center space-x-1 mr-4">
        <span class="text-sm text-muted-foreground">每页</span>
        <select 
            :value="pageSize" 
            @change="$emit('update:pageSize', Number($event.target.value))"
            class="h-8 rounded-md border border-input bg-background px-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="disabled"
        >
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
        </select>
      </div>
      
      <Button 
        variant="outline" 
        size="sm" 
        :disabled="currentPage <= 1 || disabled"
        @click="changePage(currentPage - 1)"
      >
        上一页
      </Button>
      <div class="text-sm font-medium">
        {{ currentPage }} / {{ totalPages }}
      </div>
      <Button 
        variant="outline" 
        size="sm" 
        :disabled="currentPage >= totalPages || disabled"
        @click="changePage(currentPage + 1)"
      >
        下一页
      </Button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Button from './Button.vue'

const props = defineProps({
  currentPage: {
    type: Number,
    required: true
  },
  pageSize: {
    type: Number,
    required: true
  },
  total: {
    type: Number,
    required: true
  },
  disabled: Boolean
})

const emit = defineEmits(['update:currentPage', 'update:pageSize', 'change'])

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(props.total / props.pageSize))
})

const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return
  emit('update:currentPage', page)
  emit('change', page)
}
</script>
