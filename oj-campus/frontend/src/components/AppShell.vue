<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { BookOpenCheck, Gauge, LogIn, LogOut, Menu, Medal, Settings, ShieldCheck, Tags, UserRoundPlus, X } from '@lucide/vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const open = ref(false)
const studentLinks = [
  { to: '/dashboard', label: '学习首页', icon: Gauge, auth: true },
  { to: '/problems', label: '题目', icon: BookOpenCheck },
  { to: '/submissions', label: '我的提交', icon: Settings, auth: true },
  { to: '/submissions/public', label: '全站提交', icon: Settings },
  { to: '/leaderboard', label: '排行榜', icon: Medal },
]
const links = computed(() => studentLinks.filter((item) => !item.auth || auth.isAuthenticated))

async function logout() {
  try {
    await auth.logout()
  } catch {
    // Local session state is cleared by the store even when the server is unreachable.
  } finally {
    open.value = false
    await router.replace('/login')
  }
}
</script>

<template>
  <header class="site-header">
    <div class="nav-wrap">
      <RouterLink class="brand" to="/" aria-label="OJ Campus 首页">
        <span class="brand-mark" aria-hidden="true">OJ</span><span>OJ Campus</span>
      </RouterLink>
      <button class="icon-button nav-toggle" type="button" :aria-expanded="open" aria-label="打开导航菜单" @click="open = !open">
        <X v-if="open" :size="24" /><Menu v-else :size="24" />
      </button>
      <nav :class="['main-nav', { open }]" aria-label="主导航" @click="open = false">
        <RouterLink v-for="item in links" :key="item.to" :to="item.to"><component :is="item.icon" :size="18" />{{ item.label }}</RouterLink>
        <RouterLink v-if="auth.isAdmin" to="/admin"><ShieldCheck :size="18" />管理台</RouterLink>
        <RouterLink v-if="auth.isAdmin" to="/admin/tags"><Tags :size="18" />标签管理</RouterLink>
      </nav>
      <div class="account-actions">
        <template v-if="auth.isAuthenticated">
          <RouterLink class="user-chip" to="/settings"><Settings :size="18" />{{ auth.user?.display_name }}</RouterLink>
          <button class="icon-button" type="button" aria-label="退出登录" @click="logout"><LogOut :size="20" /></button>
        </template>
        <template v-else>
          <RouterLink class="button button-ghost" to="/login"><LogIn :size="18" />登录</RouterLink>
          <RouterLink class="button button-primary" to="/register"><UserRoundPlus :size="18" />注册</RouterLink>
        </template>
      </div>
    </div>
  </header>
  <main id="main-content" class="page-shell">
    <RouterView />
  </main>
</template>
