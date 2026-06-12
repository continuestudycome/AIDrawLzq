export interface DrawResponse {
  prompt: string
  image_url: string | null
  message: string
}

export interface SpeechToTextResponse {
  text: string
  confidence?: number | null
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
    throw new Error('语音识别失败')
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
    throw new Error('图像生成失败')
  }

  return response.json()
}
