<template>
  <div class="h-full flex flex-col">
    <div v-if="loading" class="flex-1 flex justify-center items-center">
      <Loading />
    </div>
    <div v-else-if="nodes.length === 0" class="flex-1 flex justify-center items-center">
      <Empty description="暂无图谱数据,请确认本体解析是否完成" />
    </div>
    
    <!-- Graph container -->
    <div 
      v-else
      ref="graphContainer" 
      class="flex-1 relative border rounded-lg overflow-hidden bg-white"
    >
      <v-network-graph
        v-show="graphVisible"
        ref="graph"
        class="graph"
        :nodes="nodes"
        :edges="edges"
        :layouts="layouts"
        :configs="configs"
        :event-handlers="eventHandlers"
      >
        <template #edge-label="{ edge, ...slotProps }">
          <v-edge-label :text="edge.label" align="center" vertical-align="above" v-bind="slotProps" />
        </template>
      </v-network-graph>

      <!-- Layout Switcher & Fullscreen Button -->
      <div class="absolute top-4 left-4 bg-white shadow-md rounded-md border border-border p-1 flex gap-1 z-10">
          <button 
            @click="setLayout('force')"
            :class="['px-3 py-1 text-xs font-medium rounded transition-colors', layoutMode === 'force' ? 'bg-accent text-white' : 'text-muted-foreground hover:bg-muted']"
          >
            力导向 (Force)
          </button>
          <button 
            @click="setLayout('star')"
            :class="['px-3 py-1 text-xs font-medium rounded transition-colors', layoutMode === 'star' ? 'bg-accent text-white' : 'text-muted-foreground hover:bg-muted']"
          >
            星图 (Star Map)
          </button>
          <div class="w-px bg-border mx-1"></div>
          <button 
            @click="toggleFullscreen"
            :title="isFullscreen ? '退出全屏 (ESC)' : '全屏显示'"
            class="px-2 py-1 text-muted-foreground hover:text-foreground hover:bg-muted rounded transition-colors"
          >
            <svg v-if="!isFullscreen" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"/>
            </svg>
            <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
      </div>
      
      <!-- Node Detail Panel -->
      <div v-if="selectedNode" class="absolute right-0 top-0 bottom-0 w-80 bg-white shadow-lg border-l p-4 overflow-y-auto transition-transform duration-300">
        <div class="flex justify-between items-center mb-4">
          <h3 class="font-bold text-lg">{{ selectedNode.name }}</h3>
          <button @click="selectedNode = null" class="text-muted-foreground hover:text-foreground">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="space-y-2 text-sm">
          <div class="flex">
            <span class="w-20 font-medium text-muted-foreground">分类:</span>
            <Badge variant="info" size="xs">{{ selectedNode.category }}</Badge>
          </div>
          <div class="flex">
             <span class="w-20 font-medium text-muted-foreground">文件:</span>
             <span class="truncate" :title="selectedNode.file_path">{{ selectedNode.file_path }}</span>
          </div>
           <div class="mt-4">
             <h4 class="font-medium mb-2 border-b pb-1">属性 (Attributes)</h4>
             <table class="w-full text-xs">
               <tbody>
                 <tr v-for="(value, key) in parseMetadata(selectedNode.metadata)" :key="key" class="border-b last:border-0 border-dashed border-gray-200">
                   <td class="py-1 pr-2 font-medium text-muted-foreground w-1/3 break-words align-top">{{ key }}</td>
                   <td class="py-1 text-foreground w-2/3 break-words">
                      <div v-if="Array.isArray(value) && value.length > 0 && typeof value[0] === 'object'" class="overflow-x-auto">
                        <table class="w-full border-collapse mt-1 mb-1">
                          <thead>
                            <tr class="bg-muted/50">
                              <th v-for="(h, i) in Object.keys(value[0])" :key="i" class="p-1 text-left font-semibold border border-border">{{ h }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="(row, r) in value" :key="r">
                               <td v-for="(cell, c) in Object.values(row)" :key="c" class="p-1 border border-border">{{ cell }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <ul v-else-if="Array.isArray(value)" class="list-disc list-inside">
                        <li v-for="(item, i) in value" :key="i">{{ item }}</li>
                      </ul>
                      <span v-else>{{ value }}</span>
                   </td>
                 </tr>
               </tbody>
             </table>
             <div v-if="Object.keys(parseMetadata(selectedNode.metadata)).length === 0" class="text-xs text-muted-foreground italic py-2">
               无额外属性
             </div>
           </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, onUnmounted } from 'vue'
import axios from 'axios'
import { Loading, Empty, Badge } from './index.js'
// Note: User needs to install v-network-graph
import { VNetworkGraph, VEdgeLabel } from "v-network-graph"
import "v-network-graph/lib/style.css"

const props = defineProps({
  ontologyId: {
    type: String,
    required: true
  }
})

const loading = ref(false)
const nodes = ref({})
const edges = ref({})
const layouts = ref({ nodes: {} })
const selectedNode = ref(null)
const layoutMode = ref('force')
const graph = ref(null)
const graphVisible = ref(true) // Control visibility during star map initialization
const isFullscreen = ref(false) // Fullscreen mode state
const graphMounted = ref(false) // Track if graph has been mounted

const configs = ref({
  node: {
    normal: {
      type: "circle",
      radius: 16, // Smaller nodes
      color: "#4460EF",
    },
    hover: {
      color: "#6b7fff",
    },
    label: {
      visible: true,
      fontFamily: "Inter, sans-serif",
      fontSize: 11,
    },
  },
  edge: {
    normal: {
      color: "#cbd5e1",
      width: 1, // Thinner edges
    },
    marker: {
      target: {
        type: "arrow",
        width: 3,
        height: 3,
      },
    },
  },
})

const eventHandlers = {
  "node:click": ({ node }) => {
    selectedNode.value = nodes.value[node]
  },
}

const fetchGraph = async () => {
  loading.value = true
  selectedNode.value = null
  try {
    const res = await axios.get(`/api/ontologies/${props.ontologyId}/graph`)
    // Convert array to object for v-network-graph
    const nodesObj = {}
    res.data.nodes.forEach(n => {
      nodesObj[n.id] = { ...n, name: n.name, metadata: n.metadata_json } 
    })
    
    const edgesObj = {}
    res.data.links.forEach(l => {
      edgesObj[l.id] = { 
        source: l.source_id,  // FIX: Use source_id
        target: l.target_id,  // FIX: Use target_id
        label: l.relation_type 
      }
    })
    
    nodes.value = nodesObj
    edges.value = edgesObj
    
    // Apply current layout mode
    if (layoutMode.value === 'star') {
        applyStarLayout()
    } else {
        // Force mode: clear all layouts to let force engine work
        layouts.value = { nodes: {} }
        setTimeout(() => {
            try { graph.value?.fitToContents() } catch (e) {}
        }, 1000)
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const graphContainer = ref(null)

// ...

// ...

const applyStarLayout = async () => {
    const count = Object.keys(nodes.value).length
    if (count === 0) return

    // HIDE graph during initialization to prevent flash
    graphVisible.value = false

    const center = { x: 0, y: 0 }
    const nodeIds = Object.keys(nodes.value).sort()
    
    // REVERSE APPROACH: Start with a large ring, then contract inward
    // This makes auto-fitting much easier!
    
    // 1. Create initial LARGE ring (will be auto-fitted by fitToContents)
    const largeRadius = 800 // Large enough to ensure fitToContents will scale it down
    const initialNodes = {}
    const shuffledIds = [...nodeIds].sort(() => Math.random() - 0.5)
    
    for (let i = 0; i < shuffledIds.length; i++) {
        const nodeId = shuffledIds[i]
        const angle = Math.random() * 2 * Math.PI
        // All nodes start at the large radius (outer ring)
        initialNodes[nodeId] = {
            x: center.x + largeRadius * Math.cos(angle),
            y: center.y + largeRadius * Math.sin(angle),
            fixed: true
        }
    }
    
    // Set initial positions
    layouts.value = { nodes: initialNodes }
    
    // 2. Wait for layout to be set, then fit
    await new Promise(resolve => setTimeout(resolve, 50))
    
    try {
        graph.value?.fitToContents()
    } catch(e) {}
    
    // 3. Wait for fit to complete, then SHOW graph
    await new Promise(resolve => setTimeout(resolve, 100))
    graphVisible.value = true
    
    // 4. Now contract to final star map positions
    // The key: we keep the same angles, but reduce the radius with jitter
    const finalNodes = {}
    
    for (let i = 0; i < shuffledIds.length; i++) {
        const nodeId = shuffledIds[i]
        const initial = initialNodes[nodeId]
        
        // Calculate angle from initial position
        const angle = Math.atan2(initial.y - center.y, initial.x - center.x)
        
        // Contract to 10%-40% of the initial radius for compact star map
        const contractionFactor = 0.1 + Math.random() * 0.3
        const finalRadius = largeRadius * contractionFactor
        
        finalNodes[nodeId] = {
            x: center.x + finalRadius * Math.cos(angle),
            y: center.y + finalRadius * Math.sin(angle),
            fixed: true
        }
    }
    
    // 5. Animate contraction (no fitToContents - keep the explosion effect)
    animateExpansion(initialNodes, finalNodes, 2000, false)
}

const animateExpansion = (startLayout, endLayout, duration, shouldFitAfter = true) => {
    const startTime = performance.now()
    
    const animate = (time) => {
        const elapsed = time - startTime
        const progress = Math.min(elapsed / duration, 1)
        // Ease out cubic
        const ease = 1 - Math.pow(1 - progress, 3)
        
        const currentNodes = {}
        for (const nodeId in startLayout) {
             const start = startLayout[nodeId]
             const end = endLayout[nodeId]
             if (!end) continue
             
             currentNodes[nodeId] = {
                 x: start.x + (end.x - start.x) * ease,
                 y: start.y + (end.y - start.y) * ease,
                 fixed: true
             }
        }
        layouts.value = { nodes: currentNodes }
        
        if (progress < 1) {
            requestAnimationFrame(animate)
        } else if (shouldFitAfter) {
            // Animation complete, fit to contents for proper view (only if requested)
            setTimeout(() => {
                try {
                    graph.value?.fitToContents()
                } catch(e) {}
            }, 100)
        }
    }
    requestAnimationFrame(animate)
}


const applyForceLayout = async () => {
    // Strategy: Since clearing layouts doesn't work reliably,
    // we'll refetch the graph data to get a clean slate
    // This mimics what happens when switching tabs (which works)
    
    graphVisible.value = true // Ensure graph is visible
    
    // Simply refetch the graph - this will reset everything
    await fetchGraph()
}

const toggleFullscreen = async () => {
  console.log('toggleFullscreen called, current state:', isFullscreen.value)
  const wasFullscreen = isFullscreen.value
  
  if (!wasFullscreen) {
    // Enter fullscreen using native API
    try {
      if (graphContainer.value) {
        await graphContainer.value.requestFullscreen()
        isFullscreen.value = true
        console.log('Entered fullscreen')
        
        // If in star map mode, replay animation after entering fullscreen
        if (layoutMode.value === 'star') {
          setTimeout(() => {
            applyStarLayout()
          }, 100)
        } else {
          // Re-fit for other modes
          setTimeout(() => {
            try { graph.value?.fitToContents() } catch (e) {}
          }, 100)
        }
      }
    } catch (err) {
      console.error('Failed to enter fullscreen:', err)
    }
  } else {
    // Exit fullscreen
    try {
      await document.exitFullscreen()
      isFullscreen.value = false
      console.log('Exited fullscreen')
    } catch (err) {
      console.error('Failed to exit fullscreen:', err)
    }
  }
}

const setLayout = (mode) => {
    layoutMode.value = mode
    if (mode === 'star') {
        applyStarLayout()
    } else {
        applyForceLayout()
    }
}

const parseMetadata = (jsonStr) => {
  try {
    return JSON.parse(jsonStr) || {}
  } catch(e) {
    return {}
  }
}

watch(() => props.ontologyId, () => {
  if (props.ontologyId) fetchGraph()
})

onMounted(() => {
  graphMounted.value = true
  fetchGraph()
  
  // Listen for fullscreen changes (including ESC key)
  const handleFullscreenChange = () => {
    isFullscreen.value = !!document.fullscreenElement
    console.log('Fullscreen changed:', isFullscreen.value)
  }
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  
  // ESC key handler for exiting fullscreen (backup)
  const handleKeydown = (e) => {
    if (e.key === 'Escape' && isFullscreen.value) {
      // The fullscreenchange event will handle the state update
      document.exitFullscreen().catch(() => {})
    }
  }
  window.addEventListener('keydown', handleKeydown)
  
  // Cleanup on unmount
  onUnmounted(() => {
    document.removeEventListener('fullscreenchange', handleFullscreenChange)
    window.removeEventListener('keydown', handleKeydown)
  })
})
</script>

<style scoped>
.graph {
  width: 100%;
  height: 100%;
}

/* Smooth transition for fullscreen */
.fixed {
  transition: all 0.3s ease-in-out;
}

/* Breathing animation for Star Map nodes */
:deep(.v-ng-node-circle) {
    animation: breathe 4s infinite ease-in-out alternate;
    transform-origin: center;
}

@keyframes breathe {
    0% { transform: scale(1); }
    100% { transform: scale(1.15); }
}
</style>
