<template>
  <div class="w-full h-full flex flex-col overflow-hidden relative bg-white">
    <div v-if="loading" class="absolute inset-0 flex items-center justify-center z-10 bg-white/50">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--primary-color)]"></div>
    </div>
    <MoleculeViewer v-if="fileUrl" :src="fileUrl" class="w-full h-full" />
    <div v-else-if="!loading" class="flex flex-col items-center justify-center h-full text-[var(--text-tertiary)]">
      <p>{{ $t('Failed to load molecule') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { FileInfo, getFileDownloadUrl } from '../../api/file';
import MoleculeViewer from '../MoleculeViewer.vue';

const props = defineProps<{
  file: FileInfo;
}>();

const fileUrl = ref<string>('');
const loading = ref(true);

const loadUrl = async () => {
  console.log('MoleculeFilePreview: loading file', props.file);
  if (!props.file) return;
  loading.value = true;
  try {
    fileUrl.value = await getFileDownloadUrl(props.file);
    console.log('MoleculeFilePreview: fileUrl', fileUrl.value);
  } catch (error) {
    console.error('Failed to get file URL:', error);
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
