import { ref } from 'vue'
import { deleteHistoryItem, fetchHistory, type HistoryItem } from '../api/draw'

export function formatHistoryTime(iso: string): string {
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function useHistory(backendOnline: { value: boolean }) {
  const historyItems = ref<HistoryItem[]>([])
  const historyLoading = ref(false)
  const activeHistoryId = ref<string | null>(null)
  const historySidebarOpen = ref(false)
  const deleteConfirmItem = ref<HistoryItem | null>(null)
  const deleteLoading = ref(false)

  async function loadHistory() {
    if (!backendOnline.value) return

    historyLoading.value = true
    try {
      const result = await fetchHistory()
      historyItems.value = result.items
    } finally {
      historyLoading.value = false
    }
  }

  function openHistorySidebar() {
    historySidebarOpen.value = true
    if (backendOnline.value) {
      void loadHistory()
    }
  }

  function closeHistorySidebar() {
    historySidebarOpen.value = false
  }

  function toggleHistorySidebar() {
    if (historySidebarOpen.value) {
      closeHistorySidebar()
      return
    }
    openHistorySidebar()
  }

  function requestRemoveHistoryItem(item: HistoryItem) {
    deleteConfirmItem.value = item
  }

  function cancelDeleteHistory() {
    if (deleteLoading.value) return
    deleteConfirmItem.value = null
  }

  async function confirmDeleteHistory() {
    const item = deleteConfirmItem.value
    if (!item || deleteLoading.value) return

    deleteLoading.value = true
    try {
      await deleteHistoryItem(item.id)
      historyItems.value = historyItems.value.filter((entry) => entry.id !== item.id)
      if (activeHistoryId.value === item.id) {
        activeHistoryId.value = null
      }
      deleteConfirmItem.value = null
    } finally {
      deleteLoading.value = false
    }
  }

  return {
    historyItems,
    historyLoading,
    activeHistoryId,
    historySidebarOpen,
    deleteConfirmItem,
    deleteLoading,
    loadHistory,
    openHistorySidebar,
    closeHistorySidebar,
    toggleHistorySidebar,
    requestRemoveHistoryItem,
    cancelDeleteHistory,
    confirmDeleteHistory,
  }
}
