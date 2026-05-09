<template>
  <div class="flex flex-col gap-6 py-2 px-1">
    <div v-if="adminLoading" class="flex justify-center py-12">
      <Loader2 class="size-8 animate-spin text-gray-300" />
    </div>

    <div v-else class="flex flex-col gap-6">
      <!-- Description -->
      <div class="p-4 bg-gradient-to-br from-amber-50/60 to-orange-50/40 dark:from-amber-900/20 dark:to-orange-900/15 border border-amber-100/60 dark:border-amber-800/30 rounded-2xl">
        <div class="flex items-start gap-3">
          <div class="size-9 rounded-xl bg-gradient-to-br from-amber-100 to-orange-100 dark:from-amber-900/50 dark:to-orange-900/50 flex items-center justify-center flex-shrink-0">
            <Database class="size-4.5 text-amber-600 dark:text-amber-400" />
          </div>
          <div class="flex-1 min-w-0">
            <span class="text-sm font-bold text-gray-700 dark:text-gray-200">{{ t('Admin Memory Desc Title') }}</span>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1 leading-relaxed">{{ t('Admin Memory Desc') }}</p>
          </div>
        </div>
      </div>

      <!-- Entry groups by category -->
      <div v-for="(group, cat) in adminEntriesByCategory" :key="cat" class="flex flex-col gap-3">
        <h3 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider px-1 flex items-center gap-2">
          <component :is="cat === 'preferences' ? User : cat === 'patterns' ? Sparkles : cat === 'notes' ? BookOpen : Database" class="size-3.5" />
          {{ adminCategoryLabel(cat) }}
          <span class="h-px flex-1 bg-gradient-to-r from-amber-200 dark:from-amber-800 to-transparent"></span>
        </h3>

        <div class="flex flex-col gap-2">
          <!-- Existing entries -->
          <div v-for="entry in group" :key="entry.id" class="group flex items-start gap-2">
            <div class="flex-1 relative">
              <textarea
                v-model="entry.editContent"
                rows="1"
                class="w-full px-3.5 py-2.5 bg-white dark:bg-gray-800/50 border border-amber-200/60 dark:border-amber-700/50 rounded-xl text-sm text-gray-700 dark:text-gray-200 leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-400 dark:focus:border-amber-500 transition-all placeholder:text-gray-300 dark:placeholder:text-gray-600"
                :placeholder="t('Memory Item Placeholder')"
                @input="autoResize($event)"
                @focus="autoResize($event)"
              />
            </div>
            <!-- Save button (only visible when content changed) -->
            <button
              v-if="entry.editContent !== entry.content"
              :disabled="entry.saving"
              class="mt-2 size-7 rounded-lg flex items-center justify-center bg-amber-100 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400 hover:bg-amber-200 dark:hover:bg-amber-800/60 transition-all flex-shrink-0 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              @click="saveAdminEntry(entry)"
            >
              <Loader2 v-if="entry.saving" :size="14" class="animate-spin" />
              <Check v-else :size="14" />
            </button>
            <!-- Delete button -->
            <button
              :disabled="entry.saving"
              class="mt-2 size-7 rounded-lg flex items-center justify-center text-gray-300 dark:text-gray-600 opacity-0 group-hover:opacity-100 hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all flex-shrink-0 cursor-pointer disabled:opacity-30"
              @click="deleteAdminEntry(entry)"
            >
              <Trash2 :size="14" />
            </button>
          </div>

          <!-- Add entry button -->
          <button
            class="flex items-center gap-2 px-3.5 py-2.5 border border-dashed border-amber-200/60 dark:border-amber-700/50 rounded-xl text-xs text-amber-400 dark:text-amber-500 hover:text-amber-500 hover:border-amber-300 dark:hover:border-amber-600 hover:bg-amber-50/50 dark:hover:bg-amber-900/10 transition-all cursor-pointer"
            @click="addAdminEntry(cat)"
          >
            <Plus :size="14" />
            {{ t('Add Entry') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { Loader2, Plus, Check, Trash2, User, Sparkles, BookOpen, Database } from 'lucide-vue-next';
import { listAdminMemory, createAdminMemory, updateAdminMemory, deleteAdminMemory } from '@/api/memory';
import { showSuccessToast, showErrorToast } from '@/utils/toast';

const { t } = useI18n();

const ADMIN_CATEGORIES = ['preferences', 'patterns', 'notes', 'custom'];

const adminCategoryLabel = (cat: string) => {
  const labels: Record<string, string> = {
    preferences: t('User Preferences'),
    patterns: t('General Patterns'),
    notes: t('Notes'),
    custom: 'Custom',
  };
  return labels[cat] || cat;
};

interface AdminEntryVM {
  id: string;
  category: string;
  content: string;
  editContent: string;
  scope: string[] | null;
  created_by: string;
  created_at: number;
  updated_at: number;
  saving: boolean;
  _isNew: boolean;
}

const adminLoading = ref(false);
const adminEntries = ref<AdminEntryVM[]>([]);

const adminEntriesByCategory = computed(() => {
  const groups: Record<string, AdminEntryVM[]> = {};
  for (const cat of ADMIN_CATEGORIES) {
    groups[cat] = [];
  }
  for (const entry of adminEntries.value) {
    groups[entry.category]?.push(entry);
  }
  return groups;
});

const fetchAdminMemory = async () => {
  adminLoading.value = true;
  try {
    const data = await listAdminMemory();
    adminEntries.value = (data.entries || []).map((e) => ({
      ...e,
      editContent: e.content,
      saving: false,
      _isNew: false,
    }));
  } catch (err: any) {
    console.error(err);
  } finally {
    adminLoading.value = false;
  }
};

const addAdminEntry = (category: string) => {
  const entry: AdminEntryVM = {
    id: `temp_${Date.now()}`,
    category,
    content: '',
    editContent: '',
    scope: null,
    created_by: '',
    created_at: 0,
    updated_at: 0,
    saving: false,
    _isNew: true,
  };
  adminEntries.value.push(entry);
  nextTick(() => {
    const container = document.querySelector('.admin-memory-section');
    if (container) {
      const textareas = container.querySelectorAll<HTMLTextAreaElement>('textarea');
      textareas[textareas.length - 1]?.focus();
    }
  });
};

const saveAdminEntry = async (entry: AdminEntryVM) => {
  if (entry.editContent === entry.content || entry.saving) return;
  entry.saving = true;
  try {
    if (entry._isNew) {
      // New entry: create in MongoDB, then update local state with real data
      const data = await createAdminMemory({ category: entry.category, content: entry.editContent });
      entry.id = data.entry.id;
      entry.content = data.entry.content;
      entry.created_by = data.entry.created_by;
      entry.created_at = data.entry.created_at;
      entry.updated_at = data.entry.updated_at;
      entry._isNew = false;
    } else {
      // Existing entry: update in MongoDB
      const data = await updateAdminMemory(entry.id, { content: entry.editContent });
      entry.content = data.entry.content;
      entry.updated_at = data.entry.updated_at;
    }
    showSuccessToast(t('Entry saved'));
  } catch (err: any) {
    console.error(err);
    entry.editContent = entry.content;
    showErrorToast(t('Failed to save entry'));
  } finally {
    entry.saving = false;
  }
};

const deleteAdminEntry = async (entry: AdminEntryVM) => {
  if (entry.saving) return;
  if (entry._isNew) {
    // Never persisted, just remove from local array
    const idx = adminEntries.value.indexOf(entry);
    if (idx !== -1) adminEntries.value.splice(idx, 1);
    return;
  }
  entry.saving = true;
  try {
    await deleteAdminMemory(entry.id);
    const idx = adminEntries.value.indexOf(entry);
    if (idx !== -1) adminEntries.value.splice(idx, 1);
    showSuccessToast(t('Entry deleted'));
  } catch (err: any) {
    console.error(err);
    showErrorToast(t('Failed to delete entry'));
  } finally {
    entry.saving = false;
  }
};

function autoResize(event: Event) {
  const el = event.target as HTMLTextAreaElement;
  el.style.height = 'auto';
  el.style.height = el.scrollHeight + 'px';
}

onMounted(() => {
  fetchAdminMemory();
});
</script>
