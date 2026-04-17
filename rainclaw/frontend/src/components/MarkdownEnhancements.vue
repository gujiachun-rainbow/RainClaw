<template>
  <!-- 图片 Lightbox -->
  <Teleport to="body">
    <Transition name="lightbox">
      <div
        v-if="lightboxVisible"
        class="lightbox-overlay"
        @click="closeLightbox"
        @keydown.esc="closeLightbox"
      >
        <div class="lightbox-container" @click.stop>
          <!-- 关闭按钮 -->
          <button class="lightbox-close" @click="closeLightbox" title="关闭 (Esc)">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>

          <!-- 缩放控制 -->
          <div class="lightbox-controls">
            <button @click="zoomOut" title="缩小 (-)" class="lightbox-control-btn">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="8" y1="11" x2="14" y2="11"></line>
              </svg>
            </button>
            <span class="lightbox-zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
            <button @click="zoomIn" title="放大 (+)" class="lightbox-control-btn">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="11" y1="8" x2="11" y2="14"></line>
                <line x1="8" y1="11" x2="14" y2="11"></line>
              </svg>
            </button>
            <button @click="resetZoom" title="重置 (0)" class="lightbox-control-btn">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3.5 3.5v6h6"></path>
                <path d="M20.5 20.5v-6h-6"></path>
                <path d="M4 12a8 8 0 0 1 14-5.3"></path>
                <path d="M20 12a8 8 0 0 1-14 5.3"></path>
              </svg>
            </button>
          </div>

          <!-- 图片容器 -->
          <div
            class="lightbox-image-wrapper"
            @mousedown="startDrag"
            @mousemove="onDrag"
            @mouseup="endDrag"
            @mouseleave="endDrag"
            @wheel.prevent="onWheel"
          >
            <img
              ref="lightboxImage"
              :src="lightboxSrc"
              :alt="lightboxAlt"
              class="lightbox-image"
              :style="imageStyle"
              draggable="false"
            />
          </div>

          <!-- 图片信息 -->
          <div class="lightbox-info" v-if="lightboxAlt">
            {{ lightboxAlt }}
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- 代码块全屏 -->
  <Teleport to="body">
    <Transition name="fullscreen">
      <div
        v-if="codeFullscreenVisible"
        class="code-fullscreen-overlay"
        @keydown.esc="closeCodeFullscreen"
      >
        <div class="code-fullscreen-container">
          <!-- 头部 -->
          <div class="code-fullscreen-header">
            <div class="code-fullscreen-lang">
              <span class="code-fullscreen-dot"></span>
              {{ codeFullscreenLang }}
            </div>
            <div class="code-fullscreen-actions">
              <button @click="copyCodeFullscreen" class="code-fullscreen-btn" :class="{ 'code-fullscreen-btn--copied': codeCopied }">
                <svg v-if="!codeCopied" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                {{ codeCopied ? '已复制' : '复制代码' }}
              </button>
              <button @click="closeCodeFullscreen" class="code-fullscreen-btn code-fullscreen-btn--close">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
                退出全屏 (Esc)
              </button>
            </div>
          </div>

          <!-- 代码内容 -->
          <div class="code-fullscreen-content">
            <pre class="code-fullscreen-pre"><code class="hljs" v-html="codeFullscreenHtml"></code></pre>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- 文字选中菜单 -->
  <Teleport to="body">
    <Transition name="selection-menu">
      <div
        v-if="selectionMenuVisible"
        class="selection-menu"
        :style="selectionMenuStyle"
      >
        <button @click="copySelection" class="selection-menu-btn" title="复制">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          <span>复制</span>
        </button>
        <button @click="searchSelection" class="selection-menu-btn" title="搜索">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <span>搜索</span>
        </button>
        <button @click="translateSelection" class="selection-menu-btn" title="翻译">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 8l6 6"></path>
            <path d="M4 14l6-6 2-3"></path>
            <path d="M2 5h12"></path>
            <path d="M7 2v3"></path>
            <path d="M22 22l-5-10-5 10"></path>
            <path d="M14 18h6"></path>
          </svg>
          <span>翻译</span>
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';

// ==================== Lightbox ====================
const lightboxVisible = ref(false);
const lightboxSrc = ref('');
const lightboxAlt = ref('');
const zoomLevel = ref(1);
const isDragging = ref(false);
const dragStart = ref({ x: 0, y: 0 });
const imagePosition = ref({ x: 0, y: 0 });
const lightboxImage = ref<HTMLImageElement | null>(null);

const imageStyle = computed(() => ({
  transform: `translate(${imagePosition.value.x}px, ${imagePosition.value.y}px) scale(${zoomLevel.value})`,
  transition: isDragging.value ? 'none' : 'transform 0.2s ease-out',
}));

const openLightbox = (src: string, alt: string = '') => {
  lightboxSrc.value = src;
  lightboxAlt.value = alt;
  lightboxVisible.value = true;
  zoomLevel.value = 1;
  imagePosition.value = { x: 0, y: 0 };
  document.body.style.overflow = 'hidden';
};

const closeLightbox = () => {
  lightboxVisible.value = false;
  document.body.style.overflow = '';
};

const zoomIn = () => {
  if (zoomLevel.value < 5) {
    zoomLevel.value = Math.min(5, zoomLevel.value + 0.25);
  }
};

const zoomOut = () => {
  if (zoomLevel.value > 0.25) {
    zoomLevel.value = Math.max(0.25, zoomLevel.value - 0.25);
    if (zoomLevel.value <= 1) {
      imagePosition.value = { x: 0, y: 0 };
    }
  }
};

const resetZoom = () => {
  zoomLevel.value = 1;
  imagePosition.value = { x: 0, y: 0 };
};

const startDrag = (e: MouseEvent) => {
  if (zoomLevel.value > 1) {
    isDragging.value = true;
    dragStart.value = {
      x: e.clientX - imagePosition.value.x,
      y: e.clientY - imagePosition.value.y,
    };
  }
};

const onDrag = (e: MouseEvent) => {
  if (isDragging.value) {
    imagePosition.value = {
      x: e.clientX - dragStart.value.x,
      y: e.clientY - dragStart.value.y,
    };
  }
};

const endDrag = () => {
  isDragging.value = false;
};

const onWheel = (e: WheelEvent) => {
  if (e.deltaY < 0) {
    zoomIn();
  } else {
    zoomOut();
  }
};

// ==================== Code Fullscreen ====================
const codeFullscreenVisible = ref(false);
const codeFullscreenHtml = ref('');
const codeFullscreenLang = ref('plaintext');
const codeFullscreenRaw = ref('');
const codeCopied = ref(false);

const openCodeFullscreen = (html: string, lang: string, rawCode: string) => {
  codeFullscreenHtml.value = html;
  codeFullscreenLang.value = lang || 'plaintext';
  codeFullscreenRaw.value = rawCode;
  codeFullscreenVisible.value = true;
  codeCopied.value = false;
  document.body.style.overflow = 'hidden';
};

const closeCodeFullscreen = () => {
  codeFullscreenVisible.value = false;
  document.body.style.overflow = '';
};

const copyCodeFullscreen = async () => {
  try {
    await navigator.clipboard.writeText(codeFullscreenRaw.value);
    codeCopied.value = true;
    setTimeout(() => {
      codeCopied.value = false;
    }, 2000);
  } catch (err) {
    console.error('Failed to copy:', err);
  }
};

// ==================== Selection Menu ====================
const selectionMenuVisible = ref(false);
const selectionMenuStyle = ref({ top: '0px', left: '0px' });
let selectedText = '';
let hideTimeout: ReturnType<typeof setTimeout> | null = null;

const showSelectionMenu = (x: number, y: number, text: string) => {
  if (hideTimeout) {
    clearTimeout(hideTimeout);
  }
  selectedText = text;

  // 计算菜单位置，确保不超出视口
  const menuWidth = 150;
  const menuHeight = 40;
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;

  let left = x;
  let top = y + 10;

  if (left + menuWidth > viewportWidth) {
    left = viewportWidth - menuWidth - 10;
  }
  if (top + menuHeight > viewportHeight) {
    top = y - menuHeight - 10;
  }

  selectionMenuStyle.value = {
    top: `${top}px`,
    left: `${left}px`,
  };
  selectionMenuVisible.value = true;
};

const hideSelectionMenu = () => {
  hideTimeout = setTimeout(() => {
    selectionMenuVisible.value = false;
  }, 100);
};

const copySelection = async () => {
  try {
    await navigator.clipboard.writeText(selectedText);
    selectionMenuVisible.value = false;
  } catch (err) {
    console.error('Failed to copy:', err);
  }
};

const searchSelection = () => {
  const query = encodeURIComponent(selectedText);
  window.open(`https://www.google.com/search?q=${query}`, '_blank');
  selectionMenuVisible.value = false;
};

const translateSelection = () => {
  const query = encodeURIComponent(selectedText);
  window.open(`https://translate.google.com/?text=${query}`, '_blank');
  selectionMenuVisible.value = false;
};

// ==================== 事件监听 ====================
const handleSelection = () => {
  const selection = window.getSelection();
  if (selection && selection.toString().trim()) {
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    showSelectionMenu(rect.left + rect.width / 2, rect.bottom, selection.toString().trim());
  } else {
    hideSelectionMenu();
  }
};

onMounted(() => {
  document.addEventListener('selectionchange', handleSelection);

  // 键盘快捷键
  document.addEventListener('keydown', (e) => {
    if (lightboxVisible.value) {
      if (e.key === 'Escape') closeLightbox();
      if (e.key === '+' || e.key === '=') zoomIn();
      if (e.key === '-') zoomOut();
      if (e.key === '0') resetZoom();
    }
    if (codeFullscreenVisible.value && e.key === 'Escape') {
      closeCodeFullscreen();
    }
  });
});

onUnmounted(() => {
  document.removeEventListener('selectionchange', handleSelection);
  if (hideTimeout) {
    clearTimeout(hideTimeout);
  }
});

// 暴露方法给父组件
defineExpose({
  openLightbox,
  closeLightbox,
  openCodeFullscreen,
  closeCodeFullscreen,
});
</script>

<style scoped>
/* ==================== Lightbox ==================== */
.lightbox-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.lightbox-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.lightbox-close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 44px;
  height: 44px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  z-index: 10;
}

.lightbox-close:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
}

.lightbox-controls {
  position: absolute;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(0, 0, 0, 0.6);
  padding: 8px 16px;
  border-radius: 30px;
  backdrop-filter: blur(10px);
  z-index: 10;
}

.lightbox-control-btn {
  width: 36px;
  height: 36px;
  background: transparent;
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.lightbox-control-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.lightbox-zoom-level {
  color: white;
  font-size: 13px;
  font-weight: 500;
  min-width: 50px;
  text-align: center;
}

.lightbox-image-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  overflow: hidden;
}

.lightbox-image-wrapper:active {
  cursor: grabbing;
}

.lightbox-image {
  max-width: 95%;
  max-height: 85%;
  object-fit: contain;
  user-select: none;
  border-radius: 8px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.lightbox-info {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  text-align: center;
  max-width: 80%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ==================== Code Fullscreen ==================== */
.code-fullscreen-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: #0d1117;
  display: flex;
  flex-direction: column;
}

.code-fullscreen-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.code-fullscreen-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
}

.code-fullscreen-lang {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #8b949e;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.code-fullscreen-dot {
  width: 10px;
  height: 10px;
  background: linear-gradient(135deg, #22c55e, #16a34a);
  border-radius: 50%;
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.5);
}

.code-fullscreen-actions {
  display: flex;
  gap: 10px;
}

.code-fullscreen-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: #c9d1d9;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.code-fullscreen-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.code-fullscreen-btn--copied {
  color: #22c55e;
}

.code-fullscreen-btn--close {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.code-fullscreen-btn--close:hover {
  background: rgba(239, 68, 68, 0.3);
}

.code-fullscreen-content {
  flex: 1;
  overflow: auto;
  padding: 24px;
}

.code-fullscreen-pre {
  margin: 0;
  font-size: 16px;
  line-height: 1.7;
}

.code-fullscreen-pre code {
  font-family: 'Fira Code', 'JetBrains Mono', 'SF Mono', Consolas, Monaco, monospace;
}

/* ==================== Selection Menu ==================== */
.selection-menu {
  position: fixed;
  z-index: 10000;
  display: flex;
  gap: 2px;
  padding: 6px;
  background: white;
  border-radius: 10px;
  box-shadow:
    0 10px 25px -5px rgba(0, 0, 0, 0.15),
    0 4px 10px -3px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.08);
  animation: selectionMenuIn 0.15s ease-out;
}

.dark .selection-menu {
  background: #1e293b;
  border-color: rgba(255, 255, 255, 0.1);
}

@keyframes selectionMenuIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.selection-menu-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #475569;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.dark .selection-menu-btn {
  color: #94a3b8;
}

.selection-menu-btn:hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
  color: #3b82f6;
}

.selection-menu-btn:active {
  transform: scale(0.95);
}

/* ==================== Transitions ==================== */
.lightbox-enter-active,
.lightbox-leave-active,
.fullscreen-enter-active,
.fullscreen-leave-active {
  transition: all 0.3s ease;
}

.lightbox-enter-from,
.lightbox-leave-to,
.fullscreen-enter-from,
.fullscreen-leave-to {
  opacity: 0;
}

.lightbox-enter-from .lightbox-image,
.lightbox-leave-to .lightbox-image {
  transform: scale(0.9);
}

.selection-menu-enter-active,
.selection-menu-leave-active {
  transition: all 0.15s ease;
}

.selection-menu-enter-from,
.selection-menu-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style>
