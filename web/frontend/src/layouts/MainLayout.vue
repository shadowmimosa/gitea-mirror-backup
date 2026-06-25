<template>
  <n-layout has-sider class="main-layout">
    <n-layout-sider
      v-if="!isMobile"
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

    <n-drawer v-model:show="mobileMenuOpen" :width="240" placement="left">
      <n-drawer-content title="Gitea Backup" closable>
        <n-menu
          :options="menuOptions"
          :value="activeKey"
          @update:value="handleMobileMenuSelect"
        />
      </n-drawer-content>
    </n-drawer>

    <n-layout>
      <n-layout-header bordered class="main-header">
        <div class="header-left">
          <n-button v-if="isMobile" text class="menu-trigger" @click="mobileMenuOpen = true">
            <template #icon>
              <n-icon size="22"><MenuOutline /></n-icon>
            </template>
          </n-button>
          <h3>{{ currentTitle }}</h3>
        </div>

        <div class="header-right">
          <n-tag v-if="authStore.isAdmin" type="warning" size="small" style="margin-right: 8px;">
            管理员
          </n-tag>
          <n-dropdown :options="userOptions" @select="handleUserAction">
            <n-button text>
              <template #icon>
                <n-icon><PersonCircleOutline /></n-icon>
              </template>
              {{ authStore.user?.username || '用户' }}
            </n-button>
          </n-dropdown>
        </div>
      </n-layout-header>

      <n-layout-content content-style="padding: 24px;" class="main-content">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NLayout, NLayoutSider, NLayoutHeader, NLayoutContent, NMenu, NButton,
  NDropdown, NIcon, NDrawer, NDrawerContent, NTag
} from 'naive-ui'
import {
  HomeOutline,
  FolderOpenOutline,
  CameraOutline,
  DocumentTextOutline,
  SettingsOutline,
  PersonCircleOutline,
  LogOutOutline,
  PulseOutline,
  MenuOutline
} from '@vicons/ionicons5'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const collapsed = ref(false)
const mobileMenuOpen = ref(false)
const isMobile = ref(false)

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
    label: '任务监控',
    key: 'Tasks',
    icon: () => h(NIcon, null, { default: () => h(PulseOutline) })
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

const activeKey = computed(() => {
  if (route.name === 'RepositoryDetail') return 'Repositories'
  return route.name as string
})

const currentTitle = computed(() => {
  if (route.name === 'RepositoryDetail') {
    return decodeURIComponent(route.params.name as string)
  }
  const metaTitle = route.meta.title as string
  if (metaTitle) return metaTitle
  const option = menuOptions.find(item => item.key === route.name)
  return option?.label || '仪表板'
})

function handleMenuSelect(key: string) {
  router.push({ name: key })
}

function handleMobileMenuSelect(key: string) {
  mobileMenuOpen.value = false
  router.push({ name: key })
}

function handleUserAction(key: string) {
  if (key === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}

function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.main-header {
  height: 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
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

@media (max-width: 768px) {
  .main-content {
    padding: 16px !important;
  }

  .main-header {
    padding: 0 16px;
  }

  .header-left h3 {
    font-size: 16px;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
