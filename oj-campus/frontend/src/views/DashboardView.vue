<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { BookOpenCheck, Flame, Medal, Target, TrendingUp } from '@lucide/vue'
import { api, readableError } from '../api/client'
import AsyncState from '../components/AsyncState.vue'
import DifficultyBadge from '../components/DifficultyBadge.vue'
import SubmissionTable from '../components/SubmissionTable.vue'
import { useAuthStore } from '../stores/auth'
import type { Problem, Submission } from '../types'

interface Dashboard { solved_count: number; acceptance_rate: number; rank: number | null; current_streak: number; recent_submissions: Submission[]; unsolved_problems: Problem[] }
const auth = useAuthStore()
const data = ref<Dashboard | null>(null)
const state = ref<'loading' | 'error' | 'ready'>('loading')
const error = ref('')
async function load() { state.value = 'loading'; try { data.value = (await api.get<Dashboard>('/dashboard')).data; state.value = 'ready' } catch (cause) { error.value = readableError(cause, '学习数据加载失败'); state.value = 'error' } }
onMounted(load)
</script>

<template>
  <div>
    <section class="hero-card">
      <div><p class="eyebrow">今日学习站</p><h1 tabindex="-1">你好，{{ auth.user?.display_name }}</h1><p>保持节奏，每一次提交都在为下一次突破积累经验。</p></div>
      <RouterLink class="button button-accent" to="/problems"><BookOpenCheck :size="20" />开始做题</RouterLink>
    </section>
    <AsyncState v-if="state !== 'ready'" :status="state" :message="state === 'loading' ? '正在整理你的学习进度…' : error" :on-retry="load" />
    <template v-else-if="data">
      <section class="stat-grid" aria-label="学习数据">
        <article class="stat-card"><Target /><span>已解决</span><strong>{{ data.solved_count }}</strong></article>
        <article class="stat-card"><TrendingUp /><span>通过率</span><strong>{{ (data.acceptance_rate * 100).toFixed(1) }}%</strong></article>
        <article class="stat-card"><Medal /><span>当前排名</span><strong>{{ data.rank ?? '—' }}</strong></article>
        <article class="stat-card"><Flame /><span>连续学习</span><strong>{{ data.current_streak }} 天</strong></article>
      </section>
      <div class="two-column">
        <section class="card"><div class="section-heading"><div><p class="eyebrow">下一步</p><h2>推荐题目</h2></div><RouterLink to="/problems">查看全部</RouterLink></div>
          <div v-if="data.unsolved_problems.length" class="problem-stack"><RouterLink v-for="problem in data.unsolved_problems" :key="problem.id" class="problem-row" :to="`/problems/${problem.id}`"><div><strong>{{ problem.title }}</strong><small>#{{ problem.id }} · {{ problem.tags.join(' / ') || '基础' }}</small></div><DifficultyBadge :difficulty="problem.difficulty" /></RouterLink></div>
          <AsyncState v-else status="empty" message="所有已发布题目都解决啦，太棒了！" />
        </section>
        <section class="card"><div class="section-heading"><div><p class="eyebrow">最近动态</p><h2>近期提交</h2></div><RouterLink to="/submissions">查看全部</RouterLink></div><SubmissionTable v-if="data.recent_submissions.length" :items="data.recent_submissions" detail-base="/submissions" /><AsyncState v-else status="empty" message="还没有提交记录，去完成第一道题吧。" /></section>
      </div>
    </template>
  </div>
</template>
