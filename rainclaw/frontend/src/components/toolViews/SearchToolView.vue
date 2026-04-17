<template>
  <div
    class="h-[36px] flex items-center px-3 w-full bg-[var(--background-gray-main)] border-b border-[var(--border-main)] rounded-t-[12px] shadow-[inset_0px_1px_0px_0px_#FFFFFF] dark:shadow-[inset_0px_1px_0px_0px_#FFFFFF30]">
    <div class="flex-1 flex items-center justify-center">
      <div class="max-w-[250px] truncate text-[var(--text-tertiary)] text-sm font-medium text-center">
        {{ searchQuery || 'Search' }}
      </div>
    </div>
  </div>
  <div class="flex-1 min-h-0 w-full overflow-y-auto">
    <div class="flex-1 min-h-0 max-w-[640px] mx-auto">
      <div class="flex flex-col overflow-auto h-full px-4 py-3">
        <!-- 搜索查询词 -->
        <div v-if="searchQuery" class="text-[12px] text-[var(--text-tertiary)] mb-3 break-words flex items-center gap-1.5">
          <span class="text-[var(--text-tertiary)]">🔍</span>
          {{ searchQuery }}
        </div>

        <!-- 结构化搜索结果 (results 数组) -->
        <template v-if="parsedResults.length > 0">
          <div v-for="(result, index) in parsedResults" :key="index" class="py-2.5 border-b border-[var(--border-light)] last:border-b-0">
            <a v-if="result.url" :href="result.url" target="_blank"
              class="block text-[var(--text-primary)] text-sm font-medium hover:underline line-clamp-2 cursor-pointer">
              {{ result.title || result.url }}
            </a>
            <div v-else class="text-[var(--text-primary)] text-sm font-medium line-clamp-2">
              {{ result.title }}
            </div>
            <div v-if="result.snippet" class="text-[var(--text-tertiary)] text-xs mt-1 line-clamp-3 leading-relaxed">{{ result.snippet }}</div>
            <div v-if="result.url" class="text-[var(--text-tertiary)] text-[11px] mt-1 truncate opacity-60">{{ result.url }}</div>
          </div>
        </template>

        <!-- 原始文本内容（无结构化 results 时） -->
        <div v-else-if="rawTextContent" class="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap break-words font-mono text-[12px]">
          {{ rawTextContent }}
        </div>

        <!-- 加载中 -->
        <div v-else-if="toolContent.status === 'calling'" class="text-sm text-[var(--text-tertiary)] py-6 text-center flex flex-col items-center gap-2">
          <div class="w-5 h-5 border-2 border-[var(--border-light)] border-t-[var(--text-tertiary)] rounded-full animate-spin"></div>
          {{ $t('Searching...') }}
        </div>

        <!-- 无结果 -->
        <div v-else class="text-sm text-[var(--text-tertiary)] py-6 text-center">
          {{ $t('No search results') }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ToolContent } from '@/types/message';

const props = defineProps<{
  sessionId: string;
  toolContent: ToolContent;
  live: boolean;
}>();

/** 提取搜索查询词 */
const searchQuery = computed(() => {
  const args = props.toolContent?.args;
  if (!args) return '';
  // 支持多种参数格式: query, queries, q
  return args.query || args.queries || args.q || '';
});

/** 解析结构化搜索结果 */
const parsedResults = computed(() => {
  const content = props.toolContent?.content;
  if (!content) return [];

  // 格式1: content.results 数组
  if (content.results && Array.isArray(content.results)) {
    return content.results;
  }

  // 格式2: content 本身是数组
  if (Array.isArray(content)) {
    return content;
  }

  // 格式3: content 是字符串，尝试解析 JSON
  if (typeof content === 'string') {
    try {
      const parsed = JSON.parse(content);
      if (parsed.results && Array.isArray(parsed.results)) return parsed.results;
      if (Array.isArray(parsed)) return parsed;
    } catch {
      // 不是 JSON，作为文本处理
    }
  }

  return [];
});

/** 原始文本内容（当没有结构化 results 时） */
const rawTextContent = computed(() => {
  if (parsedResults.value.length > 0) return '';
  const content = props.toolContent?.content;
  if (!content) return '';
  if (typeof content === 'string') return content;
  if (typeof content === 'object') {
    try { return JSON.stringify(content, null, 2); } catch { return ''; }
  }
  return String(content);
});
</script>
