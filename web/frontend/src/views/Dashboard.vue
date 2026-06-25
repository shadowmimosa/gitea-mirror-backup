<template>
  <div class="dashboard">
    <n-spin :show="loading">
      <PageActions>
        <n-space>
          <n-button
            v-if="authStore.isAdmin"
            type="primary"
            size="small"
            :loading="backupLoading"
            @click="triggerBackup"
          >
            立即备份
          </n-button>
          <n-button size="small" @click="fetchAll">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            刷新
          </n-button>
        </n-space>
      </PageActions>

      <n-card>
        <n-empty
          v-if="!loading && loadError"
          description="统计数据加载失败"
          style="margin-bottom: 16px;"
        >
          <template #extra>
            <n-button @click="fetchAll">重试</n-button>
          </template>
        </n-empty>

        <template v-else>
          <n-grid :cols="gridCols" :x-gap="16" :y-gap="16" responsive="screen">
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
            <n-descriptions-item label="受保护快照">
              <n-button text type="warning" @click="goProtectedSnapshots">
                {{ stats.protected_snapshots }} 个
              </n-button>
            </n-descriptions-item>
            <n-descriptions-item label="运行中任务">
              <n-button text type="info" @click="$router.push('/tasks')">
                {{ runningTask ? `任务 #${runningTask.id}` : '无' }}
              </n-button>
            </n-descriptions-item>
          </n-descriptions>

          <n-divider>近 7 天备份趋势</n-divider>

          <n-empty v-if="trends.length === 0 && !trendsLoading" description="暂无趋势数据" />

          <div v-else class="trend-chart">
            <div v-for="item in trends" :key="item.date" class="trend-row">
              <span class="trend-date">{{ item.date }}</span>
              <div class="trend-bars">
                <div
                  class="trend-bar success"
                  :style="{ width: barWidth(item.success_count, item) }"
                  :title="`成功: ${item.success_count}`"
                />
                <div
                  class="trend-bar failed"
                  :style="{ width: barWidth(item.failed_count, item) }"
                  :title="`异常: ${item.failed_count}`"
                />
              </div>
              <span class="trend-label">
                成功 {{ item.success_count }} / 异常 {{ item.failed_count }}
              </span>
            </div>
          </div>
        </template>
      </n-card>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NGrid, NGi, NCard, NStatistic, NIcon, NDivider, NDescriptions,
  NDescriptionsItem, NButton, NSpin, NEmpty, useMessage
} from 'naive-ui'
import {
  FolderOpenOutline, CameraOutline, ServerOutline,
  CheckmarkCircleOutline, RefreshOutline
} from '@vicons/ionicons5'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/errorHandler'
import PageActions from '@/components/PageActions.vue'

const message = useMessage()
const router = useRouter()
const authStore = useAuthStore()

interface DashboardStats {
  total_repositories: number
  total_snapshots: number
  protected_snapshots: number
  total_disk_usage: number
  last_backup_time: string | null
  success_rate: number
  failed_backups: number
}

interface TrendItem {
  date: string
  success_count: number
  failed_count: number
  disk_usage: number
}

const loading = ref(true)
const trendsLoading = ref(false)
const loadError = ref(false)
const backupLoading = ref(false)
const gridCols = ref(4)
const runningTask = ref<any>(null)

const stats = ref<DashboardStats>({
  total_repositories: 0,
  total_snapshots: 0,
  protected_snapshots: 0,
  total_disk_usage: 0,
  last_backup_time: null,
  success_rate: 0,
  failed_backups: 0
})

const trends = ref<TrendItem[]>([])

function goProtectedSnapshots() {
  router.push({ path: '/snapshots', query: { protected: 'true' } })
}

async function fetchStats() {
  const response = await api.get('/dashboard/stats')
  stats.value = response.data
}

async function fetchTrends() {
  trendsLoading.value = true
  try {
    const response = await api.get('/dashboard/trends', { params: { days: 7 } })
    trends.value = response.data
  } finally {
    trendsLoading.value = false
  }
}

async function fetchRunning() {
  try {
    const response = await api.get('/tasks/running')
    runningTask.value = response.data
  } catch {
    runningTask.value = null
  }
}

async function fetchAll() {
  loading.value = true
  loadError.value = false
  try {
    await Promise.all([fetchStats(), fetchTrends(), fetchRunning()])
  } catch (error) {
    loadError.value = true
    message.error(getApiErrorMessage(error))
  } finally {
    loading.value = false
  }
}

async function triggerBackup() {
  backupLoading.value = true
  try {
    const response = await api.post('/tasks/backup')
    message.success(response.data.message)
    router.push('/tasks')
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    backupLoading.value = false
  }
}

function barWidth(count: number, item: TrendItem): string {
  const total = item.success_count + item.failed_count
  if (total === 0) return '0%'
  return `${Math.max(4, (count / total) * 100)}%`
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
  if (window.innerWidth < 768) gridCols.value = 2
  fetchAll()
})
</script>

<style scoped>
.trend-chart {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.trend-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.trend-date {
  width: 90px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.65);
}

.trend-bars {
  flex: 1;
  display: flex;
  height: 20px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 4px;
  overflow: hidden;
}

.trend-bar {
  height: 100%;
  min-width: 0;
  transition: width 0.3s;
}

.trend-bar.success {
  background: #18a058;
}

.trend-bar.failed {
  background: #d03050;
}

.trend-label {
  width: 140px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  text-align: right;
}

@media (max-width: 768px) {
  .trend-row {
    flex-direction: column;
    align-items: stretch;
  }

  .trend-date,
  .trend-label {
    width: auto;
    text-align: left;
  }
}
</style>
