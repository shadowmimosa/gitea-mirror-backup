<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>Gitea Mirror Backup</h1>
        <p>Web 管理界面</p>
      </div>

      <n-form
        ref="formRef"
        :model="formValue"
        :rules="rules"
        size="large"
        @submit.prevent="handleLogin"
      >
        <n-form-item path="username" label="用户名">
          <n-input
            v-model:value="formValue.username"
            placeholder="请输入用户名"
            @keydown.enter="handleLogin"
          />
        </n-form-item>

        <n-form-item path="password" label="密码">
          <n-input
            v-model:value="formValue.password"
            type="password"
            show-password-on="click"
            placeholder="请输入密码"
            @keydown.enter="handleLogin"
          />
        </n-form-item>

        <n-button
          type="primary"
          block
          size="large"
          :loading="loading"
          @click="handleLogin"
        >
          登录
        </n-button>
      </n-form>

      <div class="login-footer">
        <p>默认账号: admin / admin123</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage, NForm, NFormItem, NInput, NButton } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const authStore = useAuthStore()

const formRef = ref()
const loading = ref(false)
const formValue = ref({
  username: '',
  password: ''
})

const rules = {
  username: {
    required: true,
    message: '请输入用户名',
    trigger: 'blur'
  },
  password: {
    required: true,
    message: '请输入密码',
    trigger: 'blur'
  }
}

async function handleLogin() {
  try {
    await formRef.value?.validate()
    loading.value = true

    const success = await authStore.login(formValue.value.username, formValue.value.password)

    if (success) {
      message.success('登录成功')
      const redirect = route.query.redirect as string || '/'
      router.push(redirect)
    } else {
      message.error('用户名或密码错误')
    }
  } catch (error) {
    console.error('Login error:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  position: relative;
  overflow: hidden;
}

.login-container::before {
  content: '';
  position: absolute;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(94, 114, 228, 0.1) 0%, transparent 70%);
  border-radius: 50%;
  top: -250px;
  right: -250px;
  animation: float 6s ease-in-out infinite;
}

.login-container::after {
  content: '';
  position: absolute;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(236, 64, 122, 0.1) 0%, transparent 70%);
  border-radius: 50%;
  bottom: -200px;
  left: -200px;
  animation: float 8s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-20px) scale(1.05);
  }
}

.login-box {
  width: 100%;
  max-width: 420px;
  padding: 48px;
  background: rgba(30, 30, 46, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4),
              0 0 0 1px rgba(255, 255, 255, 0.05);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.login-header h1 {
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 12px;
  letter-spacing: -0.5px;
}

.login-header p {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
}

.login-footer {
  margin-top: 32px;
  text-align: center;
  padding-top: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.login-footer p {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 500;
  background: rgba(255, 255, 255, 0.03);
  padding: 12px 20px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}
</style>

