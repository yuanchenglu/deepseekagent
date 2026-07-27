<script setup lang="ts">
/**
 * CodeModeView.vue — Code 模式容器
 *
 * 进入 Code 模式时：
 *  1. 通过 desktopBridge.startCodeMode(sharedConfig) 启动 OpenCode 运行时
 *  2. 状态机：idle → starting → running (webview) | failed (错误+重试)
 *  3. 桌面环境用 Electron <webview> 标签承载 OpenCode WebUI
 *  4. 浏览器环境显示"仅桌面可用"降级面板
 *  5. 顶部 40px header 显示状态 + 注入的模型/provider
 */
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { desktopBridge } from '@/utils/desktop-bridge'
import { getSharedConfig, applyToOpenCode, type SharedConfig } from '@/utils/mode-config'

const { t } = useI18n()

type ViewState = 'idle' | 'starting' | 'running' | 'failed' | 'unsupported'

const state = ref<ViewState>('idle')
const codeUrl = ref('')
const errorMessage = ref('')
const sharedConfig = ref<SharedConfig>(getSharedConfig())
const isDesktop = computed(() => desktopBridge()?.isDesktop === true)

async function startCodeMode() {
  if (!isDesktop.value) {
    state.value = 'unsupported'
    return
  }
  state.value = 'starting'
  errorMessage.value = ''
  sharedConfig.value = getSharedConfig()
  const result = await applyToOpenCode(sharedConfig.value)
  if (result.ok) {
    codeUrl.value = result.url
    state.value = 'running'
  } else {
    errorMessage.value = result.error
    state.value = 'failed'
  }
}

function retry() {
  void startCodeMode()
}

onMounted(() => {
  void startCodeMode()
})
</script>

<template>
  <div class="code-mode">
    <!-- 顶部 header -->
    <header class="code-mode-header">
      <div class="code-mode-status">
        <span class="status-dot" :class="state"></span>
        <span class="status-text">
          <template v-if="state === 'starting'">{{ t('mode.starting') }}</template>
          <template v-else-if="state === 'running'">{{ t('mode.running') }}</template>
          <template v-else-if="state === 'failed'">{{ t('mode.failed') }}</template>
          <template v-else-if="state === 'unsupported'">{{ t('mode.unsupported') }}</template>
          <template v-else>OpenCode</template>
        </span>
      </div>
      <div class="code-mode-meta">
        <span v-if="sharedConfig.model" class="meta-item">
          {{ t('mode.modelLabel') }}: {{ sharedConfig.model }}
        </span>
        <span v-if="sharedConfig.provider" class="meta-item">
          {{ sharedConfig.provider }}
        </span>
      </div>
      <button
        v-if="state === 'running' || state === 'failed'"
        type="button"
        class="code-mode-restart"
        @click="retry"
      >
        ↻ {{ t('mode.restart') }}
      </button>
    </header>

    <!-- 主内容区 -->
    <div class="code-mode-body">
      <!-- 加载态 -->
      <div v-if="state === 'starting' || state === 'idle'" class="code-mode-placeholder">
        <div class="spinner"></div>
        <p class="placeholder-text">{{ t('mode.starting') }}</p>
        <p class="placeholder-subtle">{{ t('mode.startingHint') }}</p>
      </div>

      <iframe
        v-if="state === 'running'"
        class="code-mode-webview"
        :src="codeUrl"
        title="DeepCode"
        sandbox="allow-downloads allow-forms allow-same-origin allow-scripts"
      />

      <!-- 错误态 -->
      <div v-else-if="state === 'failed'" class="code-mode-placeholder code-mode-error">
        <div class="error-icon">⚠</div>
        <p class="placeholder-text">{{ t('mode.failed') }}</p>
        <p class="error-message">{{ errorMessage }}</p>
        <button type="button" class="retry-btn" @click="retry">↻ {{ t('mode.retry') }}</button>
      </div>

      <!-- 不支持（浏览器） -->
      <div v-else-if="state === 'unsupported'" class="code-mode-placeholder code-mode-unsupported">
        <div class="error-icon">💻</div>
        <p class="placeholder-text">{{ t('mode.unsupported') }}</p>
        <p class="placeholder-subtle">{{ t('mode.unsupportedHint') }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/variables' as *;

.code-mode {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background-color: $bg-primary;
}

.code-mode-header {
  flex: 0 0 40px;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 16px;
  background-color: $bg-secondary;
  border-bottom: 1px solid $border-color;
  font-size: 13px;
}

.code-mode-status {
  display: flex;
  align-items: center;
  gap: 8px;
  color: $text-primary;
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: $text-muted;
  flex-shrink: 0;

  &.starting {
    background-color: $warning;
    animation: pulse 1.2s ease-in-out infinite;
  }
  &.running {
    background-color: $success;
    box-shadow: 0 0 6px rgba(var(--success-rgb), 0.5);
  }
  &.failed {
    background-color: $error;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.code-mode-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
  color: $text-muted;
  font-size: 12px;
}

.meta-item {
  padding: 2px 8px;
  background-color: rgba(var(--accent-primary-rgb), 0.08);
  border-radius: 4px;
}

.code-mode-restart {
  border: 1px solid $border-color;
  background: transparent;
  color: $text-secondary;
  padding: 4px 12px;
  border-radius: $radius-sm;
  cursor: pointer;
  font-size: 12px;
  transition: all $transition-fast;

  &:hover {
    background-color: rgba(var(--accent-primary-rgb), 0.08);
    color: $text-primary;
  }
}

.code-mode-body {
  flex: 1;
  position: relative;
  overflow: hidden;
  min-height: 0;
}

.code-mode-webview {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

.code-mode-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  height: 100%;
  padding: 32px;
  text-align: center;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid $border-color;
  border-top-color: $accent-primary;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.placeholder-text {
  color: $text-primary;
  font-size: 15px;
  font-weight: 500;
  margin: 0;
}

.placeholder-subtle {
  color: $text-muted;
  font-size: 13px;
  margin: 0;
}

.code-mode-error .error-icon,
.code-mode-unsupported .error-icon {
  font-size: 36px;
}

.error-message {
  color: $text-muted;
  font-size: 12px;
  font-family: $font-code;
  max-width: 480px;
  word-break: break-word;
  margin: 0;
}

.retry-btn {
  margin-top: 8px;
  padding: 8px 24px;
  background-color: $accent-primary;
  color: var(--text-on-accent);
  border: none;
  border-radius: $radius-sm;
  font-weight: 600;
  cursor: pointer;
  transition: opacity $transition-fast;

  &:hover { opacity: 0.85; }
}
</style>
