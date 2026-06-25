<template>
  <div class="app-logo" :class="{ 'app-logo--compact': compact }">
    <img
      src="/logo.svg"
      alt="Gitea Mirror Backup"
      :width="size"
      :height="size"
      class="app-logo__mark"
    />
    <span v-if="showText" class="app-logo__text">{{ text }}</span>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    size?: number
    showText?: boolean
    text?: string
    compact?: boolean
  }>(),
  {
    size: 32,
    showText: true,
    text: 'Gitea Backup',
    compact: false
  }
)
</script>

<style scoped>
.app-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.app-logo--compact {
  justify-content: center;
  gap: 0;
}

.app-logo__mark {
  flex-shrink: 0;
  display: block;
}

.app-logo__text {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
