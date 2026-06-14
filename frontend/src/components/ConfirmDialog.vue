<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    title: string
    description?: string
    preview?: string
    imageUrl?: string
    time?: string
    confirmText?: string
    cancelText?: string
    loading?: boolean
  }>(),
  {
    description: '',
    preview: '',
    imageUrl: '',
    time: '',
    confirmText: '确认删除',
    cancelText: '取消',
    loading: false,
  },
)

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

function onKeydown(event: KeyboardEvent) {
  if (!props.open || props.loading) return
  if (event.key === 'Escape') {
    emit('cancel')
  }
}

watch(
  () => props.open,
  (isOpen) => {
    document.body.style.overflow = isOpen ? 'hidden' : ''
  },
)

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="confirm-fade">
      <div v-if="open" class="confirm-overlay" @click.self="!loading && emit('cancel')">
        <div class="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-dialog-title">
          <div class="confirm-icon" aria-hidden="true">🗑️</div>
          <h3 id="confirm-dialog-title" class="confirm-title">{{ title }}</h3>
          <p v-if="description" class="confirm-description">{{ description }}</p>

          <div v-if="imageUrl || preview || time" class="confirm-preview-card">
            <img v-if="imageUrl" :src="imageUrl" alt="" class="confirm-preview-image" />
            <div class="confirm-preview-meta">
              <time v-if="time" class="confirm-preview-time">{{ time }}</time>
              <p v-if="preview" class="confirm-preview-text">{{ preview }}</p>
            </div>
          </div>

          <div class="confirm-actions">
            <button
              class="confirm-button confirm-button-cancel"
              type="button"
              :disabled="loading"
              @click="emit('cancel')"
            >
              {{ cancelText }}
            </button>
            <button
              class="confirm-button confirm-button-danger"
              type="button"
              :disabled="loading"
              @click="emit('confirm')"
            >
              {{ loading ? '删除中…' : confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.confirm-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(2, 6, 23, 0.72);
  backdrop-filter: blur(8px);
}

.confirm-dialog {
  width: min(420px, 100%);
  padding: 28px 24px 22px;
  border-radius: 20px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background:
    radial-gradient(circle at top, rgba(239, 68, 68, 0.12), transparent 55%),
    rgba(15, 23, 42, 0.96);
  box-shadow: 0 24px 60px rgba(2, 6, 23, 0.55);
  animation: confirm-pop 0.28s ease;
}

.confirm-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
  border-radius: 14px;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(248, 113, 113, 0.28);
  font-size: 1.35rem;
}

.confirm-title {
  margin: 0 0 8px;
  font-size: 1.2rem;
  color: #f8fafc;
}

.confirm-description {
  margin: 0 0 16px;
  color: #94a3b8;
  line-height: 1.6;
  font-size: 0.95rem;
}

.confirm-preview-card {
  display: flex;
  gap: 12px;
  padding: 12px;
  margin-bottom: 20px;
  border-radius: 14px;
  background: rgba(2, 6, 23, 0.55);
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.confirm-preview-image {
  width: 64px;
  height: 64px;
  object-fit: cover;
  border-radius: 10px;
  flex-shrink: 0;
  background: rgba(15, 23, 42, 0.8);
}

.confirm-preview-meta {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.confirm-preview-time {
  color: #93c5fd;
  font-size: 0.82rem;
}

.confirm-preview-text {
  margin: 0;
  color: #e2e8f0;
  line-height: 1.5;
  font-size: 0.9rem;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.confirm-actions {
  display: flex;
  gap: 10px;
}

.confirm-button {
  flex: 1;
  padding: 12px 16px;
  border-radius: 12px;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.15s ease;
}

.confirm-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.confirm-button:not(:disabled):active {
  transform: scale(0.98);
}

.confirm-button-cancel {
  border: 1px solid rgba(148, 163, 184, 0.28);
  background: rgba(30, 41, 59, 0.65);
  color: #cbd5e1;
}

.confirm-button-cancel:hover:not(:disabled) {
  background: rgba(51, 65, 85, 0.85);
}

.confirm-button-danger {
  border: none;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: #fff;
  box-shadow: 0 10px 24px rgba(220, 38, 38, 0.28);
}

.confirm-button-danger:hover:not(:disabled) {
  background: linear-gradient(135deg, #f87171, #ef4444);
}

.confirm-fade-enter-active,
.confirm-fade-leave-active {
  transition: opacity 0.22s ease;
}

.confirm-fade-enter-from,
.confirm-fade-leave-to {
  opacity: 0;
}

@keyframes confirm-pop {
  from {
    opacity: 0;
    transform: scale(0.94) translateY(8px);
  }

  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
</style>
