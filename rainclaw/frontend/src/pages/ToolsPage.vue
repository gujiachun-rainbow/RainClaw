<template>
  <div class="flex flex-col h-full w-full overflow-hidden tools-page">
    <!-- Hero Header -->
    <div class="flex-shrink-0 relative overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700"></div>
      <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNCI+PHBhdGggZD0iTTM2IDM0djZoLTZ2LTZoNnptMC0zMHY2aC02VjRoNnoiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-50"></div>
      <div class="relative px-6 py-5">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-xl font-bold text-white flex items-center gap-2">
              <span class="inline-flex items-center justify-center size-8 rounded-lg bg-white/15 backdrop-blur-sm">
                <svg class="size-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
              </span>
              Tools Library
            </h1>
            <p class="text-white/60 text-xs mt-1">{{ activeTab === 'science' ? `${scienceToolsTotal} scientific tools across ${scienceCategories.length} categories` : `${externalTools.length} external tools installed` }}</p>
          </div>
          <div class="flex items-center gap-3">
            <!-- Tab 切换 -->
            <div class="flex items-center bg-white/10 backdrop-blur-sm rounded-lg p-0.5">
              <button 
                v-for="tab in tabs" :key="tab.id"
                @click="activeTab = tab.id"
                class="relative px-3.5 py-1.5 text-xs font-medium rounded-md transition-all duration-300"
                :class="activeTab === tab.id
                  ? 'bg-white text-indigo-700 shadow-lg shadow-white/20'
                  : 'text-white/70 hover:text-white hover:bg-white/10'"
              >
                {{ tab.label }}
                <span v-if="tab.count !== undefined" class="ml-1 text-[10px] tabular-nums">{{ tab.count }}</span>
              </button>
            </div>
            <!-- 搜索 -->
            <div class="relative group">
              <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-white/40 size-4 group-focus-within:text-white/70 transition-colors" />
              <input 
                v-model="searchQuery" type="text" 
                :placeholder="activeTab === 'science' ? 'Search scientific tools...' : 'Search tools...'" 
                class="w-64 bg-white/10 backdrop-blur-sm border border-white/10 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:bg-white/15 focus:border-white/25 focus:ring-1 focus:ring-white/20 transition-all duration-200"
                @input="onSearchInput"
              >
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Science Tools Tab -->
    <div v-if="activeTab === 'science'" class="flex-1 overflow-hidden flex bg-[#f8f9fb] dark:bg-[#111]">
      <!-- Category Sidebar -->
      <div class="w-56 border-r border-[var(--border-light)] bg-white/80 dark:bg-[#1a1a1a]/80 backdrop-blur-sm overflow-y-auto flex-shrink-0">
        <div class="p-2.5 space-y-0.5">
          <button @click="selectedCategory = ''"
            class="w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all duration-200"
            :class="!selectedCategory 
              ? 'bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 text-blue-700 dark:text-blue-300 font-semibold shadow-sm' 
              : 'text-[var(--text-secondary)] hover:bg-gray-50 dark:hover:bg-white/5'">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="size-1.5 rounded-full bg-blue-500"></div>
                <span>All Tools</span>
              </div>
              <span class="text-[10px] tabular-nums font-mono opacity-50">{{ scienceToolsTotal }}</span>
            </div>
          </button>
          <button v-for="cat in scienceCategories" :key="cat.name"
            @click="selectedCategory = cat.name"
            class="w-full text-left px-3 py-2 rounded-xl text-sm transition-all duration-200"
            :class="selectedCategory === cat.name 
              ? 'bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 text-blue-700 dark:text-blue-300 font-semibold shadow-sm' 
              : 'text-[var(--text-secondary)] hover:bg-gray-50 dark:hover:bg-white/5'">
            <div class="flex items-center justify-between">
              <span class="truncate text-xs">{{ (cat as any).name_zh || cat.name }}</span>
              <span class="text-[10px] tabular-nums font-mono opacity-40 flex-shrink-0">{{ cat.count }}</span>
            </div>
          </button>
        </div>
      </div>

      <!-- Tool Grid -->
      <div class="flex-1 overflow-y-auto p-5" ref="gridContainer">
        <!-- Skeleton Loading -->
        <div v-if="scienceLoading" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4 max-w-[1800px] mx-auto">
          <div v-for="i in 12" :key="i" class="rounded-xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-[#1e1e1e] p-4 animate-pulse">
            <div class="flex items-start gap-3 mb-3">
              <div class="size-10 rounded-xl bg-gray-200 dark:bg-gray-700"></div>
              <div class="flex-1 space-y-2"><div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div><div class="h-3 bg-gray-100 dark:bg-gray-800 rounded w-1/2"></div></div>
            </div>
            <div class="space-y-2"><div class="h-3 bg-gray-100 dark:bg-gray-800 rounded"></div><div class="h-3 bg-gray-100 dark:bg-gray-800 rounded w-5/6"></div></div>
          </div>
        </div>

        <!-- Tool Cards -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4 max-w-[1800px] mx-auto">
          <div 
            v-for="(tool, idx) in displayedScienceTools" :key="tool.name"
            class="tool-card group relative rounded-xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-[#1e1e1e] cursor-pointer overflow-hidden"
            :style="{ '--delay': `${Math.min(idx, 20) * 30}ms` }"
            @click="openScienceTool(tool)"
          >
            <!-- Hover glow -->
            <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
              <div class="absolute -inset-px rounded-xl bg-gradient-to-r from-blue-400/20 via-indigo-400/20 to-purple-400/20"></div>
            </div>

            <div class="relative p-4">
              <div class="flex items-start gap-3 mb-2.5">
                <div class="size-10 rounded-xl flex items-center justify-center text-white text-sm font-bold flex-shrink-0 shadow-lg transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3"
                  :style="{ background: getToolGradient(tool.name) }">
                  {{ tool.name.charAt(0) }}
                </div>
                <div class="min-w-0 flex-1">
                  <h3 class="text-sm font-semibold text-[var(--text-primary)] truncate group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-blue-600 group-hover:to-indigo-600 transition-all duration-300">
                    {{ tool.name }}
                  </h3>
                  <span class="inline-block mt-0.5 text-[10px] px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-[var(--text-tertiary)] font-mono">{{ tool.category || 'tool' }}</span>
                </div>
              </div>
              <p class="text-xs text-[var(--text-secondary)] leading-relaxed line-clamp-2 min-h-[2.5rem]">
                {{ tool.description || 'No description available' }}
              </p>
              <div class="mt-3 flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span v-if="paramCount(tool) > 0" class="flex items-center gap-1 text-[10px] text-[var(--text-tertiary)]">
                    <svg class="size-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h7" /></svg>
                    {{ paramCount(tool) }} params
                  </span>
                  <span v-if="tool.has_examples" class="size-1.5 rounded-full bg-green-400" title="Has examples"></span>
                </div>
                <div class="text-[10px] text-blue-500 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-1 group-hover:translate-x-0 flex items-center gap-0.5">
                  Open <svg class="size-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Load more -->
        <div v-if="!scienceLoading && filteredScienceTools.length > displayLimit" class="flex justify-center mt-8 mb-4">
          <button @click="displayLimit += 100"
            class="group px-6 py-2.5 text-sm font-medium text-blue-600 dark:text-blue-400 bg-white dark:bg-[#1e1e1e] rounded-xl border border-blue-200 dark:border-blue-800 hover:border-blue-400 hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-300">
            <span class="flex items-center gap-2">
              Show more
              <span class="text-xs opacity-50">({{ filteredScienceTools.length - displayLimit }} remaining)</span>
              <svg class="size-4 opacity-50 group-hover:translate-y-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" /></svg>
            </span>
          </button>
        </div>

        <!-- Empty State -->
        <div v-if="!scienceLoading && displayedScienceTools.length === 0" class="flex flex-col items-center justify-center py-20 gap-3">
          <div class="size-16 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
            <Search :size="28" class="text-gray-300 dark:text-gray-600" />
          </div>
          <p class="text-sm text-[var(--text-tertiary)]">No tools match "{{ searchQuery }}"</p>
        </div>
      </div>
    </div>

    <!-- External Tools Tab -->
    <div v-else-if="activeTab === 'external'" class="flex-1 overflow-y-auto p-5 bg-[#f8f9fb] dark:bg-[#111]">
      <div v-if="externalTools.length === 0 && !extLoading" class="flex flex-col items-center justify-center h-full text-[var(--text-tertiary)] gap-3">
        <div class="size-16 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
          <Box :size="28" class="text-gray-300 dark:text-gray-600" />
        </div>
        <span class="text-sm">{{ t('No external tools installed') }}</span>
        <p class="text-xs opacity-60">Install tools via Skills or the sandbox CLI</p>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4 max-w-[1800px] mx-auto">
        <div v-for="(tool, idx) in filteredExtTools" :key="tool.name"
          class="tool-card group relative rounded-xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-[#1e1e1e] cursor-pointer overflow-hidden"
          :style="{ '--delay': `${Math.min(idx, 20) * 30}ms` }"
          @click="router.push(`/chat/tools/${tool.name}`)">
          <!-- Hover glow -->
          <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
            <div class="absolute -inset-px rounded-xl bg-gradient-to-r from-emerald-400/20 via-teal-400/20 to-cyan-400/20"></div>
          </div>
          <div class="relative p-4">
            <div class="flex items-start gap-3 mb-2.5">
              <div class="size-10 rounded-xl flex items-center justify-center text-white text-sm font-bold flex-shrink-0 shadow-lg transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3"
                :style="{ background: getToolGradient(tool.name) }">
                {{ tool.name.charAt(0).toUpperCase() }}
              </div>
              <div class="min-w-0 flex-1">
                <h3 class="text-sm font-semibold text-[var(--text-primary)] truncate group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-emerald-600 group-hover:to-teal-600 transition-all duration-300">{{ tool.name }}</h3>
                <span class="inline-block mt-0.5 text-[10px] px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-[var(--text-tertiary)] font-mono">{{ tool.file }}</span>
              </div>
              <div class="flex items-center gap-0.5 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <button @click.stop="handleToggleBlock(tool)" class="p-1.5 rounded-lg transition-colors"
                  :class="tool.blocked ? 'text-amber-500 bg-amber-50 dark:bg-amber-900/20' : 'text-[var(--text-tertiary)] hover:bg-gray-100 dark:hover:bg-gray-800'">
                  <EyeOff v-if="tool.blocked" :size="13" /><Eye v-else :size="13" />
                </button>
                <button @click.stop="confirmDeleteTool(tool)" class="p-1.5 rounded-lg text-[var(--text-tertiary)] hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-900/20 transition-colors">
                  <Trash2 :size="13" />
                </button>
              </div>
            </div>
            <p class="text-xs text-[var(--text-secondary)] leading-relaxed line-clamp-2 min-h-[2.5rem]">{{ tool.description || 'No description' }}</p>
            <div class="mt-3 flex items-center justify-between">
              <span v-if="tool.blocked" class="text-[10px] px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 font-medium">Blocked</span>
              <span v-else class="text-[10px] text-[var(--text-tertiary)]">Custom tool</span>
              <div class="text-[10px] text-emerald-500 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-1 group-hover:translate-x-0 flex items-center gap-0.5">
                Open <svg class="size-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" /></svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Dialog -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="deleteTarget" class="fixed inset-0 z-[9999] flex items-center justify-center">
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="cancelDelete"></div>
          <div class="relative bg-white dark:bg-[#2a2a2a] rounded-2xl shadow-2xl p-6 w-[380px] z-10">
            <div class="flex items-center gap-3 mb-4">
              <div class="size-10 rounded-xl bg-red-50 dark:bg-red-900/20 flex items-center justify-center">
                <Trash2 :size="20" class="text-red-500" />
              </div>
              <div><h3 class="text-sm font-semibold">Delete "{{ deleteTarget.name }}"?</h3><p class="text-xs text-[var(--text-tertiary)]">This action cannot be undone</p></div>
            </div>
            <div class="flex justify-end gap-2">
              <button @click="cancelDelete" class="px-4 py-2 text-sm rounded-lg border border-[var(--border-light)] hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">Cancel</button>
              <button @click="executeDelete" :disabled="deleting" class="px-4 py-2 text-sm rounded-lg bg-red-500 text-white hover:bg-red-600 disabled:opacity-50 transition-all">
                {{ deleting ? 'Deleting...' : 'Delete' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { Search, Eye, EyeOff, Trash2, Box, FileCode } from 'lucide-vue-next';
import { getTools, blockTool, deleteTool as apiDeleteTool } from '../api/agent';
import { listTUTools, TUTool, TUCategory } from '../api/tooluniverse';
import { ExternalToolItem } from '../types/response';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';

const { t, locale } = useI18n();
const router = useRouter();

const tabs = computed(() => [
  { id: 'science', label: 'Science', count: scienceToolsTotal.value },
  { id: 'external', label: 'External', count: externalTools.value.length },
]);
const activeTab = ref('science');
const searchQuery = ref('');
const selectedCategory = ref('');
const displayLimit = ref(100);

const scienceTools = ref<TUTool[]>([]);
const scienceCategories = ref<TUCategory[]>([]);
const scienceToolsTotal = ref(0);
const scienceLoading = ref(false);
const externalTools = ref<ExternalToolItem[]>([]);
const extLoading = ref(false);

const gradientPalette = [
  'linear-gradient(135deg, #6366f1, #8b5cf6)',
  'linear-gradient(135deg, #3b82f6, #6366f1)',
  'linear-gradient(135deg, #06b6d4, #3b82f6)',
  'linear-gradient(135deg, #10b981, #06b6d4)',
  'linear-gradient(135deg, #f59e0b, #ef4444)',
  'linear-gradient(135deg, #ec4899, #8b5cf6)',
  'linear-gradient(135deg, #14b8a6, #22c55e)',
  'linear-gradient(135deg, #f97316, #f59e0b)',
];

const getToolGradient = (name: string) => {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return gradientPalette[Math.abs(hash) % gradientPalette.length];
};

const paramCount = (tool: TUTool) => tool.param_count || 0;

const filteredScienceTools = computed(() => {
  let list = scienceTools.value;
  if (selectedCategory.value) list = list.filter(t => t.category === selectedCategory.value);
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    list = list.filter(t => t.name.toLowerCase().includes(q) || (t.description || '').toLowerCase().includes(q));
  }
  return list;
});

const displayedScienceTools = computed(() => filteredScienceTools.value.slice(0, displayLimit.value));

const filteredExtTools = computed(() => {
  if (!searchQuery.value) return externalTools.value;
  return externalTools.value.filter(t => t.name.toLowerCase().includes(searchQuery.value.toLowerCase()));
});

let searchTimer: ReturnType<typeof setTimeout> | null = null;
const onSearchInput = () => { if (searchTimer) clearTimeout(searchTimer); searchTimer = setTimeout(() => { displayLimit.value = 100; }, 200); };

const openScienceTool = (tool: TUTool) => { router.push(`/chat/science-tools/${encodeURIComponent(tool.name)}`); };

const loadScienceTools = async () => {
  scienceLoading.value = true;
  try {
    const res = await listTUTools();
    scienceTools.value = res.tools;
    scienceToolsTotal.value = res.total;
    const catCounts: Record<string, number> = {};
    const catZh: Record<string, string> = {};
    for (const t of res.tools) {
      const c = t.category || 'other';
      catCounts[c] = (catCounts[c] || 0) + 1;
      if (t.category_zh) catZh[c] = t.category_zh;
    }
    scienceCategories.value = Object.entries(catCounts).sort().map(([name, count]) => ({
      name, count, name_zh: catZh[name] || '',
    }));
  } catch (e) { console.error('Failed to load science tools', e); }
  finally { scienceLoading.value = false; }
};

onMounted(async () => {
  extLoading.value = true;
  const [, extRes] = await Promise.allSettled([loadScienceTools(), getTools()]);
  if (extRes.status === 'fulfilled') externalTools.value = extRes.value;
  extLoading.value = false;
});

watch(selectedCategory, () => { displayLimit.value = 100; });
watch(locale, () => { loadScienceTools(); });

const handleToggleBlock = async (tool: ExternalToolItem) => {
  try { await blockTool(tool.name, !tool.blocked); tool.blocked = !tool.blocked; } catch (e) { console.error(e); }
};
const deleteTarget = ref<ExternalToolItem | null>(null);
const deleting = ref(false);
const confirmDeleteTool = (tool: ExternalToolItem) => { deleteTarget.value = tool; };
const cancelDelete = () => { if (!deleting.value) deleteTarget.value = null; };
const executeDelete = async () => {
  if (!deleteTarget.value) return; deleting.value = true;
  try { await apiDeleteTool(deleteTarget.value.name); externalTools.value = externalTools.value.filter(t => t.name !== deleteTarget.value!.name); deleteTarget.value = null; }
  catch (e) { console.error(e); } finally { deleting.value = false; }
};
</script>

<style scoped>
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

/* Card stagger entry animation */
.tool-card {
  animation: cardFadeIn 0.4s ease-out both;
  animation-delay: var(--delay, 0ms);
}
@keyframes cardFadeIn {
  from { opacity: 0; transform: translateY(12px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

/* Hover lift */
.tool-card:hover { transform: translateY(-2px); box-shadow: 0 12px 28px -8px rgba(0,0,0,0.08), 0 4px 12px -4px rgba(0,0,0,0.04); }

/* Modal transitions */
.modal-enter-active { transition: all 0.25s ease-out; }
.modal-leave-active { transition: all 0.2s ease-in; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from > div:last-child { transform: scale(0.95) translateY(10px); }
.modal-leave-to > div:last-child { transform: scale(0.95) translateY(10px); }

/* Custom scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #e0e0e0; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #ccc; }
</style>
