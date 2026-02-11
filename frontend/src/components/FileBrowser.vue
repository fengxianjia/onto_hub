<template>
  <div class="flex gap-4" style="height: 72vh;">
    <!-- Left: File Tree -->
    <div class="w-1/3 border-r border-border pr-4 overflow-y-auto">
      <div v-if="loadingFiles" class="flex items-center justify-center py-8">
        <Loading />
      </div>
      <div v-else-if="fileTree">
        <FileTree :tree="fileTree" @select="handleFileSelect" />
      </div>
      <Empty v-else description="无文件数据" />
    </div>

    <!-- Right: File Content Preview -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="!selectedFile" class="flex h-full items-center justify-center">
        <Empty description="请选择文件查看内容" />
      </div>
      <div v-else>
        <div class="mb-4 flex items-center justify-between border-b border-border pb-3">
          <h5 class="font-mono text-sm font-semibold">{{ selectedFile.name }}</h5>
          <Badge variant="default" size="sm">{{ (selectedFile.size / 1024).toFixed(2) }} KB</Badge>
        </div>

        <!-- Loading State -->
        <div v-if="loadingContent" class="flex items-center justify-center py-12">
          <Loading />
        </div>

        <!-- Markdown Rendering -->
        <div
          v-else-if="isMarkdown"
          class="markdown-body overflow-auto rounded-lg border border-border bg-white p-6"
          v-html="renderedMarkdown"
        ></div>

        <!-- Plain Text -->
        <pre
          v-else-if="fileContent"
          class="overflow-auto rounded-lg bg-muted p-4 text-xs"
        >{{ fileContent }}</pre>

        <!-- Error State -->
        <Empty v-else description="无法加载文件内容" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import MarkdownIt from 'markdown-it'
import 'github-markdown-css/github-markdown-light.css'
import { Badge, Empty, Loading } from './index.js'
import FileTree from './FileTree.vue'
import { buildFileTreeFromList } from '../utils/ontology.js'
import { message } from '../utils/message.js'

const props = defineProps({
  ontologyId: [String, Number],
  files: {
    type: Array,
    default: () => []
  }
})

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

const fileTree = computed(() => buildFileTreeFromList(props.files))
const selectedFile = ref(null)
const fileContent = ref('')
const loadingContent = ref(false)

const isMarkdown = computed(() => {
  return selectedFile.value?.name?.toLowerCase().endsWith('.md')
})

const renderedMarkdown = computed(() => {
  if (!fileContent.value || !isMarkdown.value) return ''
  return md.render(fileContent.value)
})

const handleFileSelect = async (file) => {
  if (file.type === 'directory') return
  
  selectedFile.value = file
  loadingContent.value = true
  fileContent.value = ''
  
  try {
    const res = await axios.get(`/api/ontologies/${props.ontologyId}/files`, {
      params: { path: file.path }
    })
    fileContent.value = res.data.content || '(无内容)'
  } catch (error) {
    fileContent.value = '加载失败'
    message.error('加载文件内容失败')
  } finally {
    loadingContent.value = false
  }
}

// 当本体变化时重置
watch(() => props.ontologyId, () => {
  selectedFile.value = null
  fileContent.value = ''
})
</script>
