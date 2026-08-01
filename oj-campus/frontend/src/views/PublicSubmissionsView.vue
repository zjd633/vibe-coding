<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, readableError } from '../api/client'
import AsyncState from '../components/AsyncState.vue'
import PaginationControls from '../components/PaginationControls.vue'
import SubmissionTable from '../components/SubmissionTable.vue'
import type { PageResult, Submission } from '../types'
type PublicSubmission = Pick<Submission, 'id'|'user_id'|'problem_id'|'problem_revision'|'language'|'status'|'runtime_ms'|'created_at'>
const result=ref<PageResult<PublicSubmission>>({items:[],page:1,page_size:20,total:0});const state=ref<'loading'|'error'|'ready'>('loading');const error=ref('')
function toPublicSubmission(item:Submission):PublicSubmission{return {id:item.id,user_id:item.user_id,problem_id:item.problem_id,problem_revision:item.problem_revision,language:item.language,status:item.status,runtime_ms:item.runtime_ms,created_at:item.created_at}}
async function load(page=result.value.page){state.value='loading';try{const response=(await api.get<PageResult<Submission>>('/submissions/public',{params:{page,page_size:20}})).data;result.value={...response,items:response.items.map(toPublicSubmission)};state.value='ready'}catch(cause){error.value=readableError(cause,'全站提交加载失败');state.value='error'}}onMounted(()=>load(1))
</script>
<template><div><div class="page-heading"><div><p class="eyebrow">实时评测动态</p><h1 tabindex="-1">全站提交</h1><p>这里只展示公开评测元数据，绝不会请求或显示任何源码。</p></div></div><AsyncState v-if="state!=='ready'" :status="state" :message="state==='loading'?'正在加载全站动态…':error" :on-retry="()=>load()"/><section v-else class="card"><SubmissionTable v-if="result.items.length" :items="result.items"/><AsyncState v-else status="empty" message="暂时还没有公开提交。"/></section><PaginationControls :page="result.page" :page-size="result.page_size" :total="result.total" @change="load"/></div></template>
