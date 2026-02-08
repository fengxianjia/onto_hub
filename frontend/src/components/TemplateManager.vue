<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center">
      <h2 class="text-xl font-bold text-foreground">解析模板管理</h2>
      <Button variant="primary" size="sm" @click="openDialog()">
        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        新建模板
      </Button>
    </div>

    <!-- Usage Guide Toggle -->
    <div class="flex justify-end">
      <Button variant="ghost" size="sm" @click="showGuide = !showGuide" class="text-muted-foreground hover:text-foreground">
        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        {{ showGuide ? '隐藏配置指南' : '显示配置指南' }}
      </Button>
    </div>

    <!-- Usage Guide -->
    <Card v-if="showGuide" variant="flat" class="bg-muted/30 border-dashed border-2 animate-in fade-in slide-in-from-top-2">
      <div class="space-y-3">
        <h3 class="font-bold flex items-center gap-2 text-foreground">
          <svg class="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
          模板配置指南
        </h3>
        <p class="text-sm text-muted-foreground">解析模板用于告诉系统如何从 Markdown 文件中提取实体和关系。默认假设<b>一个文件代表一个实体</b>。</p>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
          <div>
            <h4 class="font-semibold mb-2 text-foreground">1. 实体识别 (Entity)</h4>
            <ul class="list-disc list-inside space-y-1 text-muted-foreground">
              <li><code class="bg-muted px-1 rounded text-foreground">name_source</code>: 实体名称来源
                <ul class="pl-5 mt-1 list-none text-xs space-y-1">
                  <li>• "filename_no_ext": 使用文件名 (默认, e.g. <code>User.md</code> → User)</li>
                  <li>• "frontmatter:title": 使用 YAML 头部的 title 字段</li>
                </ul>
              </li>
              <li><code class="bg-muted px-1 rounded text-foreground">category_source</code>: 实体分类来源
                <ul class="pl-5 mt-1 list-none text-xs space-y-1">
                  <li>• "directory": 使用所在文件夹名 (默认, e.g. <code>Models/User.md</code> → Models)</li>
                  <li>• "frontmatter:type": 使用 YAML 头部的 type 字段</li>
                </ul>
              </li>
            </ul>
          </div>
          <div>
            <h4 class="font-semibold mb-2 text-foreground">2. 关系提取 (Relation)</h4>
            <ul class="list-disc list-inside space-y-1 text-muted-foreground">
              <li><code class="bg-muted px-1 rounded text-foreground">strategies</code>: 提取策略列表
                <ul class="pl-5 mt-1 list-none text-xs space-y-1">
                  <li>• "wikilink": 支持 <code>[[EntityName]]</code> 语法自动建立关系</li>
                </ul>
              </li>
            </ul>
          </div>
          <div class="md:col-span-2">
            <h4 class="font-semibold mb-2 text-foreground">3. 属性提取 (Attribute)</h4>
             <ul class="list-disc list-inside space-y-1 text-muted-foreground">
              <li><code class="bg-muted px-1 rounded text-foreground">regex_patterns</code>: 正则表达式提取规则列表
                <ul class="pl-5 mt-1 list-none text-xs space-y-1">
                  <li>• <code>key</code>: 属性名</li>
                  <li>• <code>pattern</code>: 正则表达式 (使用捕获组 <code>()</code> 提取值)</li>
                </ul>
              </li>
              <li><code class="bg-muted px-1 rounded text-foreground">strategies</code>: 高级提取策略列表
                <ul class="pl-5 mt-1 list-none text-xs space-y-1">
                  <li>• <code>type="table_row"</code>: 提取表格行作为对象列表</li>
                  <li>• <code>target_key</code>: 结果存储字段 (e.g. "properties")</li>
                  <li>• <code>header_mapping</code>: 表头到属性名的映射 (e.g. "显示名称": "name")</li>
                </ul>
              </li>
            </ul>
            <div class="mt-4">
                <h4 class="font-semibold mb-2 text-foreground">示例配置:</h4>
                <div class="relative group">
                    <pre class="bg-muted p-3 rounded-md text-xs font-mono overflow-x-auto text-foreground border border-border">{{ JSON.stringify(defaultRules, null, 2) }}</pre>
                </div>
            </div>
          </div>
        </div>
      </div>
    </Card>

    <!-- Template List -->
    <Card variant="elevated">
       <div v-if="loading" class="flex justify-center py-12">
          <Loading />
       </div>
       <div v-else-if="templates.length === 0" class="py-12">
          <Empty description="暂无模板" />
       </div>
       <div v-else class="overflow-x-auto rounded-lg">
          <table class="w-full">
            <thead class="bg-muted/50">
              <tr>
                <th class="px-6 py-3 text-left text-sm font-bold text-foreground">名称</th>
                <th class="px-6 py-3 text-left text-sm font-bold text-foreground">描述</th>
                <th class="px-6 py-3 text-left text-sm font-bold text-foreground">规则概览</th>
                <th class="px-6 py-3 text-left text-sm font-bold text-foreground">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border">
              <tr v-for="t in templates" :key="t.id" class="hover:bg-muted/20 transition-colors">
                <td class="px-6 py-4 font-medium">{{ t.name }}</td>
                <td class="px-6 py-4 text-muted-foreground">{{ t.description || '-' }}</td>
                <td class="px-6 py-4">
                  <Badge variant="info" size="sm">JSON Rules</Badge>
                </td>
                <td class="px-6 py-4">
                  <div class="flex gap-2">
                    <Button variant="ghost" size="xs" @click="openDialog(t)">编辑</Button>
                    <Button variant="ghost" size="xs" class="text-danger hover:text-danger hover:bg-danger/10" @click="handleDelete(t)">删除</Button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
       </div>
    </Card>

    <!-- Edit Dialog -->
    <Dialog v-model="dialogVisible" :title="editingId ? '编辑模板' : '新建模板'" width="600px">
      <div class="space-y-4">
        <Input v-model="form.name" label="模板名称" placeholder="e.g. Standard Wiki" required />
        <Input v-model="form.description" label="描述" placeholder="模板用途说明" />
        
        <div class="space-y-1">
          <label class="block text-sm font-medium text-foreground">解析规则 (JSON)</label>
          <textarea
            v-model="form.rules"
            class="w-full h-64 px-3 py-2 bg-background border border-input rounded-md focus:ring-2 focus:ring-ring focus:border-input font-mono text-sm"
            placeholder='{ "entity": { ... }, "relation": { ... } }'
          ></textarea>
          <p class="text-xs text-muted-foreground">请配置实体和关系提取规则的 JSON。</p>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <Button variant="secondary" @click="dialogVisible = false">取消</Button>
          <Button variant="primary" :loading="saving" @click="submitForm">保存</Button>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Button, Card, Empty, Loading, Badge, Dialog, Input } from './index.js'
import { showMessage } from '../utils/message.js'

const templates = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const showGuide = ref(false)

const editingId = ref(null)
const form = ref({
  name: '',
  description: '',
  rules: '{}'
})

const defaultRules = {
  entity: {
    name_source: "filename_no_ext",
    category_source: "directory"
  },
  relation: {
    strategies: ["wikilink"]
  },
  attribute: {
    regex_patterns: [
       { key: "status", pattern: "Status: (\\w+)" }
    ],
    strategies: [
       {
         type: "table_row",
         target_key: "properties",
         header_mapping: {
           "显示名称": "name",
           "类型": "dataType"
         }
       }
    ]
  }
}

const fetchTemplates = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/templates/')
    templates.value = res.data
  } catch (e) {
    showMessage('获取模板列表失败', 'error')
  } finally {
    loading.value = false
  }
}

const openDialog = (template = null) => {
  if (template) {
    editingId.value = template.id
    form.value = {
      name: template.name,
      description: template.description,
      rules: template.rules // Assuming rules is string in response? 
      // Schema says rules is str.
    }
  } else {
    editingId.value = null
    form.value = {
      name: '',
      description: '',
      rules: JSON.stringify(defaultRules, null, 2)
    }
  }
  dialogVisible.value = true
}

const submitForm = async () => {
  if (!form.value.name) {
    showMessage('请输入模板名称', 'warning')
    return
  }
  
  // Validate JSON
  try {
    JSON.parse(form.value.rules)
  } catch (e) {
    showMessage('规则 JSON 格式不正确', 'error')
    return
  }
  
  saving.value = true
  try {
    const payload = {
      name: form.value.name,
      description: form.value.description,
      rules: form.value.rules
    }
    
    if (editingId.value) {
      await axios.put(`/api/templates/${editingId.value}`, payload)
      showMessage('更新成功', 'success')
    } else {
      await axios.post('/api/templates/', payload)
      showMessage('创建成功', 'success')
    }
    dialogVisible.value = false
    fetchTemplates()
  } catch (e) {
    showMessage('保存失败', 'error')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (template) => {
  if (!confirm(`确定要删除模板 "${template.name}" 吗？`)) return
  
  try {
    await axios.delete(`/api/templates/${template.id}`)
    showMessage('删除成功', 'success')
    fetchTemplates()
  } catch (e) {
    showMessage('删除失败', 'error')
  }
}

onMounted(() => {
  fetchTemplates()
})
</script>
