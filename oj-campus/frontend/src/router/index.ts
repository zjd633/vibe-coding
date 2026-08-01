import { nextTick } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { makeGuard } from './guards'

export const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', name: 'login', component: () => import('../views/LoginView.vue'), meta: { guestOnly: true, title: '登录' } },
    { path: '/register', name: 'register', component: () => import('../views/RegisterView.vue'), meta: { guestOnly: true, title: '注册' } },
    { path: '/dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue'), meta: { requiresAuth: true, title: '学习首页' } },
    { path: '/problems', name: 'problems', component: () => import('../views/ProblemsView.vue'), meta: { title: '题目列表' } },
    { path: '/problems/:id', name: 'problem-detail', component: () => import('../views/ProblemDetailView.vue'), meta: { requiresAuth: true, title: '题目详情' } },
    { path: '/submissions', name: 'my-submissions', component: () => import('../views/SubmissionsView.vue'), meta: { requiresAuth: true, title: '我的提交' } },
    { path: '/submissions/public', name: 'public-submissions', component: () => import('../views/PublicSubmissionsView.vue'), meta: { title: '全站提交' } },
    { path: '/submissions/:id', name: 'submission-detail', component: () => import('../views/SubmissionDetailView.vue'), meta: { requiresAuth: true, title: '提交详情' } },
    { path: '/leaderboard', name: 'leaderboard', component: () => import('../views/LeaderboardView.vue'), meta: { title: '排行榜' } },
    { path: '/settings', name: 'settings', component: () => import('../views/SettingsView.vue'), meta: { requiresAuth: true, title: '个人设置' } },
    { path: '/admin', name: 'admin-dashboard', component: () => import('../views/admin/AdminDashboardView.vue'), meta: { requiresAdmin: true, title: '管理概览' } },
    { path: '/admin/problems', name: 'admin-problems', component: () => import('../views/admin/AdminProblemsView.vue'), meta: { requiresAdmin: true, title: '题目管理' } },
    { path: '/admin/problems/new', name: 'admin-problem-new', component: () => import('../views/admin/AdminProblemEditorView.vue'), meta: { requiresAdmin: true, title: '新建题目' } },
    { path: '/admin/problems/:id/edit', name: 'admin-problem-edit', component: () => import('../views/admin/AdminProblemEditorView.vue'), meta: { requiresAdmin: true, title: '编辑题目' } },
    { path: '/admin/users', name: 'admin-users', component: () => import('../views/admin/AdminUsersView.vue'), meta: { requiresAdmin: true, title: '用户管理' } },
    { path: '/admin/submissions', name: 'admin-submissions', component: () => import('../views/admin/AdminSubmissionsView.vue'), meta: { requiresAdmin: true, title: '提交管理' } },
    { path: '/admin/tags', name: 'admin-tags', component: () => import('../views/admin/AdminTagsView.vue'), meta: { requiresAdmin: true, title: '标签管理' } },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('../views/NotFoundView.vue'), meta: { title: '页面不存在' } },
  ],
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()
  if (!auth.ready) await auth.restoreSession()
  makeGuard(() => auth.user)(to, from, next)
})

router.afterEach(async (to) => {
  document.title = `${String(to.meta.title ?? '校园在线评测')} · OJ Campus`
  await nextTick()
  document.querySelector<HTMLElement>('main h1')?.focus()
})
