<script setup lang="ts">
import type { Submission } from '../types'
import { verdictLabel } from '../utils/submissions'
defineProps<{ items: Submission[]; detailBase?: string }>()
</script>

<template>
  <div class="table-wrap">
    <table>
      <thead><tr><th scope="col">编号</th><th scope="col">题目</th><th scope="col">用户</th><th scope="col">结果</th><th scope="col">用时</th><th scope="col">提交时间</th></tr></thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td><RouterLink v-if="detailBase" :to="`${detailBase}/${item.id}`">#{{ item.id }}</RouterLink><span v-else>#{{ item.id }}</span></td>
          <td><RouterLink :to="`/problems/${item.problem_id}`">题目 {{ item.problem_id }}</RouterLink></td>
          <td>{{ item.user_id }}</td>
          <td><span :class="['verdict', `verdict-${item.status.toLowerCase()}`]">{{ verdictLabel[item.status] }}</span></td>
          <td class="numeric">{{ item.runtime_ms == null ? '—' : `${item.runtime_ms} ms` }}</td>
          <td>{{ new Date(item.created_at).toLocaleString('zh-CN') }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
