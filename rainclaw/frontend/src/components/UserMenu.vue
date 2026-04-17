<template>
    <div class="pointer-events-auto cursor-default">
        <div class="min-w-max inline-block transition-all duration-300 ease-out transform origin-top-right"
            :class="[isVisible ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-95 -translate-y-2']"
            tabindex="-1"
            role="dialog">
            <div class="flex w-[300px] flex-col bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl rounded-2xl border border-gray-200/60 dark:border-gray-700/40 shadow-2xl shadow-black/10">
                <!-- User Info Header -->
                <div class="flex gap-3 px-4 pt-5 pb-4 w-full">
                    <div class="relative flex-shrink-0">
                        <div class="size-12 rounded-xl bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white text-xl shadow-md shadow-blue-500/25">
                            {{ avatarLetter }}
                        </div>
                        <div class="absolute -bottom-0.5 -right-0.5 size-3.5 rounded-full bg-emerald-400 border-2 border-white dark:border-gray-900"></div>
                    </div>
                    <div class="flex overflow-hidden flex-col justify-center min-w-0">
                        <span class="text-[15px] font-semibold text-gray-800 dark:text-gray-100 truncate">
                            {{ currentUser?.fullname || t('Unknown User') }}
                        </span>
                        <span class="text-[12px] text-gray-400 dark:text-gray-500 truncate mt-0.5">
                            {{ currentUser?.email || t('No email') }}
                        </span>
                    </div>
                </div>

                <!-- Divider -->
                <div class="mx-4 h-px bg-gradient-to-r from-transparent via-gray-200 dark:via-gray-700 to-transparent"></div>

                <!-- Menu Items -->
                <div class="flex flex-col p-2 gap-0.5">
                    <div class="menu-item flex gap-3 items-center px-3 py-2.5 rounded-xl cursor-pointer text-gray-600 dark:text-gray-300 transition-all duration-150 hover:bg-blue-50/80 dark:hover:bg-blue-900/20 hover:text-blue-600 dark:hover:text-blue-400 group"
                        @click="handleAccountClick">
                        <div class="size-8 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center transition-colors group-hover:bg-blue-100 dark:group-hover:bg-blue-900/50">
                            <User :size="16" class="text-blue-500" />
                        </div>
                        <span class="text-sm font-medium">{{ t('Account') }}</span>
                        <ChevronRight :size="14" class="ml-auto text-gray-300 dark:text-gray-600 group-hover:text-blue-400 transition-all group-hover:translate-x-0.5" />
                    </div>

                    <div class="menu-item flex gap-3 items-center px-3 py-2.5 rounded-xl cursor-pointer text-gray-600 dark:text-gray-300 transition-all duration-150 hover:bg-cyan-50/80 dark:hover:bg-cyan-900/20 hover:text-cyan-600 dark:hover:text-cyan-400 group"
                        @click="handlePersonalizationClick">
                        <div class="size-8 rounded-lg bg-cyan-50 dark:bg-cyan-900/30 flex items-center justify-center transition-colors group-hover:bg-cyan-100 dark:group-hover:bg-cyan-900/50">
                            <Brain :size="16" class="text-cyan-500" />
                        </div>
                        <span class="text-sm font-medium">{{ t('Personalization') }}</span>
                        <ChevronRight :size="14" class="ml-auto text-gray-300 dark:text-gray-600 group-hover:text-cyan-400 transition-all group-hover:translate-x-0.5" />
                    </div>

                    <div class="menu-item flex gap-3 items-center px-3 py-2.5 rounded-xl cursor-pointer text-gray-600 dark:text-gray-300 transition-all duration-150 hover:bg-violet-50/80 dark:hover:bg-violet-900/20 hover:text-violet-600 dark:hover:text-violet-400 group"
                        @click="handleSettingsClick">
                        <div class="size-8 rounded-lg bg-violet-50 dark:bg-violet-900/30 flex items-center justify-center transition-colors group-hover:bg-violet-100 dark:group-hover:bg-violet-900/50">
                            <Settings2 :size="16" class="text-violet-500" />
                        </div>
                        <span class="text-sm font-medium">{{ t('Settings') }}</span>
                        <ChevronRight :size="14" class="ml-auto text-gray-300 dark:text-gray-600 group-hover:text-violet-400 transition-all group-hover:translate-x-0.5" />
                    </div>

                    <div class="menu-item flex gap-3 items-center px-3 py-2.5 rounded-xl cursor-pointer text-gray-600 dark:text-gray-300 transition-all duration-150 hover:bg-emerald-50/80 dark:hover:bg-emerald-900/20 hover:text-emerald-600 dark:hover:text-emerald-400 group"
                        @click="handleModelsClick">
                        <div class="size-8 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 flex items-center justify-center transition-colors group-hover:bg-emerald-100 dark:group-hover:bg-emerald-900/50">
                            <Box :size="16" class="text-emerald-500" />
                        </div>
                        <span class="text-sm font-medium">{{ t('Models') }}</span>
                        <ChevronRight :size="14" class="ml-auto text-gray-300 dark:text-gray-600 group-hover:text-emerald-400 transition-all group-hover:translate-x-0.5" />
                    </div>

                    <div class="menu-item flex gap-3 items-center px-3 py-2.5 rounded-xl cursor-pointer text-gray-600 dark:text-gray-300 transition-all duration-150 hover:bg-amber-50/80 dark:hover:bg-amber-900/20 hover:text-amber-600 dark:hover:text-amber-400 group"
                        @click="handleTasksClick">
                        <div class="size-8 rounded-lg bg-amber-50 dark:bg-amber-900/30 flex items-center justify-center transition-colors group-hover:bg-amber-100 dark:group-hover:bg-amber-900/50">
                            <ListTodo :size="16" class="text-amber-500" />
                        </div>
                        <span class="text-sm font-medium">{{ t('Tasks') }}</span>
                        <ChevronRight :size="14" class="ml-auto text-gray-300 dark:text-gray-600 group-hover:text-amber-400 transition-all group-hover:translate-x-0.5" />
                    </div>

                    <div class="menu-item flex gap-3 items-center px-3 py-2.5 rounded-xl cursor-pointer text-gray-600 dark:text-gray-300 transition-all duration-150 hover:bg-rose-50/80 dark:hover:bg-rose-900/20 hover:text-rose-600 dark:hover:text-rose-400 group"
                        @click="handleNotificationsClick">
                        <div class="size-8 rounded-lg bg-rose-50 dark:bg-rose-900/30 flex items-center justify-center transition-colors group-hover:bg-rose-100 dark:group-hover:bg-rose-900/50">
                            <Bell :size="16" class="text-rose-500" />
                        </div>
                        <span class="text-sm font-medium">{{ t('Notifications') }}</span>
                        <ChevronRight :size="14" class="ml-auto text-gray-300 dark:text-gray-600 group-hover:text-rose-400 transition-all group-hover:translate-x-0.5" />
                    </div>

                    <div class="menu-item flex gap-3 items-center px-3 py-2.5 rounded-xl cursor-pointer text-gray-600 dark:text-gray-300 transition-all duration-150 hover:bg-teal-50/80 dark:hover:bg-teal-900/20 hover:text-teal-600 dark:hover:text-teal-400 group"
                        @click="handleIMClick">
                        <div class="size-8 rounded-lg bg-teal-50 dark:bg-teal-900/30 flex items-center justify-center transition-colors group-hover:bg-teal-100 dark:group-hover:bg-teal-900/50">
                            <MessageSquare :size="16" class="text-teal-500" />
                        </div>
                        <span class="text-sm font-medium">IM</span>
                        <ChevronRight :size="14" class="ml-auto text-gray-300 dark:text-gray-600 group-hover:text-teal-400 transition-all group-hover:translate-x-0.5" />
                    </div>
                </div>

                <!-- Logout Section -->
                <template v-if="authProvider !== 'none'">
                    <div class="mx-4 h-px bg-gradient-to-r from-transparent via-gray-200 dark:via-gray-700 to-transparent"></div>
                    <div class="p-2">
                        <div class="menu-item flex gap-3 items-center px-3 py-2.5 rounded-xl cursor-pointer transition-all duration-150 hover:bg-red-50/80 dark:hover:bg-red-900/20 group"
                            @click="handleLogout">
                            <div class="size-8 rounded-lg bg-red-50 dark:bg-red-900/30 flex items-center justify-center transition-colors group-hover:bg-red-100 dark:group-hover:bg-red-900/50">
                                <LogOut :size="16" class="text-red-400 group-hover:text-red-500" />
                            </div>
                            <span class="text-sm font-medium text-red-400 group-hover:text-red-500">{{ t('Logout') }}</span>
                        </div>
                    </div>
                </template>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useAuth } from '../composables/useAuth';
import { useSettingsDialog } from '../composables/useSettingsDialog';
import { getCachedAuthProvider } from '../api/auth';
import { LogOut, User, Settings2, Box, ListTodo, ChevronRight, Brain, Bell, MessageSquare } from 'lucide-vue-next';

const router = useRouter();
const { t } = useI18n();
const { currentUser, logout } = useAuth();
const { openSettingsDialog } = useSettingsDialog();
const authProvider = ref<string | null>(null);
const isVisible = ref(false);

// Get first letter of user's fullname for avatar display
const avatarLetter = computed(() => {
    return currentUser.value?.fullname?.charAt(0)?.toUpperCase() || 'M';
});

// Handle Account click - open settings dialog with account tab
const handleAccountClick = () => {
    openSettingsDialog('account');
};

// Handle Personalization click - open settings dialog with personalization tab
const handlePersonalizationClick = () => {
    openSettingsDialog('personalization');
};

// Handle Settings click - open settings dialog with settings tab
const handleSettingsClick = () => {
    openSettingsDialog('settings');
};

// Handle Models click - open settings dialog with models tab
const handleModelsClick = () => {
    openSettingsDialog('models');
};

// Handle Tasks click - open settings dialog with tasks tab
const handleTasksClick = () => {
    openSettingsDialog('tasks');
};

const handleNotificationsClick = () => {
    openSettingsDialog('notifications');
};

const handleIMClick = () => {
    openSettingsDialog('im');
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
    // Trigger animation on mount
    requestAnimationFrame(() => {
        isVisible.value = true;
    });
});
</script>
