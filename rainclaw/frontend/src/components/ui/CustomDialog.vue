<template>
    <Teleport to="body">
        <Transition name="dialog">
            <div v-if="dialogVisible" class="fixed inset-0 z-[9999] flex items-center justify-center">
                <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="handleBackdropClick"></div>
                <div class="relative bg-white dark:bg-[#2a2a2a] rounded-2xl shadow-2xl w-[440px] max-w-[95%] max-h-[95%] overflow-auto z-10">
                    <div class="pt-5 pb-3 px-5 flex items-center justify-between">
                        <h3 class="text-[var(--text-primary)] text-lg font-semibold">{{ dialogConfig.title }}</h3>
                        <button @click="handleCancel"
                            class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-[var(--text-tertiary)]">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                                stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M18 6 6 18"></path>
                                <path d="m6 6 12 12"></path>
                            </svg>
                        </button>
                    </div>
                    <div v-if="dialogConfig.content" class="px-5 py-2 text-sm text-[var(--text-secondary)] leading-relaxed">
                        {{ dialogConfig.content }}
                    </div>
                    <div class="flex justify-end gap-2 p-5">
                        <button
                            class="px-4 py-2 text-sm rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-[#2a2a2a] text-[var(--text-secondary)] hover:bg-gray-50 dark:hover:bg-gray-800 transition-all"
                            @click="handleCancel">{{ dialogConfig.cancelText }}</button>
                        <button
                            :class="[
                                'px-4 py-2 text-sm rounded-xl font-medium transition-all duration-200',
                                dialogConfig.confirmType === 'danger'
                                    ? 'bg-red-500 text-white hover:bg-red-600 active:scale-[0.97]'
                                    : 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white hover:shadow-lg hover:shadow-indigo-500/20 active:scale-[0.97]'
                            ]"
                            @click="handleConfirm">{{ dialogConfig.confirmText }}</button>
                    </div>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<script setup lang="ts">
import { useDialog } from '@/composables/useDialog'

const { dialogVisible, dialogConfig, handleConfirm, handleCancel } = useDialog()

const handleBackdropClick = () => { handleCancel() }
</script>

<style scoped>
.dialog-enter-active { transition: all 0.25s ease-out; }
.dialog-leave-active { transition: all 0.2s ease-in; }
.dialog-enter-from, .dialog-leave-to { opacity: 0; }
.dialog-enter-from > div:last-child { transform: scale(0.95) translateY(10px); }
.dialog-leave-to > div:last-child { transform: scale(0.95) translateY(10px); }
</style>
