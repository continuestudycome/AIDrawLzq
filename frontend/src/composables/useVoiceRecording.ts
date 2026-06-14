import { ref } from 'vue'

export function useVoiceRecording(onRecordingComplete: (audioBlob: Blob) => Promise<void>) {
  const isRecording = ref(false)

  const mediaRecorder = ref<MediaRecorder | null>(null)
  const audioChunks = ref<Blob[]>([])
  let recordingStream: MediaStream | null = null

  function cleanupRecordingStream() {
    recordingStream?.getTracks().forEach((track) => track.stop())
    recordingStream = null
  }

  async function startRecording() {
    cleanupRecordingStream()
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    recordingStream = stream
    audioChunks.value = []

    const preferredTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4']
    const mimeType = preferredTypes.find((type) => MediaRecorder.isTypeSupported(type))
    mediaRecorder.value = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream)

    mediaRecorder.value.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data)
      }
    }

    mediaRecorder.value.onstop = async () => {
      cleanupRecordingStream()
      const audioBlob = new Blob(audioChunks.value, {
        type: mediaRecorder.value?.mimeType || 'audio/webm',
      })
      if (!audioBlob.size) {
        throw new Error('录音内容为空，请重新录音')
      }
      await onRecordingComplete(audioBlob)
    }

    mediaRecorder.value.start()
    isRecording.value = true
  }

  function stopRecording() {
    if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
      mediaRecorder.value.stop()
      isRecording.value = false
    }
  }

  return {
    isRecording,
    startRecording,
    stopRecording,
  }
}
