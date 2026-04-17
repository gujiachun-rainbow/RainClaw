<template>
  <div class="relative">
    <Select v-model="selectedLanguage" @update:modelValue="onLanguageChange">
      <SelectTrigger class="w-[140px] h-[36px] bg-white border border-[var(--border-main)] hover:bg-[var(--background-gray-main)] transition-colors rounded-lg flex items-center gap-2">
        <Globe class="w-4 h-4 text-[var(--text-secondary)]" />
        <SelectValue :placeholder="t('Select language')" class="text-sm font-medium" />
      </SelectTrigger>
      <SelectContent :side-offset="5" class="bg-white border border-[var(--border-main)] shadow-lg rounded-lg">
        <SelectItem
          v-for="option in languageOptions"
          :key="option.value"
          :value="option.value"
          class="cursor-pointer hover:bg-[var(--background-gray-main)] px-3 py-2 text-sm"
        >
          {{ option.label }}
        </SelectItem>
      </SelectContent>
    </Select>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Globe } from 'lucide-vue-next'
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
    // Keep local ref in sync
    selectedLanguage.value = locale
  }
}
</script>
