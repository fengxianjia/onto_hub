<template>
  <div class="flex flex-col items-center justify-center gap-2 py-8">
    <svg class="h-16 w-16 text-muted-foreground/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
    </svg>
    <p class="text-sm text-muted-foreground">{{ description }}</p>
  </div>
</template>

<script setup>
defineProps({
  description: { type: String, default: '暂无数据' }
})
</script>
