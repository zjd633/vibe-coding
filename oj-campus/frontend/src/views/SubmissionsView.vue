<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, readableError } from '../api/client'
import AsyncState from '../components/AsyncState.vue'
import PaginationControls from '../components/PaginationControls.vue'
import SubmissionTable from '../components/SubmissionTable.vue'
import type { PageResult, Submission } from '../types'
const result = ref<PageResult<Submission>>({ items: [], page: 1, page_size: 20, total: 0 }); const state = ref<'loading'|'error'|'ready'>('loading'); const error = ref('')
async function load(page = result.value.page) { state.value='loading'; try { result.value=(await api.get<PageResult<Submission>>('/submissions',{params:{page,page_size:20}})).data; state.value='ready' } catch(cause){error.value=readableError(cause,'提交记录加载失败');state.value='error'} }
onMounted(()=>load(1))
</script>
<template><div><div class="page-heading"><div><p class="eyebrow">我的足迹</p><h1 tabindex="-1">个人提交</h1><p>查看每次评测的结果、用时与失败测试点。</p></div></div><AsyncState v-if="state!=='ready'" :status="state" :message="state==='loading'?'正在加载提交记录…':error" :on-retry="()=>load()"/><section v-else class="card"><SubmissionTable v-if="result.items.length" :items="result.items" detail-base="/submissions"/><AsyncState v-else status="empty" message="还没有提交记录，先去题库选择一道题吧。"/></section><PaginationControls :page="result.page" :page-size="result.page_size" :total="result.total" @change="load"/></div></template>
