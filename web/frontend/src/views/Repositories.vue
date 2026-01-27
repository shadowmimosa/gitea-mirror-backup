<template>
  <div class="repositories">
    <n-card title="仓库列表">
      <template #header-extra>
        <n-button type="primary" @click="fetchRepositories">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          刷新
        </n-button>
      </template>

      <n-data-table
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
import { NCard, NButton, NDataTable, NIcon, NTag, useMessage } from 'naive-ui'
import { RefreshOutline, EyeOutline } from '@vicons/ionicons5'
import api from '@/api/client'

const router = useRouter()
const message = useMessage()

const loading = ref(false)
const repositories = ref([])

const columns = [
  {
    title: '仓库名称',
    key: 'full_name',
    render: (row: any) => {
      return h(
        'a',
        {
          style: 'cursor: pointer; color: #18a058;',
          onClick: () => router.push(`/repositories/${encodeURIComponent(row.full_name)}`)
        },
        row.full_name
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
        return `${row.snapshot_count} (🔒 ${row.protected_snapshots})`
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
        return h(NTag, { type: 'warning' }, { default: () => '⚠️ 有异常' })
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

const pagination = {
  pageSize: 10
}

async function fetchRepositories() {
  loading.value = true
  try {
    const response = await api.get('/repositories')
    repositories.value = response.data
  } catch (error) {
    message.error('获取仓库列表失败')
    console.error(error)
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

