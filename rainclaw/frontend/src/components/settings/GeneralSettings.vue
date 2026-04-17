<template>
  <div class="flex flex-col gap-6 w-full">
    <!-- Section Header -->
    <h3 class="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider px-1 flex items-center gap-2">
      {{ t('Appearance') }}
      <span class="h-px flex-1 bg-gradient-to-r from-gray-200 dark:from-gray-700 to-transparent"></span>
    </h3>

    <div class="flex flex-col gap-4">
      <!-- Theme Selection Card -->
      <div class="p-5 bg-white dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50 rounded-2xl shadow-sm">
        <div class="flex flex-col gap-4">
          <div class="flex items-center gap-2.5">
             <div class="size-8 rounded-lg bg-gradient-to-br from-violet-50 to-purple-50 dark:from-violet-900/30 dark:to-purple-900/30 flex items-center justify-center">
               <Palette class="size-4 text-violet-500" />
             </div>
             <span class="text-sm font-bold text-gray-700 dark:text-gray-200">{{ t('Theme') }}</span>
          </div>

          <div class="grid grid-cols-3 gap-3">
            <button
              v-for="theme in themeOptions"
              :key="theme.value"
              class="relative group flex flex-col items-center gap-2.5 p-4 rounded-xl border-2 transition-all duration-200 cursor-pointer"
              :class="currentTheme === theme.value
                ? 'border-blue-400 dark:border-blue-500 bg-blue-50/60 dark:bg-blue-900/20 shadow-sm shadow-blue-500/10'
                : 'border-gray-100 dark:border-gray-700 hover:border-gray-200 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800'"
              @click="setTheme(theme.value)"
            >
              <div class="size-10 rounded-xl flex items-center justify-center transition-all duration-200"
                :class="currentTheme === theme.value
                  ? 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-md shadow-blue-500/25'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500 group-hover:bg-gray-200 dark:group-hover:bg-gray-600'">
                <component :is="theme.icon" class="size-5" />
              </div>
              <span class="text-xs font-semibold transition-colors"
                :class="currentTheme === theme.value ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'">
                {{ theme.label }}
              </span>

              <div v-if="currentTheme === theme.value" class="absolute top-2.5 right-2.5">
                <div class="size-2 rounded-full bg-blue-500 ring-2 ring-blue-500/20"></div>
              </div>
            </button>
          </div>
        </div>
      </div>

      <!-- Language Selection Card -->
      <div class="p-5 bg-white dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50 rounded-2xl shadow-sm flex items-center justify-between">
         <div class="flex items-center gap-3">
             <div class="size-8 rounded-lg bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-900/30 dark:to-amber-900/30 flex items-center justify-center">
               <Languages class="size-4 text-orange-500" />
             </div>
             <div class="flex flex-col">
                <span class="text-sm font-bold text-gray-700 dark:text-gray-200">{{ t('Language') }}</span>
                <span class="text-xs text-gray-400 dark:text-gray-500">Select your preferred interface language</span>
             </div>
         </div>

         <Select v-model="selectedLanguage" @update:modelValue="onLanguageChange">
          <SelectTrigger class="w-[160px] h-9 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 transition-colors focus:ring-2 focus:ring-blue-500/20 focus:ring-offset-0">
            <SelectValue :placeholder="t('Select language')" />
          </SelectTrigger>
          <SelectContent :side-offset="5" class="rounded-xl">
            <SelectItem
              v-for="option in languageOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Sun, Moon, Monitor, Palette, Languages } from 'lucide-vue-next'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { SelectOption } from '@/types/select'
import { useLocale } from '@/composables/useI18n'
import type { Locale } from '@/locales'

// Use i18n for translations
const { t } = useI18n()

// Use the project's i18n composable
const { currentLocale, setLocale } = useLocale()

// Language selection
const selectedLanguage = ref<Locale>(currentLocale.value)

const languageOptions = computed<SelectOption[]>(() => [
  { value: 'zh', label: t('Simplified Chinese') },
  { value: 'en', label: t('English') },
])

const onLanguageChange = (value: any) => {
  if (value && typeof value === 'string') {
    const locale = value as Locale
    setLocale(locale)
    selectedLanguage.value = locale
  }
}

// Theme Handling
type ThemeMode = 'light' | 'dark' | 'system'
const currentTheme = ref<ThemeMode>('system') // TODO: Persist this

const themeOptions = computed(() => [
  { value: 'light', label: t('Light'), icon: Sun },
  { value: 'dark', label: t('Dark'), icon: Moon },
  { value: 'system', label: t('System'), icon: Monitor },
])

const setTheme = (mode: string) => {
  currentTheme.value = mode as ThemeMode
  const root = window.document.documentElement
  
  if (mode === 'dark') {
    root.classList.add('dark')
  } else if (mode === 'light') {
    root.classList.remove('dark')
  } else {
    // System
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }
  // TODO: Save to localStorage
  localStorage.setItem('theme', mode)
}

// Init theme
const initTheme = () => {
  const saved = localStorage.getItem('theme') as ThemeMode
  if (saved) {
    setTheme(saved)
  } else {
    setTheme('system')
  }
}
initTheme()
</script>
