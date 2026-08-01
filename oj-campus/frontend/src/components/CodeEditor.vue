<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { EditorState } from '@codemirror/state'
import { EditorView, basicSetup } from 'codemirror'
import { cpp } from '@codemirror/lang-cpp'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const host = ref<HTMLElement | null>(null)
let view: EditorView | undefined

onMounted(() => {
  view = new EditorView({
    parent: host.value ?? undefined,
    state: EditorState.create({
      doc: props.modelValue,
      extensions: [basicSetup, cpp(), EditorView.lineWrapping, EditorView.updateListener.of((update) => {
        if (update.docChanged) emit('update:modelValue', update.state.doc.toString())
      })],
    }),
  })
})
watch(() => props.modelValue, (value) => {
  if (view && value !== view.state.doc.toString()) view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: value } })
})
onBeforeUnmount(() => view?.destroy())
</script>

<template><div ref="host" class="code-editor" aria-label="C++17 代码编辑器" /></template>
