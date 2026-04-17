<template>
  <div class="w-full h-[500px] border border-[var(--border-main)] rounded-lg bg-white overflow-hidden relative">
    <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-gray-50 z-10">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
    <div v-if="error" class="absolute inset-0 flex items-center justify-center text-red-500 p-4 text-center text-sm z-10">
      {{ error }}
    </div>
    
    <iframe 
      v-if="blobUrl"
      :src="blobUrl" 
      class="w-full h-full border-0"
      sandbox="allow-scripts allow-same-origin"
      @load="loading = false"
    ></iframe>
    
    <div class="absolute top-2 right-2 flex gap-2">
        <a :href="src" target="_blank" class="p-1.5 bg-white/90 backdrop-blur rounded shadow text-gray-600 hover:text-primary text-xs border border-gray-200" title="Open in new tab">
            Open New Tab
        </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';

const props = defineProps<{
  src: string;
}>();

const loading = ref(true);
const error = ref<string | null>(null);
const blobUrl = ref<string | null>(null);

const loadContent = async () => {
    loading.value = true;
    error.value = null;
    if (blobUrl.value) {
        URL.revokeObjectURL(blobUrl.value);
        blobUrl.value = null;
    }

    try {
        const response = await fetch(props.src);
        if (!response.ok) {
            throw new Error(`Failed to load HTML: ${response.statusText}`);
        }
        const html = await response.text();
        
        // Create a blob to render in iframe securely
        const blob = new Blob([html], { type: 'text/html' });
        blobUrl.value = URL.createObjectURL(blob);
    } catch (e: any) {
        error.value = e.message;
        loading.value = false;
    }
};

onMounted(loadContent);
watch(() => props.src, loadContent);

onUnmounted(() => {
    if (blobUrl.value) {
        URL.revokeObjectURL(blobUrl.value);
    }
});
</script>
