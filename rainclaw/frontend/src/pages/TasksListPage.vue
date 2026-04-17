<template>
  <div class="flex flex-col h-full w-full overflow-hidden">
    <!-- Header -->
    <div class="flex-shrink-0 px-6 py-5 border-b border-gray-100 dark:border-gray-800 bg-white dark:bg-[#1a1a1a]">
      <div class="flex items-center justify-between max-w-[1200px] mx-auto">
        <div>
          <h1 class="text-xl font-bold text-[var(--text-primary)] flex items-center gap-2.5">
            <span class="inline-flex items-center justify-center size-9 rounded-xl bg-gradient-to-br from-sky-400 to-teal-500 shadow-sm">
              <CalendarClock :size="18" class="text-white" />
            </span>
            {{ t('Scheduled Tasks') }}
          </h1>
          <p class="text-[var(--text-tertiary)] text-sm mt-1 ml-[46px]">{{ t('Manage your automated tasks') }}</p>
        </div>
        <button
          @click="router.push('/chat/tasks/new')"
          class="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-400 to-teal-500 text-white text-sm font-medium hover:shadow-lg hover:shadow-sky-400/25 transition-all duration-200"
        >
          <Plus :size="18" />
          {{ t('New Scheduled Task') }}
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-6 bg-[#f8f9fb] dark:bg-[#111]">
      <div class="max-w-[1200px] mx-auto">
        <!-- Service unavailable -->
        <div v-if="serviceUnavailable" class="flex flex-col items-center justify-center py-20 text-center">
          <div class="size-16 rounded-2xl bg-red-50 dark:bg-red-900/20 flex items-center justify-center mb-4">
            <AlertCircle :size="28" class="text-red-400" />
          </div>
          <p class="text-[var(--text-secondary)] font-medium">{{ t('Task service is not available') }}</p>
          <p class="text-sm text-[var(--text-tertiary)] mt-1">{{ t('Please ensure the task scheduler service is running') }}</p>
        </div>

        <!-- Loading -->
        <div v-else-if="loading" class="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div v-for="i in 4" :key="i" class="rounded-2xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-[#1e1e1e] p-5 animate-pulse">
            <div class="flex items-center gap-3 mb-4">
              <div class="h-5 bg-gray-200 dark:bg-gray-700 rounded-lg w-1/3"></div>
              <div class="h-5 bg-gray-200 dark:bg-gray-700 rounded-full w-14"></div>
            </div>
            <div class="grid grid-cols-2 gap-3 mb-4">
              <div class="h-4 bg-gray-100 dark:bg-gray-800 rounded w-full"></div>
              <div class="h-4 bg-gray-100 dark:bg-gray-800 rounded w-3/4"></div>
              <div class="h-4 bg-gray-100 dark:bg-gray-800 rounded w-2/3"></div>
              <div class="h-4 bg-gray-100 dark:bg-gray-800 rounded w-1/2"></div>
            </div>
            <div class="flex gap-1 mb-4">
              <div v-for="j in 7" :key="j" class="h-6 w-4 bg-gray-100 dark:bg-gray-800 rounded"></div>
            </div>
            <div class="h-8 bg-gray-100 dark:bg-gray-800 rounded-lg w-full"></div>
          </div>
        </div>

        <!-- Empty -->
        <div v-else-if="tasks.length === 0" class="flex flex-col items-center justify-center py-24 text-center">
          <div class="size-20 rounded-2xl bg-sky-50 dark:bg-sky-900/20 flex items-center justify-center mb-5">
            <CalendarClock :size="36" class="text-sky-400" />
          </div>
          <h3 class="text-lg font-semibold text-[var(--text-primary)] mb-1">{{ t('No scheduled tasks yet') }}</h3>
          <p class="text-[var(--text-tertiary)] text-sm mb-6">{{ t('Create a scheduled task to run AI at fixed times') }}</p>
          <button
            @click="router.push('/chat/tasks/new')"
            class="px-6 py-2.5 rounded-xl bg-gradient-to-r from-sky-400 to-teal-500 text-white text-sm font-medium hover:shadow-lg hover:shadow-sky-400/25 transition-all duration-200"
          >
            {{ t('Create first task') }}
          </button>
        </div>

        <!-- Task cards -->
        <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div
            v-for="task in tasks"
            :key="task.id"
            class="group rounded-2xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-[#1e1e1e] overflow-hidden hover:shadow-xl hover:shadow-gray-200/50 dark:hover:shadow-black/20 hover:-translate-y-0.5 transition-all duration-200"
          >
            <!-- Card header: title + status + edit -->
            <div class="px-5 pt-5 pb-3">
              <div class="flex items-center justify-between gap-3">
                <div class="flex items-center gap-2.5 min-w-0 flex-1">
                  <h3 class="text-base font-semibold text-[var(--text-primary)] truncate">{{ task.name }}</h3>
                  <span
                    :class="task.status === 'enabled'
                      ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/20 dark:text-emerald-400'
                      : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'"
                    class="flex-shrink-0 px-2.5 py-0.5 text-xs font-medium rounded-full"
                  >
                    {{ task.status === 'enabled' ? t('Running') : t('Disabled') }}
                  </span>
                </div>
                <button
                  @click="router.push(`/chat/tasks/${task.id}`)"
                  class="flex-shrink-0 p-1.5 rounded-lg text-[var(--text-tertiary)] opacity-0 group-hover:opacity-100 hover:bg-sky-50 dark:hover:bg-sky-900/20 hover:text-sky-600 dark:hover:text-sky-400 transition-all"
                  :title="t('Edit')"
                >
                  <Pencil :size="15" />
                </button>
              </div>

              <!-- Info grid -->
              <div class="grid grid-cols-2 gap-x-4 gap-y-2 mt-3 text-sm">
                <div class="flex items-center gap-1.5 text-[var(--text-tertiary)]">
                  <Clock :size="13" class="flex-shrink-0 text-sky-400" />
                  <span class="truncate">{{ task.schedule_desc || task.crontab }}</span>
                </div>
                <div class="flex items-center gap-1.5 text-[var(--text-tertiary)]">
                  <Globe :size="13" class="flex-shrink-0 text-sky-400" />
                  <span class="truncate">{{ task.webhook_ids?.length ? t('Webhook configured') : t('No webhook') }}</span>
                </div>
                <div class="flex items-center gap-1.5 text-[var(--text-tertiary)]">
                  <Calendar :size="13" class="flex-shrink-0 text-cyan-400" />
                  <span class="truncate">{{ task.next_run || '-' }}</span>
                </div>
                <div class="flex items-center gap-1.5 text-[var(--text-tertiary)]">
                  <Activity :size="13" class="flex-shrink-0 text-cyan-400" />
                  <span>{{ t('Runs') }}: {{ task.total_runs ?? 0 }}</span>
                  <span v-if="task.success_rate" class="text-emerald-500 font-medium ml-1">{{ task.success_rate }}</span>
                </div>
              </div>
            </div>

            <!-- Separator -->
            <div class="border-t border-gray-50 dark:border-gray-800/50"></div>

            <!-- Actions row -->
            <div class="px-5 py-3 flex items-center justify-between">
              <button
                @click="openRuns(task)"
                class="text-sm px-3 py-1.5 rounded-lg text-sky-600 dark:text-sky-400 hover:bg-sky-50 dark:hover:bg-sky-900/20 font-medium transition-colors"
              >
                {{ t('View details') }}
              </button>
              <div class="flex items-center gap-1">
                <button
                  v-if="task.status === 'enabled'"
                  @click="toggleStatus(task)"
                  class="text-xs px-2.5 py-1.5 rounded-lg text-[var(--text-tertiary)] hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-slate-600 dark:hover:text-slate-400 transition-colors"
                >
                  {{ t('Disable') }}
                </button>
                <button
                  v-else
                  @click="toggleStatus(task)"
                  class="text-xs px-2.5 py-1.5 rounded-lg text-[var(--text-tertiary)] hover:bg-emerald-50 dark:hover:bg-emerald-900/20 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
                >
                  {{ t('Enable') }}
                </button>
                <button
                  @click="confirmDelete(task)"
                  class="text-xs px-2.5 py-1.5 rounded-lg text-[var(--text-tertiary)] hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-500 transition-colors"
                >
                  {{ t('Delete') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Run history dialog using Dialog component -->
    <Dialog :open="!!runsDialogTask" @update:open="(v: boolean) => { if (!v) runsDialogTask = null }">
      <DialogContent class="w-[720px]">
        <DialogHeader class="px-6 pt-5 pb-4">
          <DialogTitle class="text-lg font-semibold text-[var(--text-primary)]">
            {{ runsDialogTask?.name }} — {{ t('Run history') }}
          </DialogTitle>
          <DialogDescription class="text-sm text-[var(--text-tertiary)] mt-1">
            {{ t('Total') }} {{ runsTotal }} {{ t('executions') }}
            <span v-if="runsDialogTask?.success_rate" class="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-600 dark:bg-emerald-900/20 dark:text-emerald-400">
              {{ t('Success rate') }} {{ runsDialogTask.success_rate }}
            </span>
          </DialogDescription>
        </DialogHeader>

        <div class="px-6 pb-2 flex items-center justify-between gap-2">
          <div class="flex items-center gap-2 text-sm text-[var(--text-tertiary)]">
            <span>{{ t('Per page') }}</span>
            <select
              v-model.number="runsPageSize"
              @change="fetchRunsPage(1)"
              class="h-8 px-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-[#1e1e1e] text-[var(--text-primary)] text-sm"
            >
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto px-6 max-h-[50vh]">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-[var(--text-tertiary)] border-b border-gray-100 dark:border-gray-800">
                <th class="pb-2.5 font-medium">{{ t('Time') }}</th>
                <th class="pb-2.5 font-medium">{{ t('Status') }}</th>
                <th class="pb-2.5 font-medium text-right">{{ t('Result') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="run in taskRuns" :key="run.id" class="border-b border-gray-50 dark:border-gray-800/50 hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">
                <td class="py-2.5 text-[var(--text-secondary)] tabular-nums">{{ formatTime(run.start_time) }}</td>
                <td class="py-2.5">
                  <span class="inline-flex items-center gap-1.5">
                    <span :class="run.status === 'success' ? 'bg-emerald-500' : 'bg-red-500'" class="size-1.5 rounded-full"></span>
                    <span :class="run.status === 'success' ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'">
                      {{ run.status === 'success' ? t('Success') : t('Failed') }}
                    </span>
                  </span>
                </td>
                <td class="py-2.5 text-right">
                  <template v-if="run.chat_id">
                    <button @click="openRunChat(run)" class="text-sky-600 dark:text-sky-400 hover:underline text-sm mr-2">{{ t('View') }}</button>
                    <button @click="copyRunChatLink(run)" class="text-xs text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]">{{ t('Copy link') }}</button>
                  </template>
                  <template v-else-if="run.result || run.error">
                    <button @click="viewRunResult(run)" class="text-sky-600 dark:text-sky-400 hover:underline text-sm">{{ t('View') }}</button>
                  </template>
                  <span v-else class="text-[var(--text-tertiary)]">-</span>
                </td>
              </tr>
            </tbody>
          </table>
          <p v-if="taskRuns.length === 0 && !runsLoading" class="text-center text-[var(--text-tertiary)] py-10">{{ t('No runs yet') }}</p>
        </div>

        <!-- Pagination -->
        <div v-if="runsTotal > 0" class="px-6 py-3 border-t border-gray-100 dark:border-gray-800 flex items-center justify-center gap-2">
          <button
            :disabled="runsPage <= 1"
            @click="fetchRunsPage(runsPage - 1)"
            class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            {{ t('Previous') }}
          </button>
          <span class="text-sm text-[var(--text-tertiary)] tabular-nums px-2">
            {{ runsPage }} / {{ runsTotalPages }}
          </span>
          <button
            :disabled="runsPage >= runsTotalPages"
            @click="fetchRunsPage(runsPage + 1)"
            class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            {{ t('Next') }}
          </button>
        </div>
      </DialogContent>
    </Dialog>

    <!-- View result dialog -->
    <Dialog :open="resultDialogContent !== null" @update:open="(v: boolean) => { if (!v) resultDialogContent = null }">
      <DialogContent class="w-[600px]">
        <DialogHeader class="px-6 pt-5 pb-4">
          <DialogTitle>{{ t('Result') }}</DialogTitle>
        </DialogHeader>
        <pre class="overflow-auto px-6 pb-6 text-sm whitespace-pre-wrap text-[var(--text-secondary)] max-h-[60vh]">{{ resultDialogContent }}</pre>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { CalendarClock, Pencil, Plus, Clock, Globe, Calendar, Activity, AlertCircle } from 'lucide-vue-next';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { listTasks, updateTask, deleteTask, listTaskRuns } from '@/api/tasks';
import type { Task, TaskRun } from '@/api/tasks';
import { showSuccessToast } from '@/utils/toast';

const { t } = useI18n();
const router = useRouter();
const tasks = ref<Task[]>([]);
const loading = ref(true);
const serviceUnavailable = ref(false);
const runsDialogTask = ref<Task | null>(null);
const taskRuns = ref<TaskRun[]>([]);
const runsTotal = ref(0);
const runsPage = ref(1);
const runsPageSize = ref(20);
const runsLoading = ref(false);
const resultDialogContent = ref<string | null>(null);

const runsTotalPages = computed(() =>
  Math.max(1, Math.ceil(runsTotal.value / runsPageSize.value))
);

const loadTasks = async () => {
  loading.value = true;
  serviceUnavailable.value = false;
  try {
    tasks.value = await listTasks();
  } catch {
    tasks.value = [];
    serviceUnavailable.value = true;
  } finally {
    loading.value = false;
  }
};

const openRuns = async (task: Task) => {
  runsDialogTask.value = task;
  runsPage.value = 1;
  runsPageSize.value = 20;
  await fetchRunsPage(1);
};

const fetchRunsPage = async (page: number) => {
  const task = runsDialogTask.value;
  if (!task) return;
  runsLoading.value = true;
  try {
    const { items, total } = await listTaskRuns(task.id, page, runsPageSize.value);
    taskRuns.value = items;
    runsTotal.value = total;
    runsPage.value = page;
  } catch {
    taskRuns.value = [];
    runsTotal.value = 0;
  } finally {
    runsLoading.value = false;
  }
};

const displayTimezone = (import.meta as any).env?.VITE_DISPLAY_TIMEZONE || 'Asia/Shanghai';
const formatTime = (iso?: string) => {
  if (!iso) return '-';
  try {
    let s = String(iso).trim();
    if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(s) && !/Z|[+-]\d{2}:?\d{2}$/.test(s)) {
      s = s.replace(/\.\d{3}$/, '') + 'Z';
    }
    const d = new Date(s);
    if (Number.isNaN(d.getTime())) return iso;
    return new Intl.DateTimeFormat(undefined, {
      timeZone: displayTimezone,
      dateStyle: 'short',
      timeStyle: 'medium',
    }).format(d);
  } catch {
    return iso;
  }
};

function getChatSessionUrl(chatId: string): string {
  const base = ((import.meta as any).env?.BASE_URL ?? '/').replace(/\/+$/, '') || '';
  const path = ['share', chatId].join('/').replace(/\/+/g, '/');
  const fullPath = base ? `${base}/${path}` : `/${path}`;
  return `${window.location.origin}${fullPath}`;
}

const openRunChat = (run: TaskRun) => {
  if (!run.chat_id) return;
  window.open(getChatSessionUrl(run.chat_id), '_blank', 'noopener,noreferrer');
};

const copyRunChatLink = async (run: TaskRun) => {
  if (!run.chat_id) return;
  const url = getChatSessionUrl(run.chat_id);
  try {
    await navigator.clipboard.writeText(url);
    showSuccessToast(t('Link copied, only visible to you'));
  } catch {
    showSuccessToast(t('Link copied, only visible to you') + ': ' + url);
  }
};

const viewRunResult = (run: TaskRun) => {
  resultDialogContent.value = run.result || run.error || '';
};

const toggleStatus = async (task: Task) => {
  try {
    await updateTask(task.id, { status: task.status === 'enabled' ? 'disabled' : 'enabled' });
    await loadTasks();
  } catch (e) {
    console.error(e);
  }
};

const confirmDelete = async (task: Task) => {
  if (!window.confirm(t('Are you sure you want to delete this task?'))) return;
  try {
    await deleteTask(task.id);
    await loadTasks();
    if (runsDialogTask.value?.id === task.id) runsDialogTask.value = null;
  } catch (e) {
    console.error(e);
  }
};

onMounted(loadTasks);
</script>
