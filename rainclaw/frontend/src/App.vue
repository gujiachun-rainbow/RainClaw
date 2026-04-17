<template>
  <router-view />
  <Toast />
</template>

<script setup lang="ts">
import Toast from './components/ui/Toast.vue';
import { useTheme } from './composables/useTheme';
import { onMounted } from 'vue';

const { initTheme } = useTheme();

onMounted(() => {
  initTheme();
});
</script>
