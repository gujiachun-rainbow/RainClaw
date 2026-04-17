import { ref } from 'vue'
import type { FileInfo } from '../api/file'
import type { RoundFileInfo } from '../types/event'
import { eventBus } from '../utils/eventBus'
import { EVENT_SHOW_FILE_PANEL } from '../constants/event'

const isShow = ref(false)
const visible = ref(true)
const fileInfo = ref<FileInfo>()
const isListMode = ref(false)
const isRoundFilesMode = ref(false)
const roundFiles = ref<RoundFileInfo[]>([])
const _cameFromRoundFiles = ref(false)

export function useFilePanel() {
  const showFilePanel = (file: FileInfo) => {
    eventBus.emit(EVENT_SHOW_FILE_PANEL)
    visible.value = true
    _cameFromRoundFiles.value = isRoundFilesMode.value
    fileInfo.value = file
    isListMode.value = false
    isRoundFilesMode.value = false
    isShow.value = true
  }

  const showFileListPanel = () => {
    eventBus.emit(EVENT_SHOW_FILE_PANEL)
    visible.value = true
    isListMode.value = true
    isRoundFilesMode.value = false
    isShow.value = true
  }

  const showRoundFilesPanel = (files: RoundFileInfo[]) => {
    eventBus.emit(EVENT_SHOW_FILE_PANEL)
    visible.value = true
    roundFiles.value = files
    isListMode.value = false
    isRoundFilesMode.value = true
    isShow.value = true
  }

  const goBackFromFile = () => {
    if (_cameFromRoundFiles.value && roundFiles.value.length > 0) {
      isRoundFilesMode.value = true
      isListMode.value = false
    } else {
      isListMode.value = true
      isRoundFilesMode.value = false
    }
    _cameFromRoundFiles.value = false
  }

  const hideFilePanel = () => {
    isShow.value = false
  }

  return {
    isShow,
    fileInfo,
    visible,
    isListMode,
    isRoundFilesMode,
    roundFiles,
    showFilePanel,
    showFileListPanel,
    showRoundFilesPanel,
    goBackFromFile,
    hideFilePanel
  }
} 