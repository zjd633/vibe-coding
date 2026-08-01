<script setup lang="ts">
import { ChevronLeft, ChevronRight } from '@lucide/vue'
const props = defineProps<{ page: number; pageSize: number; total: number }>()
const emit = defineEmits<{ change: [page: number] }>()
</script>

<template>
  <nav v-if="total > pageSize" class="pagination" aria-label="分页">
    <button class="button button-secondary" type="button" :disabled="page <= 1" @click="emit('change', page - 1)"><ChevronLeft :size="18" />上一页</button>
    <span>第 {{ page }} / {{ Math.ceil(total / pageSize) }} 页</span>
    <button class="button button-secondary" type="button" :disabled="page * pageSize >= total" @click="emit('change', page + 1)">下一页<ChevronRight :size="18" /></button>
  </nav>
</template>
