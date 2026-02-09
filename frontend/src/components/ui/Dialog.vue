<template>
  <Teleport to="body">
    <Transition enter-active-class="transition-opacity duration-300" leave-active-class="transition-opacity duration-200">
      <div v-if="modelValue" class="fixed inset-0 z-50 flex items-center justify-center bg-foreground/50 backdrop-blur-sm p-4" @click.self="handleOverlayClick">
        <div :class="dialogClasses" :style="{ maxWidth: computedWidth }">
          <div v-if="$slots.header || title" class="flex items-center justify-between border-b border-border px-6 py-4">
            <slot name="header">
              <h2 class="text-xl font-semibold text-foreground">{{ title }}</h2>
            </slot>
            <button v-if="showClose" @click="handleClose" class="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground">
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
  width: String,
  size: { type: String, default: 'md' }, // sm, md, lg, xl, full
  showClose: { type: Boolean, default: true },
  closeOnClickModal: { type: Boolean, default: false }
})

const sizeMap = {
  sm: '30vw',
  md: '50vw',
  lg: '70vw',
  xl: '90vw',
  full: '96vw'
}

const computedWidth = computed(() => {
  if (props.width) return props.width
  return sizeMap[props.size] || sizeMap.md
})

const emit = defineEmits(['update:modelValue', 'close'])

const handleOverlayClick = () => {
  if (props.closeOnClickModal) {
    emit('update:modelValue', false)
    emit('close')
  }
}

const handleClose = () => {
  emit('update:modelValue', false)
  emit('close')
}

const dialogClasses = cn('relative bg-card rounded-2xl shadow-2xl max-h-[90vh] flex flex-col overflow-hidden w-full min-w-[320px]')

watch(() => props.modelValue, (val) => {
  document.body.style.overflow = val ? 'hidden' : ''
})
</script>
