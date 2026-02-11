<template>
  <div class="h-full flex flex-col relative bg-white">
    <!-- Header Toolbar -->
    <div class="p-3 border-b flex flex-col gap-3 z-20 bg-white/80 backdrop-blur-md">
      <div class="flex items-center justify-between gap-4">
        <div class="flex items-center gap-4 flex-1 min-w-0">
          <div class="flex items-center gap-2 shrink-0">
            <span class="text-xs font-bold text-muted-foreground uppercase tracking-wider">显示节点:</span>
            <div class="flex gap-1">
              <Button variant="ghost" size="xs" @click="selectAllFilters" class="h-6 px-2 text-[10px]">全选</Button>
              <Button variant="ghost" size="xs" @click="clearAllFilters" class="h-6 px-2 text-[10px]">清空</Button>
            </div>
          </div>
          <div class="flex flex-wrap gap-2 overflow-y-auto max-h-24 py-1 pr-2 custom-scrollbar">
            <Badge 
              v-for="cat in allCategories" 
              :key="cat"
              :variant="activeFilters.includes(cat) ? 'info' : 'outline'"
              :class="['cursor-pointer transition-all hover:scale-105 shrink-0', activeFilters.includes(cat) ? 'opacity-100' : 'opacity-40 grayscale-[0.5]']"
              @click="toggleFilter(cat)"
            >
              {{ cat }}
            </Badge>
          </div>
        </div>
      
        <div class="flex items-center gap-2">
          <div class="flex items-center bg-muted/50 p-1 rounded-md border mr-2">
            <button 
              @click="setLayoutMode('force')"
              :class="['px-2 py-1 text-xs font-bold rounded transition-all', layoutMode === 'force' ? 'bg-white shadow-sm text-accent' : 'text-muted-foreground hover:text-foreground']"
            >星图模式</button>
            <button 
              @click="setLayoutMode('grid')"
              :class="['px-2 py-1 text-xs font-bold rounded transition-all', layoutMode === 'grid' ? 'bg-white shadow-sm text-accent' : 'text-muted-foreground hover:text-foreground']"
            >规约布局</button>
          </div>
          <Button variant="ghost" size="sm" @click="resetView" title="重置视角">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
          </Button>
          <div class="w-px h-4 bg-border mx-1"></div>
          <button 
            @click="toggleFullscreen"
            class="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-all"
          >
            <svg v-if="!isFullscreen" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"/>
            </svg>
            <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Main Graph Area -->
    <div class="flex-1 overflow-hidden relative" ref="container">
      <div v-if="loading" class="absolute inset-0 flex justify-center items-center z-10 bg-white/50">
        <Loading />
      </div>
      <div v-else-if="!hasData" class="absolute inset-0 flex justify-center items-center z-10">
        <Empty description="暂无图谱数据,请确认本体解析是否完成" />
      </div>
      
      <!-- Force Graph Container -->
      <div ref="graphContainer" class="w-full h-full"></div>

      <!-- Quick Node Info (Floating) -->
      <transition name="slide-fade">
        <div v-if="hoveredNode" class="absolute bottom-6 left-6 max-w-sm bg-white/90 backdrop-blur-md border shadow-2xl rounded-xl p-4 pointer-events-none z-30">
          <div class="flex items-center gap-2 mb-1">
          <div class="w-2 h-2 rounded-full" :style="{ backgroundColor: getNodeColor(hoveredNode) }"></div>
            <span class="text-xs font-bold text-muted-foreground uppercase opacity-70">{{ hoveredNode.category }}</span>
          </div>
          <h4 class="font-bold text-lg text-foreground truncate">{{ hoveredNode.name }}</h4>
          <p class="text-xs text-muted-foreground font-mono mt-1 opacity-60">{{ hoveredNode.file_path }}</p>
        </div>
      </transition>
    </div>

    <!-- Detail Side Drawer (Logic moved out or reused) -->
    <!-- We keep the existing selectedNode logic but make it optional -->
    <transition name="slide">
      <div v-if="selectedNode" class="absolute right-0 top-0 bottom-0 w-96 bg-white shadow-[-10px_0_30px_rgba(0,0,0,0.1)] border-l p-6 overflow-y-auto z-40">
        <div class="flex justify-between items-center mb-6">
          <h3 class="font-black text-2xl tracking-tight text-foreground">{{ selectedNode.name }}</h3>
          <button @click="selectedNode = null" class="p-2 hover:bg-muted rounded-full transition-colors">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
        <!-- ... content remains similar but better styled ... -->
        <div class="space-y-6">
          <section>
            <div class="flex items-center gap-3 mb-2">
              <span class="text-xs font-bold py-1 px-2 bg-accent/10 text-accent rounded uppercase tracking-widest">{{ selectedNode.category }}</span>
              <span class="text-xs text-muted-foreground font-mono truncate">{{ selectedNode.id.split('-')[0] }}...</span>
            </div>
            <p class="text-sm text-muted-foreground font-mono bg-muted p-2 rounded break-all">{{ selectedNode.file_path }}</p>
          </section>

          <section v-if="Object.keys(parseMetadata(selectedNode.metadata_json)).length">
            <h4 class="text-sm font-bold border-b pb-2 mb-4 flex items-center gap-2">
              <svg class="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              扩展属性
            </h4>
            <div class="space-y-4">
              <div v-for="(val, key) in parseMetadata(selectedNode.metadata_json)" :key="key" class="group">
                <label class="text-[10px] font-bold text-muted-foreground uppercase opacity-50 block transition-opacity group-hover:opacity-100">{{ key }}</label>
                <div class="mt-1">
                  <!-- Complex values (arrays/objects) -->
                  <div v-if="Array.isArray(val) && val.length > 0 && typeof val[0] === 'object'" class="overflow-x-auto">
                    <table class="w-full border text-[11px] bg-muted/30">
                      <thead>
                        <tr class="bg-muted">
                          <th v-for="(h, i) in Object.keys(val[0])" :key="i" class="p-1 border text-left">{{ h }}</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="(row, r) in val" :key="r">
                          <td v-for="(cell, c) in Object.values(row)" :key="c" class="p-1 border">{{ cell }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <ul v-else-if="Array.isArray(val)" class="list-disc list-inside text-sm text-foreground">
                    <li v-for="(item, i) in val" :key="i">{{ item }}</li>
                  </ul>
                  <div v-else class="text-sm text-foreground break-words leading-relaxed">
                    {{ val }}
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
import axios from 'axios'
import ForceGraph from 'force-graph'
import { Loading, Empty, Badge, Button } from './index.js'

const props = defineProps({
  ontologyId: {
    type: String,
    required: true
  }
})

// State
const container = ref(null)
const graphContainer = ref(null)
const graphInstance = ref(null)
const loading = ref(false)
const rawData = ref({ nodes: [], links: [] })
const staticCategories = ref([]) // 关键：持久化分类列表，不受过滤影响
const selectedNode = ref(null)
const hoveredNode = ref(null)
const isFullscreen = ref(false)
const activeFilters = ref([])
const layoutMode = ref('force') // 'force' or 'grid'

// Config constants
// 智能上下文感知色彩系统 (Context-Aware Coloring)
const getNodeColor = (node) => {
  if (!node) return '#94a3b8'
  
  // 核心逻辑：如果当前只显示一个类别，则在该类别内对节点进行色彩区分
  // 否则，按类别进行大的色彩区分以保持结构感
  const isSingleCategory = activeFilters.value.length === 1
  const seed = isSingleCategory ? (node.name + node.id) : node.category
  
  if (!seed) return '#94a3b8'

  // 基于种子内容计算 Hash
  let hash = 0
  for (let i = 0; i < seed.length; i++) {
    hash = seed.charCodeAt(i) + ((hash << 5) - hash)
  }
  
  const h = Math.abs(hash % 360)
  // 如果是单分类，饱和度可以稍微降低一点以显得柔和，或者保持一致
  return `hsl(${h}, 75%, 55%)`
}

// Computed
const allCategories = computed(() => {
  // 核心修复：直接使用初始化时捕获的静态分类列表
  // 彻底避免物理场动态修改 Data 对象引发的 Badge 消失
  return staticCategories.value
})

const hasData = computed(() => rawData.value.nodes.length > 0)

const filteredData = computed(() => {
  if (activeFilters.value.length === 0) return rawData.value
  
  const filteredNodes = rawData.value.nodes.filter(n => activeFilters.value.includes(n.category))
  const nodeIds = new Set(filteredNodes.map(n => n.id))
  const filteredLinks = rawData.value.links.filter(l => nodeIds.has(l.source_id) && nodeIds.has(l.target_id))
  
  return { nodes: filteredNodes, links: filteredLinks }
})

// Methods
const fetchGraph = async () => {
  loading.value = true
  try {
    const res = await axios.get(`/api/ontologies/${props.ontologyId}/graph`)
    rawData.value = res.data
    
    // 初始化静态分类列表 (全量点中提取并冻结)
    const initialCats = new Set(res.data.nodes.map(n => n.category))
    staticCategories.value = Array.from(initialCats).filter(Boolean)
    
    // 初始化过滤器
    activeFilters.value = [...staticCategories.value]
    await nextTick()
    initGraph()
  } catch (e) {
    console.error('Failed to fetch graph:', e)
  } finally {
    loading.value = false
  }
}

const toggleFilter = (cat) => {
  const isOnlyOne = activeFilters.value.length === 1 && activeFilters.value.includes(cat)
  if (isOnlyOne) return // 禁止取消最后一个，防止界面全空
  
  const idx = activeFilters.value.indexOf(cat)
  if (idx > -1) {
    activeFilters.value.splice(idx, 1)
  } else {
    activeFilters.value.push(cat)
  }
  updateGraphData()
}

const selectAllFilters = () => {
  activeFilters.value = [...staticCategories.value]
  updateGraphData()
}

const clearAllFilters = () => {
  // 至少保留一个，这里默认保留第一个分类以防万一
  if (staticCategories.value.length > 0) {
    activeFilters.value = [staticCategories.value[0]]
    updateGraphData()
  }
}

const setLayoutMode = (mode) => {
  layoutMode.value = mode
  applyLayout()
}

const applyLayout = () => {
  if (!graphInstance.value) return
  
  if (layoutMode.value === 'grid') {
    // 算法：按分类和名称进行行列排序
    const nodes = filteredData.value.nodes
    const numNodes = nodes.length
    const cols = Math.ceil(Math.sqrt(numNodes * 1.5))
    const spacing = 120
    
    nodes.forEach((node, i) => {
      node.fx = (i % cols) * spacing - (cols * spacing) / 2
      node.fy = Math.floor(i / cols) * spacing - (Math.sqrt(numNodes) * spacing) / 2
    })
    
    // 停止物理模拟
    graphInstance.value.d3AlphaTarget(0)
  } else {
    // 恢复力导向：释放固定坐标
    filteredData.value.nodes.forEach(node => {
      node.fx = null
      node.fy = null
    })
    // 重热物理模拟
    graphInstance.value.d3ReheatSimulation()
  }
}

const resetView = () => {
  graphInstance.value?.zoomToFit(800)
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    container.value?.requestFullscreen().catch(err => {
      console.error(`Error attempting to enable full-screen mode: ${err.message}`)
    })
  } else {
    document.exitFullscreen()
  }
}

const initGraph = () => {
  if (!graphContainer.value) return
  
  // Cleanup old instance
  if (graphInstance.value) {
    graphInstance.value._destructor?.()
  }

  const width = graphContainer.value.clientWidth
  const height = graphContainer.value.clientHeight

  graphInstance.value = ForceGraph()(graphContainer.value)
    .width(width)
    .height(height)
    .backgroundColor('#ffffff')
    .nodeRelSize(7)
    .width(width)
    .height(height)
    .backgroundColor('#ffffff')
    .nodeRelSize(7)
    .d3AlphaDecay(0.01)
    .d3VelocityDecay(0.3)
    .nodeId('id')
    .nodeLabel(node => `<div class="p-2 bg-white/90 border rounded-lg shadow-xl font-sans">
        <b class="text-accent">${node.name}</b><br/>
        <span class="text-xs text-muted-foreground uppercase">${node.category}</span>
      </div>`)
    .nodeColor(node => getNodeColor(node))
    .nodeCanvasObject((node, ctx, globalScale) => {
      const color = getNodeColor(node)
      
      // 1. 绘制核心发光节点 (Shadow/Halo)
      ctx.beginPath()
      ctx.arc(node.x, node.y, 8/globalScale, 0, 2 * Math.PI, false)
      ctx.fillStyle = color
      ctx.shadowBlur = (hoveredNode.value === node || selectedNode.value === node) ? 25/globalScale : 12/globalScale
      ctx.shadowColor = color
      ctx.fill()
      ctx.shadowBlur = 0

      // 2. LOD (Level of Detail) 智能标签渲染
      // 仅在足够放大、或者是悬停、或者是在“规约布局”模式下显示文字
      const isVisible = globalScale > 0.8 || hoveredNode.value === node || selectedNode.value === node || layoutMode.value === 'grid'
      
      if (isVisible) {
        const label = node.name
        const fontSize = 12/globalScale
        ctx.font = `${fontSize}px Inter, "Hiragino Sans GB", "Microsoft YaHei", sans-serif`
        const textWidth = ctx.measureText(label).width
        const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2)

        // 绘制标签背景 (玻璃拟态效果)
        ctx.fillStyle = 'rgba(255, 255, 255, 0.85)'
        ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y + 12/globalScale, bckgDimensions[0], bckgDimensions[1])

        // 绘制文字内容
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillStyle = '#0f172a'
        ctx.fillText(label, node.x, node.y + 12/globalScale + bckgDimensions[1] / 2)
        
        node.__bckgDimensions = bckgDimensions
      }
    })
    .linkSource('source_id')
    .linkTarget('target_id')
    .linkDirectionalParticles(2)
    .linkDirectionalParticleSpeed(d => 0.005)
    .linkDirectionalParticleWidth(2)
    .linkColor(() => '#e2e8f0')
    .linkWidth(1)
    .onNodeClick(node => {
      selectedNode.value = node
      graphInstance.value.centerAt(node.x, node.y, 400)
    })
    .onNodeHover(node => {
      hoveredNode.value = node
    })
    .onBackgroundClick(() => {
      selectedNode.value = null
    })

  updateGraphData()
}

const updateGraphData = () => {
  if (!graphInstance.value) return
  graphInstance.value.graphData(filteredData.value)
  
  // 关键补充：切换数据后如果是在整齐模式，需要重算位置
  if (layoutMode.value === 'grid') {
    applyLayout()
  }
}

const parseMetadata = (metadata) => {
  if (!metadata) return {}
  if (typeof metadata === 'object') return metadata
  try {
    return JSON.parse(metadata)
  } catch (e) {
    return {}
  }
}

const formatValue = (val) => {
  if (Array.isArray(val)) {
    return val.join(', ')
  }
  if (typeof val === 'object') {
    return JSON.stringify(val)
  }
  return val
}

// Lifecycle
onMounted(() => {
  fetchGraph()
  window.addEventListener('resize', handleResize)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  if (graphInstance.value) {
    graphInstance.value._destructor?.()
  }
})

const handleResize = () => {
  if (graphInstance.value && graphContainer.value) {
    graphInstance.value.width(graphContainer.value.clientWidth)
    graphInstance.value.height(graphContainer.value.clientHeight)
  }
}

const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
  
  if (graphInstance.value) {
    nextTick(() => {
      handleResize()
      
      // 影院级“大爆炸”特技调优版：确保点不飞走，且散开过程更克制
      if (isFullscreen.value) {
        // 1. 物理场瞬时重置为中心点周围的小随机范围 (避免重叠导致的剧烈爆炸)
        filteredData.value.nodes.forEach(node => {
          node.x = (Math.random() - 0.5) * 20
          node.y = (Math.random() - 0.5) * 20
        })
        
        // 2. 注入较低的初始能量 (0.3)，让散开过程更优雅舒缓
        const d3Sim = graphInstance.value.d3Force('charge')?.simulation
        if (d3Sim) {
          d3Sim.alpha(0.3)         // 低能量爆发
               .alphaDecay(0.02)   
               .restart()
        }
        
        // 3. 视角聚焦
        graphInstance.value.zoomToFit(1500)
      } else {
        graphInstance.value.d3ReheatSimulation()
        graphInstance.value.zoomToFit(800)
      }
    })
  }
}

watch(() => props.ontologyId, fetchGraph)
</script>

<style scoped>
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}
.slide-fade-leave-active {
  transition: all 0.5s cubic-bezier(1, 0.5, 0.8, 1);
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

.slide-enter-active, .slide-leave-active {
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-enter-from, .slide-leave-to {
  transform: translateX(100%);
}

canvas {
  outline: none;
}
</style>
