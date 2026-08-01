<script setup lang="ts">
import { onMounted } from 'vue'
import AppShell from './components/AppShell.vue'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
onMounted(() => {
  if (!auth.ready) void auth.restoreSession()
})
</script>

<template>
  <a class="skip-link" href="#main-content">跳到主要内容</a>
  <AppShell />
</template>
