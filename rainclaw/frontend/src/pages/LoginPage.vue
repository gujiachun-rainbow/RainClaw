<template>
  <div class="w-full min-h-[100vh] relative overflow-hidden bg-[#f8f9fb] dark:bg-[#050505]">
    <!-- Background decoration -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-[40%] -left-[20%] w-[60%] h-[60%] rounded-full bg-gradient-to-br from-blue-400/8 via-indigo-400/6 to-purple-400/4 blur-3xl"></div>
      <div class="absolute -bottom-[30%] -right-[20%] w-[50%] h-[50%] rounded-full bg-gradient-to-br from-violet-400/6 via-fuchsia-400/4 to-pink-400/3 blur-3xl"></div>
      <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiMwMDAiIGZpbGwtb3BhY2l0eT0iMC4wMiI+PHBhdGggZD0iTTM2IDM0djZoLTZ2LTZoNnptMC0zMHY2aC02VjRoNnoiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-60"></div>
    </div>

    <!-- Top Bar -->
    <div class="sticky top-0 left-0 w-full z-[10] px-[48px] max-sm:px-[12px]">
      <div class="w-full h-[60px] mx-auto flex items-center justify-between text-[var(--text-primary)]">
        <a href="/" class="flex items-center gap-2 group">
          <div class="w-[30px] h-[30px] transition-transform duration-300 group-hover:scale-110">
            <RobotAvatar :interactive="false" />
          </div>
          <RainClawLogoTextIcon />
        </a>
        <div class="flex items-center">
          <LanguageSelector />
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="relative z-[1] flex flex-col justify-center items-center min-h-[100vh] pt-[20px] pb-[60px] -mt-[60px] max-sm:pt-[80px] max-sm:pb-[80px] max-sm:mt-0 max-sm:min-h-[calc(100vh-60px)] max-sm:justify-start">
      <!-- Logo + Title -->
      <div class="login-header w-full max-w-[720px] pt-[24px] mb-[32px] max-sm:pt-[0px]">
        <div class="flex flex-col items-center gap-[16px]">
          <div class="size-[72px] rounded-2xl bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 flex items-center justify-center shadow-xl shadow-indigo-500/20 max-sm:size-[56px]">
            <RobotAvatar class="w-[44px] h-[44px] max-sm:w-[36px] max-sm:h-[36px]" :interactive="true" />
          </div>
          <h1 class="text-[20px] font-bold text-center text-[var(--text-primary)] max-sm:text-[18px]">
            <template v-if="isResettingPassword">{{ t('Reset Password') }}</template>
            <template v-else-if="isRegistering">{{ t('Register to') }} <span class="brand-text bg-clip-text text-transparent bg-gradient-to-r from-blue-500 via-red-500 to-amber-500" style="background-size:200% 100%">RainClaw</span></template>
            <template v-else>{{ t('Login to') }} <span class="brand-text bg-clip-text text-transparent bg-gradient-to-r from-blue-500 via-red-500 to-amber-500" style="background-size:200% 100%">RainClaw</span></template>
          </h1>
          <p class="text-xs text-[var(--text-tertiary)] -mt-2">
            {{ isResettingPassword ? t('Enter your email to receive a reset link') : isRegistering ? t('Create your account to get started') : t('Sign in to continue your research') }}
          </p>
        </div>
      </div>

      <!-- Form Card -->
      <div class="login-card w-full max-w-[420px] px-4">
        <div class="bg-white/80 dark:bg-[#1a1a1a]/80 backdrop-blur-xl rounded-2xl border border-gray-100 dark:border-gray-800 shadow-xl shadow-black/5 p-6">
          <LoginForm v-if="!isRegistering && !isResettingPassword" 
            @success="handleLoginSuccess" 
            @switch-to-register="switchToRegister" 
            @switch-to-reset="switchToReset" />
          <RegisterForm v-else-if="isRegistering && !isResettingPassword" 
            @success="handleLoginSuccess" 
            @switch-to-login="switchToLogin" />
          <ResetPasswordForm v-else-if="isResettingPassword" 
            @back-to-login="switchToLogin" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import RainClawLogoTextIcon from '@/components/icons/RainClawLogoTextIcon.vue'
import RobotAvatar from '@/components/icons/RobotAvatar.vue'
import LoginForm from '@/components/login/LoginForm.vue'
import RegisterForm from '@/components/login/RegisterForm.vue'
import ResetPasswordForm from '@/components/login/ResetPasswordForm.vue'
import LanguageSelector from '@/components/LanguageSelector.vue'
import { useAuth } from '@/api'

const { t } = useI18n()
const router = useRouter()
const { isAuthenticated } = useAuth()

const isRegistering = ref(false)
const isResettingPassword = ref(false)

const switchToRegister = () => { isRegistering.value = true; isResettingPassword.value = false }
const switchToLogin = () => { isRegistering.value = false; isResettingPassword.value = false }
const switchToReset = () => { isRegistering.value = false; isResettingPassword.value = true }

const handleLoginSuccess = () => {
  const redirect = router.currentRoute.value.query.redirect as string
  router.push(redirect || '/')
}

watch(isAuthenticated, (authenticated) => { if (authenticated) handleLoginSuccess() })
onMounted(() => { if (isAuthenticated.value) router.push('/') })
</script>

<style scoped>
.login-header {
  animation: fadeInDown 0.5s ease-out;
}
.login-card {
  animation: fadeInUp 0.5s ease-out 0.1s both;
}
@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-16px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
.brand-text {
  animation: gradientShift 4s ease-in-out infinite;
}
@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
</style>
