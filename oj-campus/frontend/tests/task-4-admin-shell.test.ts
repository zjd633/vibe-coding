import { fireEvent, render, screen, waitFor } from '@testing-library/vue'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from '../src/api/client'
import AppShell from '../src/components/AppShell.vue'
import { useAuthStore } from '../src/stores/auth'
import AdminDashboardView from '../src/views/admin/AdminDashboardView.vue'

const admin = {
  id: 1,
  username: 'demo_admin',
  display_name: '演示管理员',
  email: 'admin@oj-campus.local',
  role: 'admin' as const,
  is_active: true,
  created_at: '2026-01-01',
}

afterEach(() => vi.restoreAllMocks())

describe('管理入口与安全登出', () => {
  it('管理员可从主导航进入标签管理', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    useAuthStore().updateUser(admin)
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: { template: '<div />' } },
        { path: '/admin/tags', component: { template: '<h1>标签管理</h1>' } },
        { path: '/:pathMatch(.*)*', component: { template: '<div />' } },
      ],
    })
    await router.push('/')
    await router.isReady()
    render(AppShell, { global: { plugins: [pinia, router] } })
    expect(screen.getByRole('link', { name: /标签管理/ }).getAttribute('href')).toBe('/admin/tags')
  })

  it('管理概览提供标签管理入口', async () => {
    vi.spyOn(api, 'get').mockResolvedValue({ data: { users: 2, problems: 9, submissions: 3 } })
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/admin', component: AdminDashboardView },
        { path: '/admin/tags', component: { template: '<h1>标签管理</h1>' } },
        { path: '/:pathMatch(.*)*', component: { template: '<div />' } },
      ],
    })
    await router.push('/admin')
    await router.isReady()
    render(AdminDashboardView, { global: { plugins: [router] } })
    expect((await screen.findByRole('link', { name: /标签管理/ })).getAttribute('href')).toBe('/admin/tags')
  })

  it('注销请求断网时仍清空认证、离开受保护内容并前往登录页', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const auth = useAuthStore()
    auth.updateUser(admin)
    vi.spyOn(api, 'post').mockRejectedValue(new Error('offline'))
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/admin', component: { template: '<h1>受保护管理内容</h1>' } },
        { path: '/login', component: { template: '<h1>登录</h1>' } },
        { path: '/:pathMatch(.*)*', component: { template: '<div />' } },
      ],
    })
    await router.push('/admin')
    await router.isReady()
    render(AppShell, { global: { plugins: [pinia, router] } })
    expect(screen.getByRole('heading', { name: '受保护管理内容' })).toBeTruthy()
    await fireEvent.click(screen.getByRole('button', { name: '退出登录' }))
    await waitFor(() => expect(router.currentRoute.value.path).toBe('/login'))
    expect(auth.user).toBeNull()
    expect(screen.queryByRole('heading', { name: '受保护管理内容' })).toBeNull()
  })
})
