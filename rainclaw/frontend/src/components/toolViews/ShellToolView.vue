<template>
  <div
    class="h-[36px] flex items-center px-3 w-full bg-[var(--background-gray-main)] border-b border-[var(--border-main)] rounded-t-[12px] shadow-[inset_0px_1px_0px_0px_#FFFFFF] dark:shadow-[inset_0px_1px_0px_0px_#FFFFFF30]">
    <div class="flex-1 flex items-center justify-center">
      <div class="max-w-[250px] truncate text-[var(--text-tertiary)] text-sm font-medium text-center">{{
        shellSessionId }}
      </div>
    </div>
  </div>
  <div class="flex-1 min-h-0 w-full overflow-y-auto">
    <div dir="ltr" data-orientation="horizontal" class="flex flex-col flex-1 min-h-0">
      <div data-state="active" data-orientation="horizontal" role="tabpanel"
        id="radix-:r5m:-content-setup" tabindex="0"
        class="py-2 focus-visible:outline-none data-[state=inactive]:hidden flex-1 font-mono text-sm leading-relaxed px-3 outline-none overflow-auto whitespace-pre-wrap break-all"
        style="animation-duration: 0s;">
        <code v-html="shell"></code>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, watch, onUnmounted } from 'vue';
import { viewShellSession } from '@/api/agent';
import { ToolContent } from '@/types/message';
//import { showErrorToast } from '@/utils/toast';

const props = defineProps<{
  sessionId: string;
  toolContent: ToolContent;
  live: boolean;
}>();

defineExpose({
  loadContent: () => {
    loadShellContent();
  }
});

const shell = ref('');
const refreshTimer = ref<ReturnType<typeof setInterval> | null>(null);

// Get shellSessionId from toolContent
const shellSessionId = computed(() => {
  // Sandbox proxy tool: show tool function name
  if (props.toolContent?.content?._sandbox_exec) {
    return `sandbox: ${props.toolContent.function || props.toolContent.name}`;
  }
  if (props.toolContent && props.toolContent.args.id) {
    return props.toolContent.args.id;
  }
  if (props.toolContent && props.toolContent.args.script_path) {
    return props.toolContent.args.script_path.split('/').pop();
  }
  return '';
});

const updateShellContent = (console: any) => {
  if (!console) return;
  
  // Handle string content (e.g. from run_python_script)
  if (typeof console === 'string') {
    let displayContent = console;
    
    // Add command if it's run_python_script
    if (props.toolContent.name === 'run_python_script' || props.toolContent.function === 'run_python_script') {
        const script = props.toolContent.args?.script_path || '';
        const args = props.toolContent.args?.args || '';
        const cmd = `python ${script} ${args}`.trim();
        const ps1 = "$";
        // Construct a shell-like display
        displayContent = `<span style="color: rgb(0, 187, 0);">${ps1}</span><span> ${cmd}</span>\n${console}`;
    }
    
    if (shell.value !== displayContent) {
      shell.value = displayContent;
    }
    return;
  }

  let newShell = '';
  for (const e of console) {
    newShell += `<span style="color: rgb(0, 187, 0);">${e.ps1}</span><span> ${e.command}</span>\n`;
    newShell += `<span>${e.output}</span>\n`;
  }
  if (newShell !== shell.value) {
    shell.value = newShell;
  }
}

const escapeHtml = (text: string): string => {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
};

// Function to load Shell session content
const loadShellContent = async () => {
  console.log("ShellToolView debug:", {
     name: props.toolContent.name,
     args: props.toolContent.args,
     content: props.toolContent.content
  });

  // Sandbox proxy tool: display command + output in terminal style
  const content = props.toolContent.content;
  if (content && typeof content === 'object' && content._sandbox_exec) {
    const exec = content._sandbox_exec;
    const cmd = escapeHtml(exec.command || '');
    const output = escapeHtml(exec.output || '');
    const result = content.result;
    const ps1 = '<span style="color: rgb(0, 187, 0);">$</span>';

    let display = `${ps1} <span>${cmd}</span>\n`;
    if (output) {
      display += `<span style="color: rgb(180, 180, 180);">${output}</span>\n`;
    }
    if (result) {
      const resultStr = typeof result === 'string' ? result : JSON.stringify(result, null, 2);
      display += `<span>${escapeHtml(resultStr)}</span>`;
    }
    shell.value = display;
    return;
  }

  // If content is already a string (e.g. run_python_script output), just use it
  if (typeof content === 'string') {
    updateShellContent(content);
    return;
  }
  
  // Also check if content is nested in content.content (like FileToolView logic)
  if (content && typeof content.content === 'string') {
      updateShellContent(content.content);
      return;
  }

  if (!props.live) {
    updateShellContent(content?.console);
    return;
  }
  
  // Only call API if we have a valid session ID (not a script path)
  if (props.toolContent.args.id) {
    try {
      const response = await viewShellSession(props.sessionId, props.toolContent.args.id);
      updateShellContent(response.console);
    } catch (error) {
      console.error("Failed to load shell content:", error);
    }
  } else if (content) {
     // Fallback to content if no ID
     updateShellContent(content);
  }
};

// Start auto-refresh timer
const startAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value);
  }
  
  if (props.live && shellSessionId.value) {
    refreshTimer.value = setInterval(() => {
      loadShellContent();
    }, 5000);
  }
};

// Stop auto-refresh timer
const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value);
    refreshTimer.value = null;
  }
};

watch(() => props.toolContent, () => {
  loadShellContent();
});

watch(() => props.toolContent.timestamp, () => {
  loadShellContent();
});

// Watch for live prop changes
watch(() => props.live, (live: boolean) => {
  if (live) {
    loadShellContent();
    startAutoRefresh();
  } else {
    stopAutoRefresh();
  }
});

// Load content and set up refresh timer when component is mounted
onMounted(() => {
  loadShellContent();
  startAutoRefresh();
});

// Clear timer when component is unmounted
onUnmounted(() => {
  stopAutoRefresh();
});
</script>
