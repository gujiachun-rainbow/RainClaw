<template>
    <div class="w-full">
        <!-- User Card -->
        <div class="relative p-5 rounded-2xl bg-gradient-to-br from-blue-50/80 via-indigo-50/40 to-purple-50/60 dark:from-blue-900/20 dark:via-indigo-900/10 dark:to-purple-900/15 border border-blue-100/50 dark:border-blue-800/30">
            <div class="flex items-center gap-4">
                <!-- Avatar -->
                <div class="relative flex-shrink-0">
                    <div class="size-16 rounded-2xl bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white text-2xl shadow-lg shadow-blue-500/25">
                        {{ avatarLetter }}
                    </div>
                    <div class="absolute -bottom-1 -right-1 size-5 rounded-full bg-emerald-400 border-[2.5px] border-white dark:border-gray-900 flex items-center justify-center">
                        <Check :size="10" class="text-white" stroke-width="3" />
                    </div>
                </div>

                <!-- User Info -->
                <div class="flex flex-col min-w-0 flex-1">
                    <span class="text-xl font-bold text-gray-800 dark:text-gray-100 truncate">
                        {{ currentUser?.fullname || t('Unknown User') }}
                    </span>
                    <span class="text-sm text-gray-500 dark:text-gray-400 truncate mt-0.5">
                        {{ currentUser?.email || t('No email') }}
                    </span>
                </div>

                <!-- Action Buttons -->
                <div class="flex gap-2 flex-shrink-0">
                    <button @click="handleProfileClick"
                        class="size-10 rounded-xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-gray-200/60 dark:border-gray-700/40 flex items-center justify-center cursor-pointer shadow-sm hover:shadow-md hover:border-blue-200 dark:hover:border-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-all duration-200 group">
                        <UserCog :size="18" class="text-gray-400 group-hover:text-blue-500 transition-colors" />
                    </button>
                    <button v-if="authProvider !== 'none'" @click="handleLogout"
                        class="size-10 rounded-xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-gray-200/60 dark:border-gray-700/40 flex items-center justify-center cursor-pointer shadow-sm hover:shadow-md hover:border-red-200 dark:hover:border-red-700 hover:bg-red-50 dark:hover:bg-red-900/30 transition-all duration-200 group">
                        <LogOut :size="18" class="text-gray-400 group-hover:text-red-500 transition-colors" />
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { UserCog, LogOut, Check } from 'lucide-vue-next';
import { useAuth } from '../../composables/useAuth';
import { getCachedAuthProvider } from '../../api/auth';

const router = useRouter();
const { t } = useI18n();
const { currentUser, logout } = useAuth();
const authProvider = ref<string | null>(null);

// Emit events for parent components
const emit = defineEmits<{
  navigateToProfile: []
}>();

// Get first letter of user's fullname for avatar display
const avatarLetter = computed(() => {
  return currentUser.value?.fullname?.charAt(0)?.toUpperCase() || 'M';
});

// Handle profile icon click
const handleProfileClick = () => {
  emit('navigateToProfile');
};

// Handle logout action
const handleLogout = async () => {
  try {
    await logout();
    router.push('/login');
  } catch (error) {
    console.error('Logout failed:', error);
  }
};

onMounted(async () => {
   authProvider.value = await getCachedAuthProvider();
});
</script>
