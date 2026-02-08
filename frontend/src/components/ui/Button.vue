<template>
  <button :class="buttonClasses" :disabled="disabled || loading" @click="handleClick">
    <span v-if="loading" class="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"></span>
    <slot />
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { cn } from '../../utils/cn.js'

const props = defineProps({
  variant: { type: String, default: 'primary' },
  size: { type: String, default: 'md' },
  disabled: Boolean,
  loading: Boolean,
  fullWidth: Boolean
})

const emit = defineEmits(['click'])

const handleClick = (e) => {
  if (!props.disabled && !props.loading) emit('click', e)
}

const buttonClasses = computed(() => {
  const base = 'inline-flex items-center justify-center font-bold transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed'
  const variants = {
    primary: 'bg-gradient-to-r from-accent via-accent to-accent-secondary text-white shadow-lg hover:shadow-2xl hover:shadow-accent/50 hover:-translate-y-1 hover:scale-105 active:scale-100',
    secondary: 'border-2 border-border bg-transparent text-foreground hover:bg-muted hover:border-accent/50 hover:shadow-lg',
    ghost: 'bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50 hover:shadow-md',
    danger: 'bg-gradient-to-r from-red-500 to-red-600 text-white shadow-lg hover:shadow-2xl hover:shadow-red-500/50 hover:-translate-y-1 hover:scale-105'
  }
  const sizes = {
    sm: 'h-10 px-5 text-sm rounded-lg',
    md: 'h-12 px-8 text-base rounded-xl',
    lg: 'h-14 px-10 text-lg rounded-xl'
  }
  return cn(base, variants[props.variant], sizes[props.size], props.fullWidth ? 'w-full' : '')
})
</script>
