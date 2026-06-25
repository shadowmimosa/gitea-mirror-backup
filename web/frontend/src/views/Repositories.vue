<template>
  <div class="repositories">
    <n-card title="仓库列表">
      <template #header-extra>
        <RefreshButton :loading="loading" @click="fetchRepositories" />
      </template>

      <n-empty
        v-if="!loading && repositories.length === 0"
        description="暂无备份仓库，等待首次备份完成"
        style="margin: 24px 0;"
      />

      <n-data-table
        v-else
        :columns="columns"
        :data="repositories"
        :loading="loading"
        :pagination="pagination"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NButton, NDataTable, NIcon, NTag, NEmpty, useMessage } from 'naive-ui'
import { EyeOutline } from '@vicons/ionicons5'
import api from '@/api/client'
import { getApiErrorMessage } from '@/utils/errorHandler'
import RefreshButton from '@/components/RefreshButton.vue'

const router = useRouter()
const message = useMessage()

const loading = ref(false)
const repositories = ref<any[]>([])

const columns = [
  {
    title: '仓库名称',
    key: 'full_name',
    render: (row: any) => {
      return h(
        NButton,
        {
          text: true,
          type: 'primary',
          tag: 'a',
          onClick: () => router.push(`/repositories/${encodeURIComponent(row.full_name)}`)
        },
        { default: () => row.full_name }
      )
    }
  },
  {
    title: '提交数',
    key: 'commit_count',
    render: (row: any) => row.commit_count || 0
  },
  {
    title: '快照数量',
    key: 'snapshot_count',
    render: (row: any) => {
      if (row.protected_snapshots > 0) {
        return `${row.snapshot_count} (保护 ${row.protected_snapshots})`
      }
      return row.snapshot_count
    }
  },
  {
    title: '磁盘使用',
    key: 'disk_usage',
    render: (row: any) => formatBytes(row.disk_usage)
  },
  {
    title: '最后备份',
    key: 'last_backup_time',
    render: (row: any) => formatDate(row.last_backup_time)
  },
  {
    title: '状态',
    key: 'status',
    render: (row: any) => {
      if (row.status === 'warning') {
        return h(NTag, { type: 'warning', size: 'small' }, { default: () => '有异常' })
      }
      return h(NTag, { type: 'success', size: 'small' }, { default: () => '正常' })
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
          onClick: () => router.push(`/repositories/${encodeURIComponent(row.full_name)}`)
        },
        {
          icon: () => h(NIcon, null, { default: () => h(EyeOutline) }),
          default: () => '查看'
        }
      )
    }
  }
]

const pagination = { pageSize: 10 }

async function fetchRepositories() {
  loading.value = true
  try {
    const response = await api.get('/repositories')
    repositories.value = response.data
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    loading.value = false
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
  fetchRepositories()
})
</script>
