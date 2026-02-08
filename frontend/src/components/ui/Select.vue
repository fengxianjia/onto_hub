<template>
  <div class="relative">
    <label v-if="label" class="mb-1.5 block text-sm font-medium text-foreground">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    <button type="button" :class="selectClasses" @click="toggleDropdown">
      <span v-if="selectedOption" class="block truncate">{{ selectedOption.label }}</span>
      <span v-else class="block truncate text-muted-foreground/50">{{ placeholder }}</span>
      <svg class="h-5 w-5 text-muted-foreground transition-transform duration-200" :class="{ 'rotate-180': isOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>
    <Transition enter-active-class="transition-all duration-200" leave-active-class="transition-all duration-150">
      <div v-if="isOpen" class="absolute z-10 mt-2 w-full rounded-lg border border-border bg-card shadow-lg">
        <div v-if="filterable" class="border-b border-border p-2">
          <input v-model="searchQuery" type="text" placeholder="搜索..." class="w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent" @click.stop />
        </div>
        <div class="max-h-60 overflow-y-auto p-1">
          <button v-for="option in filteredOptions" :key="option.value" type="button" :class="optionClasses(option)" @click="selectOption(option)">
            {{ option.label }}
          </button>
          <div v-if="filteredOptions.length === 0" class="px-3 py-8 text-center text-sm text-muted-foreground">无匹配选项</div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { cn } from '../../utils/cn.js'

const props = defineProps({
  modelValue: [String, Number],
  options: { type: Array, default: () => [] },
  label: String,
  placeholder: { type: String, default: '请选择' },
  disabled: Boolean,
  required: Boolean,
  error: String,
  filterable: Boolean
})

const emit = defineEmits(['update:modelValue', 'change'])

const isOpen = ref(false)
const searchQuery = ref('')

const selectedOption = computed(() => props.options.find(opt => opt.value === props.modelValue))

const filteredOptions = computed(() => {
  if (!props.filterable || !searchQuery.value) return props.options
  const query = searchQuery.value.toLowerCase()
  return props.options.filter(opt => opt.label.toLowerCase().includes(query))
})

const toggleDropdown = () => {
  if (!props.disabled) isOpen.value = !isOpen.value
}

const selectOption = (option) => {
  emit('update:modelValue', option.value)
  emit('change', option.value)
  isOpen.value = false
  searchQuery.value = ''
}

const selectClasses = computed(() => {
  const base = 'relative w-full h-12 px-4 text-left border border-border rounded-lg bg-transparent text-foreground transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-between'
  return cn(base, props.error ? 'border-red-500' : '')
})

const optionClasses = (option) => {
  const base = 'w-full px-3 py-2 text-left text-sm rounded-md transition-colors duration-150'
  const active = option.value === props.modelValue ? 'bg-accent/10 text-accent font-medium' : 'text-foreground hover:bg-muted'
  return cn(base, active)
}
</script>
