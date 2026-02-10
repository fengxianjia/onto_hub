<template>
  <div class="space-y-8 animate-slideUp">
    <!-- Header Area -->
    <Card variant="flat" class="mb-0 overflow-visible">
      <div class="flex justify-between items-center py-2 px-1">
        <h3 class="text-2xl font-bold text-foreground">本体列表</h3>
        <div class="flex gap-3">
          <Button variant="ghost" size="sm" @click="fetchOntologies" title="刷新">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </Button>
          <Button variant="primary" size="sm" @click="$emit('open-upload')">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            新建本体
          </Button>
        </div>
      </div>
    </Card>
    
    <!-- Ontology List Card -->
    <Card class="shadow-xl" variant="elevated">
      <div v-if="loading" class="flex justify-center py-12">
        <Loading />
      </div>
      
      <div v-else-if="tableData.length === 0" class="py-12">
        <Empty description="暂无本体数据" />
      </div>
      
      <div v-else class="overflow-x-auto rounded-lg">
        <table class="w-full">
          <thead class="bg-gradient-to-r from-muted/80 to-muted/40">
            <tr>
              <th class="px-8 py-4 text-left text-base font-bold text-foreground">编码</th>
              <th class="px-8 py-4 text-left text-base font-bold text-foreground">名称</th>
              <th class="px-8 py-4 text-left text-base font-bold text-foreground">版本</th>
              <th class="px-8 py-4 text-left text-base font-bold text-foreground">解析模板</th>
              <th class="px-8 py-4 text-left text-base font-bold text-foreground">上传时间</th>
              <th class="px-8 py-4 text-left text-base font-bold text-foreground">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border">
            <tr v-for="(row, index) in tableData" :key="row.id" 
                :class="['transition-all duration-200 hover:bg-accent/5 hover:shadow-md', index % 2 === 0 ? 'bg-white' : 'bg-muted/20']">
              <td class="px-8 py-5">
                <Badge variant="info" outline size="lg">{{ row.code || '-' }}</Badge>
              </td>
              <td class="px-8 py-5 text-base font-medium">{{ row.name }}</td>
              <td class="px-8 py-5">
                <Badge variant="accent" size="lg">v{{ row.version }}</Badge>
              </td>
              <td class="px-8 py-5">
                <span class="text-sm text-muted-foreground">{{ row.template_name || '-' }}</span>
              </td>
              <td class="px-8 py-5 text-sm text-muted-foreground">{{ formatDate(row.upload_time) }}</td>
              <td class="px-8 py-5">
                <div class="flex gap-3">
                  <Button variant="ghost" size="sm" @click="$emit('view', row)">详情</Button>
                  <Button variant="ghost" size="sm" @click="$emit('history', row)">版本</Button>
                  <Button variant="ghost" size="sm" @click="$emit('subscription', row)">订阅状态</Button>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    class="text-red-600 hover:text-red-700 hover:bg-red-50 font-bold"
                    @click="$emit('delete', row)"
                  >
                    删除
                  </Button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>
    
    <!-- Pagination -->
    <div v-if="tableData.length" class="flex justify-center">
      <Pagination
        v-model:current-page="pagination.currentPage"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :disabled="loading"
        @change="fetchOntologies"
        @update:page-size="fetchOntologies"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { Button, Card, Badge, Empty, Loading, Pagination } from './index.js'
import { showMessage, message } from '../utils/message.js'

const emit = defineEmits(['open-upload', 'view', 'history', 'subscription', 'delete'])

const tableData = ref([])
const loading = ref(false)
const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z')
  return date.toLocaleString()
}

const fetchOntologies = async () => {
  loading.value = true
  try {
    const skip = (pagination.currentPage - 1) * pagination.pageSize
    const res = await axios.get('/api/ontologies', {
        params: {
            skip,
            limit: pagination.pageSize
        }
    })
    tableData.value = res.data.items
    pagination.total = res.data.total
  } catch (e) {
    showMessage(message.getErrorMessage(e, '获取本体列表失败'), 'error')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchOntologies()
})

// Expose fetch for parent use
defineExpose({ fetchOntologies })
</script>
