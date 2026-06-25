<template>
  <div class="reports">
    <n-card title="报告列表">
      <template #header-extra>
        <n-space>
          <n-radio-group v-model:value="statusFilter" size="small">
            <n-radio-button value="all">全部</n-radio-button>
            <n-radio-button value="normal">正常</n-radio-button>
            <n-radio-button value="alert">异常保留</n-radio-button>
          </n-radio-group>
          <RefreshButton size="small" :loading="loading" @click="fetchReports" />
        </n-space>
      </template>

      <n-empty
        v-if="!loading && filteredReports.length === 0"
        description="暂无备份报告"
        style="margin: 24px 0;"
      />

      <n-data-table
        v-else
        :columns="columns"
        :data="filteredReports"
        :loading="loading"
        :pagination="pagination"
      />
    </n-card>

    <n-modal
      v-model:show="showModal"
      preset="card"
      :title="currentReport?.filename || '报告详情'"
      style="width: 90%; max-width: 1200px;"
    >
      <n-spin :show="contentLoading">
        <n-scrollbar style="max-height: 75vh;">
          <div v-html="renderedContent" class="markdown-body"></div>
        </n-scrollbar>
      </n-spin>
    </n-modal>

    <ForceDeleteConfirmModal
      v-model:show="showForceDeleteModal"
      title="强制删除报告"
      description="此报告已标记为永久保留（含异常记录）。强制删除后无法从报告侧追溯该次备份摘要。"
      :loading="forceDeleteLoading"
      @confirm="executeForceDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import {
  NCard, NButton, NDataTable, NIcon, NModal, NScrollbar, NTag, NSpace,
  NRadioGroup, NRadioButton, NSpin, NEmpty, NPopconfirm, useMessage
} from 'naive-ui'
import { DocumentTextOutline, EyeOutline, TrashOutline } from '@vicons/ionicons5'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import 'github-markdown-css/github-markdown-dark.css'
import api from '@/api/client'
import { getApiErrorMessage } from '@/utils/errorHandler'
import RefreshButton from '@/components/RefreshButton.vue'
import ForceDeleteConfirmModal from '@/components/ForceDeleteConfirmModal.vue'
import { useAuthStore } from '@/stores/auth'

const message = useMessage()
const authStore = useAuthStore()

const loading = ref(false)
const contentLoading = ref(false)
const reports = ref<any[]>([])
const statusFilter = ref<'all' | 'normal' | 'alert'>('all')
const showModal = ref(false)
const currentReport = ref<any>(null)
const forceDeleteFilename = ref('')
const showForceDeleteModal = ref(false)
const forceDeleteLoading = ref(false)

const filteredReports = computed(() => {
  if (statusFilter.value === 'all') return reports.value
  if (statusFilter.value === 'alert') {
    return reports.value.filter((r) => r.has_alerts || r.is_protected || r.status === 'alert')
  }
  return reports.value.filter((r) => !r.has_alerts && !r.is_protected && r.status !== 'alert')
})

const columns = computed(() => [
  {
    title: '报告文件',
    key: 'filename',
    render: (row: any) => {
      return h('div', { style: 'display: flex; align-items: center; gap: 8px;' }, [
        h(NIcon, { size: 20 }, { default: () => h(DocumentTextOutline) }),
        h('span', row.filename)
      ])
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    render: (row: any) => formatDate(row.created_at)
  },
  {
    title: '大小',
    key: 'size',
    render: (row: any) => formatBytes(row.size)
  },
  {
    title: '状态',
    key: 'status',
    render: (row: any) => {
      const isAlert = row.has_alerts || row.is_protected || row.status === 'alert'
      if (isAlert) {
        const label = row.is_protected ? '异常保留' : '异常保留'
        return h(NTag, { type: 'warning', size: 'small' }, { default: () => label })
      }
      return h(NTag, { type: 'success', size: 'small' }, { default: () => '正常' })
    }
  },
  {
    title: '操作',
    key: 'actions',
    render: (row: any) => {
      const buttons: any[] = [
        h(
          NButton,
          { size: 'small', type: 'primary', onClick: () => viewReport(row) },
          {
            icon: () => h(NIcon, null, { default: () => h(EyeOutline) }),
            default: () => '查看'
          }
        )
      ]
      if (authStore.isAdmin) {
        if (row.is_protected) {
          buttons.push(
            h(
              NButton,
              {
                size: 'small',
                type: 'error',
                onClick: () => openForceDeleteModal(row.filename)
              },
              { default: () => '强制删除' }
            )
          )
        } else {
          buttons.push(
            h(
              NPopconfirm,
              { onPositiveClick: () => handleDelete(row.filename) },
              {
                trigger: () => h(
                  NButton,
                  { size: 'small', type: 'error' },
                  {
                    icon: () => h(NIcon, null, { default: () => h(TrashOutline) }),
                    default: () => '删除'
                  }
                ),
                default: () => '确定删除此报告吗？'
              }
            )
          )
        }
      }
      return h(NSpace, { size: 4 }, { default: () => buttons })
    }
  }
])

const pagination = { pageSize: 10 }

const renderedContent = computed(() => {
  if (!currentReport.value?.content) return ''
  try {
    const html = marked.parse(currentReport.value.content) as string
    return DOMPurify.sanitize(html)
  } catch (error) {
    console.error('Markdown 渲染失败:', error)
    return DOMPurify.sanitize(`<pre>${currentReport.value.content}</pre>`)
  }
})

async function fetchReports() {
  loading.value = true
  try {
    const response = await api.get('/reports')
    reports.value = response.data
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    loading.value = false
  }
}

async function viewReport(report: any) {
  showModal.value = true
  contentLoading.value = true
  currentReport.value = null
  try {
    const response = await api.get(`/reports/${report.filename}`)
    currentReport.value = response.data
  } catch (error) {
    message.error(getApiErrorMessage(error))
    showModal.value = false
  } finally {
    contentLoading.value = false
  }
}

async function handleDelete(filename: string, force = false) {
  try {
    await api.delete(`/reports/${filename}`, { params: { force } })
    message.success('报告已删除')
    await fetchReports()
  } catch (error) {
    message.error(getApiErrorMessage(error))
  }
}

function openForceDeleteModal(filename: string) {
  forceDeleteFilename.value = filename
  showForceDeleteModal.value = true
}

async function executeForceDelete() {
  forceDeleteLoading.value = true
  try {
    await handleDelete(forceDeleteFilename.value, true)
    showForceDeleteModal.value = false
  } finally {
    forceDeleteLoading.value = false
  }
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

function formatDate(date: string): string {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchReports()
})
</script>

<style>
.markdown-body {
  padding: 20px;
  box-sizing: border-box;
  background-color: transparent !important;
  color: inherit;
}

.markdown-body table {
  border-color: rgba(255, 255, 255, 0.09);
}

.markdown-body tr {
  border-color: rgba(255, 255, 255, 0.09);
  background-color: transparent;
}

.markdown-body tr:nth-child(2n) {
  background-color: rgba(255, 255, 255, 0.02);
}

.markdown-body code {
  background-color: rgba(255, 255, 255, 0.06);
  color: inherit;
}

.markdown-body pre {
  background-color: rgba(255, 255, 255, 0.06);
}
</style>
