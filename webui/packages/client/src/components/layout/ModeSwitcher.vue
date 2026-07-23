<script setup lang="ts">
/**
 * ModeSwitcher.vue — 双模式顶部 Tab 切换栏
 *
 * 在 App.vue 主布局顶部渲染「助理模式」「Code 模式」两个 Tab。
 * - 助理模式：显示导航与所有 hermes 路由
 * - Code 模式：显示 CodeModeView
 *
 * 非桌面环境下 Code Tab 禁用（title 提示仅桌面可用）。
 * 移动端（≤768px）紧凑模式（仅图标）。
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAppMode } from '@/composables/useAppMode'
import { desktopBridge } from '@/utils/desktop-bridge'
import type { AppMode } from '@/utils/mode-config'

const { t } = useI18n()
const { mode, setMode } = useAppMode()

/** 是否在桌面壳中（Code 模式仅桌面可用） */
const isDesktop = computed(() => desktopBridge()?.isDesktop === true)

/** Code Tab 是否禁用 */
const codeDisabled = computed(() => !isDesktop.value)

function select(target: AppMode) {
  if (target === 'code' && codeDisabled.value) return
  if (target === mode.value) return
  void setMode(target)
}
</script>

<template>
  <div class="mode-switcher" role="tablist" :aria-label="t('mode.switcherLabel')">
    <button
      type="button"
      class="mode-tab"
      :class="{ active: mode === 'assistant' }"
      role="tab"
      :aria-selected="mode === 'assistant'"
      :title="t('mode.assistant')"
      @click="select('assistant')"
    >
      <span class="mode-icon" aria-hidden="true">💬</span>
      <span class="mode-label">{{ t('mode.assistant') }}</span>
    </button>
    <button
      type="button"
      class="mode-tab"
      :class="{ active: mode === 'code', disabled: codeDisabled }"
      role="tab"
      :aria-selected="mode === 'code'"
      :disabled="codeDisabled"
      :title="codeDisabled ? t('mode.codeDesktopOnly') : t('mode.code')"
      @click="select('code')"
    >
      <span class="mode-icon" aria-hidden="true">⌨</span>
      <span class="mode-label">{{ t('mode.code') }}</span>
    </button>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/variables' as *;

.mode-switcher {
  flex: 0 0 auto;
  height: 44px;
  display: flex;
  align-items: stretch;
  padding: 0 12px;
  gap: 4px;
  background-color: $bg-secondary;
  border-bottom: 1px solid $border-color;
  z-index: 20;
}

.mode-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 20px;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: $text-secondary;
  font-size: 14px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: color $transition-fast, background-color $transition-fast, border-color $transition-fast;
  border-radius: 0;
  white-space: nowrap;

  &:hover:not(.disabled) {
    color: $text-primary;
    background-color: rgba(var(--accent-primary-rgb), 0.06);
  }

  &.active {
    color: $accent-primary;
    border-bottom-color: $accent-primary;
    font-weight: 600;
  }

  &.disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .mode-icon {
    font-size: 15px;
    line-height: 1;
  }
}

@media (max-width: $breakpoint-mobile) {
  .mode-switcher {
    padding: 0 6px;
  }
  .mode-tab {
    padding: 0 12px;
    .mode-label {
      display: none;
    }
  }
}
</style>
