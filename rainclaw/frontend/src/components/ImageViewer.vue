<template>
  <div class="inline-block relative group">
    <img 
      :src="src" 
      :alt="alt"
      class="max-w-full h-auto rounded-lg border border-[var(--border-main)] cursor-zoom-in bg-white"
      @click="isOpen = true"
    />
    
    <Dialog v-model:open="isOpen">
      <DialogContent class="max-w-[95vw] max-h-[95vh] w-full h-full p-0 bg-transparent border-0 shadow-none flex items-center justify-center outline-none">
         <div class="relative w-full h-full flex items-center justify-center overflow-hidden" 
              @wheel.prevent="handleWheel"
              @mousedown="handleMouseDown"
              @mousemove="handleMouseMove"
              @mouseup="handleMouseUp"
              @mouseleave="handleMouseUp"
              ref="containerRef">
            
            <img 
              :src="src" 
              :alt="alt"
              class="max-w-full max-h-full object-contain transition-transform duration-75 ease-linear select-none"
              :style="{ transform: `translate(${pos.x}px, ${pos.y}px) scale(${scale})` }"
              draggable="false"
            />

            <!-- Controls -->
            <div class="absolute bottom-8 left-1/2 -translate-x-1/2 flex gap-3 bg-black/70 backdrop-blur-md p-3 rounded-full shadow-lg z-50" @mousedown.stop>
                <button @click="zoomIn" class="p-2 text-white hover:bg-white/20 rounded-full transition-colors" title="Zoom In">
                  <PlusIcon class="w-5 h-5" />
                </button>
                <button @click="zoomOut" class="p-2 text-white hover:bg-white/20 rounded-full transition-colors" title="Zoom Out">
                  <MinusIcon class="w-5 h-5" />
                </button>
                <button @click="reset" class="p-2 text-white hover:bg-white/20 rounded-full transition-colors" title="Reset">
                  <RotateCcwIcon class="w-5 h-5" />
                </button>
                <div class="w-px bg-white/20 mx-1"></div>
                <button @click="isOpen = false" class="p-2 text-white hover:bg-white/20 rounded-full transition-colors" title="Close">
                  <XIcon class="w-5 h-5" />
                </button>
            </div>
         </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { PlusIcon, MinusIcon, RotateCcwIcon, XIcon } from 'lucide-vue-next';

defineProps<{
  src: string;
  alt?: string;
}>();

const isOpen = ref(false);
const scale = ref(1);
const pos = ref({ x: 0, y: 0 });
const isDragging = ref(false);
const startPos = ref({ x: 0, y: 0 });

const reset = () => {
  scale.value = 1;
  pos.value = { x: 0, y: 0 };
};

const zoomIn = () => {
  scale.value = Math.min(scale.value * 1.2, 10);
};

const zoomOut = () => {
  scale.value = Math.max(scale.value / 1.2, 0.5);
};

const handleWheel = (e: WheelEvent) => {
  const delta = e.deltaY > 0 ? 0.9 : 1.1;
  const newScale = Math.min(Math.max(scale.value * delta, 0.5), 10);
  scale.value = newScale;
};

const handleMouseDown = (e: MouseEvent) => {
  isDragging.value = true;
  startPos.value = { x: e.clientX - pos.value.x, y: e.clientY - pos.value.y };
};

const handleMouseMove = (e: MouseEvent) => {
  if (!isDragging.value) return;
  pos.value = {
    x: e.clientX - startPos.value.x,
    y: e.clientY - startPos.value.y
  };
};

const handleMouseUp = () => {
  isDragging.value = false;
};

watch(isOpen, (val) => {
  if (!val) reset();
});
</script>
