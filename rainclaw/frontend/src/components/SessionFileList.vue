<template>
    <Teleport to="body">
        <Transition name="panel">
            <div v-if="visible" class="fixed inset-0 z-[9999] flex items-center justify-center">
                <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="hideSessionFileList"></div>
                <div class="panel-content relative w-[520px] max-w-[92%] max-h-[85vh] flex flex-col overflow-hidden z-10">
                    <!-- Glass card -->
                    <div class="bg-white/95 dark:bg-[#1a1a1a]/95 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 border border-white/20 dark:border-gray-700/30 flex flex-col h-full" style="max-height: 85vh;">
                        
                        <!-- Header with gradient accent -->
                        <div class="relative px-6 pt-5 pb-4 flex-shrink-0">
                            <div class="absolute top-0 left-6 right-6 h-[2px] rounded-full bg-gradient-to-r from-blue-500 via-red-400 to-amber-400"></div>
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-3">
                                    <div class="size-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-md shadow-blue-500/20">
                                        <svg class="size-4.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" /></svg>
                                    </div>
                                    <div>
                                        <h1 class="text-base font-bold text-[var(--text-primary)]">{{ $t('Session Files') }}</h1>
                                        <p class="text-[10px] text-[var(--text-tertiary)] mt-0.5">{{ files.length }} {{ files.length === 1 ? 'file' : 'files' }}</p>
                                    </div>
                                </div>
                                <button @click="hideSessionFileList"
                                    class="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition-all duration-200 text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] hover:rotate-90">
                                    <X class="size-4.5" />
                                </button>
                            </div>
                        </div>

                        <!-- File list -->
                        <div class="flex-1 min-h-0 overflow-y-auto px-3 pb-4">
                            <div v-if="files.length > 0" class="space-y-1">
                                <div v-for="(file, idx) in files" :key="idx"
                                    class="file-card group flex items-center gap-3 p-3 rounded-2xl cursor-pointer transition-all duration-200 hover:bg-gray-50/80 dark:hover:bg-white/5 border border-transparent hover:border-gray-100 dark:hover:border-gray-800"
                                    :style="{ '--delay': `${idx * 40}ms` }"
                                    @click="showFile(file)">
                                    
                                    <!-- File icon with type-based color -->
                                    <div class="size-11 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm transition-transform duration-200 group-hover:scale-105"
                                        :class="getFileColor(file.filename)">
                                        <component :is="getFileType(file.filename).icon" class="size-5" />
                                    </div>

                                    <!-- File info -->
                                    <div class="flex flex-col flex-1 min-w-0">
                                        <span class="text-sm font-medium text-[var(--text-primary)] truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">{{ file.filename }}</span>
                                        <div class="flex items-center gap-2 mt-0.5">
                                            <span class="text-[10px] text-[var(--text-tertiary)]">{{ formatRelativeTime(parseISODateTime(file.upload_date)) }}</span>
                                            <span v-if="getFileExt(file.filename)" class="text-[9px] px-1.5 py-0.5 rounded-md bg-gray-100 dark:bg-gray-800 text-[var(--text-tertiary)] uppercase font-mono">{{ getFileExt(file.filename) }}</span>
                                        </div>
                                    </div>

                                    <!-- Actions -->
                                    <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button @click.stop="downloadFile(file)"
                                            class="p-2 rounded-xl text-[var(--text-tertiary)] hover:bg-white dark:hover:bg-gray-800 hover:text-blue-500 hover:shadow-sm transition-all duration-200"
                                            :title="$t('Download')">
                                            <Download class="size-4" />
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <!-- Empty state -->
                            <div v-else class="flex flex-col items-center justify-center py-16 gap-4">
                                <div class="size-20 rounded-3xl bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
                                    <svg class="size-9 text-gray-200 dark:text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" /></svg>
                                </div>
                                <div class="text-center">
                                    <p class="text-sm font-medium text-[var(--text-tertiary)]">{{ $t('No files yet') }}</p>
                                    <p class="text-xs text-[var(--text-tertiary)] opacity-60 mt-1">{{ $t('Files created during the task will appear here') }}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<script setup lang="ts">
import { X, Download } from 'lucide-vue-next';
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import type { FileInfo } from '../api/file';
import { triggerAuthenticatedDownload } from '../api/file';
import { getSessionFiles, getSharedSessionFiles } from '../api/agent';
import { formatRelativeTime, parseISODateTime } from '../utils/time';
import { getFileType } from '../utils/fileType';
import { useSessionFileList } from '../composables/useSessionFileList';
import { useFilePanel } from '../composables/useFilePanel';

const route = useRoute();
const files = ref<FileInfo[]>([]);
const { showFilePanel } = useFilePanel();
const { visible, hideSessionFileList, shared } = useSessionFileList();

const getFileExt = (name: string) => {
    const parts = name.split('.');
    return parts.length > 1 ? parts.pop() : '';
};

const getFileColor = (name: string) => {
    const ext = getFileExt(name)?.toLowerCase() || '';
    if (['py', 'js', 'ts', 'jsx', 'tsx', 'vue'].includes(ext)) return 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400';
    if (['md', 'txt', 'log', 'csv'].includes(ext)) return 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400';
    if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'].includes(ext)) return 'bg-violet-50 dark:bg-violet-900/20 text-violet-600 dark:text-violet-400';
    if (['pdf', 'doc', 'docx', 'ppt', 'pptx'].includes(ext)) return 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400';
    if (['json', 'xml', 'yaml', 'yml'].includes(ext)) return 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400';
    if (['html', 'css', 'scss'].includes(ext)) return 'bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400';
    return 'bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400';
};

const fetchFiles = async (sessionId: string) => {
    if (!sessionId) return;
    files.value = shared.value ? await getSharedSessionFiles(sessionId) : await getSessionFiles(sessionId);
};

const downloadFile = async (fileInfo: FileInfo) => { try { await triggerAuthenticatedDownload(fileInfo); } catch (err) { console.error('Download failed:', err); } };
const showFile = (file: FileInfo) => { showFilePanel(file); hideSessionFileList(); };

watch(visible, (v) => {
    if (v) {
        const sessionId = route.params.sessionId as string;
        if (sessionId) fetchFiles(sessionId);
    }
});
</script>

<style scoped>
.panel-enter-active { transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
.panel-leave-active { transition: all 0.2s ease-in; }
.panel-enter-from { opacity: 0; }
.panel-leave-to { opacity: 0; }
.panel-enter-from .panel-content { transform: scale(0.92) translateY(20px); opacity: 0; }
.panel-leave-to .panel-content { transform: scale(0.95) translateY(10px); opacity: 0; }
.panel-content { transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s ease; }

.file-card {
    animation: fileSlideIn 0.3s ease-out both;
    animation-delay: var(--delay, 0ms);
}
@keyframes fileSlideIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
