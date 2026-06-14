/// <reference types="vite/client" />

interface SpeechRecognitionErrorEvent extends Event {
  error: string
}

interface SpeechRecognitionEvent extends Event {
  resultIndex: number
  results: SpeechRecognitionResultList
}

interface SpeechRecognition extends EventTarget {
  lang: string
  continuous: boolean
  interimResults: boolean
  processLocally?: boolean
  start(): void
  stop(): void
  abort(): void
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null
  onend: (() => void) | null
}

interface SpeechRecognitionOptions {
  langs: string[]
  processLocally?: boolean
  quality?: string
}

type SpeechAvailability = 'available' | 'unavailable' | 'downloadable' | 'downloading'

interface SpeechRecognitionConstructor {
  new (): SpeechRecognition
  available?: (options: SpeechRecognitionOptions) => Promise<SpeechAvailability>
  install?: (options: SpeechRecognitionOptions) => Promise<boolean>
}

interface Window {
  SpeechRecognition?: SpeechRecognitionConstructor
  webkitSpeechRecognition?: SpeechRecognitionConstructor
}
