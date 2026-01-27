<template>
  <div class="dashboard">
    <n-card title="仪表板">
      <n-grid :cols="4" :x-gap="16" :y-gap="16">
        <n-gi>
          <n-card title="总仓库数" hoverable>
            <n-statistic :value="stats.total_repositories">
              <template #prefix>
                <n-icon><FolderOpenOutline /></n-icon>
              </template>
            </n-statistic>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card title="总快照数" hoverable>
            <n-statistic :value="stats.total_snapshots">
              <template #prefix>
                <n-icon><CameraOutline /></n-icon>
              </template>
            </n-statistic>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card title="磁盘使用" hoverable>
            <n-statistic :value="formatBytes(stats.total_disk_usage)">
              <template #prefix>
                <n-icon><ServerOutline /></n-icon>
              </template>
            </n-statistic>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card title="成功率" hoverable>
            <n-statistic :value="stats.success_rate" suffix="%">
              <template #prefix>
                <n-icon><CheckmarkCircleOutline /></n-icon>
              </template>
            </n-statistic>
          </n-card>
        </n-gi>
      </n-grid>

      <n-divider />

      <n-descriptions :column="2" bordered>
        <n-descriptions-item label="最后备份时间">
          {{ formatDate(stats.last_backup_time) }}
        </n-descriptions-item>
        <n-descriptions-item label="失败备份数">
          {{ stats.failed_backups }}
        </n-descriptions-item>
      </n-descriptions>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NGrid, NGi, NCard, NStatistic, NIcon, NDivider, NDescriptions, NDescriptionsItem, useMessage } from 'naive-ui'
import { FolderOpenOutline, CameraOutline, ServerOutline, CheckmarkCircleOutline } from '@vicons/ionicons5'
import api from '@/api/client'

const message = useMessage()

interface DashboardStats {
  total_repositories: number
  total_snapshots: number
  total_disk_usage: number
  last_backup_time: string | null
  success_rate: number
  failed_backups: number
}

const stats = ref<DashboardStats>({
  total_repositories: 0,
  total_snapshots: 0,
  total_disk_usage: 0,
  last_backup_time: null,
  success_rate: 0,
  failed_backups: 0
})

async function fetchStats() {
  try {
    const response = await api.get('/dashboard/stats')
    stats.value = response.data
  } catch (error) {
    message.error('获取统计数据失败')
    console.error(error)
  }
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

function formatDate(date: string | null): string {
  if (!date) return '暂无'
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
</style>

