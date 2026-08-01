import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { User } from '../types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const ready = ref(false)
  const isAuthenticated = computed(() => user.value !== null)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function restoreSession() {
    try {
      user.value = (await api.get<User | null>('/auth/session')).data
    } catch {
      user.value = null
    } finally {
      ready.value = true
    }
  }

  async function login(payload: { username: string; password: string }) {
    user.value = (await api.post<User>('/auth/login', payload)).data
    ready.value = true
  }

  async function register(payload: { username: string; email: string; display_name: string; password: string }) {
    user.value = (await api.post<User>('/auth/register', payload)).data
    ready.value = true
  }

  async function logout() {
    try { await api.post('/auth/logout') }
    finally { user.value = null }
  }

  function clearSession() {
    user.value = null
  }

  function updateUser(next: User) {
    user.value = next
  }

  return { user, ready, isAuthenticated, isAdmin, restoreSession, login, register, logout, clearSession, updateUser }
})
