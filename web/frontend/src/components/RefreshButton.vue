<template>
  <n-button :size="size" :loading="loading" @click="$emit('click')">
    <template #icon>
      <n-icon><RefreshOutline /></n-icon>
    </template>
    {{ label }}
  </n-button>
</template>

<script setup lang="ts">
import { NButton, NIcon } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'

withDefaults(
  defineProps<{
    loading?: boolean
    size?: 'tiny' | 'small' | 'medium' | 'large'
    label?: string
  }>(),
  {
    loading: false,
    label: '刷新'
  }
)

defineEmits<{
  click: []
}>()
</script>
