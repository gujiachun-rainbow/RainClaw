<template>
  <div class="h-screen flex overflow-hidden bg-[#f8f9fb] dark:bg-[#111]">
    <div class="flex-1 min-w-0 h-full relative">
      <div class="flex h-full">
        <div class="flex flex-1 min-w-0 min-h-0">
          <router-view />
          <FilePanel />
        </div>
      </div>
    </div>
  </div>
  <CustomDialog />
  <SessionFileList />
</template>

<script setup lang="ts">
import CustomDialog from '@/components/ui/CustomDialog.vue';
import SessionFileList from '@/components/SessionFileList.vue';
import FilePanel from '@/components/FilePanel.vue';
</script>
