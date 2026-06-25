<template>
  <div class="snapshots">
    <n-card title="快照列表">
      <template #header-extra>
        <RefreshButton :loading="loading" @click="fetchSnapshots" />
      </template>

      <div class="filter-bar">
        <n-input
          v-model:value="repositorySearch"
          placeholder="搜索仓库 owner/repo"
          clearable
          style="width: 220px;"
          @keyup.enter="applyFilters"
        />
        <n-select
          v-model:value="protectedFilter"
          :options="protectedOptions"
          style="width: 140px;"
        />
        <div class="filter-item">
          <span class="filter-item__label">{{ includeSize ? '显示大小' : '隐藏大小' }}</span>
          <n-switch v-model:value="includeSize" size="small" />
        </div>
        <n-button @click="applyFilters">筛选</n-button>
        <n-button @click="showProtectedOnly">仅受保护</n-button>
        <n-button @click="showAlertReposOnly">异常仓库</n-button>
        <n-button @click="resetFilters">重置</n-button>
      </div>
      <n-space v-if="authStore.isAdmin" style="margin-bottom: 12px;">
        <n-button
          type="error"
          :disabled="selectedSnapshots.length === 0 || batchDeleting"
          :loading="batchDeleting"
          @click="handleBatchDelete"
        >
          <template #icon>
            <n-icon><TrashOutline /></n-icon>
          </template>
          批量删除 ({{ selectedSnapshots.length }})
        </n-button>
        <n-text v-if="batchDeleting" depth="3" style="font-size: 12px;">
          正在删除 {{ batchProgress.current }}/{{ batchProgress.total }}
        </n-text>
        <n-text v-else-if="hasProtectedSelected" depth="3" style="font-size: 12px;">
          选中项含受保护快照，批量删除时将要求二次确认
        </n-text>
      </n-space>

      <n-empty
        v-if="!loading && snapshots.length === 0"
        description="暂无快照，等待下次定时备份"
        style="margin: 24px 0;"
      />

      <n-data-table
        v-else
        :columns="tableColumns"
        :data="snapshots"
        :loading="loading"
        :pagination="false"
        :row-key="(row: any) => `${row.repository}/${row.id}`"
        v-model:checked-row-keys="selectedSnapshots"
        @update:checked-row-keys="handleCheck"
      />

      <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
        <n-pagination
          v-model:page="currentPage"
          v-model:page-size="pageSize"
          :item-count="totalCount"
          :page-sizes="[10, 20, 50, 100]"
          show-size-picker
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        >
          <template #prefix="{ itemCount }">
            共 {{ itemCount }} 条
          </template>
        </n-pagination>
      </div>
    </n-card>

    <ForceDeleteSnapshotModal
      v-model:show="showForceDeleteModal"
      :snapshot-id="forceDeleteSnapshotId"
      :repository="forceDeleteRepository"
      :batch-count="forceDeleteBatchCount"
      :loading="forceDeleteLoading"
      @confirm="executeForceDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NCard, NButton, NDataTable, NIcon, NTag, NPopconfirm, NSpace, NText,
  NPagination, NInput, NSelect, NSwitch, NEmpty, useMessage, useDialog
} from 'naive-ui'
import { TrashOutline } from '@vicons/ionicons5'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/errorHandler'
import RefreshButton from '@/components/RefreshButton.vue'
import ForceDeleteSnapshotModal from '@/components/ForceDeleteSnapshotModal.vue'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const authStore = useAuthStore()

const loading = ref(false)
const batchDeleting = ref(false)
const batchProgress = ref({ current: 0, total: 0 })
const showForceDeleteModal = ref(false)
const forceDeleteLoading = ref(false)
const forceDeleteSnapshotId = ref('')
const forceDeleteRepository = ref('')
const forceDeleteBatchCount = ref(1)
const pendingForceDeletes = ref<Array<{ id: string; repository: string; is_protected?: boolean }>>([])
const snapshots = ref<any[]>([])
const selectedSnapshots = ref<string[]>([])
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const repositorySearch = ref('')
const protectedFilter = ref<string>('')
const includeSize = ref(false)

const protectedOptions = [
  { label: '全部状态', value: '' },
  { label: '仅受保护', value: 'true' },
  { label: '异常仓库', value: 'alert_repo' },
  { label: '仅正常', value: 'false' }
]

function syncQueryToState() {
  repositorySearch.value = (route.query.search as string) || ''
  if (route.query.alert_repo === 'true') {
    protectedFilter.value = 'alert_repo'
  } else {
    protectedFilter.value = route.query.protected === 'true' ? 'true' : route.query.protected === 'false' ? 'false' : ''
  }
  currentPage.value = Number(route.query.page) || 1
  pageSize.value = Number(route.query.page_size) || 10
  includeSize.value = route.query.include_size === 'true'
}

function syncStateToQuery() {
  const query: Record<string, string> = {}
  if (repositorySearch.value.trim()) query.search = repositorySearch.value.trim()
  if (protectedFilter.value === 'alert_repo') {
    query.alert_repo = 'true'
  } else if (protectedFilter.value) {
    query.protected = protectedFilter.value
  }
  if (currentPage.value > 1) query.page = String(currentPage.value)
  if (pageSize.value !== 10) query.page_size = String(pageSize.value)
  if (includeSize.value) query.include_size = 'true'
  router.replace({ query })
}

function buildFilterParams() {
  const params: Record<string, unknown> = {
    page: currentPage.value,
    page_size: pageSize.value,
    include_size: includeSize.value
  }
  if (repositorySearch.value.trim()) {
    params.repository_search = repositorySearch.value.trim()
  }
  if (protectedFilter.value === 'true') params.is_protected = true
  if (protectedFilter.value === 'false') params.is_protected = false
  if (protectedFilter.value === 'alert_repo') params.has_repo_alerts = true
  return params
}

function applyFilters() {
  currentPage.value = 1
  selectedSnapshots.value = []
  syncStateToQuery()
  fetchSnapshots()
}

function showProtectedOnly() {
  protectedFilter.value = 'true'
  applyFilters()
}

function showAlertReposOnly() {
  protectedFilter.value = 'alert_repo'
  applyFilters()
}

function resetFilters() {
  repositorySearch.value = ''
  protectedFilter.value = ''
  includeSize.value = false
  applyFilters()
}

const hasProtectedSelected = computed(() => {
  return snapshots.value.some((s: any) => {
    const rowKey = `${s.repository}/${s.id}`
    return selectedSnapshots.value.includes(rowKey) && s.is_protected
  })
})

const baseColumns = computed(() => {
  const cols: any[] = []
  if (authStore.isAdmin) {
    cols.push({
      type: 'selection' as const
    })
  }
  cols.push(
    { title: '快照 ID', key: 'id', ellipsis: { tooltip: true } },
    {
      title: '仓库',
      key: 'repository',
      render: (row: any) => {
        return h(
          NButton,
          {
            text: true,
            type: 'primary',
            tag: 'a',
            onClick: () => router.push(`/repositories/${encodeURIComponent(row.repository)}`)
          },
          { default: () => row.repository }
        )
      }
    }
  )
  if (includeSize.value) {
    cols.push({
      title: '大小',
      key: 'size',
      render: (row: any) => formatBytes(row.size)
    })
  }
  cols.push(
    {
      title: '创建时间',
      key: 'created_at',
      render: (row: any) => formatDate(row.created_at)
    },
    {
      title: '状态',
      key: 'status',
      render: (row: any) => {
        const tags: any[] = []
        if (row.is_protected) {
          tags.push(h(NTag, { type: 'warning', size: 'small' }, { default: () => '已保护' }))
          if (row.has_repo_alerts) {
            tags.push(h(NTag, { type: 'error', size: 'small' }, { default: () => '异常保留' }))
          }
        }
        if (tags.length === 0) {
          return h(NTag, { type: 'success', size: 'small' }, { default: () => '正常' })
        }
        return h(NSpace, { size: 4 }, { default: () => tags })
      }
    }
  )
  if (authStore.isAdmin) {
    cols.push({
      title: '操作',
      key: 'actions',
      render: (row: any) => {
        if (row.is_protected) {
          return h(
            NButton,
            {
              size: 'small',
              type: 'error',
              onClick: () => openForceDeleteModal(row.id, row.repository)
            },
            { default: () => '强制删除' }
          )
        }
        return h(
          NPopconfirm,
          { onPositiveClick: () => handleDelete(row.id, row.repository) },
          {
            trigger: () => h(NButton, { size: 'small', type: 'error' }, {
              icon: () => h(NIcon, null, { default: () => h(TrashOutline) }),
              default: () => '删除'
            }),
            default: () => '确定删除此快照吗？'
          }
        )
      }
    })
  }
  return cols
})

const tableColumns = computed(() => baseColumns.value)

function handlePageChange(_page: number) {
  selectedSnapshots.value = []
  syncStateToQuery()
  fetchSnapshots()
}

function handlePageSizeChange(_size: number) {
  currentPage.value = 1
  selectedSnapshots.value = []
  syncStateToQuery()
  fetchSnapshots()
}

function handleCheck(keys: Array<string | number>) {
  selectedSnapshots.value = keys as string[]
}

async function fetchSnapshots() {
  loading.value = true
  try {
    const filterParams = buildFilterParams()
    const countParams = { ...filterParams }
    delete countParams.page
    delete countParams.page_size
    delete countParams.include_size

    const countResponse = await api.get('/snapshots/count', { params: countParams })
    totalCount.value = countResponse.data.count

    const response = await api.get('/snapshots', { params: filterParams })
    snapshots.value = response.data
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    loading.value = false
  }
}

async function deleteSnapshot(id: string, repository: string, force = false) {
  const params: Record<string, string | boolean> = {
    repository,
    force
  }
  await api.delete(`/snapshots/${id}`, { params })
}

function openForceDeleteModal(id: string, repository: string) {
  forceDeleteSnapshotId.value = id
  forceDeleteRepository.value = repository
  forceDeleteBatchCount.value = 1
  pendingForceDeletes.value = [{ id, repository, is_protected: true }]
  showForceDeleteModal.value = true
}

async function executeForceDelete() {
  forceDeleteLoading.value = true
  const items = pendingForceDeletes.value
  try {
    for (const item of items) {
      await deleteSnapshot(item.id, item.repository, item.is_protected ?? true)
    }
    const protectedCount = items.filter((item) => item.is_protected).length
    if (items.length > 1) {
      message.success(`已删除 ${items.length} 个快照（含 ${protectedCount} 个受保护）`)
    } else {
      message.success('强制删除成功')
    }
    showForceDeleteModal.value = false
    pendingForceDeletes.value = []
    selectedSnapshots.value = []
    await fetchSnapshots()
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    forceDeleteLoading.value = false
  }
}

async function handleDelete(id: string, repository: string) {
  try {
    await deleteSnapshot(id, repository)
    message.success('删除成功')
    await fetchSnapshots()
  } catch (error) {
    message.error(getApiErrorMessage(error))
  }
}

async function handleBatchDelete() {
  if (selectedSnapshots.value.length === 0) return

  const items = selectedSnapshots.value.map((rowKey) => {
    const lastSlashIndex = (rowKey as string).lastIndexOf('/')
    const repository = (rowKey as string).substring(0, lastSlashIndex)
    const snapshotId = (rowKey as string).substring(lastSlashIndex + 1)
    const snapshot = snapshots.value.find(
      (s: any) => s.id === snapshotId && s.repository === repository
    )
    return { id: snapshotId, repository, is_protected: snapshot?.is_protected }
  })

  const protectedItems = items.filter((item) => item.is_protected)

  if (protectedItems.length > 0) {
    forceDeleteSnapshotId.value = protectedItems.length === 1 ? protectedItems[0].id : ''
    forceDeleteRepository.value = protectedItems.length === 1 ? protectedItems[0].repository : ''
    forceDeleteBatchCount.value = protectedItems.length
    pendingForceDeletes.value = items
    showForceDeleteModal.value = true
    return
  }

  dialog.warning({
    title: '批量删除确认',
    content: `确定要删除选中的 ${selectedSnapshots.value.length} 个快照吗？此操作不可恢复！`,
    positiveText: '确定删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      batchDeleting.value = true
      batchProgress.value = { current: 0, total: items.length }
      let successCount = 0
      let failCount = 0

      for (const item of items) {
        try {
          await deleteSnapshot(item.id, item.repository)
          successCount++
        } catch {
          failCount++
        }
        batchProgress.value.current++
      }

      batchDeleting.value = false
      if (successCount > 0) message.success(`成功删除 ${successCount} 个快照`)
      if (failCount > 0) message.error(`${failCount} 个快照删除失败`)

      selectedSnapshots.value = []
      await fetchSnapshots()
    }
  })
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

watch(() => route.query, () => {
  syncQueryToState()
  fetchSnapshots()
})

onMounted(() => {
  syncQueryToState()
  fetchSnapshots()
})
</script>
