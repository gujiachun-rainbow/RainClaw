import { computed, Ref } from 'vue';
import type { ToolContent } from '../types/message';
import { useI18n } from 'vue-i18n';
import { TOOL_ICON_MAP, TOOL_NAME_MAP, TOOL_FUNCTION_MAP, TOOL_FUNCTION_ARG_MAP, TOOL_COMPONENT_MAP } from '../constants/tool';
import SearchIcon from '../components/icons/SearchIcon.vue';
import ShellIcon from '../components/icons/ShellIcon.vue';

/** 从 args 中提取第一个有意义的参数值作为 functionArg */
function extractFirstArg(args: any): string {
  if (!args || typeof args !== 'object') return '';
  for (const key of Object.keys(args)) {
    const val = args[key];
    if (typeof val === 'string' && val.length > 0 && val.length < 80) {
      return val;
    }
  }
  // 没有字符串参数，尝试第一个值的 JSON
  const firstKey = Object.keys(args)[0];
  if (firstKey) {
    const val = args[firstKey];
    if (val !== undefined && val !== null) {
      const s = typeof val === 'string' ? val : JSON.stringify(val);
      return s.length > 50 ? s.substring(0, 50) + '...' : s;
    }
  }
  return '';
}

export function useToolInfo(tool?: Ref<ToolContent | undefined>) {
  const { t } = useI18n();

  const toolInfo = computed(() => {
    if (!tool || !tool.value) return null;
    
    // MCP tool
    if (tool.value.function.startsWith('mcp_')) {
      const mcpToolName = tool.value.function.replace(/^mcp_/, '');
      return {
        icon: TOOL_ICON_MAP['mcp'] || null,
        name: t(TOOL_NAME_MAP['mcp'] || 'MCP Tool'),
        function: mcpToolName,
        functionArg: extractFirstArg(tool.value.args),
        view: TOOL_COMPONENT_MAP['mcp'] || null
      };
    }

    // Prioritize function name for specific tools
    let toolName = tool.value.name;
    if (['run_python_script', 'read_file', 'write_file'].includes(tool.value.function)) {
        toolName = tool.value.function;
    }
    // MCP sandbox tools: use function name directly for mapping
    if (tool.value.function.startsWith('terminal_')
      || tool.value.function.startsWith('file_')
      || tool.value.function.startsWith('browser_')
      || tool.value.function.startsWith('markitdown_')
      || tool.value.function.startsWith('sandbox_')) {
        toolName = tool.value.function;
    }
    
    // 获取参数显示值
    const argKey = TOOL_FUNCTION_ARG_MAP[tool.value.function];
    let functionArg = argKey ? (tool.value.args?.[argKey] || '') : '';
    if (!functionArg) {
      // Fallback: 从 args 中提取第一个有意义的值
      functionArg = extractFirstArg(tool.value.args);
    }
    if (argKey === 'file' && functionArg) {
      functionArg = functionArg.replace(/^\/home\/ubuntu\//, '');
    }
    
    // 已知工具：用常量表映射
    const knownIcon = TOOL_ICON_MAP[toolName];
    const knownName = TOOL_NAME_MAP[toolName];
    const knownFunction = TOOL_FUNCTION_MAP[tool.value.function];
    const knownView = TOOL_COMPONENT_MAP[toolName];

    if (knownIcon || knownName || knownFunction || knownView) {
      return {
        icon: knownIcon || ShellIcon,
        name: t(knownName || toolName || tool.value.function),
        function: t(knownFunction || tool.value.function),
        functionArg: functionArg,
        view: knownView || null
      };
    }

    // 未知/自定义工具：通用 fallback
    const meta = tool.value.tool_meta;
    const displayName = meta?.description || tool.value.function;

    // Sandbox proxy tools: use ShellToolView to show execution process
    if (meta?.sandbox) {
      return {
        icon: ShellIcon,
        name: displayName,
        function: tool.value.function,
        functionArg: functionArg,
        view: TOOL_COMPONENT_MAP['execute'] || null
      };
    }

    return {
      icon: SearchIcon,
      name: displayName,
      function: tool.value.function,
      functionArg: functionArg,
      view: null
    };
  });

  return {
    toolInfo
  };
} 