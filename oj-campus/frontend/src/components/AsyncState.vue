<script setup lang="ts">
import { AlertCircle, Inbox, LoaderCircle, RotateCcw } from '@lucide/vue'

defineProps<{ status: 'loading' | 'error' | 'empty'; message: string; onRetry?: () => void; retryLabel?: string }>()
</script>

<template>
  <div v-if="status === 'loading'" class="state-card" role="status" aria-live="polite">
    <LoaderCircle class="state-icon spinning" :size="28" aria-hidden="true" />
    <p>{{ message }}</p>
  </div>
  <div v-else-if="status === 'error'" class="state-card state-error" role="alert">
    <AlertCircle class="state-icon" :size="28" aria-hidden="true" />
    <p>{{ message }}</p>
    <button v-if="onRetry" class="button button-secondary" type="button" @click="onRetry">
      <RotateCcw :size="18" aria-hidden="true" />{{ retryLabel ?? '重新加载' }}
    </button>
  </div>
  <div v-else class="state-card">
    <Inbox class="state-icon" :size="28" aria-hidden="true" />
    <p>{{ message }}</p>
  </div>
</template>
