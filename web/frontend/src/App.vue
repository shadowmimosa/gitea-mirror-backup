<template>
  <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides">
    <n-message-provider>
      <MessageSetup />
      <n-notification-provider>
        <n-dialog-provider>
          <router-view />
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { NConfigProvider, NMessageProvider, NNotificationProvider, NDialogProvider, darkTheme } from 'naive-ui'
import MessageSetup from '@/components/MessageSetup.vue'

const themeOverrides = {
  common: {
    primaryColor: '#667eea',
    primaryColorHover: '#5e72e4',
    primaryColorPressed: '#4c63d2',
    primaryColorSuppl: '#764ba2'
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: #0a0a0a;
  color: #e5e5e5;
}

#app {
  width: 100%;
  min-height: 100vh;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  margin-bottom: 12px;
  width: 100%;
}

.filter-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 34px;
}

.filter-item__label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.82);
  white-space: nowrap;
  line-height: 1;
}
</style>

