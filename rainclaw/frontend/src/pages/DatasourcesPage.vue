<template>
  <div class="flex flex-col h-full w-full overflow-hidden bg-[#f8f9fb] dark:bg-[#111]">

    <!-- ====== Header ====== -->
    <div class="flex-shrink-0 px-6 py-4 border-b border-gray-100 dark:border-gray-800 bg-white dark:bg-[#1a1a1a]">
      <div class="flex items-center justify-between">
        <h1 class="text-lg font-bold text-[var(--text-primary)]">{{ t('Datasource Management') }}</h1>
        <button @click="openCreateModal"
          class="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-br from-sky-400 to-teal-500 text-white text-sm font-medium hover:shadow-lg hover:shadow-sky-400/25 transition-all">
          <Plus :size="16" />
          {{ t('New Datasource') }}
        </button>
      </div>
    </div>

    <!-- ====== Search bar ====== -->
    <div class="flex-shrink-0 px-6 py-3 bg-white dark:bg-[#1a1a1a] border-b border-gray-100 dark:border-gray-800">
      <div class="flex items-center gap-3">
        <div class="relative flex-1 max-w-xs">
          <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)] pointer-events-none" />
          <input v-model="searchQuery" type="text" @keyup.enter="handleSearch"
            class="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-[#f8f9fb] dark:bg-[#111] text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-sky-500/30 focus:border-sky-500 transition-colors"
            :placeholder="t('Search datasource name...')" />
        </div>
        <button @click="handleSearch"
          class="px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-600 text-white text-sm font-medium transition-colors">
          {{ t('Query') }}
        </button>
        <button @click="handleReset"
          class="px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 text-sm text-[var(--text-secondary)] hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
          {{ t('Reset') }}
        </button>
      </div>
    </div>

    <!-- ====== Content area ====== -->
    <div class="flex-1 overflow-auto p-6">

      <!-- Loading state -->
      <div v-if="loading" class="flex items-center justify-center py-20">
        <div class="animate-pulse text-[var(--text-tertiary)] text-sm">{{ t('Loading...') }}</div>
      </div>

      <!-- Empty state -->
      <div v-else-if="datasources.length === 0" class="flex flex-col items-center justify-center py-20 text-center">
        <div class="size-16 rounded-2xl bg-sky-50 dark:bg-sky-900/20 flex items-center justify-center mb-4">
          <Database :size="28" class="text-sky-400" />
        </div>
        <h2 class="text-lg font-semibold text-[var(--text-primary)] mb-1">{{ t('No datasources yet') }}</h2>
        <p class="text-sm text-[var(--text-tertiary)] mb-6">{{ t('Click "New Datasource" to create one') }}</p>
        <button @click="openCreateModal"
          class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-br from-sky-400 to-teal-500 text-white text-sm font-medium hover:shadow-lg hover:shadow-sky-400/25 transition-all">
          <Plus :size="16" />
          {{ t('New Datasource') }}
        </button>
      </div>

      <!-- Table -->
      <div v-else class="bg-white dark:bg-[#1a1a1a] rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100 dark:border-gray-800 bg-[#f8f9fb] dark:bg-[#161616]">
              <th class="px-4 py-3 text-left text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider">{{ t('Datasource Name') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider">{{ t('Datasource Code') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider">{{ t('Datasource Type') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider">{{ t('Host') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider">{{ t('Port') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider">{{ t('Username') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider">{{ t('Datasource Password') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider">{{ t('Operation') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
            <tr v-for="ds in datasources" :key="ds.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
              <td class="px-4 py-3 text-sm text-[var(--text-primary)]">{{ ds.name }}</td>
              <td class="px-4 py-3 text-sm text-[var(--text-primary)]"><code class="text-xs bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded">{{ ds.code }}</code></td>
              <td class="px-4 py-3">
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-sky-50 dark:bg-sky-900/20 text-sky-600 dark:text-sky-400">
                  {{ ds.dbType }}
                </span>
              </td>
              <td class="px-4 py-3 text-sm text-[var(--text-secondary)]">{{ ds.host }}</td>
              <td class="px-4 py-3 text-sm text-[var(--text-secondary)]">{{ ds.port }}</td>
              <td class="px-4 py-3 text-sm text-[var(--text-secondary)]">{{ ds.username }}</td>
              <td class="px-4 py-3 text-sm text-[var(--text-secondary)]">
                <div class="flex items-center gap-2">
                  <span class="font-mono">{{ ds.passwordVisible ? ds.password : '***' }}</span>
                  <button @click="togglePassword(ds)" class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors">
                    <Eye v-if="!ds.passwordVisible" :size="14" />
                    <EyeOff v-else :size="14" />
                  </button>
                </div>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-1">
                  <button @click="openEditModal(ds)" class="p-1.5 rounded-lg text-[var(--text-tertiary)] hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-sky-500 transition-colors" :title="t('Edit')">
                    <Pencil :size="15" />
                  </button>
                  <button @click="confirmDelete(ds)" class="p-1.5 rounded-lg text-[var(--text-tertiary)] hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-red-500 transition-colors" :title="t('Delete')">
                    <Trash2 :size="15" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ====== Create/Edit Modal ====== -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="modalVisible" class="fixed inset-0 z-[9999] flex items-center justify-center" @click.self="closeModal">
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeModal"></div>
          <div class="relative w-[560px] max-w-[90vw] max-h-[85vh] bg-white dark:bg-[#1e1e1e] rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col" @click.stop>
            <!-- Modal Header -->
            <header class="flex items-center justify-between px-5 py-3.5 border-b border-gray-100 dark:border-gray-800 flex-shrink-0">
              <span class="text-sm font-semibold text-[var(--text-primary)]">{{ isEdit ? t('Edit Datasource') : t('New Datasource') }}</span>
              <button @click="closeModal" class="p-1.5 rounded-lg text-[var(--text-tertiary)] hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                <X :size="16" />
              </button>
            </header>

            <!-- Modal Body -->
            <div class="flex-1 overflow-y-auto p-5">
              <form @submit.prevent="submitForm">
              <div class="grid grid-cols-2 gap-x-4 gap-y-4">
                <!-- Name -->
                <div class="col-span-1">
                  <label class="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">{{ t('Datasource Name') }}</label>
                  <input v-model="form.name" type="text" required
                    class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-[#f8f9fb] dark:bg-[#111] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-sky-500/30 focus:border-sky-500 transition-colors" />
                </div>
                <!-- Code -->
                <div class="col-span-1">
                  <label class="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">{{ t('Datasource Code') }}</label>
                  <input v-model="form.code" type="text" required
                    class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-[#f8f9fb] dark:bg-[#111] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-sky-500/30 focus:border-sky-500 transition-colors"
                    :placeholder="t('Datasource code unique tip')" />
                </div>
                <!-- Host -->
                <div class="col-span-1">
                  <label class="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">{{ t('Host') }}</label>
                  <input v-model="form.host" type="text" required
                    class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-[#f8f9fb] dark:bg-[#111] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-sky-500/30 focus:border-sky-500 transition-colors" />
                </div>
                <!-- Port -->
                <div class="col-span-1">
                  <label class="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">{{ t('Port') }}</label>
                  <input v-model.number="form.port" type="number" required
                    class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-[#f8f9fb] dark:bg-[#111] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-sky-500/30 focus:border-sky-500 transition-colors" />
                </div>
                <!-- Database Name -->
                <div class="col-span-1">
                  <label class="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">{{ t('Database Name') }}</label>
                  <input v-model="form.databaseName" type="text" required
                    class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-[#f8f9fb] dark:bg-[#111] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-sky-500/30 focus:border-sky-500 transition-colors" />
                </div>
                <!-- Username -->
                <div class="col-span-1">
                  <label class="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">{{ t('Username') }}</label>
                  <input v-model="form.username" type="text" required
                    class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-[#f8f9fb] dark:bg-[#111] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-sky-500/30 focus:border-sky-500 transition-colors" />
                </div>
                <!-- Password -->
                <div class="col-span-1">
                  <label class="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">{{ t('Datasource Password') }}</label>
                  <div class="relative">
                    <input v-model="form.password" :type="formPasswordVisible ? 'text' : 'password'" required
                      class="w-full px-3 py-2 pr-9 rounded-lg border border-gray-200 dark:border-gray-700 bg-[#f8f9fb] dark:bg-[#111] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-sky-500/30 focus:border-sky-500 transition-colors" />
                    <button type="button" @click="formPasswordVisible = !formPasswordVisible"
                      class="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors">
                      <Eye v-if="!formPasswordVisible" :size="14" />
                      <EyeOff v-else :size="14" />
                    </button>
                  </div>
                </div>
                <!-- Database Type -->
                <div class="col-span-2">
                  <label class="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">{{ t('Datasource Type') }}</label>
                  <select v-model="form.dbType" required
                    class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-[#f8f9fb] dark:bg-[#111] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-sky-500/30 focus:border-sky-500 transition-colors">
                    <option value="" disabled>{{ t('Select type') }}</option>
                    <option v-for="t in dbTypes" :key="t" :value="t">{{ t }}</option>
                  </select>
                </div>
              </div>

              <!-- Error message -->
              <div v-if="formError" class="mt-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                <p class="text-sm text-red-600 dark:text-red-400">{{ formError }}</p>
              </div>
              </form>
            </div>

            <!-- Modal Footer -->
            <footer class="flex items-center justify-end gap-3 px-5 py-3.5 border-t border-gray-100 dark:border-gray-800 flex-shrink-0">
              <button @click="closeModal"
                class="px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 text-sm text-[var(--text-secondary)] hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                {{ t('Cancel') }}
              </button>
              <button @click="submitForm" :disabled="submitting"
                class="px-4 py-2 rounded-lg bg-gradient-to-br from-sky-400 to-teal-500 text-white text-sm font-medium hover:shadow-lg hover:shadow-sky-400/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all">
                <span v-if="submitting" class="inline-flex items-center gap-2">
                  <span class="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent"></span>
                  {{ t('Processing...') }}
                </span>
                <span v-else>{{ t('Save') }}</span>
              </button>
            </footer>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ====== Delete Confirmation ====== -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="deleteModalVisible" class="fixed inset-0 z-[9999] flex items-center justify-center" @click.self="deleteModalVisible = false">
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="deleteModalVisible = false"></div>
          <div class="relative w-[400px] max-w-[90vw] bg-white dark:bg-[#1e1e1e] rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 p-6" @click.stop>
            <div class="flex items-center gap-3 mb-4">
              <div class="size-10 rounded-xl bg-red-50 dark:bg-red-900/20 flex items-center justify-center flex-shrink-0">
                <AlertCircle :size="20" class="text-red-500" />
              </div>
              <div>
                <h3 class="text-sm font-semibold text-[var(--text-primary)]">{{ t('Delete Confirm') }}</h3>
                <p class="text-xs text-[var(--text-tertiary)] mt-0.5">{{ t('Delete datasource confirm message') }}</p>
              </div>
            </div>
            <div class="flex items-center justify-end gap-3">
              <button @click="deleteModalVisible = false; deletingId = null"
                class="px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 text-sm text-[var(--text-secondary)] hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                {{ t('Cancel') }}
              </button>
              <button @click="handleDelete" :disabled="deleting"
                class="px-4 py-2 rounded-lg bg-red-500 hover:bg-red-600 text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                <span v-if="deleting" class="inline-flex items-center gap-2">
                  <span class="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent"></span>
                  {{ t('Processing...') }}
                </span>
                <span v-else>{{ t('Delete') }}</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus, Search, Eye, EyeOff, Pencil, Trash2, X, Database, AlertCircle } from 'lucide-vue-next'
import { showSuccessToast, showErrorToast } from '../utils/toast'
import {
  listDatasources,
  createDatasource,
  updateDatasource,
  deleteDatasource,
  type Datasource,
  type CreateDatasourceRequest,
  type UpdateDatasourceRequest,
  type DbType,
} from '../api/datasources'

const { t } = useI18n()

const dbTypes: DbType[] = ['MySQL', 'PostgreSQL', 'Oracle', 'MongoDB', 'SQL Server']

// --- List ---
const datasources = ref<(Datasource & { passwordVisible?: boolean })[]>([])
const loading = ref(false)
const searchQuery = ref('')

async function loadList(name?: string) {
  loading.value = true
  try {
    const list = await listDatasources(name)
    datasources.value = list.map((ds) => ({ ...ds, passwordVisible: false }))
  } catch (e: any) {
    console.error('Failed to load datasources:', e)
    showErrorToast(t('Failed to load datasources'))
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  loadList(searchQuery.value || undefined)
}

function handleReset() {
  searchQuery.value = ''
  loadList()
}

function togglePassword(ds: Datasource & { passwordVisible?: boolean }) {
  ds.passwordVisible = !ds.passwordVisible
}

// --- Create / Edit Modal ---
const modalVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<string | null>(null)
const submitting = ref(false)
const formError = ref('')
const formPasswordVisible = ref(false)

const defaultForm: CreateDatasourceRequest = {
  name: '',
  code: '',
  host: '',
  port: 3306,
  databaseName: '',
  username: '',
  password: '',
  dbType: 'MySQL',
}

const form = ref<CreateDatasourceRequest>({ ...defaultForm })

function openCreateModal() {
  isEdit.value = false
  editingId.value = null
  form.value = { ...defaultForm }
  formError.value = ''
  formPasswordVisible.value = false
  modalVisible.value = true
}

function openEditModal(ds: Datasource) {
  isEdit.value = true
  editingId.value = ds.id
  form.value = {
    name: ds.name,
    code: ds.code,
    host: ds.host,
    port: ds.port,
    databaseName: ds.databaseName,
    username: ds.username,
    password: ds.password,
    dbType: ds.dbType,
  }
  formError.value = ''
  formPasswordVisible.value = true  // 编辑时密码明文回显
  modalVisible.value = true
}

function closeModal() {
  modalVisible.value = false
  formError.value = ''
}

async function submitForm() {
  // 客户端表单校验
  if (!form.value.name || !form.value.code || !form.value.host || !form.value.databaseName || !form.value.username || !form.value.password) {
    formError.value = isEdit.value
      ? t('Failed to update datasource')
      : t('Failed to create datasource')
    submitting.value = false
    return
  }
  if (!form.value.dbType) {
    formError.value = t('Select type')
    submitting.value = false
    return
  }
  const port = Number(form.value.port)
  if (isNaN(port) || port < 1 || port > 65535) {
    formError.value = t('Port must be between 1 and 65535')
    submitting.value = false
    return
  }

  submitting.value = true
  formError.value = ''
  try {
    if (isEdit.value && editingId.value) {
      await updateDatasource(editingId.value, { ...form.value })
      showSuccessToast(t('Datasource updated successfully'))
    } else {
      await createDatasource(form.value)
      showSuccessToast(t('Datasource created successfully'))
    }
    closeModal()
    await loadList(searchQuery.value || undefined)
  } catch (e: any) {
    if (e?.code === 400) {
      formError.value = t('Datasource code unique tip')
    } else {
      formError.value = isEdit.value
        ? t('Failed to update datasource')
        : t('Failed to create datasource')
    }
  } finally {
    submitting.value = false
  }
}

// --- Delete ---
const deleteModalVisible = ref(false)
const deleting = ref(false)
const deletingId = ref<string | null>(null)

function confirmDelete(ds: Datasource) {
  deletingId.value = ds.id
  deleteModalVisible.value = true
}

async function handleDelete() {
  if (!deletingId.value) return
  deleting.value = true
  try {
    await deleteDatasource(deletingId.value)
    showSuccessToast(t('Datasource deleted successfully'))
    deleteModalVisible.value = false
    await loadList(searchQuery.value || undefined)
  } catch {
    showErrorToast(t('Failed to delete datasource'))
  } finally {
    deleting.value = false
    deletingId.value = null
  }
}

// --- Init ---
onMounted(() => {
  loadList()
})
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
