<template>
  <div :class="containerClasses">
    <slot />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { cn } from '../../utils/cn.js'

const props = defineProps({
  maxWidth: { type: String, default: '7xl' },
  padding: { type: Boolean, default: true }
})

const containerClasses = computed(() => {
  const maxWidths = {
    sm: 'max-w-screen-sm', md: 'max-w-screen-md', lg: 'max-w-screen-lg',
    xl: 'max-w-screen-xl', '2xl': 'max-w-screen-2xl', 
    '6xl': 'max-w-6xl', '7xl': 'max-w-7xl', 
    full: 'max-w-full'
  }
  const paddingClass = props.padding ? 'px-4 sm:px-6 lg:px-8' : ''
  return cn('mx-auto w-full', maxWidths[props.maxWidth], paddingClass)
})
</script>
