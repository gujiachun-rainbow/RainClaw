<template>
  <div class="flex flex-col h-full w-full overflow-hidden">
    <!-- Hero Header -->
    <div class="flex-shrink-0 relative overflow-hidden">
      <div class="absolute inset-0" :style="{ background: heroGradient }"></div>
      <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNCI+PHBhdGggZD0iTTM2IDM0djZoLTZ2LTZoNnptMC0zMHY2aC02VjRoNnoiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-50"></div>
      <div class="relative px-6 py-4 flex items-center gap-4">
        <button @click="goBack" class="p-2 -ml-2 rounded-lg hover:bg-white/10 transition-colors text-white/70 hover:text-white">
          <ArrowLeft class="size-5" />
        </button>
        <div class="size-11 rounded-xl bg-white/15 backdrop-blur-sm flex items-center justify-center text-white text-lg font-bold shadow-lg">
          {{ skillName.charAt(0).toUpperCase() }}
        </div>
        <div class="min-w-0">
          <h1 class="text-base font-bold text-white truncate">{{ skillName }}</h1>
          <div class="flex items-center gap-1 text-white/50 text-xs">
            <span class="cursor-pointer hover:text-white/80 transition-colors" @click="navigateToRoot">root</span>
            <template v-for="(part, index) in pathParts" :key="index">
              <span>/</span>
              <span class="cursor-pointer hover:text-white/80 transition-colors" @click="navigateToPart(index)">{{ part }}</span>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 flex overflow-hidden bg-[#f8f9fb] dark:bg-[#111]">
      <!-- File Tree Sidebar -->
      <div class="w-64 border-r border-gray-100 dark:border-gray-800 bg-white/80 dark:bg-[#1a1a1a]/80 backdrop-blur-sm flex flex-col overflow-hidden">
        <div class="px-3 py-2.5 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
          <span class="text-[10px] font-semibold text-[var(--text-tertiary)] uppercase tracking-wider truncate">
            {{ currentPath || 'Root' }}
          </span>
          <button v-if="currentPath" @click="navigateUp"
            class="text-[10px] text-violet-600 dark:text-violet-400 hover:text-violet-700 flex items-center gap-0.5 transition-colors">
            <ArrowLeft class="size-3" /> Up
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-2">
          <div v-if="loading" class="flex flex-col items-center justify-center py-8 gap-2">
            <div class="relative size-8">
              <div class="absolute inset-0 rounded-full border-2 border-violet-100 dark:border-violet-900"></div>
              <div class="absolute inset-0 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"></div>
            </div>
          </div>
          <div v-else-if="fileTree.length === 0" class="text-center py-8 text-xs text-[var(--text-tertiary)]">Empty directory</div>
          <template v-else>
            <div v-if="currentPath"
              class="flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-xs transition-all duration-200 text-[var(--text-tertiary)] hover:bg-gray-50 dark:hover:bg-white/5 mb-1"
              @click="navigateUp">
              <ArrowLeft class="size-3 opacity-50" />
              <span>..</span>
            </div>
            <div v-for="(item, idx) in fileTree" :key="item.path"
              class="file-item flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-xs transition-all duration-200"
              :class="selectedFile === item.path
                ? 'bg-violet-50 dark:bg-violet-900/20 text-violet-700 dark:text-violet-300 font-medium'
                : 'text-[var(--text-secondary)] hover:bg-gray-50 dark:hover:bg-white/5'"
              :style="{ '--delay': `${idx * 20}ms` }"
              @click="handleItemClick(item)">
              <Folder v-if="item.type === 'directory'" class="size-4 text-amber-400 flex-shrink-0" />
              <FileText v-else class="size-4 text-gray-400 flex-shrink-0" />
              <span class="truncate">{{ item.name }}</span>
            </div>
          </template>
        </div>
      </div>

      <!-- File Content Preview -->
      <div class="flex-1 overflow-hidden flex flex-col">
        <div v-if="selectedFile" class="flex-1 flex flex-col overflow-hidden">
          <div v-if="error" class="flex-1 flex items-center justify-center p-6">
            <div class="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800/50 rounded-xl p-5 max-w-lg w-full text-center">
              <p class="text-sm font-medium text-red-600 dark:text-red-400">Error loading file</p>
              <p class="text-xs text-red-500/70 mt-1">{{ error }}</p>
            </div>
          </div>
          <FileViewer v-else :file-name="selectedFileName" :skill-name="skillName" :path="selectedFile" :content="fileContent" class="flex-1" />
        </div>
        <div v-else class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <div class="size-20 rounded-2xl bg-gray-50 dark:bg-gray-900 flex items-center justify-center mx-auto mb-3">
              <FileSearch class="size-8 opacity-20" />
            </div>
            <p class="text-sm text-[var(--text-tertiary)]">Select a file to view content</p>
            <p class="text-xs text-[var(--text-tertiary)] opacity-50 mt-1">Browse the file tree on the left</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft, Folder, FileText, FileSearch } from 'lucide-vue-next';
import { getSkillFiles, readSkillFile } from '../api/agent';
import FileViewer from '../components/FileViewer.vue';

const route = useRoute();
const router = useRouter();
const skillName = route.params.skillName as string;

const gradients = [
  'linear-gradient(135deg, #8b5cf6 0%, #a855f7 50%, #d946ef 100%)',
  'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)',
  'linear-gradient(135deg, #ec4899 0%, #f43f5e 50%, #f97316 100%)',
  'linear-gradient(135deg, #d946ef 0%, #ec4899 50%, #f43f5e 100%)',
  'linear-gradient(135deg, #7c3aed 0%, #6366f1 50%, #3b82f6 100%)',
];
const heroGradient = computed(() => {
  let h = 0; for (let i = 0; i < skillName.length; i++) h = skillName.charCodeAt(i) + ((h << 5) - h);
  return gradients[Math.abs(h) % gradients.length];
});

const loading = ref(true);
const contentLoading = ref(false);
const error = ref<string | null>(null);
const fileTree = ref<any[]>([]);
const currentPath = ref("");
const selectedFile = ref<string | null>(null);
const fileContent = ref<string | null>(null);

const selectedFileName = computed(() => selectedFile.value?.split('/').pop() || "");
const pathParts = computed(() => currentPath.value ? currentPath.value.split('/') : []);

const isTextFile = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase() || '';
  return ['md','markdown','txt','log','csv','ini','conf','cfg','env','js','ts','jsx','tsx','py','java','c','cpp','h','hpp','go','rs','php','rb','swift','kt','scala','cs','html','css','scss','less','json','xml','yaml','yml','sh','bash','zsh','bat','ps1','dockerfile','makefile','sql'].includes(ext);
};

const loadFiles = async () => {
  loading.value = true;
  try { fileTree.value = await getSkillFiles(skillName, currentPath.value); }
  catch (e) { console.error(e); }
  finally { loading.value = false; }
};

const handleItemClick = async (item: any) => {
  if (item.type === 'directory') {
    currentPath.value = item.path;
    selectedFile.value = null; fileContent.value = null;
    await loadFiles();
  } else { selectFile(item); }
};

const selectFile = async (item: any) => {
  error.value = null; selectedFile.value = item.path; fileContent.value = null;
  if (isTextFile(item.name)) {
    contentLoading.value = true;
    try { fileContent.value = (await readSkillFile(skillName, item.path)).content; }
    catch (e: any) { error.value = e.message || "Failed to load content"; }
    finally { contentLoading.value = false; }
  }
};

const navigateUp = async () => {
  if (!currentPath.value) return;
  const parts = currentPath.value.split('/'); parts.pop();
  currentPath.value = parts.join('/');
  selectedFile.value = null; fileContent.value = null;
  await loadFiles();
};
const navigateToPart = async (index: number) => {
  currentPath.value = pathParts.value.slice(0, index + 1).join('/');
  selectedFile.value = null; fileContent.value = null; await loadFiles();
};
const navigateToRoot = async () => {
  currentPath.value = ""; selectedFile.value = null; fileContent.value = null; await loadFiles();
};
const goBack = () => router.back();

onMounted(loadFiles);
</script>

<style scoped>
.file-item {
  animation: fileFadeIn 0.3s ease-out both;
  animation-delay: var(--delay, 0ms);
}
@keyframes fileFadeIn {
  from { opacity: 0; transform: translateX(-8px); }
  to { opacity: 1; transform: translateX(0); }
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #e0e0e0; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #ccc; }
</style>
