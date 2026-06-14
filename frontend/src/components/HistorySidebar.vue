<script setup lang="ts">
import type { HistoryItem } from '../api/draw'
import { formatHistoryTime } from '../composables/useHistory'

defineProps<{
  open: boolean
  backendOnline: boolean
  historyLoading: boolean
  historyItems: HistoryItem[]
  activeHistoryId: string | null
}>()

const emit = defineEmits<{
  close: []
  refresh: []
  select: [item: HistoryItem]
  delete: [item: HistoryItem]
}>()
</script>

<template>
  <div v-if="open" class="history-backdrop" aria-hidden="true" @click="emit('close')" />

  <aside class="history-sidebar" :class="{ open }" aria-label="生成历史">
    <div class="history-sidebar-header">
      <div>
        <h2>生成历史</h2>
        <p class="history-subtitle">点击记录可重新查看</p>
      </div>
      <button class="history-close" type="button" aria-label="关闭历史侧边栏" @click="emit('close')">
        ✕
      </button>
    </div>

    <button
      class="secondary-button history-refresh"
      :disabled="historyLoading"
      type="button"
      @click="emit('refresh')"
    >
      {{ historyLoading ? '加载中…' : '刷新列表' }}
    </button>

    <div class="history-sidebar-body">
      <div v-if="!backendOnline" class="history-empty">后端未连接，无法加载历史</div>
      <div v-else-if="historyLoading && historyItems.length === 0" class="history-empty">正在加载历史…</div>
      <div v-else-if="historyItems.length === 0" class="history-empty">暂无生成记录</div>

      <div v-else class="history-list">
        <article
          v-for="item in historyItems"
          :key="item.id"
          class="history-card"
          :class="{ active: activeHistoryId === item.id }"
        >
          <button class="history-card-main" type="button" @click="emit('select', item)">
            <img :src="item.image_url" :alt="item.display_prompt" class="history-thumb" />
            <div class="history-meta">
              <time class="history-time">{{ formatHistoryTime(item.created_at) }}</time>
              <p class="history-prompt">{{ item.display_prompt }}</p>
              <p v-if="item.generation_prompt !== item.display_prompt" class="history-en">
                英文：{{ item.generation_prompt }}
              </p>
            </div>
          </button>
          <button
            class="history-delete"
            type="button"
            title="删除这条记录"
            @click.stop="emit('delete', item)"
          >
            删除
          </button>
        </article>
      </div>
    </div>
  </aside>
</template>
