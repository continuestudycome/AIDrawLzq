export interface DrawResponse {
  prompt: string
  image_url: string | null
  message: string
}

export interface SpeechToTextResponse {
  text: string
  confidence?: number | null
}

export interface OptimizePromptResponse {
  original: string
  optimized: string
  optimized_en: string
  message: string
  method: string
}

async function readApiError(response: Response, fallback: string): Promise<Error> {
  try {
    const data = (await response.json()) as { detail?: string | Array<{ msg?: string }> }
    if (typeof data.detail === 'string' && data.detail.trim()) {
      return new Error(data.detail)
    }
    if (Array.isArray(data.detail) && data.detail[0]?.msg) {
      return new Error(data.detail[0].msg)
    }
  } catch {
    // ignore parse errors and use fallback
  }
  return new Error(fallback)
}

export async function checkHealth(): Promise<boolean> {
  const response = await fetch('/health')
  if (!response.ok) return false
  const data = (await response.json()) as { status: string }
  return data.status === 'ok'
}

export async function speechToText(audioBlob: Blob): Promise<SpeechToTextResponse> {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'recording.webm')

  const response = await fetch('/api/speech-to-text', {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw await readApiError(response, '语音识别失败')
  }

  return response.json()
}

export async function generateFromText(text: string): Promise<DrawResponse> {
  const response = await fetch('/api/transcript', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })

  if (!response.ok) {
    throw await readApiError(response, '图像生成失败')
  }

  return response.json()
}

export async function optimizePrompt(text: string): Promise<OptimizePromptResponse> {
  const response = await fetch('/api/optimize-prompt', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })

  if (!response.ok) {
    throw await readApiError(response, '提示词优化失败')
  }

  return response.json()
}
