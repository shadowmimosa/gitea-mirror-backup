<template>
  <div class="reports">
    <n-card title="报告列表">
      <template #header-extra>
        <n-button type="primary" @click="fetchReports">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          刷新
        </n-button>
      </template>

      <n-data-table
        :columns="columns"
        :data="reports"
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
      <n-scrollbar style="max-height: 75vh;">
        <div v-html="renderedContent" class="markdown-body"></div>
      </n-scrollbar>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { NCard, NButton, NDataTable, NIcon, NModal, NScrollbar, NTag, useMessage } from 'naive-ui'
import { RefreshOutline, DocumentTextOutline, EyeOutline } from '@vicons/ionicons5'
import { marked } from 'marked'
import 'github-markdown-css/github-markdown-dark.css'
import api from '@/api/client'

const message = useMessage()

const loading = ref(false)
const reports = ref<any[]>([])
const showModal = ref(false)
const currentReport = ref<any>(null)

const columns = [
  {
    title: '报告文件',
    key: 'filename',
    render: (row: any) => {
      return h(
        'div',
        { style: 'display: flex; align-items: center; gap: 8px;' },
        [
          h(NIcon, { size: 20 }, { default: () => h(DocumentTextOutline) }),
          h('span', row.filename)
        ]
      )
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
      if (row.is_protected) {
        return h(NTag, { type: 'warning' }, { default: () => '🔒 已保护' })
      }
      return h(NTag, { type: 'success' }, { default: () => '正常' })
    }
  },
  {
    title: '操作',
    key: 'actions',
    render: (row: any) => {
      return h(
        NButton,
        {
          size: 'small',
          type: 'primary',
          onClick: () => viewReport(row)
        },
        {
          icon: () => h(NIcon, null, { default: () => h(EyeOutline) }),
          default: () => '查看'
        }
      )
    }
  }
]

const pagination = {
  pageSize: 10
}

const renderedContent = computed(() => {
  if (!currentReport.value?.content) return ''
  try {
    return marked.parse(currentReport.value.content)
  } catch (error) {
    console.error('Markdown 渲染失败:', error)
    return '<pre>' + currentReport.value.content + '</pre>'
  }
})

async function fetchReports() {
  loading.value = true
  try {
    const response = await api.get('/reports')
    reports.value = response.data
  } catch (error) {
    message.error('获取报告列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

async function viewReport(report: any) {
  try {
    const response = await api.get(`/reports/${report.filename}`)
    currentReport.value = response.data
    showModal.value = true
  } catch (error) {
    message.error('获取报告详情失败')
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

/* 适配暗色主题 */
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

