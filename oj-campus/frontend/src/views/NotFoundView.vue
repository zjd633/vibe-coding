<script setup lang="ts">import { MapPinOff } from '@lucide/vue'</script>
<template><section class="not-found"><MapPinOff :size="52"/><p class="eyebrow">404</p><h1 tabindex="-1">这个页面走丢了</h1><p>链接可能已失效，返回题库继续练习吧。</p><RouterLink class="button button-primary" to="/problems">返回题库</RouterLink></section></template>
