<script setup lang="ts">
import { onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { darkTheme, NConfigProvider, NMessageProvider, NDialogProvider, NNotificationProvider } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { getThemeOverrides } from '@/styles/theme'
import { useTheme } from '@/composables/useTheme'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import DesktopTitleBar from '@/components/layout/DesktopTitleBar.vue'
// 双模式切换栏（Stage 9 新增）
import ModeSwitcher from '@/components/layout/ModeSwitcher.vue'
// Code 模式容器（Stage 9 新增）
import CodeModeView from '@/views/hermes/CodeModeView.vue'
import { useAppMode } from '@/composables/useAppMode'
import { useKeyboard } from '@/composables/useKeyboard'
import { useAppStore } from '@/stores/hermes/app'
import SessionSearchModal from '@/components/hermes/chat/SessionSearchModal.vue'
import AuthEventListener from '@/components/auth/AuthEventListener.vue'
import DefaultCredentialPrompt from '@/components/auth/DefaultCredentialPrompt.vue'
import WebPet from '@/components/hermes/pets/WebPet.vue'
import { desktopBridge } from '@/utils/desktop-bridge'

const { isDark, isComic } = useTheme()
const { t } = useI18n()
const appStore = useAppStore()
const route = useRoute()
const router = useRouter()
// 双模式状态：assistant（助理模式）| code（Code 模式）
const { mode: appMode } = useAppMode()

const themeOverrides = computed(() => getThemeOverrides(isDark.value, isComic.value))
const naiveTheme = computed(() => isDark.value ? darkTheme : null)

const isLoginPage = computed(() => route.name === 'login')
const usesPageSidebar = computed(() =>
  ['hermes.chat', 'hermes.session', 'hermes.history', 'hermes.historySession', 'hermes.globalAgent', 'hermes.globalAgentSession', 'hermes.groupChat', 'hermes.groupChatRoom', 'hermes.workflow'].includes(route.name as string),
)
const showAppSidebar = computed(() => !isLoginPage.value && !usesPageSidebar.value)
const showMobileMenuButton = computed(() => !isLoginPage.value && (showAppSidebar.value || usesPageSidebar.value))

const nodeVersionLow = computed(() => {
  const v = appStore.nodeVersion
  const major = parseInt(v.split('.')[0], 10)
  return !isNaN(major) && major < 23
})

const isDesktopShell = computed(() => desktopBridge()?.isDesktop === true)
const isDesktopPetRoute = computed(() => route.name === 'desktop.pet')
const showWebPet = computed(() => !isLoginPage.value && !isDesktopShell.value && !isDesktopPetRoute.value)
const hasDesktopTitleBar = computed(() => {
  const platform = desktopBridge()?.platform
  return isDesktopShell.value && (platform === 'darwin' || platform === 'win32')
})
// 双模式：是否显示模式切换栏 + 当前是否 Code 模式
const showModeSwitcher = computed(() => !isLoginPage.value && !isDesktopPetRoute.value)
const isCodeMode = computed(() => appMode.value === 'code')
const LAST_ASSISTANT_ROUTE_KEY = 'deepagent_last_assistant_route'
// Code 模式下不显示助理侧边栏
const showSidebarInCurrentMode = computed(() => showAppSidebar.value && !isCodeMode.value)

function handleMobileMenuClick() {
  if (usesPageSidebar.value) {
    window.dispatchEvent(new CustomEvent('hermes:open-page-sidebar'))
    return
  }
  appStore.toggleSidebar()
}

watch(isLoginPage, (loginPage) => {
  if (loginPage) {
    appStore.stopHealthPolling()
    return
  }
  appStore.loadModels()
  appStore.startHealthPolling()
}, {
  immediate: true,
})

onUnmounted(() => {
  appStore.stopHealthPolling()
})

// 双模式路由联动：进入 Code 模式时切到 /hermes/code，切回助理模式则不强行跳转
// （切回助理模式保留用户离开前的 hermes 路由）
// 登录页不受双模式影响，忽略模式切换以防路由循环
watch(() => route.fullPath, (path) => {
  if (route.name !== 'login' && route.name !== 'hermes.code') {
    localStorage.setItem(LAST_ASSISTANT_ROUTE_KEY, path)
  }
}, { immediate: true })

watch(appMode, (next) => {
  if (route.name === 'login') return
  if (next === 'code' && route.name !== 'hermes.code') {
    router.push({ name: 'hermes.code' }).catch(() => { /* navigation duplicated */ })
  } else if (next === 'assistant' && route.name === 'hermes.code') {
    const previous = localStorage.getItem(LAST_ASSISTANT_ROUTE_KEY) || '/hermes/chat'
    router.push(previous).catch(() => {})
  }
}, { immediate: false })

useKeyboard()
</script>

<template>
  <NConfigProvider :theme="naiveTheme" :theme-overrides="themeOverrides">
    <NMessageProvider>
      <AuthEventListener />
      <NDialogProvider>
        <NNotificationProvider>
          <router-view v-if="isDesktopPetRoute" />
          <div v-else class="app-shell" :class="{ desktop: isDesktopShell, 'desktop-titlebar-host': hasDesktopTitleBar }">
            <DesktopTitleBar v-if="isDesktopShell" />
            <!-- 双模式切换栏：login 页与宠物窗口不显示 -->
            <ModeSwitcher v-if="showModeSwitcher" />
            <div v-if="nodeVersionLow" class="node-warning-bar">
              {{ t('sidebar.nodeVersionWarning', { version: appStore.nodeVersion }) }}
            </div>
            <div class="app-layout" :class="{ 'no-sidebar': isLoginPage || !showSidebarInCurrentMode, 'code-mode': isCodeMode }">
              <button v-if="!isCodeMode && showMobileMenuButton" class="hamburger-btn" @click="handleMobileMenuClick">
                <img src="/logo.png" alt="Menu" style="width: 24px; height: 24px;" />
              </button>
              <div v-if="!isLoginPage && !isCodeMode && showAppSidebar && appStore.sidebarOpen" class="mobile-backdrop" @click="appStore.closeSidebar" />
              <!-- 助理模式侧边栏（Code 模式下隐藏） -->
              <AppSidebar v-if="!isLoginPage && showSidebarInCurrentMode" />
              <main class="app-main">
                <!-- 登录页不受双模式影响，始终显示路由视图 -->
                <router-view v-if="isLoginPage" />
                <template v-else>
                  <!-- 助理模式：路由视图（keep-alive 保留状态） -->
                  <router-view v-if="!isCodeMode" v-slot="{ Component }">
                    <keep-alive>
                      <component :is="Component" />
                    </keep-alive>
                  </router-view>
                  <!-- Code 模式：OpenCode 容器 -->
                  <CodeModeView v-else />
                </template>
              </main>
            </div>
          </div>
          <WebPet v-if="showWebPet" />
          <SessionSearchModal v-if="!isDesktopPetRoute" />
          <DefaultCredentialPrompt v-if="!isDesktopPetRoute" />
        </NNotificationProvider>
      </NDialogProvider>
    </NMessageProvider>
  </NConfigProvider>
</template>

<style scoped lang="scss">
@use '@/styles/variables' as *;

.app-shell {
  height: calc(100 * var(--vh));
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background-color: $bg-primary;
}

.app-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  width: 100%;
  max-width: 100%;
  overflow: hidden;

  &.no-sidebar {
    display: block;
  }
}

.app-shell.desktop-titlebar-host .app-layout {
  --vh: calc(1vh - 0.36px);
}

.app-main {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  background-color: $bg-primary;

  .no-sidebar & {
    height: 100%;
  }
}

.node-warning-bar {
  flex: 0 0 auto;
  width: 100%;
  z-index: 100;
  padding: 4px 16px;
  font-size: 12px;
  font-weight: 500;
  color: #b45309;
  background-color: #fef3c7;
  border-bottom: 1px solid #fde68a;
  text-align: center;
  line-height: 1.4;
}
</style>
