<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { CircleCheck, Clock3, FileCode2, FlaskConical } from '@lucide/vue'
import { api, readableError } from '../api/client'
import AsyncState from '../components/AsyncState.vue'
import type { Submission } from '../types'
import { startSubmissionPolling } from '../utils/polling'
import { isPending, safeDiagnostic, verdictLabel } from '../utils/submissions'
const route=useRoute();const item=ref<Submission|null>(null);const state=ref<'loading'|'error'|'ready'>('loading');const error=ref('');let stop:(()=>void)|undefined
const statusText=computed(()=>item.value?verdictLabel[item.value.status]:'')
async function fetchItem(){return(await api.get<Submission>(`/submissions/${route.params.id}`)).data}
function pollingFailed(cause:unknown){stop?.();stop=undefined;error.value=readableError(cause,'评测状态更新失败，请重试');state.value='error'}
async function load(){state.value='loading';error.value='';stop?.();stop=undefined;try{item.value=await fetchItem();state.value='ready';if(isPending(item.value.status))stop=startSubmissionPolling(fetchItem,(next)=>item.value=next,pollingFailed)}catch(cause){error.value=readableError(cause,'提交详情加载失败');state.value='error'}}
onMounted(load);onBeforeUnmount(()=>stop?.())
</script>
<template><AsyncState v-if="state!=='ready'" :status="state" :message="state==='loading'?'正在获取评测状态…':error" :on-retry="load" :retry-label="'重新获取评测状态'"/><div v-else-if="item"><div class="page-heading"><div><p class="eyebrow">提交 #{{item.id}}</p><h1 tabindex="-1">{{statusText}}</h1><p aria-live="polite">{{isPending(item.status)?'评测进行中，本页每秒自动更新。':'评测已完成。'}}</p></div><span :class="['verdict','verdict-large',`verdict-${item.status.toLowerCase()}`]">{{statusText}}</span></div><section class="detail-grid"><article class="card detail-stat"><Clock3/><span>运行时间</span><strong>{{item.runtime_ms==null?'—':`${item.runtime_ms} ms`}}</strong></article><article class="card detail-stat"><FlaskConical/><span>失败测试点</span><strong>{{item.failed_case??'—'}}</strong></article><article class="card detail-stat"><CircleCheck/><span>语言</span><strong>C++17</strong></article></section><section class="card"><h2>评测说明</h2><p>{{safeDiagnostic(item)}}</p></section><section v-if="item.source" class="card"><h2 class="icon-heading"><FileCode2 :size="22"/>提交源码</h2><pre class="source-code"><code>{{item.source}}</code></pre></section></div></template>
