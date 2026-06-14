export interface BrowserSpeechOptions {
  lang?: string
  onResult: (text: string) => void
  onError: (message: string) => void
  onEnd?: () => void
  onInterim?: (text: string) => void
  onStatus?: (message: string) => void
  onModeChange?: (mode: 'local' | 'cloud') => void
}

export interface BrowserSpeechSession {
  stop: () => void
  abort: () => void
}

export function isBrowserSpeechSupported(): boolean {
  return (
    typeof window !== 'undefined' &&
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)
  )
}

function getSpeechRecognitionCtor(): SpeechRecognitionConstructor {
  const ctor = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!ctor) {
    throw new Error('当前浏览器不支持免费语音识别，请使用 Chrome 或 Edge')
  }
  return ctor
}

function supportsOnDeviceSpeech(ctor: SpeechRecognitionConstructor): boolean {
  return typeof ctor.available === 'function' && typeof ctor.install === 'function'
}

async function prepareOnDeviceSpeech(
  ctor: SpeechRecognitionConstructor,
  lang: string,
  onStatus?: (message: string) => void,
): Promise<boolean> {
  if (!supportsOnDeviceSpeech(ctor)) {
    return false
  }

  onStatus?.('正在检查离线语音包…')
  const availability = await ctor.available!({ langs: [lang], processLocally: true })

  if (availability === 'available') {
    return true
  }

  if (availability === 'downloadable' || availability === 'downloading') {
    onStatus?.('正在下载中文离线语音包，请稍候…')
    await ctor.install!({ langs: [lang], processLocally: true })
    const afterInstall = await ctor.available!({ langs: [lang], processLocally: true })
    return afterInstall === 'available' || afterInstall === 'downloading'
  }

  return false
}

const ERROR_MESSAGES: Record<string, string> = {
  'no-speech': '未检测到语音，请靠近麦克风后重试',
  'not-allowed': '无法访问麦克风，请在浏览器地址栏允许麦克风权限',
  'service-not-allowed': '浏览器禁止语音识别，请使用 Chrome 或 Edge',
  network:
    '云端语音识别不可用（国内网络可能无法访问 Google 服务），正在尝试本地识别…',
  'language-not-supported':
    '当前浏览器未安装中文离线语音包，请改用手动输入或在 Chrome 设置中下载',
  aborted: '',
}

export function startBrowserSpeechRecognition(
  options: BrowserSpeechOptions,
): BrowserSpeechSession {
  const SpeechRecognitionCtor = getSpeechRecognitionCtor()
  const lang = options.lang ?? 'zh-CN'

  let latestTranscript = ''
  let hasFinalResult = false
  let hasRetriedLocally = false
  let hasRetriedCloud = false
  let currentMode: 'local' | 'cloud' = 'cloud'
  let recognition: SpeechRecognition | null = null
  let stoppedByUser = false
  let startupGeneration = 0

  function createRecognitionInstance(): SpeechRecognition {
    const instance = new SpeechRecognitionCtor()
    instance.lang = lang
    instance.continuous = true
    instance.interimResults = true
    return instance
  }

  function attachHandlers(target: SpeechRecognition) {
    target.onresult = (event: SpeechRecognitionEvent) => {
      latestTranscript = Array.from(event.results)
        .map((result) => result[0]?.transcript ?? '')
        .join('')
        .trim()

      if (latestTranscript) {
        options.onInterim?.(latestTranscript)
      }

      const lastResult = event.results[event.results.length - 1]
      if (lastResult?.isFinal && latestTranscript) {
        hasFinalResult = true
        options.onResult(latestTranscript)
        latestTranscript = ''
      }
    }

    target.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (stoppedByUser && event.error === 'aborted') {
        return
      }

      if (
        event.error === 'network' &&
        !hasRetriedLocally &&
        supportsOnDeviceSpeech(SpeechRecognitionCtor)
      ) {
        hasRetriedLocally = true
        options.onStatus?.('云端不可用，正在切换本地识别…')
        void beginRecognition(true)
        return
      }

      if (event.error === 'language-not-supported' && !hasRetriedCloud) {
        hasRetriedCloud = true
        options.onStatus?.('本地语音包不可用，正在尝试云端识别…')
        void beginRecognition(false)
        return
      }

      const message = ERROR_MESSAGES[event.error]
      if (message) {
        options.onError(message)
      } else if (event.error !== 'aborted') {
        options.onError(`语音识别失败：${event.error}`)
      }
    }

    target.onend = () => {
      if (stoppedByUser) {
        if (!hasFinalResult && latestTranscript) {
          hasFinalResult = true
          options.onResult(latestTranscript)
          latestTranscript = ''
        } else if (!hasFinalResult) {
          options.onError('未检测到语音，请说完后再次点击麦克风停止')
        }
        options.onEnd?.()
        return
      }

      if (!hasFinalResult && latestTranscript) {
        hasFinalResult = true
        options.onResult(latestTranscript)
        latestTranscript = ''
      }

      options.onEnd?.()
    }
  }

  async function beginRecognition(preferLocal: boolean) {
    const generation = ++startupGeneration
    hasFinalResult = false
    latestTranscript = ''
    recognition?.abort()
    recognition = createRecognitionInstance()
    attachHandlers(recognition)

    let useLocal = false
    if (preferLocal) {
      useLocal = await prepareOnDeviceSpeech(SpeechRecognitionCtor, lang, options.onStatus)
    }

    if (generation !== startupGeneration || stoppedByUser) {
      return
    }

    if ('processLocally' in recognition) {
      recognition.processLocally = useLocal
    }

    currentMode = useLocal ? 'local' : 'cloud'
    options.onModeChange?.(currentMode)
    options.onStatus?.(useLocal ? '正在聆听（本地离线）…' : '正在聆听，请说话…')

    try {
      recognition.start()
    } catch {
      if (useLocal && !hasRetriedCloud) {
        hasRetriedCloud = true
        await beginRecognition(false)
        return
      }
      options.onError('无法启动语音识别，请刷新页面后重试')
    }
  }

  void (async () => {
    try {
      const canUseLocal = supportsOnDeviceSpeech(SpeechRecognitionCtor)
      await beginRecognition(canUseLocal)
    } catch (error) {
      options.onError(error instanceof Error ? error.message : '无法启动语音识别')
    }
  })()

  return {
    stop() {
      stoppedByUser = true
      recognition?.stop()
    },
    abort() {
      stoppedByUser = true
      startupGeneration += 1
      recognition?.abort()
    },
  }
}

/** @deprecated 使用 startBrowserSpeechRecognition */
export function createBrowserSpeechRecognition(options: BrowserSpeechOptions) {
  let activeSession: BrowserSpeechSession | null = null

  return {
    start() {
      activeSession = startBrowserSpeechRecognition(options)
    },
    stop() {
      activeSession?.stop()
    },
    abort() {
      activeSession?.abort()
    },
  }
}
