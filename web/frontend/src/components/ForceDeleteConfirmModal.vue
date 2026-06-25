<template>
  <n-modal
    v-model:show="showProxy"
    preset="card"
    :title="title"
    style="width: 480px;"
  >
    <n-space vertical>
      <n-alert type="warning" :show-icon="false">
        {{ description }}
      </n-alert>
      <n-checkbox v-model:checked="confirmed">
        我确认要强制删除此受保护资源
      </n-checkbox>
    </n-space>
    <template #footer>
      <n-space justify="end">
        <n-button @click="showProxy = false">取消</n-button>
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
import { ref, watch, computed } from 'vue'
import { NModal, NAlert, NCheckbox, NButton, NSpace } from 'naive-ui'

const props = defineProps<{
  show: boolean
  title: string
  description: string
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  confirm: []
}>()

const confirmed = ref(false)

const showProxy = computed({
  get: () => props.show,
  set: (value: boolean) => emit('update:show', value)
})

watch(
  () => props.show,
  (visible) => {
    if (visible) {
      confirmed.value = false
    }
  }
)

function handleConfirm() {
  emit('confirm')
}
</script>
