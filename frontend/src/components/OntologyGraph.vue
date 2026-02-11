<template>
  <div class="h-full flex flex-col relative bg-white">
    <!-- Header Toolbar -->
    <div class="p-4 border-b flex items-center justify-between gap-4 z-20 bg-white/80 backdrop-blur-md">
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-muted-foreground uppercase tracking-wider">显示节点:</span>
          <div class="flex gap-1">
            <Badge 
              v-for="cat in allCategories" 
              :key="cat"
              :variant="activeFilters.includes(cat) ? 'info' : 'outline'"
              class="cursor-pointer transition-all hover:scale-105"
              @click="toggleFilter(cat)"
            >
              {{ cat }}
            </Badge>
          </div>
        </div>
      </div>
      
      <div class="flex items-center gap-2">
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
            <div class="w-2 h-2 rounded-full" :style="{ backgroundColor: getCategoryColor(hoveredNode.category) }"></div>
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
const selectedNode = ref(null)
const hoveredNode = ref(null)
const isFullscreen = ref(false)
const activeFilters = ref([])

// Config constants
const COLORS = [
  '#4460EF', // Indigo
  '#10B981', // Emerald
  '#F59E0B', // Amber
  '#EF4444', // Red
  '#8B5CF6', // Violet
  '#EC4899', // Pink
  '#06B6D4'  // Cyan
]

const categoryColorMap = {}
const getCategoryColor = (cat) => {
  if (!cat) return '#94a3b8'
  if (!categoryColorMap[cat]) {
    const idx = Object.keys(categoryColorMap).length % COLORS.length
    categoryColorMap[cat] = COLORS[idx]
  }
  return categoryColorMap[cat]
}

// Computed
const allCategories = computed(() => {
  const cats = new Set(rawData.value.nodes.map(n => n.category))
  return Array.from(cats).filter(Boolean)
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
    // Initialize filters with all categories
    activeFilters.value = allCategories.value
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
    .nodeId('id')
    .nodeLabel(node => `<div class="p-2 bg-white/90 border rounded-lg shadow-xl font-sans">
        <b class="text-accent">${node.name}</b><br/>
        <span class="text-xs text-muted-foreground uppercase">${node.category}</span>
      </div>`)
    .nodeColor(node => getCategoryColor(node.category))
    .nodeCanvasObject((node, ctx, globalScale) => {
      const label = node.name
      const fontSize = 12/globalScale
      ctx.font = `${fontSize}px Inter, "Hiragino Sans GB", "Microsoft YaHei", sans-serif`
      const textWidth = ctx.measureText(label).width
      const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2)

      // Draw shadow/halo
      ctx.beginPath()
      ctx.arc(node.x, node.y, 8/globalScale, 0, 2 * Math.PI, false)
      ctx.fillStyle = getCategoryColor(node.category)
      ctx.shadowBlur = 15/globalScale
      ctx.shadowColor = getCategoryColor(node.category)
      ctx.fill()
      ctx.shadowBlur = 0

      // Draw label Background
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)'
      ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y + 12/globalScale, bckgDimensions[0], bckgDimensions[1])

      // Draw text
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillStyle = '#1e293b'
      ctx.fillText(label, node.x, node.y + 12/globalScale + bckgDimensions[1] / 2)
      
      node.__bckgDimensions = bckgDimensions
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
