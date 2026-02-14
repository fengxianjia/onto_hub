<template>
  <div class="space-y-4">
    <div class="flex justify-between items-center">
      <h3 class="font-bold text-lg">实体列表</h3>
      <div class="w-64">
        <Input v-model="searchQuery" placeholder="搜索实体..." />
      </div>
    </div>
    
    <div v-if="loading" class="flex justify-center py-8">
      <Loading />
    </div>
    <div v-else-if="filteredEntities.length === 0" class="py-8">
      <Empty description="暂无实体数据" />
    </div>
    <div v-else class="border rounded-lg overflow-hidden">
      <table class="w-full">
        <thead class="bg-muted/50">
          <tr>
            <th class="px-4 py-2 text-left text-sm font-bold text-foreground">名称</th>
            <th class="px-4 py-2 text-left text-sm font-bold text-foreground">分类</th>
            <th class="px-4 py-2 text-left text-sm font-bold text-foreground">来源文件</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border">
          <tr v-for="entity in filteredEntities" :key="entity.id" class="hover:bg-muted/20">
            <td class="px-4 py-3 font-medium">{{ entity.name }}</td>
            <td class="px-4 py-3">
              <Badge variant="info" size="xs">{{ entity.category }}</Badge>
            </td>
            <td class="px-4 py-3 text-sm text-muted-foreground">{{ entity.file_path }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'

import { getOntologyEntities } from '../api/ontologies.js'
import { Input, Loading, Empty, Badge } from './index.js'

const props = defineProps({
  ontologyId: {
    type: String,
    required: true
  }
})

const loading = ref(false)
const entities = ref([])
const searchQuery = ref('')

const fetchEntities = async () => {
  loading.value = true
  try {
    const res = await getOntologyEntities(props.ontologyId)
    entities.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const filteredEntities = computed(() => {
  if (!searchQuery.value) return entities.value
  const q = searchQuery.value.toLowerCase()
  return entities.value.filter(e => 
    e.name.toLowerCase().includes(q) || 
    e.category.toLowerCase().includes(q) ||
    e.file_path.toLowerCase().includes(q)
  )
})

watch(() => props.ontologyId, () => {
  if (props.ontologyId) fetchEntities()
})

onMounted(() => {
  if (props.ontologyId) fetchEntities()
})
</script>
