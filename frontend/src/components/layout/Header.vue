<template>
  <header class="sticky top-0 z-40 w-full border-b-2 border-border bg-card/90 backdrop-blur-md shadow-lg">
    <Container max-width="full">
      <div class="flex h-20 items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-accent-secondary text-2xl shadow-lg">
            📦
          </div>
          <div>
            <h1 class="text-2xl font-bold text-foreground">{{ title }}</h1>
            <p v-if="subtitle" class="text-sm text-muted-foreground">{{ subtitle }}</p>
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
