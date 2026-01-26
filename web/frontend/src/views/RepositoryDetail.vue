<template>
  <div class="repository-detail">
    <n-card>
      <template #header>
        <n-space align="center">
          <n-button text @click="$router.back()">
            <template #icon>
              <n-icon><ArrowBackOutline /></n-icon>
            </template>
          </n-button>
          <span>{{ repositoryName }}</span>
        </n-space>
      </template>

      <template #header-extra>
        <n-button type="primary" @click="fetchSnapshots">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          刷新
        </n-button>
      </template>

      <!-- 仓库信息 -->
      <n-descriptions v-if="repoInfo" :column="3" bordered style="margin-bottom: 20px;">
        <n-descriptions-item label="仓库全名">
          {{ repoInfo.full_name }}
        </n-descriptions-item>
        <n-descriptions-item label="提交数">
          {{ repoInfo.commit_count || 0 }}
        </n-descriptions-item>
        <n-descriptions-item label="快照数量">
          {{ repoInfo.snapshot_count }}
          <span v-if="repoInfo.protected_snapshots > 0" style="color: #f0a020;">
            (🔒 {{ repoInfo.protected_snapshots }})
          </span>
        </n-descriptions-item>
        <n-descriptions-item label="磁盘使用">
          {{ formatBytes(repoInfo.disk_usage) }}
        </n-descriptions-item>
        <n-descriptions-item label="最后备份">
          {{ formatDate(repoInfo.last_backup_time) }}
        </n-descriptions-item>
        <n-descriptions-item label="状态">
          <n-tag :type="repoInfo.status === 'warning' ? 'warning' : 'success'">
            {{ repoInfo.status === 'warning' ? '⚠️ 有异常' : '正常' }}
          </n-tag>
        </n-descriptions-item>
      </n-descriptions>

      <!-- 快照列表 -->
      <n-divider>快照列表</n-divider>
      
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
        :pagination="pagination"
        :row-key="(row: any) => row.id"
        v-model:checked-row-keys="selectedSnapshots"
        @update:checked-row-keys="handleCheck"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  NCard, NButton, NDataTable, NIcon, NTag, NPopconfirm, NSpace, 
  NDivider, NDescriptions, NDescriptionsItem, NText, useMessage, useDialog 
} from 'naive-ui'
import { RefreshOutline, TrashOutline, ArrowBackOutline } from '@vicons/ionicons5'
import api from '@/api/client'

const route = useRoute()
const message = useMessage()
const dialog = useDialog()

const repositoryName = computed(() => decodeURIComponent(route.params.name as string))
const loading = ref(false)
const snapshots = ref([])
const repoInfo = ref<any>(null)
const selectedSnapshots = ref<string[]>([])

const hasProtectedSelected = computed(() => {
  return snapshots.value.some((s: any) => 
    selectedSnapshots.value.includes(s.id) && s.is_protected
  )
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
          onPositiveClick: () => handleDelete(row.id)
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

const pagination = {
  pageSize: 10
}

function handleCheck(keys: Array<string | number>) {
  selectedSnapshots.value = keys as string[]
}

async function fetchSnapshots() {
  loading.value = true
  try {
    // 使用仓库详情接口，一次性获取仓库信息和快照列表
    const response = await api.get(`/repositories/${encodeURIComponent(repositoryName.value)}`)
    repoInfo.value = response.data
    snapshots.value = response.data.snapshots || []
  } catch (error) {
    message.error('获取快照列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

async function handleDelete(id: string) {
  try {
    await api.delete(`/snapshots/${id}?repository=${encodeURIComponent(repositoryName.value)}`)
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

      for (const snapshotId of selectedSnapshots.value) {
        try {
          await api.delete(`/snapshots/${snapshotId}?repository=${encodeURIComponent(repositoryName.value)}`)
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

function formatDate(date: string | null): string {
  if (!date) return '暂无'
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchSnapshots()
})
</script>

<style scoped>
.repository-detail {
  padding: 20px;
}
</style>
