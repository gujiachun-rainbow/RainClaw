<template>
  <div class="relative border border-[var(--border-main)] rounded-lg bg-white overflow-hidden group min-h-[300px]">
    <div ref="viewerContainer" class="w-full h-full relative z-0 min-h-[300px]"></div>
    
    <!-- Controls Overlay -->
    <div class="absolute top-2 right-2 flex flex-col gap-2 z-[9999]" @mousedown.stop @click.stop>
      <button 
        @click.prevent.stop="resetView" 
        class="p-2 bg-white/90 backdrop-blur-sm rounded-md shadow-sm hover:bg-gray-50 text-gray-600 border border-gray-200 cursor-pointer flex items-center justify-center transition-colors"
        title="Reset View">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-rotate-ccw"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 12"/><path d="M3 3v9h9"/></svg>
      </button>
      <button 
        @click.prevent.stop="toggleSpin" 
        class="p-2 bg-white/90 backdrop-blur-sm rounded-md shadow-sm hover:bg-gray-50 text-gray-600 border border-gray-200 cursor-pointer flex items-center justify-center transition-colors"
        :class="{ 'text-blue-500 bg-blue-50/90': isSpinning }"
        title="Toggle Spin">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-refresh-cw"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 12"/><path d="M21 3v9h-9"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 12"/><path d="M3 21v-9h9"/></svg>
      </button>
       <button 
        @click.prevent.stop="toggleStyle" 
        class="p-2 bg-white/90 backdrop-blur-sm rounded-md shadow-sm hover:bg-gray-50 text-gray-600 border border-gray-200 cursor-pointer flex items-center justify-center transition-colors"
        title="Change Style (Stick/Sphere/Line)">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-box"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
      </button>
    </div>

    <!-- Molecule Info -->
    <div v-if="moleculeInfo" class="absolute top-2 left-2 bg-white/90 backdrop-blur-sm p-2 rounded-md shadow border border-gray-200 text-xs text-gray-600 z-[9999] max-w-[200px] pointer-events-none select-none">
        <div class="font-semibold text-gray-800 mb-1">Molecule Info</div>
        <div v-if="moleculeInfo.formula">Formula: {{ moleculeInfo.formula }}</div>
        <div v-if="moleculeInfo.weight">Weight: {{ moleculeInfo.weight }}</div>
        <div v-if="moleculeInfo.atoms">Atoms: {{ moleculeInfo.atoms }}</div>
        <div v-if="moleculeInfo.bonds">Bonds: {{ moleculeInfo.bonds }}</div>
    </div>

    <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-gray-50 bg-opacity-50 z-20">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
    <div v-if="error" class="absolute inset-0 flex items-center justify-center text-red-500 p-4 text-center text-sm z-20">
      {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, shallowRef } from 'vue';

const props = defineProps<{
  src: string;
}>();

const viewerContainer = ref<HTMLDivElement | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const isSpinning = ref(false);
const moleculeInfo = ref<{formula?: string, weight?: string, atoms?: number, bonds?: number} | null>(null);

const viewer = shallowRef<any>(null);
let currentStyleIndex = 0;
const styles = [
    { name: 'Stick', style: { stick: {} } },
    { name: 'Sphere', style: { sphere: {} } },
    { name: 'Line', style: { line: {} } },
    { name: 'Stick + Sphere', style: { stick: {}, sphere: { scale: 0.3 } } }
];

const resetView = () => {
    console.log('Reset view clicked', viewer.value);
    if (viewer.value) {
        viewer.value.zoomTo();
        viewer.value.render();
    }
};

const toggleSpin = () => {
    if (!viewer.value) return;
    isSpinning.value = !isSpinning.value;
    viewer.value.spin(isSpinning.value);
};

const toggleStyle = () => {
    if (!viewer.value) return;
    currentStyleIndex = (currentStyleIndex + 1) % styles.length;
    viewer.value.setStyle({}, styles[currentStyleIndex].style);
    viewer.value.render();
};

// Initialize 3Dmol viewer
const initViewer = async () => {
  console.log('MoleculeViewer: initializing with src:', props.src);
  if (!viewerContainer.value) {
      console.warn('MoleculeViewer: viewerContainer is null');
      return;
  }
  
  // Wait for 3Dmol to be available globally
  if (!(window as any).$3Dmol) {
    console.log('MoleculeViewer: $3Dmol not ready, retrying...');
    // If not loaded yet, try again in 500ms
    setTimeout(initViewer, 500);
    return;
  }

  try {
    loading.value = true;
    error.value = null;

    // Create viewer
    const $3Dmol = (window as any).$3Dmol;
    viewer.value = $3Dmol.createViewer(viewerContainer.value, {
      backgroundColor: 'white',
    });

    // Fetch molecule data
    console.log('MoleculeViewer: fetching data from', props.src);
    const response = await fetch(props.src);
    console.log('MoleculeViewer: fetch response status:', response.status);
    
    if (!response.ok) {
      const text = await response.text();
      console.error('MoleculeViewer: fetch failed response:', text);
      throw new Error(`Failed to load molecule: ${response.statusText} (${response.status})`);
    }
    const data = await response.text();
    console.log('MoleculeViewer: fetched data length:', data.length);
    console.log('MoleculeViewer: fetched data preview:', data.substring(0, 100));

    if (!data || data.trim().length === 0) {
        throw new Error('Fetched molecule data is empty');
    }
    
    // Determine format from extension in src or try to auto-detect
    let format = 'sdf'; // Default
    // Handle URL parameters or clean path
    const cleanSrc = props.src.split('?')[0];
    if (cleanSrc.endsWith('.mol')) format = 'mol';
    else if (cleanSrc.endsWith('.pdb')) format = 'pdb';
    
    // Add model
    viewer.value.addModel(data, format);
    
    // Style: Stick representation
    viewer.value.setStyle({}, { stick: {} });
    
    // Zoom to fit
    viewer.value.zoomTo();
    viewer.value.render();
    viewer.value.resize();
    
    // Render 2D structure if OCL is available
    if ((window as any).OCL && (format === 'mol' || format === 'sdf')) {
        try {
            const OCL = (window as any).OCL;
            const mol = OCL.Molecule.fromMolfile(data);
            const svg = mol.toSVG(150, 150); // Smaller size for thumbnail
            
            // Calculate basic info
            moleculeInfo.value = {
                formula: mol.getMolecularFormula().formula,
                weight: mol.getMolecularFormula().absoluteWeight.toFixed(2),
                atoms: mol.getAllAtoms(),
                bonds: mol.getAllBonds()
            };

            // Create container for 2D view
            const container2d = document.createElement('div');
            // Use flex to center SVG
            container2d.className = 'absolute bottom-2 right-2 w-40 h-40 bg-white border border-gray-200 rounded shadow-lg p-2 z-20 flex items-center justify-center';
            container2d.innerHTML = svg;
            viewerContainer.value.appendChild(container2d);
        } catch (e) {
            console.warn('Failed to render 2D structure:', e);
        }
    } else if (!(window as any).OCL) {
        console.warn('OpenChemLib (OCL) not loaded');
        // Still show 3D even if 2D/info fails
    } else {
        // Fallback for non-mol/sdf formats or other issues
        moleculeInfo.value = null;
    }

    loading.value = false;
  } catch (e: any) {
    console.error('Molecule viewer error:', e);
    error.value = e.message || 'Failed to render molecule';
    loading.value = false;
  }
};



// Re-init if src changes
watch(() => props.src, () => {
  if (viewer.value) {
    viewer.value.clear();
  }
  initViewer();
});

// Handle resize
const handleResize = () => {
  if (viewer.value) {
    viewer.value.resize();
  }
};

let resizeObserver: ResizeObserver | null = null;

onMounted(() => {
  initViewer();
  
  if (viewerContainer.value) {
    resizeObserver = new ResizeObserver(() => {
        handleResize();
    });
    resizeObserver.observe(viewerContainer.value);
  }
});

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect();
  }
});
</script>