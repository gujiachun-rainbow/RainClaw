<template>
  <div class="flex flex-wrap gap-2 mt-2">
    <button
      v-for="(question, index) in questions"
      :key="index"
      class="px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-full hover:bg-gray-50 text-gray-700 transition-colors text-left"
      @click="$emit('click', question)"
    >
      {{ question }}
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  questions: string[];
}>();

defineEmits<{
  (e: 'click', question: string): void;
}>();
</script>
