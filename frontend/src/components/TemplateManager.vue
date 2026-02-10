<template>
  <div class="space-y-6 animate-slideUp">
    <!-- Header -->
    <Card variant="flat" class="mb-0 overflow-visible">
      <div class="flex justify-between items-center py-2 px-1">
        <h2 class="text-2xl font-bold text-foreground">解析模板管理</h2>
        <div class="flex gap-3">
          <Button variant="ghost" size="sm" @click="fetchTemplates" title="刷新">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </Button>
          <Button variant="ghost" size="sm" @click="showGuide = !showGuide" :class="['transition-colors', showGuide ? 'text-accent bg-accent/10' : 'text-muted-foreground hover:text-foreground']" title="配置指南">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </Button>
          <Button variant="primary" size="sm" @click="openDialog()">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            新建模板
          </Button>
        </div>
      </div>
    </Card>

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
                  <li>• <code>target_key</code>: 结果存储字段</li>
                  <li>• <code>header_mapping</code>: 解析后的属性映射</li>
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
                    <Button variant="ghost" size="xs" class="text-red-600 hover:text-red-700 hover:bg-red-50 font-bold" @click="handleDelete(t)">删除</Button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
       </div>
    </Card>

    <!-- Edit Dialog -->
    <Dialog v-model="dialogVisible" :title="editingId ? '编辑模板' : '新建模板'" size="lg" :closeOnClickModal="false">
      <div class="space-y-6">
        <div class="grid grid-cols-2 gap-4">
          <Input v-model="form.name" label="模板名称" placeholder="e.g. Standard Wiki" required />
          <Select 
            v-model="form.parser_type" 
            label="解析器类型" 
            :options="[
              { label: 'Markdown (通用文档)', value: 'markdown' },
              { label: 'OWL/RDF (本体文件)', value: 'owl' },
              { label: 'Custom (自定义 JSON)', value: 'custom' }
            ]"
            :disabled="!!editingId"
            @change="handleParserTypeChange"
          />
        </div>
        <div class="grid grid-cols-1">
          <Input v-model="form.description" label="描述" placeholder="模板用途说明" />
        </div>
        
        <div class="flex items-center justify-between border-b pb-4">
          <div class="space-y-1">
            <h3 class="font-bold text-lg text-foreground">
              {{ form.parser_type === 'owl' ? 'OWL 解析策略配置' : (form.parser_type === 'custom' ? '自定义 JSON 规则' : 'Markdown 解析规则配置') }}
            </h3>
            <p class="text-xs text-muted-foreground">
              {{ 
                form.parser_type === 'owl' ? '配置如何从本体图中提取类名和继承关系' : 
                (form.parser_type === 'custom' ? '手动编写 JSON 定义复杂的解析逻辑' : '定义如何从文件内容中通过正则或表格提取实体属性') 
              }}
            </p>
          </div>
          <!-- 仅在特定模式下显示切换，Custom 模式强制源码模式 -->
          <div v-if="form.parser_type !== 'custom'" class="flex items-center bg-muted/30 p-1 rounded-lg border border-border">
            <button 
              @click="configMode = 'visual'"
              :class="['px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-2', 
                        configMode === 'visual' ? 'bg-white text-accent shadow-sm' : 'text-muted-foreground hover:text-foreground']"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7"></path></svg>
              可视化模式
            </button>
            <button 
              @click="toggleToSource"
              :class="['px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-2', 
                        configMode === 'json' ? 'bg-white text-accent shadow-sm' : 'text-muted-foreground hover:text-foreground']"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path></svg>
              源码模式 (JSON)
            </button>
          </div>
        </div>

        <!-- Visual Config Mode (Markdown) -->
        <div v-if="configMode === 'visual' && form.parser_type === 'markdown'" class="space-y-6 max-h-[550px] overflow-y-auto pr-2 custom-scrollbar">
          <!-- 1. Entity Config Block -->
          <div class="bg-muted/30 p-5 rounded-xl border border-border/50 space-y-4 shadow-sm hover:shadow-md transition-shadow">
            <h4 class="font-bold text-base flex items-center gap-2 text-foreground">
              <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
              实体识别 (Entity Recognition)
            </h4>
            <div class="grid grid-cols-2 gap-6">
              <Select
                v-model="visualRules.entity.name_source"
                label="名称来源"
                :options="[
                  { label: '文件名 (无后缀)', value: 'filename_no_ext' },
                  { label: 'YAML 头部 (title)', value: 'frontmatter:title' }
                ]"
              />
              <Select
                v-model="visualRules.entity.category_source"
                label="分类来源"
                :options="[
                  { label: '所在目录名', value: 'directory' },
                  { label: 'YAML 头部 (type)', value: 'frontmatter:type' }
                ]"
              />
            </div>
            <p class="text-[11px] text-muted-foreground px-1">配置系统如何从单文件中识别并命名实体。</p>
          </div>

          <!-- 2. Relation Strategy Block -->
          <div class="bg-muted/30 p-5 rounded-xl border border-border/50 space-y-4 shadow-sm hover:shadow-md transition-shadow">
            <h4 class="font-bold text-base flex items-center gap-2 text-foreground">
              <svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
              关系提取策略 (Relation Extraction)
            </h4>
            <div class="flex items-center justify-between p-4 border border-dashed rounded-lg bg-background shadow-inner">
              <div class="flex items-center gap-3">
                <input type="checkbox" :checked="true" disabled class="w-4 h-4 rounded border-gray-300 text-accent outline-none cursor-not-allowed">
                <div>
                  <div class="text-sm font-semibold">WikiLink 提取</div>
                  <div class="text-xs text-muted-foreground">自动提取 [[Entity]] 格式的内链为关联关系</div>
                </div>
              </div>
              <Badge variant="info" size="xs">Markdown 规范</Badge>
            </div>
          </div>

          <!-- 3. Attribute Extraction Block -->
          <div class="bg-indigo-50/30 p-5 rounded-xl border border-indigo-100 space-y-6 shadow-sm hover:shadow-md transition-shadow">
            <h4 class="font-bold text-base flex items-center gap-2 text-foreground">
              <svg class="w-5 h-5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path></svg>
              实体属性提取 (Attribute Extraction)
            </h4>
            <!-- Regex / Table Patterns (Existing Logic) -->
            <div class="space-y-4">
               <!-- ... 保持现有 Regex 配置逻辑 ... -->
                <div class="flex justify-between items-center bg-white/60 p-2 rounded-lg border border-border/40">
                  <h5 class="font-semibold text-sm">正则规则</h5>
                  <Button variant="ghost" size="xs" @click="addRegexPattern" class="text-accent">+ 添加</Button>
                </div>
                <!-- ... 省略重复内容以便聚焦改动 ... -->
            </div>
          </div>
        </div>

        <!-- Visual Config Mode (OWL) -->
        <div v-else-if="form.parser_type === 'owl'" class="space-y-6 max-h-[550px] overflow-y-auto pr-2 custom-scrollbar">
           <!-- OWL 特定配置 -->
           <div class="bg-amber-50/30 p-6 rounded-xl border border-amber-100 space-y-6">
              <div class="flex items-center gap-3 mb-2">
                <div class="p-2 bg-amber-100 rounded-lg text-amber-700">
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.691.31a2 2 0 01-1.636 0l-.691-.31a6 6 0 00-3.86-.517l-2.387.477a2 2 0 00-1.022.547l1.16 2.32a2 2 0 001.789 1.106h8.182a2 2 0 001.789-1.106l1.16-2.32z"></path></svg>
                </div>
                <div>
                  <h4 class="font-bold text-lg text-foreground">OWL 语义映射</h4>
                  <p class="text-xs text-muted-foreground">本体图形数据与 OntoHub 实体的映射逻辑</p>
                </div>
              </div>

              <div class="grid grid-cols-1 gap-6">
                <div class="space-y-3 p-4 bg-background border border-border rounded-lg">
                  <label class="text-sm font-semibold text-foreground flex items-center gap-2">
                    实体名称来源 (Entity Name)
                    <Badge variant="info" size="xs">推荐</Badge>
                  </label>
                  <Select
                    v-model="visualRules.entity.name_source"
                    :options="[
                      { label: '使用 rdfs:label (最优, 智能 fallback)', value: 'metadata:name' },
                      { label: '使用 URI Fragment (ID 部分)', value: 'metadata:uri_fragment' },
                      { label: '原始文件名', value: 'filename_no_ext' }
                    ]"
                  />
                  <p class="text-[11px] text-muted-foreground italic">
                    提示：OWL 文件通常包含多个类。系统会自动提取 `owl:Class` 并优先尝试读取其 `rdfs:label`。
                  </p>
                </div>

                <div class="space-y-3 p-4 bg-background border border-border rounded-lg">
                  <label class="text-sm font-semibold text-foreground">继承关系映射 (Hierarchy)</label>
                  <div class="flex items-center justify-between p-3 bg-muted/20 border border-dashed rounded-md">
                     <span class="text-xs font-mono text-foreground">rdfs:subClassOf &rarr; OntologyRelation</span>
                     <Badge variant="success" size="xs">自动开启</Badge>
                  </div>
                </div>
              </div>
           </div>
        </div>

        <!-- Raw JSON Mode -->
        <div v-else class="space-y-1">
          <!-- ... 保持现有 JSON 模式逻辑 ... -->
          <label class="block text-sm font-medium text-foreground">规则源码 (JSON)</label>
          <textarea
            v-model="form.rules"
            class="w-full h-96 px-3 py-2 bg-background border border-input rounded-md font-mono text-sm"
          ></textarea>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <Button variant="secondary" @click="dialogVisible = false">取消</Button>
          <Button variant="primary" :loading="saving" @click="submitForm">保存模板</Button>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import axios from 'axios'
import { Button, Card, Empty, Loading, Badge, Dialog, Input, Select } from './index.js'
import { showMessage, message, showConfirm } from '../utils/message.js'

const templates = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const showGuide = ref(false)

const editingId = ref(null)
const configMode = ref('visual')

const form = ref({
  name: '',
  description: '',
  parser_type: 'markdown',
  rules: '{}'
})

const visualRules = reactive({
  entity: {
    name_source: 'filename_no_ext',
    category_source: 'directory'
  },
  relation: {
    wikilink: true
  },
  attribute: {
    regex_patterns: [],
    strategies: []
  }
})

const defaultRulesMarkdown = {
  entity: { name_source: "filename_no_ext", category_source: "directory" },
  relation: { strategies: ["wikilink"] },
  attribute: { regex_patterns: [], strategies: [] }
}

const defaultRulesOWL = {
  entity: { name_source: "metadata:name", category_source: "metadata:type" },
  relation: { strategies: ["owl_subclass"] },
  attribute: { regex_patterns: [], strategies: [] }
}

const defaultRulesCustom = {
  entity: { name_source: "filename_no_ext" },
  relation: { strategies: [] },
  attribute: { regex_patterns: [], strategies: [] }
}

const handleParserTypeChange = (newType) => {
  if (editingId.value) return
  
  // 关键修复：确保 form 表单中的 parser_type 实时同步，
  // 否则 syncJsonToVisual 会因为读取的是旧类型而导致回显/逻辑错误
  form.value.parser_type = newType
  
  let defaults = defaultRulesMarkdown
  if (newType === 'owl') defaults = defaultRulesOWL
  if (newType === 'custom') {
    defaults = defaultRulesCustom
    configMode.value = 'json'
  } else {
    configMode.value = 'visual'
  }
  form.value.rules = JSON.stringify(defaults, null, 2)
  syncJsonToVisual()
}

const syncVisualToJson = () => {
  const rules = {
    entity: { ...visualRules.entity },
    relation: {
      strategies: form.value.parser_type === 'owl' ? ['owl_subclass'] : (visualRules.relation.wikilink ? ['wikilink'] : [])
    },
    attribute: {
      regex_patterns: visualRules.attribute.regex_patterns.filter(p => p.key && p.pattern),
      strategies: visualRules.attribute.strategies.map(s => {
        const mapping = {}
        s.header_maps.forEach(m => { if (m.from) mapping[m.from] = m.to })
        return { type: s.type, target_key: s.target_key, header_mapping: mapping }
      })
    }
  }
  form.value.rules = JSON.stringify(rules, null, 2)
}

const syncJsonToVisual = () => {
  try {
    const rules = JSON.parse(form.value.rules || '{}')
    
    // 基础配置回显
    if (form.value.parser_type === 'owl') {
      visualRules.entity.name_source = rules.entity?.name_source || 'metadata:name'
      visualRules.entity.category_source = rules.entity?.category_source || 'metadata:type'
    } else {
      visualRules.entity.name_source = rules.entity?.name_source || 'filename_no_ext'
      visualRules.entity.category_source = rules.entity?.category_source || 'directory'
    }

    visualRules.relation.wikilink = rules.relation?.strategies?.includes('wikilink') || false
    visualRules.attribute.regex_patterns = rules.attribute?.regex_patterns || []
    visualRules.attribute.strategies = (rules.attribute?.strategies || []).map(s => {
      const header_maps = []
      if (s.header_mapping) Object.entries(s.header_mapping).forEach(([from, to]) => header_maps.push({ from, to }))
      return { type: s.type || 'table_row', target_key: s.target_key || 'properties', header_maps }
    })
    return true
  } catch (e) { 
    console.error('JSON Parse Error:', e)
    return false 
  }
}

const fetchTemplates = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/templates/')
    templates.value = res.data
  } catch (error) {
    showMessage(message.getErrorMessage(error, '获取模板列表失败'), 'error')
  } finally { loading.value = false }
}

const openDialog = (template = null) => {
  if (template) {
    editingId.value = template.id
    form.value = {
      name: template.name,
      description: template.description,
      parser_type: template.parser_type || 'markdown',
      rules: template.rules
    }
    // 联动逻辑：如果是 custom 则进入 JSON 模式，否则进入 visual 模式
    configMode.value = form.value.parser_type === 'custom' ? 'json' : 'visual'
    syncJsonToVisual()
  } else {
    editingId.value = null
    form.value = {
      name: '',
      description: '',
      parser_type: 'markdown',
      rules: JSON.stringify(defaultRulesMarkdown, null, 2)
    }
    configMode.value = 'visual'
    syncJsonToVisual()
  }
  dialogVisible.value = true
}

const submitForm = async () => {
  if (!form.value.name) { showMessage('请输入模板名称', 'warning'); return }
  syncVisualToJson()
  saving.value = true
  try {
    const payload = { ...form.value }
    if (editingId.value) {
      await axios.put(`/api/templates/${editingId.value}`, payload)
      showMessage('更新成功', 'success')
    } else {
      await axios.post('/api/templates/', payload)
      showMessage('创建成功', 'success')
    }
    dialogVisible.value = false
    fetchTemplates()
  } catch (error) {
    showMessage(message.getErrorMessage(error, '保存失败'), 'error')
  } finally { saving.value = false }
}

const handleDelete = async (template) => {
  try {
    await showConfirm(`确定要删除模板 "${template.name}" 吗？`, '删除请求')
    await axios.delete(`/api/templates/${template.id}`)
    showMessage('删除成功', 'success')
    fetchTemplates()
  } catch (error) { if (error !== 'cancel') showMessage(message.getErrorMessage(error, '删除失败'), 'error') }
}

const addRegexPattern = () => {
  visualRules.attribute.regex_patterns.push({ key: '', pattern: '' })
}

const removeRegexPattern = (idx) => {
  visualRules.attribute.regex_patterns.splice(idx, 1)
}

const addTableStrategy = () => {
  visualRules.attribute.strategies.push({
    type: 'table_row',
    target_key: 'properties',
    header_maps: []
  })
}

const removeTableStrategy = (idx) => {
  visualRules.attribute.strategies.splice(idx, 1)
}

const addHeaderMap = (strat) => {
  strat.header_maps.push({ from: '', to: '' })
}

const removeHeaderMap = (strat, idx) => {
  strat.header_maps.splice(idx, 1)
}

const toggleToSource = () => {
  syncVisualToJson()
  configMode.value = 'json'
}

onMounted(fetchTemplates)
</script>
