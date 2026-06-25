<script setup lang="ts">
import { onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { setMessageHandler } from '@/utils/messageBus'

const message = useMessage()

onMounted(() => {
  setMessageHandler((msg, type) => {
    if (type === 'warning') {
      message.warning(msg)
    } else if (type === 'info') {
      message.info(msg)
    } else {
      message.error(msg)
    }
  })
})
</script>
