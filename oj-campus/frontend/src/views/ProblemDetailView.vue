<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Clock3, Play, Send } from '@lucide/vue'
import { api, readableError } from '../api/client'
import AsyncState from '../components/AsyncState.vue'
import CodeEditor from '../components/CodeEditor.vue'
import DifficultyBadge from '../components/DifficultyBadge.vue'
import MarkdownContent from '../components/MarkdownContent.vue'
import type { Problem, Submission } from '../types'
import { startSubmissionPolling } from '../utils/polling'

const template = `#include <iostream>\nusing namespace std;\n\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n\n    // 在这里编写你的解法\n    return 0;\n}\n`
const route = useRoute(); const router = useRouter()
const problem = ref<Problem | null>(null); const code = ref(template); const submission = ref<Submission | null>(null)
const state = ref<'loading' | 'error' | 'ready'>('loading'); const error = ref(''); const sending = ref(false); const notice = ref('')
async function load() { state.value = 'loading'; try { problem.value = (await api.get<Problem>(`/problems/${route.params.id}`)).data; state.value = 'ready' } catch (cause) { error.value = readableError(cause, '题目加载失败'); state.value = 'error' } }
async function submit() { if (!problem.value) return; sending.value = true; notice.value = ''; try { submission.value = (await api.post<Submission>('/submissions', { problem_id: problem.value.id, language: 'cpp17', source: code.value })).data; await router.push(`/submissions/${submission.value.id}`) } catch (cause) { notice.value = readableError(cause, '提交失败，请稍后重试') } finally { sending.value = false } }
onMounted(load)
</script>

<template>
  <AsyncState v-if="state !== 'ready'" :status="state" :message="state === 'loading' ? '正在打开题目…' : error" :on-retry="load" />
  <div v-else-if="problem" class="problem-workspace">
    <section class="card problem-reading"><div class="problem-title"><div><p class="eyebrow">题目 #{{ problem.id }}</p><h1 tabindex="-1">{{ problem.title }}</h1></div><DifficultyBadge :difficulty="problem.difficulty" /></div><p class="time-limit"><Clock3 :size="18" />时间限制 {{ problem.time_limit_ms }} ms</p>
      <h2>题目描述</h2><MarkdownContent :source="problem.statement" /><h2>输入说明</h2><MarkdownContent :source="problem.input" /><h2>输出说明</h2><MarkdownContent :source="problem.output" />
      <h2>样例</h2><div v-if="problem.test_cases?.length" class="sample-grid"><article v-for="sample in problem.test_cases" :key="sample.position" class="sample-card"><h3>样例 {{ sample.position }}</h3><strong>输入</strong><pre>{{ sample.input }}</pre><strong>输出</strong><pre>{{ sample.output }}</pre></article></div><p v-else class="muted">本题暂无公开样例。</p>
    </section>
    <aside class="card editor-panel"><div class="section-heading"><div><p class="eyebrow">在线作答</p><h2>C++17</h2></div><Play :size="24" aria-hidden="true" /></div><CodeEditor v-model="code" /><p class="helper">源码最大 64 KiB。提交后将自动跳转并每秒更新评测状态。</p><p v-if="notice" class="form-error" role="alert">{{ notice }}</p><button class="button button-primary button-wide" type="button" :disabled="sending || !code.trim()" @click="submit"><Send :size="19" />{{ sending ? '正在提交…' : '提交评测' }}</button></aside>
  </div>
</template>
