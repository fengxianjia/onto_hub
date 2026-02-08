<template>
  <div :class="cardClasses">
    <div v-if="$slots.header || header" class="border-b border-border px-6 py-4">
      <slot name="header">
        <h3 class="text-lg font-semibold text-foreground">{{ header }}</h3>
      </slot>
    </div>
    <div :class="contentClasses">
      <slot />
    </div>
    <div v-if="$slots.footer" class="border-t border-border px-6 py-4">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { cn } from '../../utils/cn.js'

const props = defineProps({
  header: String,
  variant: { type: String, default: 'default' },
  padding: { type: String, default: 'md' },
  hoverable: { type: Boolean, default: true }
})

const cardClasses = computed(() => {
  const base = 'bg-card border border-border rounded-2xl transition-all duration-300'
  const variants = { 
    default: 'shadow-lg', 
    elevated: 'shadow-2xl', 
    featured: 'shadow-2xl border-accent/20' 
  }
  const hover = props.hoverable ? 'hover:shadow-2xl hover:-translate-y-1 hover:bg-gradient-to-br hover:from-accent/[0.05] hover:to-transparent' : ''
  return cn(base, variants[props.variant], hover)
})

const contentClasses = computed(() => {
  const paddings = { sm: 'p-4', md: 'p-6', lg: 'p-10' }
  return paddings[props.padding]
})
</script>
