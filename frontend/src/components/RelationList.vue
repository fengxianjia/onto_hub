<template>
  <div class="space-y-4">
    <div class="flex justify-between items-center">
      <h3 class="font-bold text-lg">关系列表</h3>
      <div class="w-64">
        <!-- Search could be added later, simplified for now -->
      </div>
    </div>
    
    <div v-if="loading" class="flex justify-center py-8">
      <Loading />
    </div>
    <div v-else-if="relations.length === 0" class="py-8">
      <Empty description="暂无关系数据" />
    </div>
    <div v-else class="border rounded-lg overflow-hidden">
      <table class="w-full">
        <thead class="bg-muted/50">
          <tr>
            <th class="px-4 py-2 text-left text-sm font-bold text-foreground">源实体 (Source)</th>
            <th class="px-4 py-2 text-left text-sm font-bold text-foreground">关系类型 (Type)</th>
            <th class="px-4 py-2 text-left text-sm font-bold text-foreground">目标实体 (Target)</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border">
          <tr v-for="rel in relations" :key="rel.id" class="hover:bg-muted/20">
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                 <Badge variant="outline" size="xs">{{ rel.source.category || 'Unknown' }}</Badge>
                 <span class="font-medium">{{ rel.source.name }}</span>
              </div>
            </td>
            <td class="px-4 py-3">
              <Badge variant="accent" size="xs">{{ rel.relation_type }}</Badge>
            </td>
            <td class="px-4 py-3">
               <div class="flex items-center gap-2">
                 <Badge variant="outline" size="xs">{{ rel.target.category || 'Unknown' }}</Badge>
                 <span class="font-medium">{{ rel.target.name }}</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      
      <!-- Pagination (Simple implementation for now) -->
      <div v-if="total > limit" class="p-4 flex justify-between items-center bg-muted/20 border-t border-border">
          <span class="text-xs text-muted-foreground">显示 {{ relations.length }} / {{ total }} 项</span>
          <div class="flex gap-2">
             <Button variant="ghost" size="xs" :disabled="skip === 0" @click="prevPage">上一页</Button>
             <Button variant="ghost" size="xs" :disabled="skip + relations.length >= total" @click="nextPage">下一页</Button>
          </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { Loading, Empty, Badge, Button } from './index.js'

const props = defineProps({
  ontologyId: {
    type: String,
    required: true
  }
})

const loading = ref(false)
const relations = ref([])
const total = ref(0)
const skip = ref(0)
const limit = ref(20)

const fetchRelations = async () => {
  loading.value = true
  try {
    const res = await axios.get(`/api/ontologies/${props.ontologyId}/relations`, {
        params: { skip: skip.value, limit: limit.value }
    })
    relations.value = res.data.items
    total.value = res.data.total
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const nextPage = () => {
    if (skip.value + relations.value.length < total.value) {
        skip.value += limit.value
        fetchRelations()
    }
}

const prevPage = () => {
    if (skip.value > 0) {
        skip.value = Math.max(0, skip.value - limit.value)
        fetchRelations()
    }
}

watch(() => props.ontologyId, () => {
  if (props.ontologyId) {
      skip.value = 0
      fetchRelations()
  }
})

onMounted(() => {
  if (props.ontologyId) fetchRelations()
})
</script>
