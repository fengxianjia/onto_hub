<template>
  <Teleport to="body">
    <Transition enter-active-class="transition-opacity duration-300" leave-active-class="transition-opacity duration-200">
      <div v-if="modelValue" class="fixed inset-0 z-50 bg-foreground/30 backdrop-blur-sm" @click="handleClose" />
    </Transition>
    <Transition :enter-active-class="`transition-transform duration-300`" :leave-active-class="`transition-transform duration-200`">
      <div v-if="modelValue" :class="drawerClasses" :style="{ width: size }">
        <div class="flex items-center justify-between border-b border-border px-6 py-4">
          <slot name="header">
            <h2 class="text-xl font-semibold text-foreground">{{ title }}</h2>
          </slot>
          <button @click="handleClose" class="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="flex-1 overflow-y-auto px-6 py-6">
          <slot />
        </div>
        <div v-if="$slots.footer" class="border-t border-border px-6 py-4">
          <slot name="footer" />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, watch } from 'vue'
import { cn } from '../../utils/cn.js'

const props = defineProps({
  modelValue: Boolean,
  title: String,
  direction: { type: String, default: 'rtl' },
  size: { type: String, default: '50%' }
})

const emit = defineEmits(['update:modelValue', 'close'])

const handleClose = () => {
  emit('update:modelValue', false)
  emit('close')
}

const drawerClasses = computed(() => {
  const position = props.direction === 'rtl' ? 'fixed top-0 right-0 bottom-0' : 'fixed top-0 left-0 bottom-0'
  return cn(position, 'z-50 bg-card shadow-2xl flex flex-col')
})

watch(() => props.modelValue, (val) => {
  document.body.style.overflow = val ? 'hidden' : ''
})
</script>
