<template>
  <p v-if="tool.name === 'message' && tool.args?.text" class="text-[var(--text-secondary)] text-[14px] overflow-hidden text-ellipsis whitespace-pre-line pl-1">
    {{ tool.args.text }}
  </p>
  <div v-else-if="toolInfo" class="tool-use-card flex items-center group/tool gap-1.5 w-full max-w-full">
    <div
      @click="handleClick"
      class="flex items-center gap-2.5 px-2.5 py-2 rounded-xl transition-all duration-200 cursor-pointer min-w-0 flex-1 border border-transparent hover:border-gray-100 dark:hover:border-gray-700/50 hover:bg-white dark:hover:bg-gray-800/60 hover:shadow-sm"
    >
      <!-- Icon -->
      <div class="flex-shrink-0 size-7 rounded-lg flex items-center justify-center text-sm transition-colors"
        :class="tool.status === 'calling'
          ? 'bg-blue-50 dark:bg-blue-900/30'
          : 'bg-gray-50 dark:bg-gray-800'">
        <span v-if="toolMetaIcon" class="leading-none">{{ toolMetaIcon }}</span>
        <div v-else-if="tool.status === 'calling'" class="relative size-3.5">
          <div class="absolute inset-0 rounded-full border-[1.5px] border-blue-200 dark:border-blue-800"></div>
          <div class="absolute inset-0 rounded-full border-[1.5px] border-blue-500 border-t-transparent animate-spin"></div>
        </div>
        <component :is="toolInfo.icon" :size="13" v-else class="text-gray-400 dark:text-gray-500" />
      </div>

      <!-- Loading spinner when calling (alongside emoji icon) -->
      <div v-if="tool.status === 'calling' && toolMetaIcon" class="relative size-3 flex-shrink-0">
        <div class="absolute inset-0 rounded-full border-[1.5px] border-blue-200 dark:border-blue-800"></div>
        <div class="absolute inset-0 rounded-full border-[1.5px] border-blue-500 border-t-transparent animate-spin"></div>
      </div>

      <!-- Content -->
      <div class="flex items-center gap-2 min-w-0 flex-1 text-xs font-mono">
        <span class="text-gray-700 dark:text-gray-200 font-semibold flex-shrink-0">{{ toolInfo.function }}</span>
        <span v-if="toolInfo.functionArg" class="text-gray-400 dark:text-gray-500 truncate bg-gray-50 dark:bg-gray-800/80 px-1.5 py-0.5 rounded-md border border-gray-100 dark:border-gray-700/50 max-w-full">
          {{ toolInfo.functionArg }}
        </span>
      </div>

      <!-- Duration badge -->
      <span v-if="tool.duration_ms != null && tool.status === 'called'"
        class="flex-shrink-0 text-[10px] font-bold font-mono px-2 py-0.5 rounded-md tabular-nums bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/15 text-emerald-600 dark:text-emerald-400 border border-emerald-200/40 dark:border-emerald-800/30">
        {{ formatDuration(tool.duration_ms) }}
      </span>
    </div>

    <!-- Timestamp -->
    <div class="flex-shrink-0 text-[10px] text-gray-300 dark:text-gray-600 opacity-0 group-hover/tool:opacity-100 transition-opacity duration-200 font-mono tabular-nums">
      {{ relativeTime(tool.timestamp) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { ToolContent } from "../types/message";
import { useToolInfo } from "../composables/useTool";
import { useRelativeTime } from "../composables/useTime";

const props = defineProps<{
  tool: ToolContent;
}>();

const emit = defineEmits<{
  (e: "click"): void;
}>();

const { relativeTime } = useRelativeTime();
const { toolInfo } = useToolInfo(ref(props.tool));

const toolMetaIcon = computed(() => props.tool.tool_meta?.icon || '');

const formatDuration = (ms: number): string => {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
};

const handleClick = () => { emit("click"); };
</script>

<style scoped>
</style>
