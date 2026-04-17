<template>
  <div class="flex flex-col w-full my-2">
    <!-- Header / Toggle Button -->
    <div
      @click="toggleCollapse"
      class="flex items-center gap-2.5 px-3.5 py-2 cursor-pointer rounded-xl transition-all duration-200 w-fit select-none group border"
      :class="isRunning
        ? 'bg-gradient-to-r from-blue-50/80 to-indigo-50/60 dark:from-blue-950/30 dark:to-indigo-950/20 border-blue-200/50 dark:border-blue-800/30 shadow-sm shadow-blue-500/5 hover:shadow-md'
        : 'bg-white dark:bg-gray-800/50 border-gray-100 dark:border-gray-700/50 hover:border-gray-200 dark:hover:border-gray-600 hover:shadow-sm'"
    >
      <!-- Running: spinning ring -->
      <div v-if="isRunning" class="relative size-4 flex-shrink-0">
        <div class="absolute inset-0 rounded-full border-2 border-blue-200 dark:border-blue-800"></div>
        <div class="absolute inset-0 rounded-full border-2 border-blue-500 border-t-transparent animate-spin"></div>
      </div>
      <!-- Completed: gradient check -->
      <div v-else class="size-4 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center flex-shrink-0 shadow-sm shadow-emerald-400/30">
        <svg class="size-2.5 text-white" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="2 6.5 5 9.5 10 3"/></svg>
      </div>

      <span class="text-[13px] font-semibold transition-colors"
        :class="isRunning
          ? 'text-blue-600 dark:text-blue-400'
          : 'text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-200'"
      >
        {{ isRunning ? t('Reasoning') + '...' : t('Reasoning completed') }}
      </span>

      <span v-if="toolCount > 0"
        class="text-[10px] font-bold px-2 py-0.5 rounded-full tabular-nums"
        :class="isRunning
          ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-300'
          : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'"
      >
        {{ toolCount }} {{ toolCount === 1 ? t('tool') : t('tools') }}
      </span>

      <ChevronDownIcon
        class="size-3.5 transition-transform duration-300 flex-shrink-0"
        :class="isCollapsed
          ? 'text-gray-300 dark:text-gray-600'
          : 'text-gray-400 dark:text-gray-500 rotate-180'"
      />
    </div>

    <!-- Collapsible Content -->
    <div class="process-collapse relative ml-2 pl-4" :class="isCollapsed ? 'collapsed' : 'expanded'">
      <!-- Gradient left line -->
      <div class="absolute left-0 top-0 bottom-0 w-0.5 rounded-full"
        :class="isRunning
          ? 'bg-gradient-to-b from-blue-400 via-indigo-400 to-purple-400'
          : 'bg-gradient-to-b from-gray-200 via-gray-100 to-transparent dark:from-gray-700 dark:via-gray-800 dark:to-transparent'">
      </div>

      <div class="flex flex-col gap-2.5 py-2">
        <!-- Thinking message -->
        <div v-if="thinkingContent"
          class="flex items-start gap-2 text-xs text-gray-600 dark:text-gray-300 bg-gradient-to-r from-amber-50/80 to-orange-50/40 dark:from-amber-950/20 dark:to-orange-950/10 px-3 py-2.5 rounded-xl border border-amber-200/40 dark:border-amber-800/20">
          <span class="flex-shrink-0 mt-0.5 text-amber-400">
            <Lightbulb :size="14" />
          </span>
          <span class="whitespace-pre-wrap leading-relaxed">{{ thinkingContent?.replace(/\n{3,}/g, '\n\n').trim() }}</span>
        </div>

        <template v-for="(msg, index) in messages" :key="index">
          <StepMessage v-if="msg.type === 'step'" :message="msg" @toolClick="handleToolClick" />
          <ToolUse v-else-if="msg.type === 'tool'" :tool="msg.content as any" @click="handleToolClick(msg.content as any)" />
        </template>

        <!-- Running Indicator -->
        <div v-if="isRunning" class="flex items-center gap-2 text-xs text-blue-500 dark:text-blue-400 pl-1 py-1">
          <span class="flex gap-0.5">
            <span class="size-1 rounded-full bg-blue-400 animate-bounce" style="animation-delay: 0ms"></span>
            <span class="size-1 rounded-full bg-blue-400 animate-bounce" style="animation-delay: 150ms"></span>
            <span class="size-1 rounded-full bg-blue-400 animate-bounce" style="animation-delay: 300ms"></span>
          </span>
          <span class="font-medium">{{ t('Thinking') }}...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { Message, ToolContent } from '../types/message';
import StepMessage from './StepMessage.vue';
import ToolUse from './ToolUse.vue';
import { ChevronDown as ChevronDownIcon, Lightbulb } from 'lucide-vue-next';

const { t } = useI18n();

const props = defineProps<{
  messages: Message[];
  thinkingContent?: string;
}>();

const emit = defineEmits<{
  (e: 'toolClick', tool: ToolContent): void;
}>();

const isCollapsed = ref(false);

const isRunning = computed(() => {
  const lastMsg = props.messages[props.messages.length - 1];
  if (!lastMsg) return false;
  if (lastMsg.type === 'step') return (lastMsg.content as any).status !== 'completed';
  return false;
});

const toolCount = computed(() => props.messages.filter(msg => msg.type === 'tool').length);

watch(() => props.messages.length, () => { if (isRunning.value) isCollapsed.value = false; });

const toggleCollapse = () => { isCollapsed.value = !isCollapsed.value; };
const handleToolClick = (tool: ToolContent) => { emit('toolClick', tool); };
</script>

<style scoped>
.process-collapse {
  display: grid;
  transition: grid-template-rows 0.35s ease-in-out, opacity 0.25s ease-in-out;
}
.process-collapse.collapsed {
  grid-template-rows: 0fr;
  opacity: 0;
}
.process-collapse.expanded {
  grid-template-rows: 1fr;
  opacity: 1;
  margin-top: 4px;
}
.process-collapse > div {
  overflow: hidden;
}
</style>
