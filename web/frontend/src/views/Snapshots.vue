<template>
  <div class="snapshots">
    <n-card title="快照列表">
      <template #header-extra>
        <n-button type="primary" @click="fetchSnapshots">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          刷新
        </n-button>
      </template>

      <n-space style="margin-bottom: 12px;">
        <n-button 
          type="error" 
          :disabled="selectedSnapshots.length === 0 || hasProtectedSelected"
          @click="handleBatchDelete"
        >
          <template #icon>
            <n-icon><TrashOutline /></n-icon>
          </template>
          批量删除 ({{ selectedSnapshots.length }})
        </n-button>
        <n-text v-if="hasProtectedSelected" depth="3" style="font-size: 12px;">
          * 已选择的快照中包含受保护的快照，无法删除
        </n-text>
      </n-space>

      <n-data-table
        :columns="columns"
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
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted, computed } from 'vue'
import { NCard, NButton, NDataTable, NIcon, NTag, NPopconfirm, NSpace, NText, NPagination, useMessage, useDialog } from 'naive-ui'
import { RefreshOutline, TrashOutline } from '@vicons/ionicons5'
import api from '@/api/client'

const message = useMessage()
const dialog = useDialog()

const loading = ref(false)
const snapshots = ref([])
const selectedSnapshots = ref<string[]>([])
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

const hasProtectedSelected = computed(() => {
  return snapshots.value.some((s: any) => {
    const rowKey = `${s.repository}/${s.id}`
    return selectedSnapshots.value.includes(rowKey) && s.is_protected
  })
})

const columns = [
  {
    type: 'selection' as const,
    disabled: (row: any) => row.is_protected
  },
  {
    title: '快照 ID',
    key: 'id',
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '仓库',
    key: 'repository'
  },
  {
    title: '大小',
    key: 'size',
    render: (row: any) => formatBytes(row.size)
  },
  {
    title: '创建时间',
    key: 'created_at',
    render: (row: any) => formatDate(row.created_at)
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
      // 如果快照受保护，显示禁用的删除按钮
      if (row.is_protected) {
        return h(
          NButton,
          { size: 'small', type: 'error', disabled: true },
          {
            icon: () => h(NIcon, null, { default: () => h(TrashOutline) }),
            default: () => '已保护'
          }
        )
      }
      
      return h(
        NPopconfirm,
        {
          onPositiveClick: () => handleDelete(row.id, row.repository)
        },
        {
          trigger: () => h(
            NButton,
            { size: 'small', type: 'error' },
            {
              icon: () => h(NIcon, null, { default: () => h(TrashOutline) }),
              default: () => '删除'
            }
          ),
          default: () => '确定删除此快照吗？'
        }
      )
    }
  }
]

function handlePageChange(page: number) {
  console.log('切换到页面:', page)
  selectedSnapshots.value = []  // 切换页面时清空选中
  fetchSnapshots()
}

function handlePageSizeChange(size: number) {
  console.log('更新页面大小:', size)
  currentPage.value = 1
  selectedSnapshots.value = []  // 切换页面大小时清空选中
  fetchSnapshots()
}

function handleCheck(keys: Array<string | number>) {
  selectedSnapshots.value = keys as string[]
}

async function fetchSnapshots() {
  loading.value = true
  try {
    // 获取总数
    const countResponse = await api.get('/snapshots/count')
    totalCount.value = countResponse.data.count
    
    // 获取当前页数据（包含大小）
    const response = await api.get('/snapshots', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        include_size: true
      }
    })
    snapshots.value = response.data
  } catch (error) {
    message.error('获取快照列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

async function handleDelete(id: string, repository: string) {
  try {
    await api.delete(`/snapshots/${id}?repository=${encodeURIComponent(repository)}`)
    message.success('删除成功')
    await fetchSnapshots()
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail || '删除失败'
    message.error(errorMsg)
    console.error(error)
  }
}

async function handleBatchDelete() {
  if (selectedSnapshots.value.length === 0) {
    return
  }

  dialog.warning({
    title: '批量删除确认',
    content: `确定要删除选中的 ${selectedSnapshots.value.length} 个快照吗？此操作不可恢复！`,
    positiveText: '确定删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      let successCount = 0
      let failCount = 0

      for (const rowKey of selectedSnapshots.value) {
        // rowKey 格式为 "repository/snapshotId"
        // 需要解析出 repository 和 snapshotId
        const lastSlashIndex = (rowKey as string).lastIndexOf('/')
        if (lastSlashIndex === -1) continue
        
        const repository = (rowKey as string).substring(0, lastSlashIndex)
        const snapshotId = (rowKey as string).substring(lastSlashIndex + 1)

        try {
          await api.delete(`/snapshots/${snapshotId}?repository=${encodeURIComponent(repository)}`)
          successCount++
        } catch (error) {
          failCount++
          console.error(`删除快照 ${snapshotId} 失败:`, error)
        }
      }

      if (successCount > 0) {
        message.success(`成功删除 ${successCount} 个快照`)
      }
      if (failCount > 0) {
        message.error(`${failCount} 个快照删除失败`)
      }

      // 先清空选中状态
      selectedSnapshots.value = []
      // 再刷新列表
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

onMounted(() => {
  fetchSnapshots()
})
</script>

