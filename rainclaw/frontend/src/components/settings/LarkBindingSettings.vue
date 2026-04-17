<template>
  <div class="flex flex-col w-full gap-5">
    <div class="p-4 rounded-xl bg-gray-50/80 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50">
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-sm font-semibold text-gray-700 dark:text-gray-200">飞书账号绑定状态</span>
          <span class="text-xs" :class="statusTextClass">{{ statusText }}</span>
        </div>
        <button
          @click="$emit('back')"
          class="px-3 py-1.5 rounded-lg text-xs font-medium bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:border-blue-300 dark:hover:border-blue-600 transition-colors cursor-pointer">
          返回
        </button>
      </div>
      <div v-if="status.bound" class="mt-3 text-xs text-gray-500 dark:text-gray-400">
        已绑定用户 ID：{{ status.platform_user_id }}
      </div>
    </div>

    <div class="p-4 rounded-xl bg-gray-50/80 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50">
      <label class="text-sm font-semibold text-gray-700 dark:text-gray-200">飞书用户 ID（open_id / 配对命令）</label>
      <input
        v-model="larkUserId"
        placeholder="例如：ou_xxx 或 /bind_lark ou_xxx"
        class="mt-2 w-full h-10 rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 px-3 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 dark:focus:border-blue-600" />
      <p class="mt-2 text-xs text-gray-500 dark:text-gray-400">
        可直接粘贴机器人返回的 <code>/bind_lark ou_xxx</code> 配对命令，或只粘贴 open_id。
      </p>
      <div class="mt-3 flex gap-2">
        <button
          @click="handleBind"
          :disabled="loading || !larkUserId.trim()"
          class="px-4 py-2 rounded-xl text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer">
          {{ loading ? '绑定中...' : '立即绑定' }}
        </button>
        <button
          @click="handleRefresh"
          :disabled="loading"
          class="px-4 py-2 rounded-xl text-sm font-medium bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:border-blue-300 dark:hover:border-blue-600 transition-colors cursor-pointer">
          刷新状态
        </button>
      </div>
    </div>

    <div class="p-4 rounded-xl bg-gray-50/80 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50">
      <div class="flex items-center justify-between">
        <div class="flex flex-col">
          <span class="text-sm font-semibold text-gray-700 dark:text-gray-200">解除绑定</span>
          <span class="text-xs text-gray-500 dark:text-gray-400">解除后机器人会提示重新配对</span>
        </div>
        <button
          @click="handleUnbind"
          :disabled="loading || !status.bound"
          class="px-4 py-2 rounded-xl text-sm font-medium bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer">
          {{ loading ? '处理中...' : '解除绑定' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { bindLarkAccount, getLarkBindingStatus, unbindLarkAccount, type LarkBindingStatus } from '../../api/im';
import { showErrorToast, showSuccessToast } from '../../utils/toast';

const emit = defineEmits<{
  back: []
}>();

const status = ref<LarkBindingStatus>({ bound: false });
const larkUserId = ref('');
const loading = ref(false);

const statusText = computed(() => {
  if (!status.value.bound) {
    return '未绑定';
  }
  return '已绑定';
});

const statusTextClass = computed(() => {
  if (!status.value.bound) {
    return 'text-amber-600 dark:text-amber-400';
  }
  return 'text-emerald-600 dark:text-emerald-400';
});

const handleRefresh = async () => {
  loading.value = true;
  try {
    status.value = await getLarkBindingStatus();
    if (status.value.bound && status.value.platform_user_id) {
      larkUserId.value = status.value.platform_user_id;
    }
  } catch (error: any) {
    showErrorToast(error?.response?.data?.msg || error?.message || '获取绑定状态失败');
  } finally {
    loading.value = false;
  }
};

const handleBind = async () => {
  const userId = larkUserId.value.trim();
  if (!userId) {
    showErrorToast('请先输入飞书用户 ID');
    return;
  }
  loading.value = true;
  try {
    await bindLarkAccount({ lark_user_id: userId });
    showSuccessToast('飞书账号绑定成功');
    await handleRefresh();
  } catch (error: any) {
    showErrorToast(error?.response?.data?.msg || error?.message || '绑定失败');
  } finally {
    loading.value = false;
  }
};

const handleUnbind = async () => {
  loading.value = true;
  try {
    await unbindLarkAccount();
    showSuccessToast('飞书账号已解绑');
    await handleRefresh();
  } catch (error: any) {
    showErrorToast(error?.response?.data?.msg || error?.message || '解绑失败');
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  handleRefresh();
});
</script>
