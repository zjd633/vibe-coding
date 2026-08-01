<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Medal } from '@lucide/vue'
import { api, readableError } from '../api/client'
import AsyncState from '../components/AsyncState.vue'
interface Row{user_id:number;username:string;display_name:string;solved:number;attempts:number}interface Board{items:Row[];current_user_position:number|null}
const board=ref<Board|null>(null);const state=ref<'loading'|'error'|'ready'>('loading');const error=ref('');async function load(){state.value='loading';try{board.value=(await api.get<Board>('/leaderboard')).data;state.value='ready'}catch(cause){error.value=readableError(cause,'排行榜加载失败');state.value='error'}}onMounted(load)
</script>
<template><div><div class="page-heading"><div><p class="eyebrow">校园挑战榜</p><h1 tabindex="-1">排行榜</h1><p>按当前版本通过题数排序，同分时提交更少者优先。</p></div><div v-if="board?.current_user_position" class="rank-callout"><Medal :size="22"/>我的排名：第 {{board.current_user_position}} 名</div></div><AsyncState v-if="state!=='ready'" :status="state" :message="state==='loading'?'正在加载排名…':error" :on-retry="load"/><section v-else class="card table-wrap"><table><thead><tr><th scope="col">排名</th><th scope="col">同学</th><th scope="col">用户名</th><th scope="col">已解决</th><th scope="col">提交数</th></tr></thead><tbody><tr v-for="(row,index) in board?.items" :key="row.user_id" :class="{'current-row':index+1===board?.current_user_position}"><td class="rank-number">{{index+1}}</td><td>{{row.display_name}}</td><td>@{{row.username}}</td><td class="numeric">{{row.solved}}</td><td class="numeric">{{row.attempts}}</td></tr></tbody></table><AsyncState v-if="!board?.items.length" status="empty" message="排行榜还没有数据。"/></section></div></template>
