<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, readableError } from '../../api/client'
import AsyncState from '../../components/AsyncState.vue'
import PaginationControls from '../../components/PaginationControls.vue'
import type { PageResult, User } from '../../types'
const result=ref<PageResult<User>>({items:[],page:1,page_size:20,total:0});const state=ref<'loading'|'error'|'ready'>('loading');const error=ref('');async function load(page=1){state.value='loading';try{result.value=(await api.get<PageResult<User>>('/admin/users',{params:{page,page_size:20}})).data;state.value='ready'}catch(cause){error.value=readableError(cause,'用户列表加载失败');state.value='error'}}onMounted(()=>load())
</script>
<template><div><div class="page-heading"><div><p class="eyebrow">账号目录</p><h1 tabindex="-1">用户管理</h1><p>查看用户身份、账号状态和注册时间。</p></div></div><AsyncState v-if="state!=='ready'" :status="state" :message="state==='loading'?'正在加载用户…':error" :on-retry="()=>load(result.page)"/><section v-else class="card table-wrap"><table><thead><tr><th scope="col">编号</th><th scope="col">显示名称</th><th scope="col">用户名</th><th scope="col">邮箱</th><th scope="col">角色</th><th scope="col">状态</th><th scope="col">注册时间</th></tr></thead><tbody><tr v-for="user in result.items" :key="user.id"><td>#{{user.id}}</td><td>{{user.display_name}}</td><td>@{{user.username}}</td><td>{{user.email}}</td><td>{{user.role==='admin'?'管理员':'学生'}}</td><td>{{user.is_active?'正常':'停用'}}</td><td>{{new Date(user.created_at).toLocaleDateString('zh-CN')}}</td></tr></tbody></table><AsyncState v-if="!result.items.length" status="empty" message="还没有用户。"/></section><PaginationControls :page="result.page" :page-size="result.page_size" :total="result.total" @change="load"/></div></template>
