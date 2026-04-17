<template>
  <div class="flex flex-col group/step">
    <!-- Step Header -->
    <div
      class="flex items-start gap-2.5 w-full cursor-pointer group/header transition-all duration-150 rounded-lg py-1.5 px-2 -ml-1 hover:bg-gray-50/80 dark:hover:bg-gray-800/40"
      @click="isExpanded = !isExpanded"
    >
      <!-- Status Icon -->
      <div class="flex-shrink-0 mt-0.5">
        <div v-if="stepContent.status !== 'completed'" class="relative size-4">
          <div class="absolute inset-0 rounded-full border-[1.5px] border-blue-200 dark:border-blue-800"></div>
          <div class="absolute inset-0 rounded-full border-[1.5px] border-blue-500 border-t-transparent animate-spin"></div>
        </div>
        <div v-else class="size-4 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shadow-sm shadow-emerald-400/20">
          <CheckIcon :size="9" class="text-white" stroke-width="3" />
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0 flex flex-col gap-0.5">
        <div class="flex items-center justify-between gap-2">
          <div class="font-medium text-[13px] text-gray-600 dark:text-gray-300 markdown-content line-clamp-2 leading-relaxed"
            v-html="stepContent.description ? renderMarkdown(stepContent.description) : ''">
          </div>

          <div class="flex items-center gap-2 flex-shrink-0 opacity-0 group-hover/header:opacity-100 transition-opacity">
            <span class="text-[10px] text-gray-400 dark:text-gray-500 font-mono tabular-nums">
              {{ relativeTime(message.content.timestamp) }}
            </span>
            <ChevronDownIcon
              class="size-3 text-gray-300 dark:text-gray-600 transition-transform duration-200"
              :class="{ 'rotate-180': isExpanded }"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Tools / Sub-content -->
    <div
      class="step-tools flex flex-col gap-1.5 pl-7 overflow-hidden transition-[max-height,opacity] duration-200 ease-in-out"
      :class="{ 'max-h-[10000px] opacity-100 mt-1': isExpanded, 'max-h-0 opacity-0': !isExpanded }"
    >
      <ToolUse v-for="(tool, index) in stepContent.tools" :key="index" :tool="tool" @click="handleToolClick(tool)" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { Message, StepContent, ToolContent } from '../types/message';
import { Check as CheckIcon, ChevronDown as ChevronDownIcon } from 'lucide-vue-next';
import { marked } from 'marked';
import ToolUse from './ToolUse.vue';
import { useRelativeTime } from '../composables/useTime';
import { sanitizeHtml } from '../utils/content';

const props = defineProps<{
  message: Message;
}>();

const emit = defineEmits<{
  (e: 'toolClick', tool: ToolContent): void;
}>();

const stepContent = computed(() => props.message.content as StepContent);
const isExpanded = ref(true);
const { relativeTime } = useRelativeTime();

const renderMarkdown = (text: string) => {
  if (typeof text !== 'string') return '';
  const html = marked(text) as string;
  return sanitizeHtml(html);
};

const handleToolClick = (tool: ToolContent) => {
  emit('toolClick', tool);
};
</script>
