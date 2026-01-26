<template>
    <n-layout has-sider style="height: 100vh">
      <n-layout-sider
        bordered
        collapse-mode="width"
        :collapsed-width="64"
        :width="240"
        :collapsed="collapsed"
        show-trigger
        @collapse="collapsed = true"
        @expand="collapsed = false"
      >
        <div class="logo">
          <h2 v-if="!collapsed">Gitea Backup</h2>
          <h2 v-else>GB</h2>
        </div>
  
        <n-menu
          :collapsed="collapsed"
          :collapsed-width="64"
          :collapsed-icon-size="22"
          :options="menuOptions"
          :value="activeKey"
          @update:value="handleMenuSelect"
        />
      </n-layout-sider>
  
      <n-layout>
        <n-layout-header bordered style="height: 64px; padding: 0 24px; display: flex; align-items: center; justify-content: space-between;">
          <div class="header-left">
            <h3>{{ currentTitle }}</h3>
          </div>
  
          <div class="header-right">
            <n-dropdown :options="userOptions" @select="handleUserAction">
              <n-button text>
                <template #icon>
                  <n-icon><PersonCircleOutline /></n-icon>
                </template>
                {{ authStore.user?.username }}
              </n-button>
            </n-dropdown>
          </div>
        </n-layout-header>
  
        <n-layout-content content-style="padding: 24px;">
          <router-view />
        </n-layout-content>
      </n-layout>
    </n-layout>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, h } from 'vue'
  import { useRouter, useRoute } from 'vue-router'
  import { NLayout, NLayoutSider, NLayoutHeader, NLayoutContent, NMenu, NButton, NDropdown, NIcon } from 'naive-ui'
  import { 
    HomeOutline, 
    FolderOpenOutline, 
    CameraOutline, 
    DocumentTextOutline, 
    SettingsOutline,
    PersonCircleOutline,
    LogOutOutline
  } from '@vicons/ionicons5'
  import { useAuthStore } from '@/stores/auth'
  
  const router = useRouter()
  const route = useRoute()
  const authStore = useAuthStore()
  
  const collapsed = ref(false)
  
  const menuOptions = [
    {
      label: '仪表板',
      key: 'Dashboard',
      icon: () => h(NIcon, null, { default: () => h(HomeOutline) })
    },
    {
      label: '仓库管理',
      key: 'Repositories',
      icon: () => h(NIcon, null, { default: () => h(FolderOpenOutline) })
    },
    {
      label: '快照管理',
      key: 'Snapshots',
      icon: () => h(NIcon, null, { default: () => h(CameraOutline) })
    },
    {
      label: '报告查看',
      key: 'Reports',
      icon: () => h(NIcon, null, { default: () => h(DocumentTextOutline) })
    },
    {
      label: '系统设置',
      key: 'Settings',
      icon: () => h(NIcon, null, { default: () => h(SettingsOutline) })
    }
  ]
  
  const userOptions = [
    {
      label: '退出登录',
      key: 'logout',
      icon: () => h(NIcon, null, { default: () => h(LogOutOutline) })
    }
  ]
  
  const activeKey = computed(() => route.name as string)
  
  const currentTitle = computed(() => {
    const option = menuOptions.find(item => item.key === activeKey.value)
    return option?.label || '仪表板'
  })
  
  function handleMenuSelect(key: string) {
    router.push({ name: key })
  }
  
  function handleUserAction(key: string) {
    if (key === 'logout') {
      authStore.logout()
      router.push('/login')
    }
  }
  </script>
  
  <style scoped>
  .logo {
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .logo h2 {
    font-size: 20px;
    font-weight: 700;
    color: #fff;
  }
  
  .header-left h3 {
    font-size: 18px;
    font-weight: 600;
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  </style>
  