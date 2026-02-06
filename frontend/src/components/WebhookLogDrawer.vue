<template>
  <el-drawer v-model="visible" :title="title" size="700px">
    <el-table :data="logsData" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="created_at" label="时间" width="160">
        <template #default="scope">
          {{ formatDate(scope.row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="webhook_name" label="订阅名称" width="120" show-overflow-tooltip />
      <el-table-column label="版本" width="80">
        <template #default="scope">
          <el-tag size="small" effect="plain" v-if="getOntologyVersion(scope.row.payload)">
            v{{ getOntologyVersion(scope.row.payload) }}
          </el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="结果" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'SUCCESS' ? 'success' : 'danger'">
            {{ scope.row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="response_status" label="Code" width="80" />
      <el-table-column label="详情" width="100">
        <template #default="scope">
          <el-popover placement="left" :width="400" trigger="click">
            <template #reference>
              <el-button size="small" type="primary" link>
                {{ scope.row.status === 'SUCCESS' ? '查看详情' : '查看错误' }}
              </el-button>
            </template>
            <div style="word-break: break-all;">
              <p v-if="scope.row.error_message" style="color: red;"><strong>错误信息:</strong> {{ scope.row.error_message }}</p>
              <div v-if="scope.row.payload">
                <p><strong>推送内容 (Payload):</strong></p>
                <pre style="background: #f4f4f5; padding: 10px; border-radius: 4px; overflow: auto; max-height: 300px; font-size: 12px;">{{ formatJson(scope.row.payload) }}</pre>
              </div>
            </div>
          </el-popover>
        </template>
      </el-table-column>
    </el-table>
    <div style="margin-top: 20px; text-align: center;">
      <el-button @click="$emit('refresh')" icon="Refresh" circle />
    </div>
  </el-drawer>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: Boolean,
  title: String,
  logsData: Array,
  loading: Boolean
})

const emit = defineEmits(['update:modelValue', 'refresh'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const getOntologyVersion = (payloadStr) => {
    if (!payloadStr) return null
    try {
        const data = JSON.parse(payloadStr)
        return data.version || null
    } catch (e) {
        return null
    }
}

const formatJson = (jsonStr) => {
    if (!jsonStr) return ''
    try {
        const obj = JSON.parse(jsonStr)
        return JSON.stringify(obj, null, 2)
    } catch (e) {
        return jsonStr
    }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z')
  return date.toLocaleString()
}
</script>
