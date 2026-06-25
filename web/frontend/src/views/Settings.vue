<template>
  <div class="settings">
    <n-card>
      <n-spin :show="loading">
        <n-tabs type="line" animated>
          <n-tab-pane name="basic" tab="基础信息">
            <n-form label-placement="left" label-width="120">
              <n-form-item label="应用名称">
                <n-input :value="appInfo.name" disabled />
              </n-form-item>
              <n-form-item label="版本">
                <n-input :value="appInfo.version" disabled />
              </n-form-item>
            </n-form>
          </n-tab-pane>

          <n-tab-pane name="password" tab="修改密码">
            <n-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="100">
              <n-form-item label="当前密码" path="password">
                <n-input v-model:value="passwordForm.password" type="password" show-password-on="click" />
              </n-form-item>
              <n-form-item label="新密码" path="new_password">
                <n-input v-model:value="passwordForm.new_password" type="password" show-password-on="click" />
              </n-form-item>
              <n-form-item>
                <n-button type="primary" :loading="passwordLoading" @click="changePassword">
                  保存密码
                </n-button>
              </n-form-item>
            </n-form>
          </n-tab-pane>

          <n-tab-pane v-if="authStore.isAdmin" name="users" tab="用户管理">
            <n-space vertical>
              <n-button type="primary" @click="showAddUser = true">添加用户</n-button>
              <n-data-table :columns="userColumns" :data="users" :loading="usersLoading" />
            </n-space>
          </n-tab-pane>

          <n-tab-pane v-if="authStore.isAdmin" name="backup-scope" tab="备份范围">
            <n-space vertical>
              <n-alert type="info" :show-icon="false">
                组织列表为空时备份全部组织；修改后于下次全量备份任务生效。单仓「立即备份」不受此限制。
              </n-alert>
              <n-alert
                v-for="(warning, index) in backupScope.warnings"
                :key="index"
                type="warning"
                :show-icon="false"
              >
                {{ warning }}
              </n-alert>
              <n-form label-placement="left" label-width="140">
                <n-form-item label="备份组织">
                  <n-select
                    v-model:value="backupScope.organizations"
                    :options="organizationOptions"
                    multiple
                    filterable
                    tag
                    placeholder="留空表示备份全部组织"
                    style="width: 100%; max-width: 520px;"
                  />
                </n-form-item>
                <n-form-item label="仅备份镜像仓">
                  <n-switch v-model:value="backupScope.check_mirror_only" />
                </n-form-item>
                <n-form-item v-if="backupScope.effective_organizations?.length" label="当前生效组织">
                  <n-text depth="3">{{ backupScope.effective_organizations.join(', ') }}</n-text>
                </n-form-item>
                <n-form-item label="当前生效镜像过滤">
                  <n-text depth="3">
                    {{ backupScope.effective_check_mirror_only ? '是' : '否' }}
                  </n-text>
                </n-form-item>
                <n-form-item>
                  <n-button type="primary" :loading="backupScopeSaving" @click="saveBackupScope">
                    保存备份范围
                  </n-button>
                </n-form-item>
              </n-form>
            </n-space>
          </n-tab-pane>

          <n-tab-pane v-if="authStore.isAdmin" name="config" tab="备份配置">
            <n-space vertical>
              <n-alert type="info" :show-icon="false">只读展示当前 config.yaml，修改后需重启服务生效。</n-alert>
              <n-input
                v-model:value="configContent"
                type="textarea"
                :rows="16"
                readonly
                placeholder="加载中..."
              />
              <n-button :loading="validateLoading" @click="validateConfig">校验配置</n-button>
              <n-alert v-if="validateResult" :type="validateResult.valid ? 'success' : 'error'">
                {{ validateResult.valid ? '配置校验通过' : validateResult.errors.join('\n') }}
              </n-alert>
            </n-space>
          </n-tab-pane>

          <n-tab-pane v-if="authStore.isAdmin" name="notifications" tab="通知测试">
            <n-space vertical>
              <n-alert type="info" :show-icon="false">向已启用的通知渠道发送测试消息。</n-alert>
              <n-space>
                <n-button :loading="notifyLoading === 'email'" @click="testNotification('email')">测试邮件</n-button>
                <n-button :loading="notifyLoading === 'webhook'" @click="testNotification('webhook')">测试 Webhook</n-button>
                <n-button :loading="notifyLoading === 'wechat'" @click="testNotification('wechat')">测试企业微信</n-button>
                <n-button :loading="notifyLoading === 'dingtalk'" @click="testNotification('dingtalk')">测试钉钉</n-button>
              </n-space>
            </n-space>
          </n-tab-pane>

          <n-tab-pane name="about" tab="关于">
            <n-alert type="info">
              <strong>{{ appInfo.name }}</strong>
              <p>版本: {{ appInfo.version }}</p>
              <p>基于 FastAPI + Vue 3 + Naive UI 构建</p>
            </n-alert>
          </n-tab-pane>
        </n-tabs>
      </n-spin>
    </n-card>

    <n-modal v-model:show="showAddUser" preset="card" title="添加用户" style="width: 480px;">
      <n-form ref="addUserFormRef" :model="addUserForm" :rules="addUserRules" label-width="80">
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="addUserForm.username" />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="addUserForm.email" />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input v-model:value="addUserForm.password" type="password" show-password-on="click" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddUser = false">取消</n-button>
          <n-button type="primary" :loading="addUserLoading" @click="addUser">创建</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted, computed } from 'vue'
import {
  NCard, NTabs, NTabPane, NForm, NFormItem, NInput, NSpace, NAlert,
  NButton, NDataTable, NTag, NSpin, NModal, useMessage, NSelect, NSwitch, NText
} from 'naive-ui'
import api from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { getApiErrorMessage } from '@/utils/errorHandler'

const message = useMessage()
const authStore = useAuthStore()

const loading = ref(true)
const appInfo = ref({ name: 'Gitea Mirror Backup Web', version: '加载中...' })

const passwordFormRef = ref()
const passwordLoading = ref(false)
const passwordForm = ref({ password: '', new_password: '' })
const passwordRules = {
  password: { required: true, message: '请输入当前密码', trigger: 'blur' },
  new_password: { required: true, message: '请输入新密码', trigger: 'blur', min: 6 }
}

const users = ref<any[]>([])
const usersLoading = ref(false)
const showAddUser = ref(false)
const addUserLoading = ref(false)
const addUserFormRef = ref()
const addUserForm = ref({ username: '', email: '', password: '' })
const addUserRules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: { required: true, message: '请输入密码', trigger: 'blur', min: 6 }
}

const configContent = ref('')
const validateLoading = ref(false)
const validateResult = ref<{ valid: boolean; errors: string[] } | null>(null)
const notifyLoading = ref('')
const backupScope = ref({
  organizations: [] as string[],
  check_mirror_only: false,
  available_organizations: [] as string[],
  effective_organizations: [] as string[],
  effective_check_mirror_only: false,
  warnings: [] as string[]
})
const backupScopeSaving = ref(false)

const organizationOptions = computed(() =>
  backupScope.value.available_organizations.map((org) => ({
    label: org,
    value: org
  }))
)

const userColumns = [
  { title: '用户名', key: 'username' },
  { title: '邮箱', key: 'email', render: (row: any) => row.email || '-' },
  {
    title: '角色',
    key: 'is_admin',
    render: (row: any) => h(NTag, { type: row.is_admin ? 'warning' : 'default', size: 'small' }, {
      default: () => row.is_admin ? '管理员' : '只读'
    })
  },
  {
    title: '状态',
    key: 'is_active',
    render: (row: any) => h(NTag, { type: row.is_active ? 'success' : 'error', size: 'small' }, {
      default: () => row.is_active ? '启用' : '禁用'
    })
  },
  {
    title: '操作',
    key: 'actions',
    render: (row: any) => {
      if (row.id === authStore.user?.id) return '-'
      return h(
        NButton,
        { size: 'small', onClick: () => toggleUserActive(row) },
        { default: () => row.is_active ? '禁用' : '启用' }
      )
    }
  }
]

async function fetchAppInfo() {
  try {
    const response = await api.get('/system/info')
    appInfo.value = response.data
  } catch (error) {
    message.error(getApiErrorMessage(error))
  }
}

async function fetchUsers() {
  if (!authStore.isAdmin) return
  usersLoading.value = true
  try {
    const response = await api.get('/auth/users')
    users.value = response.data
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    usersLoading.value = false
  }
}

async function fetchBackupScope() {
  if (!authStore.isAdmin) return
  try {
    const response = await api.get('/system/backup-scope')
    backupScope.value = response.data
  } catch (error) {
    message.error(getApiErrorMessage(error))
  }
}

async function saveBackupScope() {
  backupScopeSaving.value = true
  try {
    const response = await api.put('/system/backup-scope', {
      organizations: backupScope.value.organizations,
      check_mirror_only: backupScope.value.check_mirror_only
    })
    backupScope.value = response.data
    message.success('备份范围已保存，下次全量备份生效')
    await fetchConfig()
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    backupScopeSaving.value = false
  }
}

async function fetchConfig() {
  if (!authStore.isAdmin) return
  try {
    const response = await api.get('/system/config')
    configContent.value = response.data.content
  } catch (error) {
    message.error(getApiErrorMessage(error))
  }
}

async function changePassword() {
  try {
    await passwordFormRef.value?.validate()
    passwordLoading.value = true
    await api.post('/auth/change-password', passwordForm.value)
    message.success('密码修改成功')
    passwordForm.value = { password: '', new_password: '' }
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    passwordLoading.value = false
  }
}

async function addUser() {
  try {
    await addUserFormRef.value?.validate()
    addUserLoading.value = true
    await api.post('/auth/register', {
      username: addUserForm.value.username,
      email: addUserForm.value.email || undefined,
      password: addUserForm.value.password
    })
    message.success('用户创建成功')
    showAddUser.value = false
    addUserForm.value = { username: '', email: '', password: '' }
    await fetchUsers()
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    addUserLoading.value = false
  }
}

async function toggleUserActive(user: any) {
  try {
    await api.put(`/auth/users/${user.id}`, { is_active: !user.is_active })
    message.success('用户状态已更新')
    await fetchUsers()
  } catch (error) {
    message.error(getApiErrorMessage(error))
  }
}

async function validateConfig() {
  validateLoading.value = true
  validateResult.value = null
  try {
    const response = await api.post('/system/config/validate')
    validateResult.value = response.data
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    validateLoading.value = false
  }
}

async function testNotification(channel: string) {
  notifyLoading.value = channel
  try {
    const response = await api.post('/system/notifications/test', { channel })
    if (response.data.success) {
      message.success(response.data.message)
    } else {
      message.warning(response.data.message)
    }
  } catch (error) {
    message.error(getApiErrorMessage(error))
  } finally {
    notifyLoading.value = ''
  }
}

onMounted(async () => {
  loading.value = true
  await fetchAppInfo()
  await Promise.all([fetchUsers(), fetchConfig(), fetchBackupScope()])
  loading.value = false
})
</script>
