import { ref } from 'vue'

const onSessionTitleUpdate = ref<((sessionId: string, title: string) => void) | null>(null)

/**
 * Shared composable for updating session title in the left-panel session list
 * when the backend sends a title event (e.g. after first user message).
 */
export function useSessionListUpdate() {
  return {
    setOnSessionTitleUpdate: (fn: ((sessionId: string, title: string) => void) | null) => {
      onSessionTitleUpdate.value = fn
    },
    updateSessionTitle: (sessionId: string, title: string) => {
      onSessionTitleUpdate.value?.(sessionId, title)
    },
  }
}
