<template>
  <n-modal
    v-model:show="show"
    preset="card"
    :title="title"
    style="width: 480px;"
    :mask-closable="false"
    @after-leave="reset"
  >
    <n-alert type="warning" :show-icon="false" style="margin-bottom: 12px;">
      受保护快照通常由异常检测保留，强制删除后无法恢复。
    </n-alert>
    <p v-if="snapshotId" style="margin-bottom: 12px;">
      快照 ID：<code>{{ snapshotId }}</code>
    </p>
    <p v-if="repository" style="margin-bottom: 12px;">
      仓库：{{ repository }}
    </p>
    <p v-if="batchCount > 1" style="margin-bottom: 12px;">
      将强制删除 {{ batchCount }} 个受保护快照。
    </p>
    <n-checkbox v-model:checked="confirmed">
      我确认强制删除受保护快照，此操作不可恢复
    </n-checkbox>
    <template #footer>
      <n-space justify="end">
        <n-button @click="show = false">取消</n-button>
        <n-button
          type="error"
          :disabled="!confirmed"
          :loading="loading"
          @click="handleConfirm"
        >
          强制删除
        </n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { NModal, NAlert, NCheckbox, NButton, NSpace } from 'naive-ui'

const props = withDefaults(
  defineProps<{
    show: boolean
    snapshotId?: string
    repository?: string
    batchCount?: number
    loading?: boolean
  }>(),
  {
    batchCount: 1,
    loading: false
  }
)

const emit = defineEmits<{
  'update:show': [value: boolean]
  confirm: []
}>()

const confirmed = ref(false)

const title = computed(() =>
  props.batchCount > 1 ? '强制删除受保护快照' : '强制删除受保护快照'
)

const show = computed({
  get: () => props.show,
  set: (value: boolean) => emit('update:show', value)
})

function reset() {
  confirmed.value = false
}

function handleConfirm() {
  if (!confirmed.value) return
  emit('confirm')
}
</script>
