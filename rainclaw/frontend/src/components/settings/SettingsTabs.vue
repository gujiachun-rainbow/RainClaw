<template>
  <div class="flex flex-col md:flex-row h-[580px] md:h-[672px] max-h-[90vh]">
    <!-- Tab Sidebar -->
    <div class="md:w-[230px] overflow-x-auto md:overflow-x-visible border-r border-gray-100 dark:border-gray-800 pb-2 md:pb-0 relative bg-gradient-to-b from-gray-50/80 to-white dark:from-gray-900/80 dark:to-gray-800">
      <!-- Logo Area -->
      <div class="items-center hidden px-5 pt-5 pb-4 md:flex">
        <div class="flex items-center gap-2">
          <div class="w-[30px] h-[30px]">
             <RobotAvatar :interactive="false" />
          </div>
          <RainClawLogoTextIcon width="69.47368421052632" height="30" />
        </div>
      </div>

      <!-- Mobile Title -->
      <h3 class="block md:hidden self-stretch pt-4 px-4 pb-2 text-lg font-bold text-gray-800 dark:text-gray-100 sticky left-0">
        {{ t('Settings') }}
      </h3>

      <!-- Tab Buttons -->
      <div class="relative flex w-full max-md:pe-3">
        <div class="flex-1 flex-shrink-0 flex items-start self-stretch px-3 overflow-auto w-max md:w-full border-b border-gray-100 dark:border-gray-800 md:border-b-0 md:flex-col md:gap-1 md:px-2.5 max-md:gap-2">
          <div class="flex md:gap-1 gap-2 md:flex-col items-start self-stretch">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="setActiveTab(tab.id)"
              class="flex px-1 py-2 items-center text-sm max-md:whitespace-nowrap md:h-9 md:gap-2.5 md:self-stretch md:px-3 md:rounded-xl transition-all duration-200"
              :class="activeTab === tab.id
                ? 'md:bg-white dark:md:bg-gray-700 md:shadow-sm md:border md:border-gray-200/60 dark:md:border-gray-600/40 font-semibold text-gray-800 dark:text-gray-100 max-md:border-b-2 max-md:border-blue-500'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 md:hover:bg-white/50 dark:md:hover:bg-gray-700/50'">
              <span class="hidden md:flex items-center justify-center size-5 rounded-lg transition-colors"
                :class="activeTab === tab.id
                  ? 'text-blue-500'
                  : 'text-gray-400 dark:text-gray-500'">
                <component :is="tab.icon" class="size-4" />
              </span>
              <span class="truncate text-[13px]">{{ t(tab.label) }}</span>
            </button>
          </div>
          <div class="hidden md:block self-stretch px-3 py-2">
            <div class="h-px bg-gradient-to-r from-transparent via-gray-200 dark:via-gray-700 to-transparent"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab Content -->
    <div class="flex flex-col items-start self-stretch flex-1 overflow-hidden bg-white dark:bg-gray-900">
      <!-- Content Header -->
      <div class="gap-2 items-center px-6 py-5 hidden md:flex self-stretch border-b border-gray-100 dark:border-gray-800">
        <button
          v-if="currentSubPage"
          @click="handleBack"
          class="size-8 rounded-lg flex items-center justify-center hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors mr-1 cursor-pointer">
          <ChevronLeft :size="20" class="text-gray-400" />
        </button>
        <h3 class="text-lg font-bold text-gray-800 dark:text-gray-100">
          {{ activeTabTitle }}
        </h3>
      </div>

      <!-- Content Area -->
      <div class="flex-1 self-stretch items-start overflow-y-auto flex flex-col gap-8 px-4 pt-5 pb-4 md:px-6 md:pt-5">
        <slot :name="currentSlotName" :active-tab="activeTab" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ChevronLeft } from 'lucide-vue-next'
import RainClawLogoTextIcon from '@/components/icons/RainClawLogoTextIcon.vue'
import RobotAvatar from '@/components/icons/RobotAvatar.vue'

export interface TabItem {
  id: string
  label: string
  icon: any
}

export interface SubPageConfig {
  id: string
  title: string
  parentTabId?: string
}

interface Props {
  tabs: TabItem[]
  defaultTab?: string
  currentSubPage?: string | null
  subPageConfigs?: SubPageConfig[]
}

const props = withDefaults(defineProps<Props>(), {
  defaultTab: undefined,
  currentSubPage: null,
  subPageConfigs: () => []
})

const emit = defineEmits<{
  tabChange: [tabId: string]
  navigateToProfile: []
  back: []
}>()

const { t } = useI18n()

// Active tab state
const activeTab = ref<string>(props.defaultTab || props.tabs[0]?.id || '')

watch(
  () => props.defaultTab,
  (nextTab) => {
    if (!nextTab) {
      return
    }
    const exists = props.tabs.some(tab => tab.id === nextTab)
    if (exists && activeTab.value !== nextTab) {
      activeTab.value = nextTab
    }
  }
)

// Computed active tab title
const activeTabTitle = computed(() => {
  // Show sub-page title if in sub-page
  if (props.currentSubPage) {
    const subPageConfig = props.subPageConfigs.find(config => config.id === props.currentSubPage)
    if (subPageConfig) {
      return t(subPageConfig.title)
    }
  }
  
  const currentTab = props.tabs.find(tab => tab.id === activeTab.value)
  return currentTab ? t(currentTab.label) : ''
})

// Computed slot name based on current view
const currentSlotName = computed(() => {
  if (props.currentSubPage) {
    const subPageConfig = props.subPageConfigs.find(config => config.id === props.currentSubPage)
    if (subPageConfig && subPageConfig.parentTabId) {
      return `${subPageConfig.parentTabId}-${props.currentSubPage}`
    }
    return props.currentSubPage
  }
  return activeTab.value
})

// Set active tab
const setActiveTab = (tabId: string) => {
  activeTab.value = tabId
  emit('tabChange', tabId)
}

// Handle back button click
const handleBack = () => {
  emit('back')
}

// Expose active tab for parent component
defineExpose({
  activeTab
})
</script>
