<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { checkHealth, generateFromText, optimizePrompt, speechToText } from './api/draw'

type AppStatus = 'idle' | 'recording' | 'processing' | 'done' | 'error'

const status = ref<AppStatus>('idle')
const transcript = ref('')
const resultMessage = ref('')
const imageUrl = ref<string | null>(null)
const errorMessage = ref('')
const backendOnline = ref(false)
const isOptimizing = ref(false)

const mediaRecorder = ref<MediaRecorder | null>(null)
const audioChunks = ref<Blob[]>([])

const statusText = computed(() => {
  switch (status.value) {
    case 'recording':
      return '正在录音…'
    case 'processing':
      return '正在生成图像，免费服务可能需要 1-3 分钟…'
    case 'done':
      return '完成'
    case 'error':
      return '出错了'
    default:
      return '点击麦克风开始语音描述'
  }
})

const isBusy = computed(
  () => status.value === 'recording' || status.value === 'processing' || isOptimizing.value,
)

async function startRecording() {
  errorMessage.value = ''
  resultMessage.value = ''
  imageUrl.value = null

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioChunks.value = []
    mediaRecorder.value = new MediaRecorder(stream)

    mediaRecorder.value.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data)
      }
    }

    mediaRecorder.value.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop())
      await handleRecordingComplete()
    }

    mediaRecorder.value.start()
    status.value = 'recording'
  } catch {
    status.value = 'error'
    errorMessage.value = '无法访问麦克风，请检查浏览器权限'
  }
}

function stopRecording() {
  if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
    mediaRecorder.value.stop()
  }
}

async function handleRecordingComplete() {
  status.value = 'processing'

  try {
    const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' })
    const speechResult = await speechToText(audioBlob)
    transcript.value = speechResult.text

    const drawResult = await generateFromText(speechResult.text)
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
  backendOnline.value = await checkHealth().catch(() => false)
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
            :disabled="isBusy && status !== 'recording'"
            @click="status === 'recording' ? stopRecording() : startRecording()"
          >
            <span class="mic-icon">{{ status === 'recording' ? '■' : '🎤' }}</span>
          </button>
          <p class="status-text">{{ statusText }}</p>
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
