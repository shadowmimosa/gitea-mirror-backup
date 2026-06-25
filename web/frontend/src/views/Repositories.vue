<template>
  <div class="repositories">
    <n-card title="仓库列表">
      <template #header-extra>
        <RefreshButton :loading="loading" @click="fetchRepositories" />
      </template>

      <n-alert type="info" :show-icon="false" style="margin-bottom: 16px;">
        列表来自本地备份目录，与 Gitea 源仓对照：源仓已删除的仓库标记为「源仓已删」，可删除本地备份释放空间。
      </n-alert>

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

    <ForceDeleteConfirmModal
      v-model:show="showForceDeleteModal"
      title="强制删除仓库备份"
      :description="forceDeleteDescription"
      :loading="forceDeleteLoading"
      @confirm="executeForceDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard, NButton, NDataTable, NIcon, NTag, NEmpty, NAlert, NSpace,
  NPopconfirm, useMessage
} from 'naive-ui'
import { EyeOutline, TrashOutline } from '@vicons/ionicons5'
import api from '@/api/client'
import { getApiErrorMessage } from '@/utils/errorHandler'
import RefreshButton from '@/components/RefreshButton.vue'
import ForceDeleteConfirmModal from '@/components/ForceDeleteConfirmModal.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const loading = ref(false)
const repositories = ref<any[]>([])
const showForceDeleteModal = ref(false)
const forceDeleteTarget = ref('')
const forceDeleteProtectedCount = ref(0)
const forceDeleteLoading = ref(false)

const forceDeleteDescription = computed(() => {
  const name = forceDeleteTarget.value
  const count = forceDeleteProtectedCount.value
  if (count > 0) {
    return `仓库 ${name} 含 ${count} 个受保护快照。强制删除将清除整个本地备份目录（快照、归档、.alerts 等），不会删除 Gitea 源仓。`
  }
  return `将删除仓库 ${name} 的全部本地备份数据，不会删除 Gitea 源仓。`
})

const columns = computed(() => {
  const cols: any[] = [
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
        const tags: any[] = []
        if (!row.source_exists) {
          tags.push(h(NTag, { type: 'default', size: 'small' }, { default: () => '源仓已删' }))
        }
        if (row.status === 'warning') {
          tags.push(h(NTag, { type: 'warning', size: 'small' }, { default: () => '有异常' }))
        }
        if (tags.length === 0) {
          tags.push(h(NTag, { type: 'success', size: 'small' }, { default: () => '正常' }))
        }
        return h(NSpace, { size: 4 }, { default: () => tags })
      }
    },
    {
      title: '操作',
      key: 'actions',
      render: (row: any) => {
        const buttons: any[] = [
          h(
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
        ]
        if (authStore.isAdmin) {
          if (row.protected_snapshots > 0) {
            buttons.push(
              h(
                NButton,
                {
                  size: 'small',
                  type: 'error',
                  onClick: () => openForceDeleteModal(row)
                },
                { default: () => '强制删除' }
              )
            )
          } else {
            buttons.push(
              h(
                NPopconfirm,
                { onPositiveClick: () => handleDelete(row.full_name) },
                {
                  trigger: () => h(
                    NButton,
                    { size: 'small', type: 'error' },
                    {
                      icon: () => h(NIcon, null, { default: () => h(TrashOutline) }),
                      default: () => '删除备份'
                    }
                  ),
                  default: () => `确定删除 ${row.full_name} 的本地备份吗？`
                }
              )
            )
          }
        }
        return h(NSpace, { size: 4 }, { default: () => buttons })
      }
    }
  ]
  return cols
})

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

async function handleDelete(fullName: string, force = false) {
  try {
    await api.delete(`/repositories/${fullName}`, { params: { force } })
    message.success('仓库备份已删除')
    await fetchRepositories()
  } catch (error) {
    message.error(getApiErrorMessage(error))
  }
}

function openForceDeleteModal(row: any) {
  forceDeleteTarget.value = row.full_name
  forceDeleteProtectedCount.value = row.protected_snapshots || 0
  showForceDeleteModal.value = true
}

async function executeForceDelete() {
  forceDeleteLoading.value = true
  try {
    await handleDelete(forceDeleteTarget.value, true)
    showForceDeleteModal.value = false
  } finally {
    forceDeleteLoading.value = false
  }
}

function formatBytes(bytes: number): string {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

function formatDate(date: string | null): string {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchRepositories()
})
</script>
