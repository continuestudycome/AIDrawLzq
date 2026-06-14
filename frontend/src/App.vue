<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import ConfirmDialog from './components/ConfirmDialog.vue'
import HistorySidebar from './components/HistorySidebar.vue'
import {
  checkHealth,
  generateFromText,
  optimizePrompt,
  speechToText,
  type HistoryItem,
} from './api/draw'
import { formatHistoryTime, useHistory } from './composables/useHistory'
import { useVoiceRecording } from './composables/useVoiceRecording'

type AppStatus = 'idle' | 'recording' | 'transcribing' | 'processing' | 'done' | 'error'

const status = ref<AppStatus>('idle')
const transcript = ref('')
const generationPrompt = ref<string | null>(null)
const resultMessage = ref('')
const imageUrl = ref<string | null>(null)
const errorMessage = ref('')
const backendOnline = ref(false)
const isOptimizing = ref(false)
const skipTranscriptWatch = ref(false)

const {
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
} = useHistory(backendOnline)

const { isRecording, startRecording, stopRecording } = useVoiceRecording(async (audioBlob) => {
  status.value = 'transcribing'
  try {
    const speechResult = await speechToText(audioBlob)
    skipTranscriptWatch.value = true
    transcript.value = speechResult.text
    generationPrompt.value = null
    skipTranscriptWatch.value = false
    activeHistoryId.value = null
    resultMessage.value = '语音识别完成，可编辑后点击「生成图像」'
    status.value = 'idle'
  } catch (error) {
    status.value = 'error'
    errorMessage.value = error instanceof Error ? error.message : '语音识别失败'
  }
})

watch(isRecording, (recording) => {
  if (recording) {
    status.value = 'recording'
  }
})

const statusText = computed(() => {
  switch (status.value) {
    case 'recording':
      return '正在录音，请说话…'
    case 'transcribing':
      return '正在识别语音…'
    case 'processing':
      return '正在生成图像，通常需要 10–60 秒…'
    case 'done':
      return '完成'
    case 'error':
      return '出错了'
    default:
      return '点击麦克风开始录音，说完后再点一次停止'
  }
})

const isBusy = computed(
  () =>
    status.value === 'recording' ||
    status.value === 'transcribing' ||
    status.value === 'processing' ||
    isOptimizing.value,
)

const suggestOptimizeBeforeGenerate = computed(
  () =>
    transcript.value.trim() &&
    !generationPrompt.value?.trim() &&
    /[\u4e00-\u9fff]/.test(transcript.value),
)

watch(transcript, () => {
  if (skipTranscriptWatch.value) return
  generationPrompt.value = null
})

async function handleMicClick() {
  errorMessage.value = ''
  resultMessage.value = ''

  if (status.value === 'recording') {
    stopRecording()
    return
  }

  try {
    await startRecording()
  } catch {
    status.value = 'error'
    errorMessage.value = '无法访问麦克风，请检查浏览器权限'
  }
}

async function optimizePromptInput() {
  if (!transcript.value.trim()) return

  isOptimizing.value = true
  errorMessage.value = ''
  resultMessage.value = ''

  try {
    const result = await optimizePrompt(transcript.value.trim())
    skipTranscriptWatch.value = true
    transcript.value = result.optimized
    generationPrompt.value = result.optimized_en
    skipTranscriptWatch.value = false
    resultMessage.value = result.message
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '提示词优化失败'
  } finally {
    isOptimizing.value = false
  }
}

async function generateFromInput() {
  if (!transcript.value.trim()) return

  status.value = 'processing'
  errorMessage.value = ''
  resultMessage.value = ''
  imageUrl.value = null
  activeHistoryId.value = null

  const displayPrompt = transcript.value.trim()
  const prompt = generationPrompt.value?.trim() || displayPrompt

  try {
    const drawResult = await generateFromText(prompt, { displayPrompt })
    resultMessage.value = drawResult.message
    if (drawResult.history_saved === false) {
      resultMessage.value = `${drawResult.message}（历史记录未保存）`
    }
    imageUrl.value = drawResult.image_url
    activeHistoryId.value = drawResult.history_id ?? null
    status.value = 'done'
    await loadHistory()
  } catch (error) {
    status.value = 'error'
    errorMessage.value = error instanceof Error ? error.message : '生成失败'
  }
}

function applyHistoryItem(item: HistoryItem) {
  skipTranscriptWatch.value = true
  transcript.value = item.display_prompt
  generationPrompt.value =
    item.generation_prompt !== item.display_prompt ? item.generation_prompt : null
  skipTranscriptWatch.value = false
  imageUrl.value = item.image_url
  activeHistoryId.value = item.id
  resultMessage.value = item.message || '已加载历史记录'
  status.value = 'done'
  errorMessage.value = ''

  if (window.matchMedia('(max-width: 900px)').matches) {
    closeHistorySidebar()
  }
}

async function handleDeleteHistory() {
  try {
    await confirmDeleteHistory()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '删除历史记录失败'
  }
}

onMounted(async () => {
  backendOnline.value = await checkHealth().catch(() => false)
  if (backendOnline.value) {
    try {
      await loadHistory()
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '获取历史记录失败'
    }
  }
})
</script>

<template>
  <div class="app-shell">
    <HistorySidebar
      :open="historySidebarOpen"
      :backend-online="backendOnline"
      :history-loading="historyLoading"
      :history-items="historyItems"
      :active-history-id="activeHistoryId"
      @close="closeHistorySidebar"
      @refresh="loadHistory"
      @select="applyHistoryItem"
      @delete="requestRemoveHistoryItem"
    />

    <button
      class="history-toggle"
      type="button"
      :class="{ open: historySidebarOpen }"
      :aria-expanded="historySidebarOpen"
      aria-label="打开或关闭历史侧边栏"
      @click="toggleHistorySidebar"
    >
      {{ historySidebarOpen ? '◀' : '历史' }}
    </button>

    <div class="page">
      <header class="header">
        <div>
          <p class="eyebrow">AI Voice Draw</p>
          <h1>语音描述，AI 帮你画</h1>
          <p class="subtitle">说出你想要的画面，或手动输入提示词生成图像</p>
        </div>
        <div class="header-actions">
          <button class="secondary-button history-open-btn" type="button" @click="openHistorySidebar">
            📋 历史记录
          </button>
          <span class="badge" :class="{ online: backendOnline }">
            {{ backendOnline ? '后端已连接' : '后端未连接' }}
          </span>
        </div>
      </header>

      <main class="layout">
        <section class="panel control-panel">
          <div class="voice-box">
            <button
              class="mic-button"
              :class="{ recording: status === 'recording', busy: isBusy && status !== 'recording' }"
              :disabled="isBusy && status !== 'recording'"
              @click="handleMicClick"
            >
              <span class="mic-icon">{{ status === 'recording' ? '■' : '🎤' }}</span>
            </button>
            <p class="status-text">{{ statusText }}</p>
            <p v-if="status === 'recording'" class="speech-hint">说完后再次点击 ■ 停止录音</p>
            <p v-else class="speech-hint">阿里云语音识别（qwen3-asr-flash）</p>
          </div>

          <label class="field">
            <span>识别文本 / 提示词（中文说明）</span>
            <textarea
              v-model="transcript"
              rows="5"
              placeholder="例如：一只在星空下奔跑的猫，赛博朋克风格"
            />
          </label>

          <details v-if="generationPrompt" class="en-prompt-details">
            <summary>查看英文绘图提示词（生成图像时自动使用）</summary>
            <p class="en-prompt-text">{{ generationPrompt }}</p>
          </details>

          <p v-if="suggestOptimizeBeforeGenerate" class="speech-hint">
            建议先点「优化提示词」再绘图，可获得更完整的中英文描述
          </p>

          <div class="action-row">
            <button
              class="secondary-button"
              :disabled="isBusy || !transcript.trim()"
              @click="optimizePromptInput"
            >
              {{ isOptimizing ? '优化中…' : '✨ 优化提示词' }}
            </button>
            <button class="primary-button" :disabled="isBusy || !transcript.trim()" @click="generateFromInput">
              生成图像
            </button>
          </div>

          <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
          <p v-if="resultMessage" class="hint">{{ resultMessage }}</p>
        </section>

        <section class="panel preview-panel">
          <h2>预览</h2>
          <div class="canvas">
            <img v-if="imageUrl" :src="imageUrl" alt="生成结果" />
            <div v-else class="placeholder">
              <p>生成结果将显示在这里</p>
              <p v-if="transcript" class="prompt-preview">当前提示词：{{ transcript }}</p>
            </div>
          </div>
        </section>
      </main>
    </div>

    <ConfirmDialog
      :open="deleteConfirmItem !== null"
      title="删除这条历史记录？"
      description="删除后将无法恢复，图片与提示词都会从本地历史中移除。"
      :preview="deleteConfirmItem?.display_prompt ?? ''"
      :image-url="deleteConfirmItem?.image_url ?? ''"
      :time="deleteConfirmItem ? formatHistoryTime(deleteConfirmItem.created_at) : ''"
      :loading="deleteLoading"
      @confirm="handleDeleteHistory"
      @cancel="cancelDeleteHistory"
    />
  </div>
</template>
