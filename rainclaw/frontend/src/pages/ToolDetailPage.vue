<template>
  <div class="flex flex-col h-full w-full bg-[#FAFAFA] overflow-hidden">
    <!-- Header -->
    <div class="h-14 border-b border-[var(--border-light)] bg-white flex items-center px-6 justify-between flex-shrink-0">
      <div class="flex items-center gap-4">
        <button 
          @click="goBack" 
          class="p-2 -ml-2 rounded-lg hover:bg-[var(--background-gray-main)] transition-colors text-[var(--text-secondary)]"
        >
          <ArrowLeft class="size-5" />
        </button>
        <div class="flex items-center gap-3">
          <div class="size-8 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600 font-bold">
            {{ toolName.charAt(0).toUpperCase() }}
          </div>
          <div class="flex flex-col">
            <h1 class="text-sm font-semibold text-[var(--text-primary)]">{{ toolName }}</h1>
            <div class="text-xs text-[var(--text-tertiary)] font-mono">{{ toolName }}.py</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-hidden flex flex-col bg-white">
      <div v-if="loading" class="flex justify-center items-center flex-1">
        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
      </div>
      <div v-else-if="error" class="flex flex-col items-center justify-center flex-1 text-red-500">
        <div class="bg-red-50 p-4 rounded-lg border border-red-100 max-w-lg w-full text-center">
          <p class="font-medium">Error loading file</p>
          <p class="text-sm mt-1 opacity-80">{{ error }}</p>
        </div>
      </div>
      <div v-else class="flex-1 overflow-auto">
        <pre class="p-6 text-sm font-mono leading-relaxed text-[var(--text-primary)] whitespace-pre"><code>{{ fileContent }}</code></pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft } from 'lucide-vue-next';
import { readToolFile } from '../api/agent';

const route = useRoute();
const router = useRouter();
const toolName = route.params.toolName as string;

const loading = ref(true);
const error = ref<string | null>(null);
const fileContent = ref<string | null>(null);

const goBack = () => {
  router.back();
};

onMounted(async () => {
  try {
    const res = await readToolFile(toolName);
    fileContent.value = res.content;
  } catch (e: any) {
    error.value = e.message || "Failed to load tool source";
  } finally {
    loading.value = false;
  }
});
</script>
