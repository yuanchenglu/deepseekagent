import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import { i18n } from './i18n'
import App from './App.vue'
import './styles/global.scss'
import 'katex/dist/katex.min.css'
import { desktopBridge } from '@/utils/desktop-bridge'

// Apply theme classes before mount to prevent FOUC (Flash of Unstyled Content)
const savedBrightness = localStorage.getItem('hermes_brightness') || 'system'
const savedStyle = localStorage.getItem('hermes_style') || 'ink'

// Resolve dark mode
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
const isDark = savedBrightness === 'dark' || (savedBrightness === 'system' && prefersDark)

// Resolve style
const isComic = savedStyle === 'comic'
const bridge = desktopBridge()
const isDesktopShell = bridge?.isDesktop === true
const isDesktopPetWindow = bridge?.windowKind === 'pet' || window.location.hash.startsWith('#/desktop-pet')

// Apply classes to prevent FOUC
if (isDark) {
  document.documentElement.classList.add('dark')
}
if (isComic) {
  document.documentElement.classList.add('comic')
}
if (isDesktopShell) {
  document.documentElement.classList.add('hermes-desktop-shell')
}
if (isDesktopPetWindow) {
  document.documentElement.classList.add('hermes-desktop-pet-window')
}

const app = createApp(App)
app.use(createPinia())
app.use(i18n)
app.use(router)
router.isReady().finally(() => {
  app.mount('#app')
})
