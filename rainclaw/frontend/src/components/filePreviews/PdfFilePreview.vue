<template>
  <div class="w-full h-full flex flex-col bg-white">
    <iframe 
      v-if="fileUrl" 
      :src="fileUrl" 
      class="w-full h-full border-none"
      title="PDF Preview"
    ></iframe>
    <div v-else-if="loading" class="flex items-center justify-center h-full">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--primary-color)]"></div>
    </div>
    <div v-else class="flex items-center justify-center h-full text-[var(--text-tertiary)]">
      {{ $t('Failed to load PDF') }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import type { FileInfo } from '../../api/file';
import { getFileDownloadUrl } from '../../api/file';

const props = defineProps<{
  file: FileInfo;
}>();

const fileUrl = ref('');
const loading = ref(true);

const loadUrl = async () => {
  if (!props.file) return;
  loading.value = true;
  try {
    const url = await getFileDownloadUrl(props.file);
    // Use the URL directly for iframe
    fileUrl.value = url;
  } catch (error) {
    console.error('Failed to get PDF URL:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadUrl();
});

watch(() => props.file, () => {
  loadUrl();
});
</script>
