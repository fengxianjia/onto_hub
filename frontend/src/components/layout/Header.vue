<template>
  <header class="sticky top-0 z-40 w-full border-b-2 border-border bg-card/90 backdrop-blur-md shadow-lg">
    <Container max-width="full">
      <div class="flex h-14 items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-accent to-accent-secondary text-xl shadow-md">
            📦
          </div>
          <div>
            <h1 class="text-lg font-bold text-foreground">{{ title }}</h1>
            <p v-if="subtitle" class="text-xs text-muted-foreground">{{ subtitle }}</p>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <slot name="actions" />
        </div>
      </div>
    </Container>
  </header>
</template>

<script setup>
import Container from './Container.vue'

defineProps({
  title: { type: String, default: 'OntoHub' },
  subtitle: { type: String, default: '本体管理中心' }
})
</script>
