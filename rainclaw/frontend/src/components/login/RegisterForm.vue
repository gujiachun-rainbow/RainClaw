<template>
  <div class="w-full max-w-[384px] py-[24px] pt-0 px-[12px] relative" style="z-index:1">
    <div class="flex flex-col justify-center gap-[40px] text-[var(--text-primary)] max-sm:gap-[12px]">
      <form @submit.prevent="handleSubmit" class="flex flex-col items-stretch gap-[20px]">
        <div class="relative">
          <div class="transition-all duration-500 ease-out opacity-100 scale-100">
            <div class="flex flex-col gap-[12px]">
              <!-- Full name field -->
              <div class="flex flex-col items-start">
                <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                  <label for="fullname"
                    class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                    <span>{{ t('Full Name') }}</span>
                  </label>
                </div>
                <input v-model="formData.fullname"
                  class="rounded-xl overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-white dark:bg-[#2a2a2a] border border-gray-200 dark:border-gray-700 pt-1 pr-1.5 pb-1 pl-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all duration-200 w-full"
                  :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.fullname }" id="fullname"
                  :placeholder="t('Enter your full name')" :disabled="isLoading" @input="validateField('fullname')"
                  @blur="validateField('fullname')">
                <div
                  class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                  :class="validationErrors.fullname ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                  {{ validationErrors.fullname }}
                </div>
              </div>

              <!-- Email field -->
              <div class="flex flex-col items-start">
                <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                  <label for="email"
                    class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                    <span>{{ t('Email') }}</span>
                  </label>
                </div>
                <input v-model="formData.email"
                  class="rounded-xl overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-white dark:bg-[#2a2a2a] border border-gray-200 dark:border-gray-700 pt-1 pr-1.5 pb-1 pl-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all duration-200 w-full"
                  :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.email }" id="email"
                  placeholder="mail@domain.com" type="email" :disabled="isLoading" @input="validateField('email')"
                  @blur="validateField('email')">
                <div
                  class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                  :class="validationErrors.email ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                  {{ validationErrors.email }}
                </div>
              </div>

              <!-- Verification Code field -->
              <div class="flex flex-col items-start">
                <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                  <label for="verificationCode"
                    class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                    <span>{{ t('Verification Code') }}</span>
                  </label>
                </div>
                <div class="w-full flex gap-[12px]">
                  <input v-model="formData.verificationCode"
                    class="rounded-xl overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-white dark:bg-[#2a2a2a] border border-gray-200 dark:border-gray-700 pt-1 pr-1.5 pb-1 pl-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all duration-200 flex-1"
                    :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.verificationCode }" id="verificationCode"
                    placeholder="Enter verification code" type="text" :disabled="isLoading || isSendingCode"
                    @input="validateField('verificationCode')" @blur="validateField('verificationCode')">
                  <button type="button"
                    class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors h-10 px-[16px] rounded-[10px] gap-[6px] text-sm"
                    :class="(!isLoading && !isSendingCode && !countdown) ? 'bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-600 text-white hover:shadow-xl hover:shadow-indigo-500/25 active:scale-[0.98]' : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed shadow-none'"
                    :disabled="isLoading || isSendingCode || countdown > 0 || !formData.email || !!validationErrors.email"
                    @click="sendVerificationCode">
                    <LoaderCircle v-if="isSendingCode" :size="16" class="animate-spin" />
                    <span v-else-if="countdown > 0">{{ countdown }}s</span>
                    <span v-else>{{ t('Send Code') }}</span>
                  </button>
                </div>
                <div
                  class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                  :class="validationErrors.verificationCode ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                  {{ validationErrors.verificationCode }}
                </div>
              </div>

              <!-- Password field -->
              <div class="flex flex-col items-start">
                <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                  <label for="password"
                    class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                    <span>{{ t('Password') }}</span>
                  </label>
                </div>
                <div class="relative w-full">
                  <input v-model="formData.password"
                    class="rounded-xl overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 w-full disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-white dark:bg-[#2a2a2a] border border-gray-200 dark:border-gray-700 pt-1 pb-1 pl-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all duration-200 pr-[40px]"
                    :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.password }"
                    :placeholder="t('Enter password')" :type="showPassword ? 'text' : 'password'"
                    :disabled="isLoading" @input="validateField('password')" @blur="validateField('password')">
                  <div
                    class="text-[var(--icon-tertiary)] absolute z-30 right-[6px] top-[50%] p-[6px] rounded-md transform -translate-y-1/2 cursor-pointer hover:text-[--icon-primary] active:opacity-90 transition-all"
                    @click="showPassword = !showPassword">
                    <Eye v-if="showPassword" :size="16" />
                    <EyeOff v-else :size="16" />
                  </div>
                </div>
                <div
                  class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                  :class="validationErrors.password ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                  {{ validationErrors.password }}
                </div>
              </div>

              <!-- Confirm password field -->
              <div class="flex flex-col items-start">
                <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                  <label for="confirmPassword"
                    class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                    <span>{{ t('Confirm Password') }}</span>
                  </label>
                </div>
                <div class="relative w-full">
                  <input v-model="formData.confirmPassword"
                    class="rounded-xl overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 w-full disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-white dark:bg-[#2a2a2a] border border-gray-200 dark:border-gray-700 pt-1 pb-1 pl-3 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all duration-200 pr-[40px]"
                    :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.confirmPassword }"
                    :placeholder="t('Enter password again')" :type="showConfirmPassword ? 'text' : 'password'"
                    :disabled="isLoading" @input="validateField('confirmPassword')"
                    @blur="validateField('confirmPassword')">
                  <div
                    class="text-[var(--icon-tertiary)] absolute z-30 right-[6px] top-[50%] p-[6px] rounded-md transform -translate-y-1/2 cursor-pointer hover:text-[--icon-primary] active:opacity-90 transition-all"
                    @click="showConfirmPassword = !showConfirmPassword">
                    <Eye v-if="showConfirmPassword" :size="16" />
                    <EyeOff v-else :size="16" />
                  </div>
                </div>
                <div
                  class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                  :class="validationErrors.confirmPassword ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                  {{ validationErrors.confirmPassword }}
                </div>
              </div>

              <!-- Submit button -->
              <button type="submit"
                class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors h-[40px] px-[16px] rounded-[10px] gap-[6px] text-sm min-w-16 w-full"
                :class="isFormValid && !isLoading
                  ? 'bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-600 text-white hover:shadow-xl hover:shadow-indigo-500/25 active:scale-[0.98]'
                  : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed shadow-none'"
                :disabled="!isFormValid || isLoading">
                <LoaderCircle v-if="isLoading" :size="16" class="animate-spin" />
                <span>{{ isLoading ? t('Processing...') : t('Register') }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Toggle to login -->
        <div class="text-center text-[13px] leading-[18px] text-[var(--text-tertiary)] mt-[8px]">
          <span>{{ t('Already have an account?') }}</span>
          <span
            class="ms-[8px] text-[var(--text-secondary)] cursor-pointer select-none hover:opacity-80 active:opacity-70 transition-all underline"
            @click="emits('switchToLogin')">
            {{ t('Login') }}
          </span>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Eye, EyeOff, LoaderCircle } from 'lucide-vue-next'
import { useAuth } from '@/api'
import { validateUserInput } from '@/utils/auth'
import { showErrorToast, showSuccessToast } from '@/utils/toast'

const { t } = useI18n()

// Emits
const emits = defineEmits<{
  success: []
  switchToLogin: []
}>()

const { register, isLoading, authError } = useAuth()

// Form state
const showPassword = ref(false)
const showConfirmPassword = ref(false)

// Form data
const formData = ref({
  fullname: '',
  email: '',
  password: '',
  confirmPassword: '',
  verificationCode: ''
})

// Validation errors
const validationErrors = ref<Record<string, string>>({})

// Verification code related state
const isSendingCode = ref(false)
const countdown = ref(0)
let countdownTimer: number | null = null

// Clear form
const clearForm = () => {
  formData.value = {
    fullname: '',
    email: '',
    password: '',
    confirmPassword: '',
    verificationCode: ''
  }
  validationErrors.value = {}
  resetCountdown()
}

// Reset countdown
const resetCountdown = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  countdown.value = 0
}

// Start countdown
const startCountdown = () => {
  countdown.value = 60
  countdownTimer = window.setInterval(() => {
    if (countdown.value > 0) {
      countdown.value--
    } else {
      resetCountdown()
    }
  }, 1000)
}

// Send verification code
const sendVerificationCode = async () => {
  if (!formData.value.email || validationErrors.value.email) {
    return
  }

  try {
    isSendingCode.value = true
    const response = await fetch('/api/v1/auth/send-verification-code', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email: formData.value.email })
    })

    const result = await response.json()
    if (result.code === 0) {
      showSuccessToast(t('Verification code sent successfully!'))
      startCountdown()
    } else {
      showErrorToast(result.msg || t('Failed to send verification code'))
    }
  } catch (error) {
    console.error('Failed to send verification code:', error)
    showErrorToast(t('Failed to send verification code'))
  } finally {
    isSendingCode.value = false
  }
}

// Validate single field
const validateField = (field: string) => {
  const errors: Record<string, string> = {}

  if (field === 'fullname') {
    const result = validateUserInput({ fullname: formData.value.fullname })
    if (result.errors.fullname) {
      errors.fullname = result.errors.fullname
    }
  }

  if (field === 'email') {
    const result = validateUserInput({ email: formData.value.email })
    if (result.errors.email) {
      errors.email = result.errors.email
    }
  }

  if (field === 'password') {
    const result = validateUserInput({ password: formData.value.password })
    if (result.errors.password) {
      errors.password = result.errors.password
    }
  }

  if (field === 'confirmPassword') {
    if (formData.value.password !== formData.value.confirmPassword) {
      errors.confirmPassword = t('Passwords do not match')
    }
  }

  if (field === 'verificationCode') {
    if (!formData.value.verificationCode.trim()) {
      errors.verificationCode = t('Verification code is required')
    } else if (formData.value.verificationCode.length !== 6) {
      errors.verificationCode = t('Verification code must be 6 digits')
    }
  }

  // Update error state
  Object.keys(errors).forEach(key => {
    validationErrors.value[key] = errors[key]
  })

  // Clear fixed errors
  if (!errors[field]) {
    delete validationErrors.value[field]
  }
}

// Validate entire form
const validateForm = () => {
  const data = {
    fullname: formData.value.fullname,
    email: formData.value.email,
    password: formData.value.password
  }

  const result = validateUserInput(data)
  validationErrors.value = { ...result.errors }

  // Validate confirm password
  if (formData.value.password !== formData.value.confirmPassword) {
    validationErrors.value.confirmPassword = t('Passwords do not match')
  }

  // Validate verification code
  if (!formData.value.verificationCode.trim()) {
    validationErrors.value.verificationCode = t('Verification code is required')
  } else if (formData.value.verificationCode.length !== 6) {
    validationErrors.value.verificationCode = t('Verification code must be 6 digits')
  }

  return Object.keys(validationErrors.value).length === 0
}

// Check if form is valid
const isFormValid = computed(() => {
  const hasRequiredFields = formData.value.fullname.trim() && 
                           formData.value.email.trim() && 
                           formData.value.password.trim() && 
                           formData.value.confirmPassword.trim() &&
                           formData.value.verificationCode.trim()

  const hasNoErrors = Object.keys(validationErrors.value).length === 0

  return hasRequiredFields && hasNoErrors
})

// Submit form
const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  try {
    await register({
      fullname: formData.value.fullname,
      email: formData.value.email,
      password: formData.value.password,
      verification_code: formData.value.verificationCode
    })
    
    // Registration success message
    showSuccessToast(t('Registration successful! Welcome to RainClaw'))
    
    // Emit success event
    emits('success')
  } catch (error: any) {
    console.error('Registration failed:', error)
    // Display error message using toast
    showErrorToast(authError.value || t('Registration failed, please try again'))
  }
}

// Re-validate confirm password when original password changes
watch(() => formData.value.password, () => {
  if (formData.value.confirmPassword) {
    validateField('confirmPassword')
  }
})

// Expose clearForm method for parent component
defineExpose({
  clearForm
})
</script>
