<template>
  <n-breadcrumb v-if="items.length > 0" style="margin-bottom: 16px;">
    <n-breadcrumb-item
      v-for="(item, index) in items"
      :key="index"
      :clickable="!!item.path && index < items.length - 1"
      @click="item.path && index < items.length - 1 ? $router.push(item.path) : undefined"
    >
      {{ item.label }}
    </n-breadcrumb-item>
  </n-breadcrumb>
</template>

<script setup lang="ts">
import { NBreadcrumb, NBreadcrumbItem } from 'naive-ui'

export interface BreadcrumbItem {
  label: string
  path?: string
}

defineProps<{
  items: BreadcrumbItem[]
}>()
</script>
