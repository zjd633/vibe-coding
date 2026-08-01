import { describe, expect, it } from 'vitest'
import { guardDecision } from '../src/router/guards'
import { router } from '../src/router'

describe('路由守卫', () => {
  it('未登录访问受保护页时保留目标地址', () => {
    expect(guardDecision({ requiresAuth: true }, null, '/problems/8?from=home')).toEqual({ name: 'login', query: { redirect: '/problems/8?from=home' } })
  })

  it('普通学生访问管理页时回到学生首页', () => {
    expect(guardDecision({ requiresAdmin: true }, { role: 'student' }, '/admin')).toEqual({ name: 'dashboard' })
  })

  it('管理员可以访问管理页', () => {
    expect(guardDecision({ requiresAdmin: true }, { role: 'admin' }, '/admin')).toBe(true)
  })

  it('标签管理路由仅允许管理员访问', () => {
    const route = router.getRoutes().find((item) => item.path === '/admin/tags')
    expect(route?.meta.requiresAdmin).toBe(true)
    expect(guardDecision(route?.meta ?? {}, { role: 'student' }, '/admin/tags')).toEqual({ name: 'dashboard' })
  })
})
