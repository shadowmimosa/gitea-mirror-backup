<template>
  <div class="not-found">
    <n-result status="404" title="页面不存在" description="您访问的页面不存在或已被移除">
      <template #footer>
        <n-button type="primary" @click="$router.push('/')">返回仪表板</n-button>
      </template>
    </n-result>
  </div>
</template>

<script setup lang="ts">
import { NResult, NButton } from 'naive-ui'
</script>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}
</style>
