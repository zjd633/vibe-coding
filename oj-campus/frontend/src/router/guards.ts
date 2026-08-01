import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import type { Role, User } from '../types'

type GuardMeta = { requiresAuth?: boolean; requiresAdmin?: boolean; guestOnly?: boolean }
type GuardUser = Pick<User, 'role'> | { role: Role } | null

export function guardDecision(meta: GuardMeta, user: GuardUser, fullPath: string) {
  if ((meta.requiresAuth || meta.requiresAdmin) && !user) return { name: 'login', query: { redirect: fullPath } }
  if (meta.requiresAdmin && user?.role !== 'admin') return { name: 'dashboard' }
  if (meta.guestOnly && user) return { name: user.role === 'admin' ? 'admin-dashboard' : 'dashboard' }
  return true
}

export function makeGuard(getUser: () => GuardUser) {
  return (to: RouteLocationNormalized, _from: RouteLocationNormalized, next: NavigationGuardNext) => {
    const decision = guardDecision(to.meta, getUser(), to.fullPath)
    if (decision === true) next()
    else next(decision)
  }
}
