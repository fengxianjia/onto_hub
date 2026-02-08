<template>
  <span :class="badgeClasses">
    <span v-if="dot" :class="dotClasses"></span>
    <slot />
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { cn } from '../../utils/cn.js'

const props = defineProps({
  variant: { type: String, default: 'default' },
  size: { type: String, default: 'md' },
  dot: Boolean,
  outline: Boolean
})

const badgeClasses = computed(() => {
  const base = 'inline-flex items-center gap-2 font-bold rounded-full transition-all duration-200'
  const sizes = { 
    sm: 'px-3 py-1 text-xs', 
    md: 'px-4 py-1.5 text-sm', 
    lg: 'px-5 py-2 text-base' 
  }
  const variants = props.outline ? {
    default: 'border-2 border-border bg-transparent text-foreground',
    success: 'border-2 border-green-500 bg-transparent text-green-600',
    warning: 'border-2 border-yellow-500 bg-transparent text-yellow-600',
    danger: 'border-2 border-red-500 bg-transparent text-red-600',
    info: 'border-2 border-blue-500 bg-transparent text-blue-600',
    accent: 'border-2 border-accent bg-transparent text-accent'
  } : {
    default: 'bg-muted text-muted-foreground shadow-sm',
    success: 'bg-green-100 text-green-700 shadow-sm',
    warning: 'bg-yellow-100 text-yellow-700 shadow-sm',
    danger: 'bg-red-100 text-red-700 shadow-sm',
    info: 'bg-blue-100 text-blue-700 shadow-sm',
    accent: 'bg-gradient-to-r from-accent/20 to-accent-secondary/20 text-accent shadow-sm'
  }
  return cn(base, sizes[props.size], variants[props.variant])
})

const dotClasses = computed(() => {
  const colors = {
    default: 'bg-muted-foreground',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    danger: 'bg-red-500',
    info: 'bg-blue-500',
    accent: 'bg-accent'
  }
  return cn('h-2 w-2 rounded-full', colors[props.variant])
})
</script>
