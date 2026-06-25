<template>
  <div class="tasks">
    <PageActions>
      <n-space>
        <n-button
          v-if="authStore.isAdmin"
          type="primary"
          :loading="triggerLoading"
          :disabled="runningTask?.status === 'running'"
          @click="triggerBackup"
        >
          立即全量备份
        </n-button>
        <RefreshButton :loading="loading" @click="refreshAll" />
      </n-space>
    </PageActions>

    <n-card>
      <n-alert
        v-if="runningTask"
        type="info"
        style="margin-bottom: 16px;"
        title="备份任务运行中"
      >
        任务 #{{ runningTask.id }} 正在执行，开始于 {{ formatDate(runningTask.started_at) }}
        <template v-if="runningTask.repository">（目标: {{ runningTask.repository }}）</template>
      </n-alert>

      <n-data-table
        :columns="columns"
        :data="tasks"
        :loading="loading"
        :pagination="false"
      />

      <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
        <n-pagination
          v-model:page="currentPage"
          v-model:page-size="pageSize"
          :item-count="total"
          :page-sizes="[10, 20, 50]"
          show-size-picker
          @update:page="fetchTasks"
          @update:page-size="handlePageSizeChange"
        />
      </div>
    </n-card>

    <n-modal
      v-model:show="showLogModal"
      preset="card"
      :title="`任务 #${selectedTask?.id} 日志`"
      style="width: 90%; max-width: 1000px;"
    >
      <n-spin :show="logLoading">
        <n-scrollbar style="max-height: 60vh;">
          <pre class="log-content">{{ logContent || '暂无日志' }}</pre>
        </n-scrollbar>
      </n-spin>
      <template #footer>
        <n-space>
          <RefreshButton label="刷新日志" :loading="logLoading" @click="refreshLog" />
          <n-button v-if="selectedTask?.status === 'running'" type="primary" @click="startLogPolling">
            自动刷新
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted, onUnmounted } from 'vue'
import {
  NCard, NButton, NDataTable, NIcon, NTag, NSpace, NPagination,
  NModal, NScrollbar, NSpin, NAlert, useMessage
} from 'naive-ui'
import { EyeOutline } from '@vicons/ionicons5'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import PageActions from '@/components/PageActions.vue'
import RefreshButton from '@/components/RefreshButton.vue'
import { getApiErrorMessage } from '@/utils/errorHandler'

const message = useMessage()
const authStore = useAuthStore()

const loading = ref(false)
const triggerLoading = ref(false)
const tasks = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const runningTask = ref<any>(null)

const showLogModal = ref(false)
const selectedTask = ref<any>(null)
const logContent = ref('')
const logLoading = ref(false)
let logPollTimer: ReturnType<typeof setInterval> | null = null
let runningPollTimer: ReturnType<typeof setInterval> | null = null

const columns = [
  { title: 'ID', key: 'id', width: 70 },
  {
    title: '状态',
    key: 'status',
    render: (row: any) => {
      const map: Record<string, { type: 'info' | 'success' | 'error'; label: string }> = {
        running: { type: 'info', label: '运行中' },
        success: { type: 'success', label: '成功' },
        failed: { type: 'error', label: '失败' }
      }
      const info = map[row.status] || { type: 'info', label: row.status }
      return h(NTag, { type: info.type, size: 'small' }, { default: () => info.label })
    }
  },
  {
    title: '目标仓库',
    key: 'repository',
    render: (row: any) => row.repository || '全量备份'
  },
  {
    title: '开始时间',
    key: 'started_at',
    render: (row: any) => formatDate(row.started_at)
  },
  {
    title: '结束时间',
    key: 'finished_at',
    render: (row: any) => row.finished_at ? formatDate(row.finished_at) : '-'
  },
  {
    title: '错误信息',
    key: 'error_message',
    ellipsis: { tooltip: true },
    render: (row: any) => row.error_message || '-'
  },
  {
    title: '操作',
    key: 'actions',
    render: (row: any) => h(
      NButton,
      { size: 'small', onClick: () => viewLog(row) },
      {
        icon: () => h(NIcon, null, { default: () => h(EyeOutline) }),
        default: () => '查看日志'
      }
    )
  }
]

async function fetchTasks() {
  loading.value = true
  try {
    const response = await api.get('/tasks', {
      params: { page: currentPage.value, page_size: pageSize.value }
    })
    tasks.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    loading.value = false
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

async function triggerBackup() {
  triggerLoading.value = true
  try {
    const response = await api.post('/tasks/backup')
    message.success(response.data.message)
    await refreshAll()
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    triggerLoading.value = false
  }
}

function handlePageSizeChange() {
  currentPage.value = 1
  fetchTasks()
}

async function refreshAll() {
  await Promise.all([fetchTasks(), fetchRunning()])
}

async function viewLog(task: any) {
  selectedTask.value = task
  showLogModal.value = true
  await refreshLog()
  if (task.status === 'running') {
    startLogPolling()
  }
}

async function refreshLog() {
  if (!selectedTask.value) return
  logLoading.value = true
  try {
    const response = await api.get(`/tasks/${selectedTask.value.id}/logs`, { params: { tail: 300 } })
    logContent.value = response.data.content
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    logLoading.value = false
  }
}

function startLogPolling() {
  stopLogPolling()
  logPollTimer = setInterval(async () => {
    await refreshLog()
    if (selectedTask.value?.status !== 'running') {
      stopLogPolling()
      await refreshAll()
    }
  }, 3000)
}

function stopLogPolling() {
  if (logPollTimer) {
    clearInterval(logPollTimer)
    logPollTimer = null
  }
}

function startRunningPoll() {
  runningPollTimer = setInterval(fetchRunning, 5000)
}

function formatDate(date: string): string {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  refreshAll()
  startRunningPoll()
})

onUnmounted(() => {
  stopLogPolling()
  if (runningPollTimer) clearInterval(runningPollTimer)
})
</script>

<style scoped>
.log-content {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
