<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api, readableError } from '../../api/client'
import AsyncState from '../../components/AsyncState.vue'
import type { Tag } from '../../types'

const tags = ref<Tag[]>([])
const drafts = reactive<Record<number, string>>({})
const state = ref<'loading' | 'error' | 'ready'>('loading')
const loadError = ref('')
const actionError = ref('')
const notice = ref('')
const newName = ref('')
const creating = ref(false)
const busyTagId = ref<number | null>(null)
const failedDelete = ref<Tag | null>(null)

function sorted(rows: Tag[]) {
  return [...rows].sort((left, right) => left.name.localeCompare(right.name))
}

function setTags(rows: Tag[]) {
  tags.value = sorted(rows)
  for (const tag of rows) drafts[tag.id] = tag.name
}

function resetFeedback() {
  actionError.value = ''
  notice.value = ''
  failedDelete.value = null
}

async function load() {
  state.value = 'loading'
  loadError.value = ''
  resetFeedback()
  try {
    setTags((await api.get<Tag[]>('/admin/tags')).data)
    state.value = 'ready'
  } catch (cause) {
    loadError.value = readableError(cause, '标签加载失败')
    state.value = 'error'
  }
}

async function createTag() {
  const name = newName.value.trim().toLowerCase()
  if (!name || creating.value) return
  creating.value = true
  resetFeedback()
  try {
    const created = (await api.post<Tag>('/admin/tags', { name })).data
    setTags([...tags.value.filter((tag) => tag.id !== created.id), created])
    newName.value = ''
    notice.value = `标签“${created.name}”已创建`
  } catch (cause) {
    actionError.value = readableError(cause, '标签创建失败')
  } finally {
    creating.value = false
  }
}

async function renameTag(tag: Tag) {
  const name = drafts[tag.id]?.trim().toLowerCase()
  if (!name || busyTagId.value !== null) return
  busyTagId.value = tag.id
  resetFeedback()
  try {
    const updated = (await api.patch<Tag>(`/admin/tags/${tag.id}`, { name })).data
    setTags(tags.value.map((item) => item.id === tag.id ? updated : item))
    notice.value = `标签已重命名为“${updated.name}”`
  } catch (cause) {
    actionError.value = readableError(cause, '标签重命名失败')
  } finally {
    busyTagId.value = null
  }
}

async function deleteTag(tag: Tag, askForConfirmation = true) {
  if (busyTagId.value !== null) return
  if (askForConfirmation && !window.confirm(`确定删除标签“${tag.name}”吗？`)) return
  busyTagId.value = tag.id
  resetFeedback()
  try {
    await api.delete(`/admin/tags/${tag.id}`)
    tags.value = tags.value.filter((item) => item.id !== tag.id)
    delete drafts[tag.id]
    notice.value = `标签“${tag.name}”已删除`
  } catch (cause) {
    actionError.value = readableError(cause, '标签删除失败')
    failedDelete.value = tag
  } finally {
    busyTagId.value = null
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="page-heading">
      <div>
        <p class="eyebrow">题库配置</p>
        <h1 tabindex="-1">标签管理</h1>
        <p>维护题目分类标签；正在使用的标签需要先从题目中移除。</p>
      </div>
    </div>

    <AsyncState
      v-if="state !== 'ready'"
      :status="state"
      :message="state === 'loading' ? '正在加载标签…' : loadError"
      :on-retry="load"
      retry-label="重新加载标签"
    />

    <template v-else>
      <form class="card tag-create" @submit.prevent="createTag">
        <div>
          <label for="new-tag-name">新标签名称</label>
          <input id="new-tag-name" v-model="newName" maxlength="64" autocomplete="off" placeholder="例如：动态规划" />
        </div>
        <button class="button button-primary" type="submit" :disabled="creating || !newName.trim()">
          {{ creating ? '正在创建…' : '创建标签' }}
        </button>
      </form>

      <p v-if="notice" class="feedback success" role="status" aria-live="polite">{{ notice }}</p>
      <div v-if="actionError" class="feedback error" role="alert">
        <p>{{ actionError }}</p>
        <button
          v-if="failedDelete"
          class="button button-secondary"
          type="button"
          :disabled="busyTagId !== null"
          :aria-label="`重试删除标签 ${failedDelete.name}`"
          @click="deleteTag(failedDelete, false)"
        >
          重试删除
        </button>
      </div>

      <AsyncState v-if="tags.length === 0" status="empty" message="暂无标签，可以在上方创建第一个标签。" />
      <section v-else class="card tag-list-card" aria-labelledby="tag-list-heading">
        <div class="section-heading">
          <div>
            <p class="eyebrow">现有标签</p>
            <h2 id="tag-list-heading">共 {{ tags.length }} 个标签</h2>
          </div>
        </div>
        <div class="table-wrap">
          <table class="tag-table">
            <thead><tr><th scope="col">当前名称</th><th scope="col">重命名</th><th scope="col">操作</th></tr></thead>
            <tbody>
              <tr v-for="tag in tags" :key="tag.id">
                <th scope="row">{{ tag.name }}</th>
                <td>
                  <form class="tag-name-form" @submit.prevent="renameTag(tag)">
                    <label :for="`tag-name-${tag.id}`">重命名标签 {{ tag.name }}</label>
                    <input :id="`tag-name-${tag.id}`" v-model="drafts[tag.id]" maxlength="64" autocomplete="off" />
                    <button
                      class="button button-secondary"
                      type="submit"
                      :disabled="busyTagId !== null || !drafts[tag.id]?.trim()"
                      :aria-label="`保存标签 ${tag.name}`"
                    >
                      {{ busyTagId === tag.id ? '保存中…' : '保存' }}
                    </button>
                  </form>
                </td>
                <td>
                  <button
                    class="button button-secondary"
                    type="button"
                    :disabled="busyTagId !== null"
                    :aria-label="`删除标签 ${tag.name}`"
                    @click="deleteTag(tag)"
                  >
                    删除
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.tag-create { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 16px; align-items: end; margin-bottom: 24px; }
.tag-create > div, .tag-name-form { display: grid; gap: 7px; }
.tag-list-card { padding-top: 24px; }
.tag-name-form { grid-template-columns: minmax(180px, 1fr) auto; align-items: end; }
.tag-name-form label { grid-column: 1 / -1; }
.feedback p { margin: 0; }
.feedback .button { margin-top: 10px; }
@media (max-width: 720px) {
  .tag-create, .tag-name-form { grid-template-columns: 1fr; }
  .tag-create .button, .tag-name-form .button { width: 100%; }
  .tag-list-card .table-wrap { overflow: visible; }
  .tag-table { min-width: 0; display: block; }
  .tag-table thead { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
  .tag-table tbody { display: grid; gap: 14px; }
  .tag-table tr { display: grid; grid-template-columns: minmax(0, 1fr); gap: 12px; padding: 16px; background: var(--surface-soft); border: var(--border); border-radius: var(--radius-md); }
  .tag-table th, .tag-table td { display: block; width: 100%; padding: 0; border: 0; }
  .tag-table tbody th { font-size: 1.05rem; overflow-wrap: anywhere; }
  .tag-table .tag-name-form { grid-template-columns: minmax(0, 1fr); }
  .tag-table .tag-name-form label { overflow-wrap: anywhere; }
  .tag-table input { min-width: 0; width: 100%; }
  .tag-table td > .button { width: 100%; }
}
</style>
