<template>
  <div class="flex flex-col gap-4 w-full">
    <!-- Description -->
    <p class="text-sm text-[var(--text-tertiary)]">{{ t('Manage webhook notification channels') }}</p>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-8">
      <div class="animate-pulse text-[var(--text-tertiary)]">{{ t('Loading...') }}</div>
    </div>

    <template v-else>
      <!-- Webhook list -->
      <div
        v-for="wh in webhooks"
        :key="wh.id"
        class="w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-[#f8f9fb] dark:bg-[#111] p-4"
      >
        <!-- View mode -->
        <template v-if="editingId !== wh.id">
          <div class="flex items-center justify-between gap-3">
            <div class="flex items-center gap-2.5 min-w-0 flex-1">
              <component :is="typeIcon(wh.type)" :size="16" class="flex-shrink-0" :class="typeColor(wh.type)" />
              <span class="font-medium text-[var(--text-primary)] truncate">{{ wh.name }}</span>
              <span class="text-xs px-2 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700 text-[var(--text-tertiary)]">{{ typeLabel(wh.type) }}</span>
            </div>
            <div class="flex items-center gap-1.5 flex-shrink-0">
              <button @click="handleTest(wh)" :disabled="testingId === wh.id"
                class="text-xs px-2.5 py-1 rounded-lg border border-blue-500 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 disabled:opacity-50 transition-colors">
                {{ testingId === wh.id ? t('Sending...') : t('Test') }}
              </button>
              <button @click="startEdit(wh)" class="p-1.5 rounded-lg text-[var(--text-tertiary)] hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
                <Pencil :size="14" />
              </button>
              <button @click="handleDelete(wh)" class="p-1.5 rounded-lg text-[var(--text-tertiary)] hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-500 transition-colors">
                <Trash2 :size="14" />
              </button>
            </div>
          </div>
          <p class="text-xs text-[var(--text-tertiary)] mt-1.5 truncate">{{ wh.url }}</p>
        </template>

        <!-- Edit mode -->
        <template v-else>
          <div class="space-y-3">
            <div class="flex gap-2">
              <input v-model="editForm.name" type="text" :placeholder="t('Webhook name')"
                class="flex-1 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-[#1e1e1e] text-sm text-[var(--text-primary)] focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500" />
              <select v-model="editForm.type"
                class="px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-[#1e1e1e] text-sm text-[var(--text-primary)] focus:ring-2 focus:ring-blue-500/30">
                <option value="feishu">{{ t('Feishu') }}</option>
                <option value="dingtalk">{{ t('DingTalk') }}</option>
                <option value="wecom">{{ t('WeCom') }}</option>
              </select>
            </div>
            <input v-model="editForm.url" type="url" :placeholder="t('Webhook URL')"
              class="w-full px-3 py-2 rounded-lg border text-sm text-[var(--text-primary)] focus:ring-2 focus:ring-blue-500/30"
              :class="editUrlError ? 'border-red-400 dark:border-red-500 bg-red-50/50 dark:bg-red-900/10' : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-[#1e1e1e] focus:border-blue-500'"
              @input="editUrlError = ''" />
            <p v-if="editUrlError" class="text-xs text-red-500 flex items-center gap-1">
              <AlertTriangle :size="12" /> {{ editUrlError }}
            </p>
            <div class="flex gap-2 justify-end">
              <button @click="cancelEdit(); editUrlError = ''" class="px-3 py-1.5 rounded-lg text-sm text-[var(--text-secondary)] hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
                {{ t('Cancel') }}
              </button>
              <button @click="saveEdit" :disabled="!editForm.name?.trim() || !editForm.url?.trim() || savingEdit"
                class="px-3 py-1.5 rounded-lg text-sm bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-medium disabled:opacity-50 transition-all">
                {{ savingEdit ? t('Saving...') : t('Save') }}
              </button>
            </div>
          </div>
        </template>
      </div>

      <!-- Empty state -->
      <div v-if="webhooks.length === 0 && !showCreateForm" class="text-center py-8">
        <Bell :size="32" class="mx-auto text-[var(--text-tertiary)] mb-3" />
        <p class="text-[var(--text-tertiary)] text-sm">{{ t('No webhooks configured') }}</p>
      </div>

      <!-- Create form -->
      <div v-if="showCreateForm" class="w-full rounded-xl border-2 border-dashed border-blue-300 dark:border-blue-700 bg-blue-50/50 dark:bg-blue-900/10 p-4 space-y-3">
        <p class="text-sm font-medium text-[var(--text-primary)]">{{ t('New webhook') }}</p>
        <div class="flex gap-2">
          <input v-model="createForm.name" type="text" :placeholder="t('Webhook name')"
            class="flex-1 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-[#1e1e1e] text-sm text-[var(--text-primary)] focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500" />
          <select v-model="createForm.type"
            class="px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-[#1e1e1e] text-sm text-[var(--text-primary)] focus:ring-2 focus:ring-blue-500/30">
            <option value="feishu">{{ t('Feishu') }}</option>
            <option value="dingtalk">{{ t('DingTalk') }}</option>
            <option value="wecom">{{ t('WeCom') }}</option>
          </select>
        </div>
        <input v-model="createForm.url" type="url" :placeholder="t('Webhook URL')"
          class="w-full px-3 py-2 rounded-lg border text-sm text-[var(--text-primary)] focus:ring-2 focus:ring-blue-500/30"
          :class="createUrlError ? 'border-red-400 dark:border-red-500 bg-red-50/50 dark:bg-red-900/10' : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-[#1e1e1e] focus:border-blue-500'"
          @input="createUrlError = ''" />
        <p v-if="createUrlError" class="text-xs text-red-500 flex items-center gap-1">
          <AlertTriangle :size="12" /> {{ createUrlError }}
        </p>
        <div class="flex gap-2 justify-end">
          <button @click="showCreateForm = false; createUrlError = ''" class="px-3 py-1.5 rounded-lg text-sm text-[var(--text-secondary)] hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
            {{ t('Cancel') }}
          </button>
          <button @click="handleCreate" :disabled="!createForm.name?.trim() || !createForm.url?.trim() || creating"
            class="px-3 py-1.5 rounded-lg text-sm bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-medium disabled:opacity-50 transition-all">
            {{ creating ? t('Creating...') : t('Create') }}
          </button>
        </div>
      </div>

      <!-- Add button -->
      <button @click="showCreateForm = true" v-if="!showCreateForm"
        class="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-dashed border-gray-300 dark:border-gray-600 text-[var(--text-secondary)] hover:border-blue-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors text-sm">
        <Plus :size="16" />
        {{ t('Add webhook') }}
      </button>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, markRaw } from 'vue';
import { useI18n } from 'vue-i18n';
import { Pencil, Trash2, Plus, Bell, MessageSquare, Send, AlertTriangle } from 'lucide-vue-next';
import { listWebhooks, createWebhook, updateWebhook, deleteWebhook, testWebhook } from '@/api/webhooks';
import type { Webhook } from '@/api/webhooks';
import { showSuccessToast, showErrorToast } from '@/utils/toast';

const { t } = useI18n();
const webhooks = ref<Webhook[]>([]);
const loading = ref(true);
const showCreateForm = ref(false);
const creating = ref(false);
const editingId = ref<string | null>(null);
const savingEdit = ref(false);
const testingId = ref<string | null>(null);

const createForm = ref({ name: '', type: 'feishu', url: '' });
const editForm = ref({ name: '', type: 'feishu', url: '' });
const createUrlError = ref('');
const editUrlError = ref('');

function detectTypeFromUrl(url: string): string | null {
  if (!url) return null;
  try {
    const host = new URL(url).hostname;
    if (host.includes('feishu.cn') || host.includes('larksuite.com')) return 'feishu';
    if (host.includes('dingtalk.com') || host.includes('dingtalk.cn')) return 'dingtalk';
    if (host.includes('weixin.qq.com') || host.includes('qyapi.weixin.qq.com')) return 'wecom';
  } catch { /* invalid URL */ }
  return null;
}

const TYPE_NAMES: Record<string, string> = { feishu: '飞书', dingtalk: '钉钉', wecom: '企微' };

function validateUrlType(url: string, selectedType: string): string {
  const detected = detectTypeFromUrl(url);
  if (detected && detected !== selectedType) {
    return t('URL type mismatch', { detected: TYPE_NAMES[detected] || detected, selected: TYPE_NAMES[selectedType] || selectedType });
  }
  return '';
}

const TYPE_LABELS: Record<string, string> = { feishu: '飞书', dingtalk: '钉钉', wecom: '企微' };
const typeLabel = (t: string) => TYPE_LABELS[t] || t;
const typeColor = (t: string) => t === 'feishu' ? 'text-blue-500' : t === 'dingtalk' ? 'text-sky-500' : 'text-green-500';
const typeIcon = (_t: string) => markRaw(MessageSquare);

async function loadWebhooks() {
  loading.value = true;
  try {
    webhooks.value = await listWebhooks();
  } catch { webhooks.value = []; }
  finally { loading.value = false; }
}

async function handleCreate() {
  createUrlError.value = validateUrlType(createForm.value.url, createForm.value.type);
  if (createUrlError.value) return;
  creating.value = true;
  try {
    await createWebhook(createForm.value);
    showCreateForm.value = false;
    createForm.value = { name: '', type: 'feishu', url: '' };
    createUrlError.value = '';
    await loadWebhooks();
    showSuccessToast(t('Webhook created'));
  } catch (e: any) {
    showErrorToast(e?.response?.data?.detail || t('Create failed'));
  } finally { creating.value = false; }
}

function startEdit(wh: Webhook) {
  editingId.value = wh.id;
  editForm.value = { name: wh.name, type: wh.type, url: wh.url };
}

function cancelEdit() {
  editingId.value = null;
}

async function saveEdit() {
  if (!editingId.value) return;
  editUrlError.value = validateUrlType(editForm.value.url, editForm.value.type);
  if (editUrlError.value) return;
  savingEdit.value = true;
  try {
    await updateWebhook(editingId.value, editForm.value);
    editingId.value = null;
    editUrlError.value = '';
    await loadWebhooks();
    showSuccessToast(t('Webhook updated'));
  } catch (e: any) {
    showErrorToast(e?.response?.data?.detail || t('Save failed'));
  } finally { savingEdit.value = false; }
}

async function handleDelete(wh: Webhook) {
  if (!window.confirm(t('Are you sure you want to delete this webhook?'))) return;
  try {
    await deleteWebhook(wh.id);
    await loadWebhooks();
    showSuccessToast(t('Webhook deleted'));
  } catch (e: any) {
    showErrorToast(e?.response?.data?.detail || t('Delete failed'));
  }
}

async function handleTest(wh: Webhook) {
  testingId.value = wh.id;
  try {
    const res = await testWebhook(wh.id);
    showSuccessToast(res.message || t('Test message sent'));
  } catch (e: any) {
    showErrorToast(e?.response?.data?.detail || t('Test failed'));
  } finally { testingId.value = null; }
}

defineExpose({ loadWebhooks });

onMounted(loadWebhooks);
</script>
