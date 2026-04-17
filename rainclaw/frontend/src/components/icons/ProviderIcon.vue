<template>
  <span class="inline-flex items-center justify-center shrink-0" :class="$attrs.class" aria-hidden="true">
    <img v-if="iconSrc" :src="iconSrc" :alt="provider" class="w-full h-full object-contain" />
    <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-full h-full text-[var(--text-tertiary)]">
      <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
      <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
      <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
    </svg>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  provider: string;
}>();

const normalizedProvider = computed(() => (props.provider || '').toLowerCase());

const iconSrc = computed(() => {
  const p = normalizedProvider.value;
  if (p === 'openai') return '/openai.svg';
  if (p === 'anthropic') return '/anthropic.svg';
  if (p === 'deepseek') return '/deepseek-color.svg';
  if (p === 'google' || p === 'gemini') return '/gemini-color.svg';
  if (p === 'qwen' || p === 'alibaba') return '/qwen-color.svg';
  if (p === 'kimi' || p === 'moonshot') return '/kimi-color.svg';
  if (p === 'minimax') return '/minimax-color.svg';
  if (p === 'taichu' || p === 'aimass') return '/taichu-color.svg';
  if (p === 'glm' || p === 'zhipu') return '/glm-color.svg';
  return null;
});
</script>
