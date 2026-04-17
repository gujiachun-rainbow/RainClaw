<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14,2 14,8 20,8" />
    <text
      x="12"
      y="16.5"
      text-anchor="middle"
      font-size="6"
      font-weight="bold"
      fill="currentColor"
      stroke="none"
    >
      PDF
    </text>
  </svg>
</template>

<script setup lang="ts">
defineProps<{
  size?: number | string;
}>();
</script>
