<script setup lang="ts">
import { computed } from 'vue'
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'

const props = defineProps<{ source: string }>()
const markdown = new MarkdownIt({ html: false, linkify: true, breaks: true })
const html = computed(() => DOMPurify.sanitize(markdown.render(props.source || '暂无内容')))
</script>

<template><div class="markdown" v-html="html" /></template>
