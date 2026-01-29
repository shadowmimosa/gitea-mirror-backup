<template>
  <div class="settings">
    <n-card title="系统设置">
      <n-tabs type="line" animated>
        <n-tab-pane name="basic" tab="基础设置">
          <n-form label-placement="left" label-width="120">
            <n-form-item label="应用名称">
              <n-input :value="appInfo.name" disabled />
            </n-form-item>
            <n-form-item label="版本">
              <n-input :value="appInfo.version" disabled />
            </n-form-item>
          </n-form>
        </n-tab-pane>

        <n-tab-pane name="about" tab="关于">
          <n-space vertical>
            <n-alert type="info">
              <strong>{{ appInfo.name }}</strong>
              <p>版本: {{ appInfo.version }}</p>
              <p>基于 FastAPI + Vue 3 + Naive UI 构建</p>
            </n-alert>
          </n-space>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NCard, NTabs, NTabPane, NForm, NFormItem, NInput, NSpace, NAlert } from 'naive-ui'
import axios from 'axios'

const appInfo = ref({
  name: 'Gitea Mirror Backup Web',
  version: '加载中...'
})

onMounted(async () => {
  try {
    const response = await axios.get('/api/system/info')
    appInfo.value = response.data
  } catch (error) {
    console.error('获取系统信息失败:', error)
    // 如果 API 不存在，尝试从根路径获取
    try {
      const response = await axios.get('/')
      appInfo.value = {
        name: response.data.name || 'Gitea Mirror Backup Web',
        version: response.data.version || '未知'
      }
    } catch (err) {
      console.error('获取版本信息失败:', err)
    }
  }
})
</script>
