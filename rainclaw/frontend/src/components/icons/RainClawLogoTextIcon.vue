<template>
  <div class="flex items-center">
    <span class="logo-text font-sans font-extrabold text-2xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-500 via-red-500 to-amber-500" style="background-size: 200% 100%;">
      RainClaw
    </span>
  </div>
</template>

<script setup lang="ts">
defineProps({
  width: { type: [String, Number], default: 140 },
  height: { type: [String, Number], default: 38 },
})
</script>

<style scoped>
.logo-text {
  animation: gradientShift 4s ease-in-out infinite;
}
@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
</style>
