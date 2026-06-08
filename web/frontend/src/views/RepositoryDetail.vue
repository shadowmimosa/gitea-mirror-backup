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
        <n-space>
          <n-button type="warning" @click="openRestoreModal">
            恢复
          </n-button>
          <n-button type="primary" @click="fetchSnapshots">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          刷新
          </n-button>
        </n-space>
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
        :pagination="false"
        :row-key="(row: any) => row.id"
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

    <n-modal
      v-model:show="showRestoreModal"
      preset="card"
      title="恢复向导"
      style="width: 640px;"
    >
      <n-space vertical size="large">
        <n-alert type="info" :show-icon="false">
          生成可在宿主机执行的恢复命令，Web 不会自动运行 docker 操作。
        </n-alert>

        <n-form-item label="选择快照">
          <n-select
            v-model:value="restoreSnapshotId"
            :options="restoreSnapshotOptions"
            placeholder="选择要恢复的快照"
          />
        </n-form-item>

        <n-form-item label="恢复方式">
          <n-radio-group v-model:value="restoreMode">
            <n-space vertical>
              <n-radio value="interactive">交互式 restore.sh（推荐）</n-radio>
              <n-radio value="inplace">恢复到原位置（覆盖原仓库）</n-radio>
              <n-radio value="export_new">导出为新仓库</n-radio>
              <n-radio value="bundle">导出为 Git Bundle</n-radio>
            </n-space>
          </n-radio-group>
        </n-form-item>

        <n-form-item v-if="restoreMode === 'export_new'" label="新仓库名称">
          <n-input v-model:value="restoreNewRepoName" placeholder="例如 my-repo-restored" />
        </n-form-item>

        <n-form-item v-if="restoreMode === 'bundle'" label="Bundle 路径">
          <n-input v-model:value="restoreBundlePath" placeholder="/tmp/owner-repo.bundle" />
        </n-form-item>

        <n-button type="primary" :loading="restoreLoading" @click="generateRestoreCommand">
          生成命令
        </n-button>

        <div v-if="restorePreview">
          <n-alert v-for="(w, i) in restorePreview.warnings" :key="'w-' + i" type="warning" style="margin-bottom: 8px;">
            {{ w }}
          </n-alert>
          <n-input
            type="textarea"
            :rows="8"
            readonly
            :value="restoreCommandText"
          />
          <n-space style="margin-top: 8px;">
            <n-button @click="copyRestoreCommand">复制命令</n-button>
          </n-space>
          <n-text v-if="restorePreview.archives?.length" depth="3" style="display: block; margin-top: 12px; font-size: 12px;">
            归档备选：{{ restorePreview.archives.join('；') }}
          </n-text>
        </div>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  NCard, NButton, NDataTable, NIcon, NTag, NPopconfirm, NSpace, 
  NDivider, NDescriptions, NDescriptionsItem, NText, NPagination,
  NModal, NAlert, NFormItem, NSelect, NRadioGroup, NRadio, NInput,
  useMessage, useDialog 
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
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

const showRestoreModal = ref(false)
const restoreSnapshotId = ref<string | null>(null)
const restoreMode = ref('interactive')
const restoreNewRepoName = ref('')
const restoreBundlePath = ref('')
const restoreLoading = ref(false)
const restorePreview = ref<any>(null)
const allSnapshotsForRestore = ref<any[]>([])

const restoreSnapshotOptions = computed(() =>
  allSnapshotsForRestore.value.map((s: any) => ({
    label: `${s.is_protected ? '🔒 ' : ''}${s.id} (${formatDate(s.created_at)})`,
    value: s.id
  }))
)

const restoreCommandText = computed(() => {
  if (!restorePreview.value) return ''
  const lines = [
    ...(restorePreview.value.notes || []),
    '',
    ...(restorePreview.value.commands || []),
  ]
  return lines.join('\n')
})

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
    // 先获取快照总数
    const countResponse = await api.get('/snapshots/count', {
      params: {
        repository: repositoryName.value
      }
    })
    totalCount.value = countResponse.data.count
    
    // 获取仓库详情和当前页快照
    const response = await api.get(`/repositories/${encodeURIComponent(repositoryName.value)}`, {
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        include_size: true
      }
    })
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

async function openRestoreModal() {
  showRestoreModal.value = true
  restorePreview.value = null
  try {
    const response = await api.get('/snapshots', {
      params: {
        repository: repositoryName.value,
        page: 1,
        page_size: 200,
        include_size: false
      }
    })
    allSnapshotsForRestore.value = response.data || []
    const preferred = allSnapshotsForRestore.value.find((s: any) => s.is_protected)
      || allSnapshotsForRestore.value[0]
    restoreSnapshotId.value = preferred?.id || null
  } catch (error) {
    message.error('加载快照列表失败')
    console.error(error)
  }
}

async function generateRestoreCommand() {
  if (!restoreSnapshotId.value) {
    message.warning('请选择快照')
    return
  }
  if (restoreMode.value === 'export_new' && !restoreNewRepoName.value.trim()) {
    message.warning('请输入新仓库名称')
    return
  }

  restoreLoading.value = true
  try {
    const response = await api.post('/restore/preview', {
      repository: repositoryName.value,
      snapshot_id: restoreSnapshotId.value,
      mode: restoreMode.value,
      new_repo_name: restoreNewRepoName.value || undefined,
      bundle_path: restoreBundlePath.value || undefined
    })
    restorePreview.value = response.data
  } catch (error: any) {
    message.error(error.response?.data?.detail || '生成命令失败')
    console.error(error)
  } finally {
    restoreLoading.value = false
  }
}

async function copyRestoreCommand() {
  try {
    await navigator.clipboard.writeText(restoreCommandText.value)
    message.success('已复制到剪贴板')
  } catch {
    message.error('复制失败，请手动选择复制')
  }
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
