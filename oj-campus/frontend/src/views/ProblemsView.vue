<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { Search, SlidersHorizontal } from '@lucide/vue'
import { api, readableError } from '../api/client'
import AsyncState from '../components/AsyncState.vue'
import DifficultyBadge from '../components/DifficultyBadge.vue'
import PaginationControls from '../components/PaginationControls.vue'
import type { PageResult, Problem } from '../types'
import { buildProblemParams } from '../utils/problems'

const filters = reactive({ keyword: '', difficulty: '' as '' | 'easy' | 'medium' | 'hard', tag: '', solved: '' as '' | boolean, page: 1 })
const result = ref<PageResult<Problem>>({ items: [], page: 1, page_size: 20, total: 0 })
const state = ref<'loading' | 'error' | 'ready'>('loading')
const error = ref('')
let debounce: ReturnType<typeof setTimeout>
async function load() { state.value = 'loading'; try { result.value = (await api.get<PageResult<Problem>>('/problems', { params: buildProblemParams(filters) })).data; state.value = 'ready' } catch (cause) { error.value = readableError(cause, '题目列表加载失败'); state.value = 'error' } }
function resetPageAndLoad() { filters.page = 1; clearTimeout(debounce); debounce = setTimeout(load, 250) }
watch(() => [filters.keyword, filters.difficulty, filters.tag, filters.solved], resetPageAndLoad)
onMounted(load)
</script>

<template>
  <div>
    <div class="page-heading"><div><p class="eyebrow">练习题库</p><h1 tabindex="-1">找到今天要攻克的题目</h1><p>按难度、标签和完成状态组合筛选。</p></div></div>
    <section class="card filter-bar" aria-label="题目筛选">
      <label class="search-field"><span>关键词</span><div><Search :size="18" /><input v-model="filters.keyword" placeholder="搜索题目名称" /></div></label>
      <label><span>难度</span><select v-model="filters.difficulty"><option value="">全部难度</option><option value="easy">简单 · 1 星</option><option value="medium">中等 · 2 星</option><option value="hard">困难 · 3 星</option></select></label>
      <label><span>标签</span><input v-model="filters.tag" placeholder="如 math" /></label>
      <label><span>完成状态</span><select v-model="filters.solved"><option value="">全部状态</option><option :value="true">已解决</option><option :value="false">未解决</option></select></label>
      <SlidersHorizontal class="filter-icon" :size="22" aria-hidden="true" />
    </section>
    <AsyncState v-if="state !== 'ready'" :status="state" :message="state === 'loading' ? '正在加载题目…' : error" :on-retry="load" />
    <section v-else class="problem-grid" aria-live="polite">
      <article v-for="problem in result.items" :key="problem.id" class="card problem-card"><div class="problem-top"><span class="problem-id">#{{ problem.id }}</span><DifficultyBadge :difficulty="problem.difficulty" /></div><h2><RouterLink :to="`/problems/${problem.id}`">{{ problem.title }}</RouterLink></h2><div class="tag-list"><span v-for="tag in problem.tags" :key="tag" class="tag">{{ tag }}</span><span v-if="!problem.tags.length" class="tag">基础</span></div><RouterLink class="button button-secondary" :to="`/problems/${problem.id}`">查看并作答</RouterLink></article>
      <AsyncState v-if="!result.items.length" status="empty" message="没有找到符合条件的题目，试试调整筛选。" />
    </section>
    <PaginationControls :page="result.page" :page-size="result.page_size" :total="result.total" @change="filters.page = $event; load()" />
  </div>
</template>
