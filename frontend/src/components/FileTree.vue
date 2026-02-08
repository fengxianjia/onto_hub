<template>
  <div class="file-tree">
    <div v-for="(item, index) in tree" :key="index" class="file-tree-item">
      <div 
        :class="['flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all duration-200', 
                 selectedPath === item.path ? 'bg-accent/10 text-accent' : 'hover:bg-muted/50']"
        :style="{ paddingLeft: `${level * 20 + 12}px` }"
        @click="handleClick(item)"
      >
        <!-- Icon -->
        <svg v-if="item.type === 'directory'" class="h-4 w-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
        <svg v-else class="h-4 w-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
        
        <!-- Expand/Collapse Icon for directories -->
        <svg v-if="item.type === 'directory'" 
             :class="['h-3 w-3 flex-shrink-0 transition-transform', expanded[item.path] ? 'rotate-90' : '']" 
             fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
        
        <!-- Name -->
        <span class="text-sm truncate">{{ item.name }}</span>
        
        <!-- Size badge for files -->
        <Badge v-if="item.type === 'file' && item.size" variant="default" size="sm" class="ml-auto">
          {{ formatSize(item.size) }}
        </Badge>
      </div>
      
      <!-- Children (recursive) -->
      <div v-if="item.type === 'directory' && expanded[item.path] && item.children" class="file-tree-children">
        <FileTree 
          :tree="item.children" 
          :level="level + 1"
          :selected-path="selectedPath"
          @select="$emit('select', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Badge } from './index.js'

const props = defineProps({
  tree: {
    type: Array,
    default: () => []
  },
  level: {
    type: Number,
    default: 0
  },
  selectedPath: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['select'])

const expanded = ref({})

// 默认展开所有文件夹
watch(() => props.tree, (newVal) => {
  if (!newVal) return
  newVal.forEach(item => {
    if (item.type === 'directory') {
      expanded.value[item.path] = true
    }
  })
}, { immediate: true })

const handleClick = (item) => {
  if (item.type === 'directory') {
    expanded.value[item.path] = !expanded.value[item.path]
  } else {
    emit('select', item)
  }
}

const formatSize = (bytes) => {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
}
</script>

<style scoped>
.file-tree {
  user-select: none;
}
</style>
