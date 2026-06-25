<template>
  <div class="page-actions">
    <slot />
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.page-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 34px;
  margin-bottom: 12px;
}

.page-actions :deep(.n-space) {
  flex-wrap: wrap;
  justify-content: flex-end;
  align-items: center;
  gap: 8px !important;
}

.page-actions :deep(.n-button) {
  vertical-align: middle;
}
</style>
