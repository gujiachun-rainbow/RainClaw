<template>
  <SimpleBar>
    <div
      class="flex flex-col h-full flex-1 min-w-0 mx-auto w-full sm:min-w-[390px] px-5 justify-center items-start gap-2 relative max-w-full sm:max-w-full">
      <div class="w-full pt-4 pb-4 px-5 bg-[var(--background-gray-main)] sticky top-0 z-10 mx-[-1.25]">
        <div class="flex justify-between items-center w-full absolute left-0 right-0">
          <div class="h-8 relative z-20 overflow-hidden flex gap-2 items-center flex-shrink-0">
            <div class="relative flex items-center">
            </div>
            <div class="flex items-center gap-2">
              <div class="w-[30px] h-[30px]">
                 <RobotAvatar :interactive="false" />
              </div>
              <RainClawLogoTextIcon />
            </div>
          </div>
          <div class="flex items-center gap-2">
            <div class="relative flex items-center" aria-expanded="false" aria-haspopup="dialog"
              @mouseenter="handleUserMenuEnter" @mouseleave="handleUserMenuLeave">
              <div class="relative flex items-center justify-center font-bold cursor-pointer flex-shrink-0">
                <div
                  class="relative flex items-center justify-center font-bold flex-shrink-0 rounded-full overflow-hidden"
                  style="width: 32px; height: 32px; font-size: 16px; color: rgba(255, 255, 255, 0.9); background-color: rgb(59, 130, 246);">
                  {{ avatarLetter }}</div>
              </div>
              <!-- User Menu -->
              <div v-if="showUserMenu" @mouseenter="handleUserMenuEnter" @mouseleave="handleUserMenuLeave"
                class="absolute top-full right-0 mt-1 mr-[-15px] z-50">
                <UserMenu />
              </div>
            </div>
          </div>
        </div>
        <div class="h-8"></div>
      </div>
      <div class="w-full max-w-full sm:max-w-[768px] sm:min-w-[390px] mx-auto mt-[120px] mb-auto">
        <!-- Welcome Area -->
        <div class="welcome-area w-full flex flex-col items-center justify-center pb-6">
          <div class="size-14 rounded-2xl bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 mb-4">
            <svg class="size-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" /></svg>
          </div>
          <h1 class="text-2xl font-bold text-[var(--text-primary)] text-center">
            {{ fullGreeting }}
          </h1>
          <p class="text-sm text-[var(--text-tertiary)] mt-1 typewriter-line">
            <span
              v-for="(char, i) in displayedChars"
              :key="`${typingCycle}-${i}`"
              class="typewriter-char"
              :class="{ 'typewriter-space': char === ' ' }"
              :style="{ '--char-index': i }"
            >{{ char }}</span><span class="typewriter-cursor" :class="{ 'typing-active': isTyping }"></span>
          </p>
        </div>

        <!-- Quick Prompts -->
        <div class="grid grid-cols-2 gap-3 mb-5 px-2">
          <div v-for="(prompt, idx) in quickPrompts" :key="idx"
            class="prompt-card group relative rounded-2xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-[#1e1e1e] cursor-pointer overflow-hidden"
            :style="{ '--delay': `${idx * 80 + 200}ms` }"
            @click="usePrompt(prompt.query)">
            <!-- Hover glow -->
            <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
              <div class="absolute -inset-px rounded-2xl" :class="prompt.glow"></div>
            </div>
            <div class="relative p-4">
              <!-- Header: icon + title -->
              <div class="flex items-center gap-2.5 mb-2">
                <div class="size-9 rounded-xl bg-gradient-to-br flex items-center justify-center text-lg shadow-sm transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3"
                  :class="prompt.gradient">
                  <span class="drop-shadow-sm">{{ prompt.icon }}</span>
                </div>
                <div>
                  <h3 class="text-sm font-semibold text-[var(--text-primary)] group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r transition-all duration-300" :class="prompt.textGradient">{{ prompt.title }}</h3>
                  <p class="text-[10px] text-[var(--text-tertiary)]">{{ prompt.desc }}</p>
                </div>
              </div>
              <!-- Query preview -->
              <p class="text-[11px] text-[var(--text-secondary)] leading-relaxed line-clamp-2 min-h-[2rem]">{{ prompt.query }}</p>
              <!-- Bottom arrow -->
              <div class="mt-2 flex items-center justify-end">
                <span class="text-[10px] flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-1 group-hover:translate-x-0"
                  :class="prompt.textGradient.replace(/group-hover:/g, '') ? 'text-blue-500' : 'text-blue-500'">
                  {{ $t('Try it') }}
                  <svg class="size-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- ChatBox -->
        <div class="flex flex-col gap-1 w-full">
          <div class="flex flex-col bg-[var(--background-gray-main)] w-full">
            <div class="[&amp;:not(:empty)]:pb-2 bg-[var(--background-gray-main)] rounded-[22px_22px_0px_0px]"></div>
            <ChatBox 
              ref="chatBoxRef"
              :rows="2" 
              v-model="message" 
              @submit="handleSubmit" 
              :isRunning="isSubmitting" 
              :attachments="attachments"
              :models="models"
              :selectedModelId="selectedModelId"
              @update:selectedModelId="selectedModelId = $event"
              @open-model-settings="openSettingsDialog('models')"
            />
          </div>
        </div>
      </div>
    </div>
  </SimpleBar>
</template>

<script setup lang="ts">
import SimpleBar from '../components/SimpleBar.vue';
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import ChatBox from '../components/ChatBox.vue';
import { createSession } from '../api/agent';
import { listModels, type ModelConfig } from '../api/models';
import { showErrorToast } from '../utils/toast';
import RainClawLogoTextIcon from '../components/icons/RainClawLogoTextIcon.vue';
import RobotAvatar from '../components/icons/RobotAvatar.vue';
import type { FileInfo } from '../api/file';
import { useFilePanel } from '../composables/useFilePanel';
import { setPendingChat } from '../composables/usePendingChat';
import { useAuth } from '../composables/useAuth';
import { useSettingsDialog } from '../composables/useSettingsDialog';
import UserMenu from '../components/UserMenu.vue';

const { t } = useI18n();
const router = useRouter();
const { currentUser } = useAuth();
const message = ref('');

// ── Typewriter effect ──
const displayedChars = ref<string[]>([]);
const typingCycle = ref(0);
const isTyping = ref(false);
const currentSubtitleIdx = ref(0);
let typeTimer: ReturnType<typeof setTimeout> | null = null;

// 静态问候语
const fullGreeting = computed(() => {
  const name = currentUser.value?.fullname || 'User';
  return `${t('Hello')}, ${name}`;
});

// 打字机效果循环显示的副标题
const subtitleTemplates = computed(() => [
  t('What are you researching today?'),
  t('Any questions about proteins or genes?'),
  t('Need help analyzing drug data?'),
  t('Ready to explore scientific insights?'),
]);

const currentSubtitle = computed(() => subtitleTemplates.value[currentSubtitleIdx.value]);

function clearTimer() {
  if (typeTimer) { clearTimeout(typeTimer); typeTimer = null; }
}

function startTyping() {
  const text = currentSubtitle.value;
  let idx = 0;
  displayedChars.value = [];
  isTyping.value = true;

  const typeNext = () => {
    if (idx < text.length) {
      displayedChars.value = [...displayedChars.value, text[idx]];
      idx++;
      // 随机延迟让打字效果更自然
      typeTimer = setTimeout(typeNext, 90 + Math.random() * 60);
    } else {
      isTyping.value = false;
      typeTimer = setTimeout(startErasing, 3000);
    }
  };
  typeNext();
}

function startErasing() {
  isTyping.value = true;
  const eraseNext = () => {
    if (displayedChars.value.length > 0) {
      displayedChars.value = displayedChars.value.slice(0, -1);
      typeTimer = setTimeout(eraseNext, 35);
    } else {
      currentSubtitleIdx.value = (currentSubtitleIdx.value + 1) % subtitleTemplates.value.length;
      typingCycle.value++;
      typeTimer = setTimeout(startTyping, 400);
    }
  };
  eraseNext();
}

const quickPrompts = computed(() => [
  {
    icon: '📅',
    title: t('Protein & Disease'),
    desc: t('Multi-step target analysis pipeline'),
    query: t('I am studying Alzheimer\'s disease (EFO_0000249). Please: 1) Find the top 5 drug targets associated with this disease 2) Query the protein function of the top-ranked target 3) Compile the findings into a comprehensive PDF research report'),
    glow: 'bg-gradient-to-r from-blue-400/20 via-indigo-400/20 to-purple-400/20',
    textGradient: 'group-hover:from-blue-600 group-hover:to-indigo-600',
    gradient: 'from-blue-500 to-indigo-600',
  },
  {
    icon: '📧',
    title: t('Drug Safety Profile'),
    desc: t('FDA adverse event analysis with data visualization'),
    query: t('Analyze the drug safety profile of aspirin: 1) Query the top 10 most common adverse reactions from the FDA FAERS database 2) Analyze the results and generate a detailed Excel spreadsheet of adverse reactions sorted by report count'),
    glow: 'bg-gradient-to-r from-emerald-400/20 via-teal-400/20 to-cyan-400/20',
    textGradient: 'group-hover:from-emerald-600 group-hover:to-teal-600',
    gradient: 'from-emerald-500 to-teal-600',
  },
  {
    icon: '📄',
    title: t('Compound ADMET'),
    desc: t('Multi-dimensional drug property prediction'),
    query: t('Evaluate the drug-likeness of compound CC(=O)Oc1ccccc1C(=O)O (aspirin SMILES): predict its BBB penetrance, toxicity, and bioavailability using ADMET tools, then produce a detailed Word document with the comprehensive assessment'),
    glow: 'bg-gradient-to-r from-violet-400/20 via-fuchsia-400/20 to-pink-400/20',
    textGradient: 'group-hover:from-violet-600 group-hover:to-fuchsia-600',
    gradient: 'from-violet-500 to-fuchsia-600',
  },
  {
    icon: '📈',
    title: t('Literature & Data'),
    desc: t('Cross-database research synthesis'),
    query: t('Conduct a research overview on BRCA1 gene and breast cancer: 1) Search for relevant publications about BRCA1 mutations 2) Query BRCA1 protein (P38398) function from UniProt 3) Find top drug targets for breast cancer (EFO_0000305) 4) Synthesize all findings into a comprehensive PDF research report'),
    glow: 'bg-gradient-to-r from-amber-400/20 via-orange-400/20 to-red-400/20',
    textGradient: 'group-hover:from-amber-600 group-hover:to-orange-600',
    gradient: 'from-amber-500 to-orange-600',
  },
]);

const usePrompt = (query: string) => { message.value = query; };
const isSubmitting = ref(false);
const attachments = ref<FileInfo[]>([]);
const chatBoxRef = ref<InstanceType<typeof ChatBox> | null>(null);
const { hideFilePanel } = useFilePanel();
const { isSettingsDialogOpen, openSettingsDialog } = useSettingsDialog();

const models = ref<ModelConfig[]>([]);
const selectedModelId = ref<string | null>(null);

const avatarLetter = computed(() => {
  return currentUser.value?.fullname?.charAt(0)?.toUpperCase() || 'M';
});

const showUserMenu = ref(false);
const userMenuTimeout = ref<ReturnType<typeof setTimeout> | null>(null);

const handleUserMenuEnter = () => {
  if (userMenuTimeout.value) {
    clearTimeout(userMenuTimeout.value);
    userMenuTimeout.value = null;
  }
  showUserMenu.value = true;
};

const handleUserMenuLeave = () => {
  userMenuTimeout.value = setTimeout(() => {
    showUserMenu.value = false;
  }, 200);
};

onMounted(async () => {
  hideFilePanel();
  startTyping(); // 启动打字机效果
  const modelsData = await listModels().catch(err => {
    console.error("Failed to load models", err);
    return [];
  });
  models.value = modelsData;

  if (models.value.length === 0) {
    openSettingsDialog('models');
  } else {
    const sys = models.value.find(m => m.is_system);
    if (sys) selectedModelId.value = sys.id;
    else if (models.value.length > 0) selectedModelId.value = models.value[0].id;
  }
})

onUnmounted(() => {
  clearTimer(); // 组件卸载时清理定时器
})

watch(isSettingsDialogOpen, async (newVal, oldVal) => {
  if (oldVal === true && newVal === false) {
    try {
      const modelsData = await listModels();
      models.value = modelsData;
      if (!selectedModelId.value || !modelsData.find(m => m.id === selectedModelId.value)) {
        const sys = modelsData.find(m => m.is_system);
        selectedModelId.value = sys ? sys.id : (modelsData.length > 0 ? modelsData[0].id : null);
      }
    } catch (err) {
      console.error("Failed to refresh models after settings change", err);
    }
  }
});

const handleSubmit = async () => {
  if (!message.value.trim() || isSubmitting.value) return;
  isSubmitting.value = true;

  try {
    // Step 1: Create session
    const session = await createSession({
      mode: 'deep',
      model_config_id: selectedModelId.value || undefined
    });
    const sessionId = session.session_id;

    // Step 2: Upload any local files (kept in browser memory until now)
    let uploadedFiles: FileInfo[] = [];
    if (chatBoxRef.value) {
      uploadedFiles = await chatBoxRef.value.uploadPendingFiles(sessionId);
    }

    // Step 3: Store pending data and navigate
    setPendingChat({
      message: message.value,
      files: uploadedFiles,
      mode: 'deep',
      selectedModelId: selectedModelId.value
    });
    router.push(`/chat/${sessionId}`);
  } catch (error) {
    console.error('Failed to create session:', error);
    showErrorToast(t('Failed to create session, please try again later'));
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
.welcome-area { animation: fadeInUp 0.5s ease-out; }
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
.prompt-card {
  animation: cardFadeIn 0.4s ease-out both;
  animation-delay: var(--delay, 0ms);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
@keyframes cardFadeIn {
  from { opacity: 0; transform: translateY(12px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.prompt-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 28px -8px rgba(0,0,0,0.08), 0 4px 12px -4px rgba(0,0,0,0.04);
}
.line-clamp-2 { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

/* Typewriter effect styles */
.typewriter-line {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 1.5em;
}

.typewriter-char {
  display: inline-block;
  animation: charFadeIn 0.2s ease-out forwards;
}

.typewriter-space {
  width: 0.3em;
}

.typewriter-cursor {
  display: inline-block;
  width: 3px;
  height: 1.1em;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  margin-left: 0;
  border-radius: 2px;
  animation: cursorBlink 1s ease-in-out infinite;
}

.typewriter-cursor.typing-active {
  animation: cursorBlink 0.5s ease-in-out infinite;
}

@keyframes charFadeIn {
  0% {
    opacity: 0;
    transform: translateY(2px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes cursorBlink {
  0%, 45% { opacity: 1; }
  50%, 95% { opacity: 0; }
  100% { opacity: 1; }
}
</style>
