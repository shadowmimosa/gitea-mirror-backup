<template>
  <div class="settings">
    <n-card title="系统设置">
      <n-tabs type="line" animated>
        <n-tab-pane name="basic" tab="基础设置">
          <n-form label-placement="left" label-width="120">
            <n-form-item label="应用名称">
              <n-input value="Gitea Mirror Backup" disabled />
            </n-form-item>
            <n-form-item label="版本">
              <n-input value="1.5.0" disabled />
            </n-form-item>
          </n-form>
        </n-tab-pane>

        <n-tab-pane name="about" tab="关于">
          <n-space vertical>
            <n-alert type="info">
              <strong>Gitea Mirror Backup Web 管理界面</strong>
              <p>版本: 1.5.0</p>
              <p>基于 FastAPI + Vue 3 + Naive UI 构建</p>
            </n-alert>
          </n-space>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { NCard, NTabs, NTabPane, NForm, NFormItem, NInput, NSpace, NAlert } from 'naive-ui'
</script>

