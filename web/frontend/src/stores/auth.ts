import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/client'

export interface User {
  id: number
  username: string
  email: string | null
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)
  const authReady = ref(false)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)

  async function login(username: string, password: string) {
    try {
      const response = await api.post('/auth/login', { username, password })
      token.value = response.data.access_token
      localStorage.setItem('token', token.value!)
      await fetchUser()
      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    }
  }

  async function fetchUser() {
    if (!token.value) {
      authReady.value = true
      return
    }

    try {
      const response = await api.get('/auth/me')
      user.value = response.data
    } catch (error) {
      console.error('Fetch user failed:', error)
      logout()
    } finally {
      authReady.value = true
    }
  }

  async function initAuth() {
    authReady.value = false
    await fetchUser()
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    authReady.value = true
  }

  return {
    token,
    user,
    isAuthenticated,
    isAdmin,
    authReady,
    login,
    fetchUser,
    initAuth,
    logout
  }
})
