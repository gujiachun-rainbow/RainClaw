<template>
  <div class="w-full h-full flex flex-col bg-white overflow-hidden">
    <!-- Code / Text Editor -->
    <div v-if="isCode || isText" class="flex-1 h-0 overflow-hidden relative">
      <MonacoEditor
        v-if="content"
        :value="content"
        :filename="fileName"
        :read-only="true"
        theme="vs"
        :minimap="false"
        :word-wrap="'on'"
      />
      <div v-else class="flex items-center justify-center h-full">
         <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    </div>

    <!-- Markdown -->
    <div v-else-if="isMarkdown" class="flex-1 h-0 overflow-y-auto p-8 bg-white">
      <div class="max-w-4xl mx-auto">
        <MarkdownFilePreview v-if="content" :content="content" />
        <div v-else class="flex items-center justify-center h-full">
           <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      </div>
    </div>

    <!-- Image -->
    <div v-else-if="isImage" class="flex-1 h-0 flex items-center justify-center p-4 bg-gray-50 overflow-auto">
      <img :src="downloadUrl" class="max-w-full max-h-full object-contain shadow-sm" />
    </div>

    <!-- PDF -->
    <div v-else-if="isPdf" class="flex-1 h-0 bg-gray-100">
      <iframe :src="downloadUrl" class="w-full h-full border-none" title="PDF Preview"></iframe>
    </div>

    <!-- Unsupported / Download Only -->
    <div v-else class="flex flex-col items-center justify-center h-full text-[var(--text-tertiary)] bg-gray-50 p-6">
       <div class="bg-white p-8 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center max-w-sm w-full">
          <div class="size-16 rounded-full bg-blue-50 flex items-center justify-center mb-4 text-blue-500">
             <FileIcon class="size-8" />
          </div>
          <h3 class="text-lg font-medium text-gray-900 mb-2">{{ fileName }}</h3>
          <p class="text-sm text-gray-500 text-center mb-6">
            This file type cannot be previewed directly.
          </p>
          <a 
            :href="downloadUrl" 
            download
            class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            <Download class="size-4" />
            Download to View
          </a>
       </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { FileText as FileIcon, Download } from 'lucide-vue-next';
import MonacoEditor from './ui/MonacoEditor.vue';
import MarkdownFilePreview from './filePreviews/MarkdownFilePreview.vue';
import { getSkillFileDownloadUrl } from '../api/agent';

const props = defineProps<{
  fileName: string;
  skillName: string;
  path: string; // Relative path in skill
  content?: string | null; // For text based files
}>();

const extension = computed(() => props.fileName.split('.').pop()?.toLowerCase() || '');

const isMarkdown = computed(() => ['md', 'markdown'].includes(extension.value));

const isCode = computed(() => {
  const codeExts = [
    'js', 'ts', 'jsx', 'tsx', 'py', 'pyc', 'java', 'c', 'cpp', 'h', 'hpp', 
    'go', 'rs', 'php', 'rb', 'swift', 'kt', 'kts', 'scala', 'cs', 
    'html', 'css', 'scss', 'less', 'json', 'xml', 'yaml', 'yml', 
    'sh', 'bash', 'zsh', 'bat', 'ps1', 'dockerfile', 'makefile', 'sql'
  ];
  return codeExts.includes(extension.value);
});

const isText = computed(() => {
    return ['txt', 'log', 'csv', 'ini', 'conf', 'cfg', 'env'].includes(extension.value);
});

const isImage = computed(() => ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'ico'].includes(extension.value));

const isPdf = computed(() => ['pdf'].includes(extension.value));

const downloadUrl = computed(() => {
    return getSkillFileDownloadUrl(props.skillName, props.path);
});

</script>
