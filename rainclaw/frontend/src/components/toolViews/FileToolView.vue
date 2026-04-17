<template>
  <div
    class="h-[36px] flex items-center px-3 w-full bg-[var(--background-gray-main)] border-b border-[var(--border-main)] rounded-t-[12px] shadow-[inset_0px_1px_0px_0px_#FFFFFF] dark:shadow-[inset_0px_1px_0px_0px_#FFFFFF30]"
  >
    <div class="flex-1 flex items-center justify-center">
      <div
        class="max-w-[250px] truncate text-[var(--text-tertiary)] text-sm font-medium text-center"
      >
        {{ fileName }}
      </div>
    </div>
  </div>
  <div class="flex-1 min-h-0 w-full overflow-y-auto">
    <div
      dir="ltr"
      data-orientation="horizontal"
      class="flex flex-col min-h-0 h-full relative"
    >
      <div
        data-state="active"
        data-orientation="horizontal"
        role="tabpanel"
        id="radix-:r2ke:-content-/home/ubuntu/llm_papers/todo.md"
        tabindex="0"
        class="focus-visible:outline-none data-[state=inactive]:hidden flex-1 min-h-0 h-full text-sm flex flex-col py-0 outline-none overflow-auto"
      >
        <section
          style="
            display: flex;
            position: relative;
            text-align: initial;
            width: 100%;
            height: 100%;
          "
        >
          <MonacoEditor
            :value="fileContent"
            :filename="fileName"
            :read-only="true"
            theme="vs"
            :line-numbers="'off'"
            :word-wrap="'on'"
            :minimap="false"
            :scroll-beyond-last-line="false"
            :automatic-layout="true"
          />
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, watch, onUnmounted } from "vue";
import { ToolContent } from "@/types/message";
import { viewFile } from "@/api/agent";
import MonacoEditor from "@/components/ui/MonacoEditor.vue";
//import { showErrorToast } from "../utils/toast";
//import { useI18n } from "vue-i18n";

//const { t } = useI18n();

const props = defineProps<{
  sessionId: string;
  toolContent: ToolContent;
  live: boolean;
}>();

defineExpose({
  loadContent: () => {
    loadFileContent();
  },
});

const fileContent = ref("");
const refreshTimer = ref<ReturnType<typeof setInterval> | null>(null);

const filePath = computed(() => {
  if (props.toolContent && props.toolContent.args.file) {
    return props.toolContent.args.file;
  }
  if (props.toolContent && props.toolContent.args.file_path) {
    return props.toolContent.args.file_path;
  }
  return "";
});

const fileName = computed(() => {
  if (filePath.value) {
    return filePath.value.split("/").pop() || "";
  }
  return "";
});

// Load file content
const loadFileContent = async () => {
  console.log("FileToolView debug:", {
    name: props.toolContent.name,
    function: props.toolContent.function,
    args: props.toolContent.args,
    content: props.toolContent.content,
    live: props.live
  });

  // If it's write_file, we should prioritize showing what was written (from args)
  // because the content returned by the tool is just a success message.
  // Also checking 'function' field and existence of content/file_path args to be robust
  const isWriteOp = props.toolContent.name === 'write_file' || 
                    props.toolContent.function === 'write_file' ||
                    (props.toolContent.args?.content && props.toolContent.args?.file_path);

  if (isWriteOp) {
    let contentToWrite = props.toolContent.args?.content;
    
    // Fallback: check if args is a string and try to parse it
    if (!contentToWrite && typeof props.toolContent.args === 'string') {
        try {
            const parsed = JSON.parse(props.toolContent.args);
            contentToWrite = parsed.content;
        } catch (e) {
            console.error("Failed to parse args string:", e);
        }
    }
    
    if (contentToWrite) {
        console.log("FileToolView: Using content for write operation");
        fileContent.value = contentToWrite;
        return;
    }
  }
  
  // Try to load from API first if we have a file path and session is active
  // This ensures we get the actual file content for write_file
  if (props.live && filePath.value) {
    try {
      const response = await viewFile(props.sessionId, filePath.value);
      fileContent.value = response.content;
      return;
    } catch (error) {
      console.error("Failed to load file content:", error);
      // Fallback to content from tool execution if API fails
    }
  }

  // Handle content from tool execution history
  if (props.toolContent.content) {
    if (typeof props.toolContent.content === 'string') {
        fileContent.value = props.toolContent.content;
    } else if (props.toolContent.content.content) {
        fileContent.value = props.toolContent.content.content;
    }
    return;
  }
  
  fileContent.value = "";
};

// Start auto-refresh timer
const startAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value);
  }
  
  if (props.live && filePath.value) {
    refreshTimer.value = setInterval(() => {
      loadFileContent();
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

// Watch for filename changes to reload content
watch(filePath, (newVal: string) => {
  if (newVal) {
    loadFileContent();
    startAutoRefresh();
  } else {
    stopAutoRefresh();
  }
});

watch(() => props.toolContent, () => {
  loadFileContent();
});

watch(() => props.toolContent.timestamp, () => {
  loadFileContent();
});

// Watch for live prop changes
watch(() => props.live, (live: boolean) => {
  if (live) {
    loadFileContent();
    startAutoRefresh();
  } else {
    stopAutoRefresh();
  }
});

// Load content when component is mounted
onMounted(() => {
  loadFileContent();
  startAutoRefresh();
});

onUnmounted(() => {
  stopAutoRefresh();
});
</script>
