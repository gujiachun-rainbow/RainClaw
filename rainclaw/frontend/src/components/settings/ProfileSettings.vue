<template>
    <div class="flex flex-col w-full gap-6">
        <!-- Avatar & Name Section -->
        <div class="flex items-center gap-6 pb-6 border-b border-gray-100 dark:border-gray-800">
            <!-- Avatar -->
            <div class="relative flex-shrink-0">
                <div class="size-20 rounded-2xl bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white text-[36px] shadow-lg shadow-blue-500/20">
                    {{ avatarLetter }}
                </div>
            </div>

            <!-- Name Input -->
            <div class="flex flex-col gap-1.5 flex-1">
                <label class="text-sm font-semibold text-gray-500 dark:text-gray-400">{{ t('Name') }}</label>
                <div class="group relative w-full sm:w-[300px]">
                    <input
                        maxlength="20"
                        class="w-full h-10 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-4 text-sm font-medium text-gray-800 dark:text-gray-100 placeholder:text-gray-300 dark:placeholder:text-gray-600 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 dark:focus:border-blue-600"
                        v-model="localFullname"
                        @blur="handleFullnameSubmit"
                        @keyup.enter="handleFullnameSubmit"
                        :placeholder="t('Unknown User')"
                    />
                    <button @click="clearFullname"
                        class="absolute right-3 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-60 group-focus-within:opacity-60 hover:!opacity-100 transition-opacity cursor-pointer">
                        <ClearIcon :size="14" class="text-gray-400" />
                    </button>
                </div>
            </div>
        </div>

        <!-- Info Cards -->
        <div class="flex flex-col gap-3">
            <!-- Email Card -->
            <div class="flex items-center justify-between p-4 rounded-xl bg-gray-50/80 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50">
                <div class="flex items-center gap-3">
                    <div class="size-9 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center">
                        <Mail :size="16" class="text-blue-500" />
                    </div>
                    <div class="flex flex-col">
                        <span class="text-sm font-semibold text-gray-700 dark:text-gray-200">{{ t('Email') }}</span>
                        <span class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{{ currentUser?.email || t('No email') }}</span>
                    </div>
                </div>
            </div>

            <!-- Password Card -->
            <div class="flex items-center justify-between p-4 rounded-xl bg-gray-50/80 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50">
                <div class="flex items-center gap-3">
                    <div class="size-9 rounded-lg bg-amber-50 dark:bg-amber-900/30 flex items-center justify-center">
                        <Lock :size="16" class="text-amber-500" />
                    </div>
                    <div class="flex flex-col">
                        <span class="text-sm font-semibold text-gray-700 dark:text-gray-200">{{ t('Password') }}</span>
                        <div class="flex items-center gap-1 mt-1">
                            <span v-for="i in 8" :key="i" class="size-1.5 rounded-full bg-gray-300 dark:bg-gray-600"></span>
                        </div>
                    </div>
                </div>
                <button @click="openChangePasswordDialog"
                    class="px-4 py-2 rounded-xl text-sm font-medium bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 shadow-sm hover:shadow-md hover:border-blue-200 dark:hover:border-blue-600 hover:text-blue-600 dark:hover:text-blue-400 transition-all duration-200">
                    {{ t('Update Password') }}
                </button>
            </div>
        </div>
    </div>

    <!-- Change Password Dialog -->
    <ChangePasswordDialog ref="changePasswordDialogRef" />
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { Mail, Lock } from 'lucide-vue-next';
import { useAuth } from '../../composables/useAuth';
import { changeFullname } from '../../api/auth';
import { showSuccessToast, showErrorToast } from '../../utils/toast';
import ClearIcon from '../icons/ClearIcon.vue';
import ChangePasswordDialog from './ChangePasswordDialog.vue';

const { t } = useI18n();
const { currentUser, loadCurrentUser } = useAuth();

// Dialog refs
const changePasswordDialogRef = ref<InstanceType<typeof ChangePasswordDialog>>();

// Local fullname state
const localFullname = ref(currentUser.value?.fullname || '');

// Watch for currentUser changes to sync localFullname
watch(currentUser, (newUser) => {
  if (newUser) {
    localFullname.value = newUser.fullname || '';
  }
}, { immediate: true });



// Update fullname function
const updateFullname = async (newFullname: string) => {
  // Skip if empty or same as current
  if (!newFullname.trim() || newFullname === currentUser.value?.fullname) {
    return;
  }

  try {
    await changeFullname({ fullname: newFullname.trim() });
    // Refresh current user data to get updated info
    await loadCurrentUser();
    showSuccessToast(t('Full name updated successfully'));
  } catch (error: any) {
    console.error('Failed to update fullname:', error);
    // Reset local state to original value
    localFullname.value = currentUser.value?.fullname || '';
    
    // Show error message
    const errorMessage = error?.response?.data?.message || error?.message || t('Failed to update full name');
    showErrorToast(errorMessage);
  }
};

// Handle input change on blur or Enter
const handleFullnameSubmit = () => {
  updateFullname(localFullname.value);
};

// Clear fullname input
const clearFullname = () => {
  localFullname.value = '';
};

// Get first letter of user's fullname for avatar display
const avatarLetter = computed(() => {
  return currentUser.value?.fullname?.charAt(0)?.toUpperCase() || 'M';
});

// Open change password dialog
const openChangePasswordDialog = () => {
  changePasswordDialogRef.value?.open();
};
</script>
