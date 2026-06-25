<template>
  <div class="repository-detail">
    <PageBreadcrumb :items="breadcrumbItems" />

    <PageActions>
      <n-space>
        <n-button text @click="$router.push('/repositories')">
          <template #icon>
            <n-icon><ArrowBackOutline /></n-icon>
          </template>
          返回列表
        </n-button>
        <n-button
          v-if="authStore.isAdmin"
          type="warning"
          @click="openRestoreModal"
        >
          恢复
        </n-button>
        <n-button
          v-if="authStore.isAdmin"
          type="success"
          :loading="backupLoading"
          @click="triggerBackup"
        >
          立即备份
        </n-button>
        <n-button type="primary" @click="fetchSnapshots">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          刷新
        </n-button>
      </n-space>
    </PageActions>

    <n-card>
      <n-spin :show="loading && !repoInfo">
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
              (保护 {{ repoInfo.protected_snapshots }})
            </span>
          </n-descriptions-item>
          <n-descriptions-item label="磁盘使用">
            {{ formatBytes(repoInfo.disk_usage) }}
          </n-descriptions-item>
          <n-descriptions-item label="最后备份">
            {{ formatDate(repoInfo.last_backup_time) }}
          </n-descriptions-item>
          <n-descriptions-item label="状态">
            <n-tag :type="repoInfo.status === 'warning' ? 'warning' : 'success'" size="small">
              {{ repoInfo.status === 'warning' ? '有异常' : '正常' }}
            </n-tag>
          </n-descriptions-item>
        </n-descriptions>
      </n-spin>

      <n-divider>快照列表</n-divider>

      <div class="filter-bar">
        <div class="filter-item">
          <span class="filter-item__label">{{ includeSize ? '显示大小' : '隐藏大小' }}</span>
          <n-switch v-model:value="includeSize" size="small" @update:value="fetchSnapshots" />
        </div>
        <template v-if="authStore.isAdmin">
          <n-button
            type="error"
            :disabled="selectedSnapshots.length === 0 || hasProtectedSelected || batchDeleting"
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
        </template>
      </div>

      <n-empty
        v-if="!loading && snapshots.length === 0"
        description="该仓库暂无快照"
        style="margin: 16px 0;"
      />

      <n-data-table
        v-else
        :columns="tableColumns"
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

      <n-divider v-if="repoInfo?.recent_logs?.length">最近相关日志</n-divider>
      <n-scrollbar v-if="repoInfo?.recent_logs?.length" style="max-height: 200px;">
        <pre class="log-preview">{{ repoInfo.recent_logs.join('\n') }}</pre>
      </n-scrollbar>
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
          <n-input
            v-model:value="restoreBundlePath"
            placeholder="/tmp/owner-repo.bundle"
            @blur="validateBundlePath"
          />
          <n-text v-if="bundlePathError" type="error" depth="3" style="font-size: 12px;">
            {{ bundlePathError }}
          </n-text>
        </n-form-item>

        <n-button type="primary" :loading="restoreLoading" @click="generateRestoreCommand">
          生成命令
        </n-button>

        <div v-if="restorePreview">
          <n-alert v-for="(w, i) in restorePreview.warnings" :key="'w-' + i" type="warning" style="margin-bottom: 8px;">
            {{ w }}
          </n-alert>
          <n-input type="textarea" :rows="8" readonly :value="restoreCommandText" />
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
import { useRoute, useRouter } from 'vue-router'
import {
  NCard, NButton, NDataTable, NIcon, NTag, NPopconfirm, NSpace,
  NDivider, NDescriptions, NDescriptionsItem, NText, NPagination,
  NModal, NAlert, NFormItem, NSelect, NRadioGroup, NRadio, NInput,
  NSwitch, NEmpty, NSpin, NScrollbar, useMessage, useDialog
} from 'naive-ui'
import { RefreshOutline, TrashOutline, ArrowBackOutline } from '@vicons/ionicons5'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import PageBreadcrumb from '@/components/PageBreadcrumb.vue'
import PageActions from '@/components/PageActions.vue'
import { getApiErrorMessage } from '@/utils/errorHandler'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const authStore = useAuthStore()

const repositoryName = computed(() => decodeURIComponent(route.params.name as string))
const breadcrumbItems = computed(() => [
  { label: '仓库管理', path: '/repositories' }
])

const loading = ref(false)
const backupLoading = ref(false)
const batchDeleting = ref(false)
const batchProgress = ref({ current: 0, total: 0 })
const snapshots = ref<any[]>([])
const repoInfo = ref<any>(null)
const selectedSnapshots = ref<string[]>([])
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const includeSize = ref(false)

const showRestoreModal = ref(false)
const restoreSnapshotId = ref<string | null>(null)
const restoreMode = ref('interactive')
const restoreNewRepoName = ref('')
const restoreBundlePath = ref('')
const bundlePathError = ref('')
const restoreLoading = ref(false)
const restorePreview = ref<any>(null)
const allSnapshotsForRestore = ref<any[]>([])

const restoreSnapshotOptions = computed(() =>
  allSnapshotsForRestore.value.map((s: any) => ({
    label: `${s.is_protected ? '[保护] ' : ''}${s.id} (${formatDate(s.created_at)})`,
    value: s.id
  }))
)

const restoreCommandText = computed(() => {
  if (!restorePreview.value) return ''
  return [
    ...(restorePreview.value.notes || []),
    '',
    ...(restorePreview.value.commands || []),
  ].join('\n')
})

const hasProtectedSelected = computed(() =>
  snapshots.value.some((s: any) =>
    selectedSnapshots.value.includes(s.id) && s.is_protected
  )
)

const tableColumns = computed(() => {
  const cols: any[] = []
  if (authStore.isAdmin) {
    cols.push({
      type: 'selection' as const,
      disabled: (row: any) => row.is_protected
    })
  }
  cols.push({ title: '快照 ID', key: 'id', ellipsis: { tooltip: true } })
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
        if (row.is_protected) {
          return h(NTag, { type: 'warning', size: 'small' }, { default: () => '已保护' })
        }
        return h(NTag, { type: 'success', size: 'small' }, { default: () => '正常' })
      }
    }
  )
  if (authStore.isAdmin) {
    cols.push({
      title: '操作',
      key: 'actions',
      render: (row: any) => {
        if (row.is_protected) {
          return h(NButton, { size: 'small', type: 'error', disabled: true }, { default: () => '已保护' })
        }
        return h(
          NPopconfirm,
          { onPositiveClick: () => handleDelete(row.id) },
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

function handlePageChange() {
  selectedSnapshots.value = []
  fetchSnapshots()
}

function handlePageSizeChange() {
  currentPage.value = 1
  selectedSnapshots.value = []
  fetchSnapshots()
}

function handleCheck(keys: Array<string | number>) {
  selectedSnapshots.value = keys as string[]
}

async function fetchSnapshots() {
  loading.value = true
  try {
    const countResponse = await api.get('/snapshots/count', {
      params: { repository: repositoryName.value }
    })
    totalCount.value = countResponse.data.count

    const response = await api.get(`/repositories/${encodeURIComponent(repositoryName.value)}`, {
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        include_size: includeSize.value
      }
    })
    repoInfo.value = response.data
    snapshots.value = response.data.snapshots || []
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    loading.value = false
  }
}

async function triggerBackup() {
  backupLoading.value = true
  try {
    const response = await api.post(
      `/repositories/${encodeURIComponent(repositoryName.value)}/backup`
    )
    message.success(response.data.message)
    router.push('/tasks')
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    backupLoading.value = false
  }
}

async function handleDelete(id: string) {
  try {
    await api.delete(`/snapshots/${id}?repository=${encodeURIComponent(repositoryName.value)}`)
    message.success('删除成功')
    await fetchSnapshots()
  } catch (error) {
    message.error(getApiErrorMessage(error))
  }
}

async function handleBatchDelete() {
  if (selectedSnapshots.value.length === 0) return

  dialog.warning({
    title: '批量删除确认',
    content: `确定要删除选中的 ${selectedSnapshots.value.length} 个快照吗？此操作不可恢复！`,
    positiveText: '确定删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      batchDeleting.value = true
      batchProgress.value = { current: 0, total: selectedSnapshots.value.length }
      let successCount = 0
      let failCount = 0

      for (const snapshotId of selectedSnapshots.value) {
        try {
          await api.delete(`/snapshots/${snapshotId}?repository=${encodeURIComponent(repositoryName.value)}`)
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

function validateBundlePath() {
  const path = restoreBundlePath.value.trim()
  if (!path) {
    bundlePathError.value = ''
    return
  }
  if (!path.endsWith('.bundle')) {
    bundlePathError.value = 'Bundle 路径应以 .bundle 结尾'
    return
  }
  if (path.includes(' ')) {
    bundlePathError.value = '路径不能包含空格'
    return
  }
  bundlePathError.value = ''
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
    message.error(getApiErrorMessage(error))
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
  if (restoreMode.value === 'bundle') {
    validateBundlePath()
    if (bundlePathError.value) {
      message.warning(bundlePathError.value)
      return
    }
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
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    restoreLoading.value = false
  }
}

async function copyRestoreCommand() {
  try {
    await navigator.clipboard.writeText(restoreCommandText.value)
    message.success('命令已复制到剪贴板')
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
  padding: 0;
}

.log-preview {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  padding: 8px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 4px;
}
</style>
