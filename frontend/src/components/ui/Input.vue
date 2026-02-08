<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="inputId" class="text-sm font-medium text-foreground">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    <input
      :id="inputId"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :class="inputClasses"
      @input="emit('update:modelValue', $event.target.value)"
    />
    <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
    <p v-else-if="hint" class="text-sm text-muted-foreground">{{ hint }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { cn } from '../../utils/cn.js'

const props = defineProps({
  modelValue: [String, Number],
  type: { type: String, default: 'text' },
  label: String,
  placeholder: String,
  disabled: Boolean,
  required: Boolean,
  error: String,
  hint: String,
  size: { type: String, default: 'md' }
})

const emit = defineEmits(['update:modelValue'])

const inputId = computed(() => `input-${Math.random().toString(36).substr(2, 9)}`)

const inputClasses = computed(() => {
  const base = 'w-full border border-border rounded-lg bg-transparent text-foreground placeholder:text-muted-foreground/50 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50'
  const sizes = { sm: 'h-10 px-3 text-sm', md: 'h-12 px-4 text-base', lg: 'h-14 px-5 text-lg' }
  const errorClass = props.error ? 'border-red-500 focus:ring-red-500' : ''
  return cn(base, sizes[props.size], errorClass)
})
</script>
