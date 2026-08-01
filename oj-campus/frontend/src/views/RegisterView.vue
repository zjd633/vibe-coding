<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { UserRoundPlus } from '@lucide/vue'
import { fieldErrors, readableError } from '../api/client'
import { useAuthStore } from '../stores/auth'

const form = reactive({ username: '', email: '', display_name: '', password: '' })
const errors = ref<Record<string, string>>({})
const message = ref('')
const loading = ref(false)
const auth = useAuthStore()
const router = useRouter()

async function submit() {
  loading.value = true; errors.value = {}; message.value = ''
  try { await auth.register(form); await router.replace('/dashboard') }
  catch (cause) { errors.value = fieldErrors(cause); message.value = readableError(cause, '注册失败，请检查填写内容') }
  finally { loading.value = false }
}
</script>

<template>
  <section class="auth-layout">
    <div class="auth-intro"><p class="eyebrow">加入校园练习场</p><h1 tabindex="-1">从第一道题开始积累</h1><p>用户名支持 3–24 位英文、数字与下划线，密码至少 8 位。</p></div>
    <form class="card auth-card" @submit.prevent="submit">
      <h2>创建账号</h2>
      <label for="reg-name">显示名称</label><input id="reg-name" v-model.trim="form.display_name" autocomplete="name" maxlength="32" required /><small v-if="errors.display_name" class="field-error">{{ errors.display_name }}</small>
      <label for="reg-username">用户名</label><input id="reg-username" v-model.trim="form.username" autocomplete="username" pattern="[A-Za-z0-9_]{3,24}" required /><small v-if="errors.username" class="field-error">{{ errors.username }}</small>
      <label for="reg-email">邮箱</label><input id="reg-email" v-model.trim="form.email" type="email" autocomplete="email" required /><small v-if="errors.email" class="field-error">{{ errors.email }}</small>
      <label for="reg-password">密码</label><input id="reg-password" v-model="form.password" type="password" autocomplete="new-password" minlength="8" required /><small v-if="errors.password" class="field-error">{{ errors.password }}</small>
      <p v-if="message" class="form-error" role="alert">{{ message }}</p>
      <button class="button button-primary button-wide" type="submit" :disabled="loading"><UserRoundPlus :size="19" />{{ loading ? '正在创建…' : '创建账号' }}</button>
      <p class="form-foot">已有账号？<RouterLink to="/login">直接登录</RouterLink></p>
    </form>
  </section>
</template>
