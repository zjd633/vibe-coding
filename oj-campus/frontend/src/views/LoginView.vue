<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LogIn } from '@lucide/vue'
import { readableError } from '../api/client'
import { useAuthStore } from '../stores/auth'

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const error = ref('')
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

async function submit() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(form)
    const redirect = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/') ? route.query.redirect : (auth.isAdmin ? '/admin' : '/dashboard')
    await router.replace(redirect)
  } catch (cause) {
    error.value = readableError(cause, '登录失败，请检查用户名和密码')
  } finally { loading.value = false }
}
</script>

<template>
  <section class="auth-layout">
    <div class="auth-intro"><p class="eyebrow">欢迎回来</p><h1 tabindex="-1">继续今天的解题旅程</h1><p>登录后查看学习进度、编写 C++17 代码并追踪评测结果。</p></div>
    <form class="card auth-card" @submit.prevent="submit">
      <h2>登录 OJ Campus</h2>
      <label for="login-username">用户名</label><input id="login-username" v-model.trim="form.username" autocomplete="username" required />
      <label for="login-password">密码</label><input id="login-password" v-model="form.password" type="password" autocomplete="current-password" required />
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <button class="button button-primary button-wide" type="submit" :disabled="loading"><LogIn :size="19" />{{ loading ? '正在登录…' : '登录' }}</button>
      <p class="form-foot">还没有账号？<RouterLink to="/register">创建账号</RouterLink></p>
    </form>
  </section>
</template>
