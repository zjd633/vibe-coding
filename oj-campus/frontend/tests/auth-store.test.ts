import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '../src/api/client'
import { useAuthStore } from '../src/stores/auth'

vi.mock('../src/api/client', () => ({
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}))

describe('认证状态', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('初始化时从真实会话接口恢复用户', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { id: 7, username: 'lin', display_name: '林同学', email: 'lin@example.com', role: 'student', is_active: true, created_at: '2026-01-01' } })
    const store = useAuthStore()
    await store.restoreSession()
    expect(api.get).toHaveBeenCalledWith('/auth/session')
    expect(store.user?.display_name).toBe('林同学')
    expect(store.ready).toBe(true)
  })

  it('匿名会话探针返回 null 时清空用户并完成初始化', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: null })
    const store = useAuthStore()
    await store.restoreSession()
    expect(store.user).toBeNull()
    expect(store.ready).toBe(true)
  })

  it('会话探针网络失败时仍安全清空用户', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('offline'))
    const store = useAuthStore()
    await store.restoreSession()
    expect(store.user).toBeNull()
    expect(store.ready).toBe(true)
  })

  it('登录成功后保存服务端返回用户', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { id: 1, username: 'alice', display_name: 'Alice', email: 'a@example.com', role: 'admin', is_active: true, created_at: '2026-01-01' } })
    const store = useAuthStore()
    await store.login({ username: 'alice', password: 'secret123' })
    expect(api.post).toHaveBeenCalledWith('/auth/login', { username: 'alice', password: 'secret123' })
    expect(store.isAdmin).toBe(true)
  })
})
