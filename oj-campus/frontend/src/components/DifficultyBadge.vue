<script setup lang="ts">
import type { Difficulty } from '../types'
import { difficultyLabel } from '../utils/problems'
defineProps<{ difficulty: Difficulty }>()
</script>

<template><span :class="['difficulty', `difficulty-${difficulty}`]">{{ difficultyLabel(difficulty) }}</span></template>
