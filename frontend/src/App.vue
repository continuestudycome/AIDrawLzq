<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { checkHealth, generateFromText, optimizePrompt } from './api/draw'
import {
  isBrowserSpeechSupported,
  startBrowserSpeechRecognition,
  type BrowserSpeechSession,
} from './composables/useBrowserSpeechRecognition'

type AppStatus = 'idle' | 'recording' | 'processing' | 'done' | 'error'

const status = ref<AppStatus>('idle')
const transcript = ref('')
const resultMessage = ref('')
const imageUrl = ref<string | null>(null)
const errorMessage = ref('')
const backendOnline = ref(false)
const isOptimizing = ref(false)
const browserSpeechSupported = ref(isBrowserSpeechSupported())
const speechMode = ref<'local' | 'cloud' | null>(null)
const speechStatus = ref('')

let activeSpeechSession: BrowserSpeechSession | null = null
let speechResultHandled = false

const speechHint = computed(() => {
  if (!browserSpeechSupported.value) return ''
  if (speechMode.value === 'local') return '免费语音识别（本地离线，无需外网）'
  if (speechMode.value === 'cloud') return '免费语音识别（云端，需可访问 Google 服务）'
  return '免费语音识别（优先本地，不可用则尝试云端）'
})

const statusText = computed(() => {
  switch (status.value) {
    case 'recording':
      return speechStatus.value || '正在准备语音识别…'
    case 'processing':
      return '正在生成图像，免费服务可能需要 1-3 分钟…'
    case 'done':
      return '完成'
    case 'error':
      return '出错了'
    default:
      return browserSpeechSupported.value
        ? '点击麦克风，使用浏览器免费语音识别'
        : '请使用 Chrome 或 Edge 浏览器进行语音识别'
  }
})

const isBusy = computed(
  () => status.value === 'recording' || status.value === 'processing' || isOptimizing.value,
)

function startRecording() {
  activeSpeechSession?.abort()

  errorMessage.value = ''
  resultMessage.value = ''
  imageUrl.value = null
  speechResultHandled = false
  speechMode.value = null
  speechStatus.value = '正在准备语音识别…'

  if (!browserSpeechSupported.value) {
    status.value = 'error'
    errorMessage.value = '当前浏览器不支持免费语音识别，请使用 Chrome 或 Edge'
    return
  }

  status.value = 'recording'

  activeSpeechSession = startBrowserSpeechRecognition({
    lang: 'zh-CN',
    onStatus: (message) => {
      speechStatus.value = message
    },
    onModeChange: (mode) => {
      speechMode.value = mode
    },
    onInterim: (text) => {
      transcript.value = text
    },
    onResult: (text) => {
      if (speechResultHandled) return
      speechResultHandled = true
      transcript.value = text
      void handleSpeechComplete(text)
    },
    onError: (message) => {
      status.value = 'error'
      errorMessage.value = message
    },
    onEnd: () => {
      speechStatus.value = ''
      if (status.value === 'recording') {
        status.value = speechResultHandled ? 'processing' : 'idle'
      }
    },
  })
}

function stopRecording() {
  activeSpeechSession?.stop()
}

async function handleSpeechComplete(text: string) {
  status.value = 'processing'

  try {
    const drawResult = await generateFromText(text)
    resultMessage.value = drawResult.message
    imageUrl.value = drawResult.image_url
    status.value = 'done'
  } catch (error) {
    status.value = 'error'
    errorMessage.value = error instanceof Error ? error.message : '处理失败'
  }
}

async function optimizePromptInput() {
  if (!transcript.value.trim()) return

  isOptimizing.value = true
  errorMessage.value = ''
  resultMessage.value = ''

  try {
    const result = await optimizePrompt(transcript.value.trim())
    transcript.value = result.optimized
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

  try {
    const drawResult = await generateFromText(transcript.value.trim())
    resultMessage.value = drawResult.message
    imageUrl.value = drawResult.image_url
    status.value = 'done'
  } catch (error) {
    status.value = 'error'
    errorMessage.value = error instanceof Error ? error.message : '生成失败'
  }
}

onMounted(async () => {
  browserSpeechSupported.value = isBrowserSpeechSupported()
  backendOnline.value = await checkHealth().catch(() => false)
})

onUnmounted(() => {
  activeSpeechSession?.abort()
})
</script>

<template>
  <div class="page">
    <header class="header">
      <div>
        <p class="eyebrow">AI Voice Draw</p>
        <h1>语音描述，AI 帮你画</h1>
        <p class="subtitle">说出你想要的画面，或手动输入提示词生成图像</p>
      </div>
      <span class="badge" :class="{ online: backendOnline }">
        {{ backendOnline ? '后端已连接' : '后端未连接' }}
      </span>
    </header>

    <main class="layout">
      <section class="panel control-panel">
        <div class="voice-box">
          <button
            class="mic-button"
            :class="{ recording: status === 'recording', busy: isBusy }"
            :disabled="!browserSpeechSupported || (isBusy && status !== 'recording')"
            @click="status === 'recording' ? stopRecording() : startRecording()"
          >
            <span class="mic-icon">{{ status === 'recording' ? '■' : '🎤' }}</span>
          </button>
          <p class="status-text">{{ statusText }}</p>
          <p v-if="status === 'recording'" class="speech-hint">说完后请再次点击麦克风 ■ 停止</p>
          <p v-if="speechHint" class="speech-hint">{{ speechHint }}</p>
        </div>

        <label class="field">
          <span>识别文本 / 提示词</span>
          <textarea
            v-model="transcript"
            rows="5"
            placeholder="例如：一只在星空下奔跑的猫，赛博朋克风格"
          />
        </label>

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
</template>
