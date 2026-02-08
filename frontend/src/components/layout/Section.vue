<template>
  <section :class="sectionClasses">
    <Container :max-width="maxWidth">
      <slot />
    </Container>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { cn } from '../../utils/cn.js'
import Container from './Container.vue'

const props = defineProps({
  inverted: Boolean,
  maxWidth: { type: String, default: '6xl' },
  padding: { type: String, default: 'lg' }
})

const sectionClasses = computed(() => {
  const base = 'relative'
  const color = props.inverted ? 'bg-foreground text-background' : 'bg-background text-foreground'
  const paddings = { sm: 'py-12', md: 'py-20', lg: 'py-28', xl: 'py-44' }
  return cn(base, color, paddings[props.padding])
})
</script>
