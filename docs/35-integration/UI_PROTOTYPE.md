# UI_PROTOTYPE — 双模式切换 UI 原型

> 阶段 8 产出物 · 2026-07-22

## 1. 交互流程图

```
┌──────────────────────────────────────────────────────┐
│  Electron MainWindow                                 │
│                                                       │
│  ┌─ TitleBar (darwin/win32 only) ──────────────────┐ │
│  │ traffic-lights / window-controls                │ │
│  └─────────────────────────────────────────────────┘ │
│  ┌─ ModeSwitcher (⭐ 新增, 高 44px) ──────────────┐ │
│  │ [💬 助理模式]   [⌨ Code 模式]   ← Tab 风格     │ │
│  │  active-tab 有高亮指示器(底部 2px accent 线)    │ │
│  └─────────────────────────────────────────────────┘ │
│  ┌─ Content Area ─────────────────────────────────┐ │
│  │                                                 │ │
│  │  助理模式:                    │ Code 模式:      │ │
│  │  ┌─Sidebar─┐ ┌─router-view─┐  │ ┌─CodeModeView─┐│ │
│  │  │ nav...  │ │ (keep-alive)│  │ │ 启动进度/    ││ │
│  │  │         │ │ chat/jobs/..│  │ │ <webview>    ││ │
│  │  └─────────┘ └─────────────┘  │ │ 错误面板     ││ │
│  │                               │ └──────────────┘│ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

## 2. 组件树

```
App.vue (NConfigProvider 包裹)
├── DesktopTitleBar (桌面 darwin/win32)
├── ⭐ ModeSwitcher ← 新增，在 app-layout 之上
│     ├── button.mode-tab.assistant (active when mode=assistant)
│     └── button.mode-tab.code (active when mode=code)
├── div.app-layout
│     ├── AppSidebar (仅助理模式 + 非 login)
│     └── main.app-main
│           ├── <router-view v-if="mode==='assistant'">  ← keep-alive
│           └── <CodeModeView v-else>
├── WebPet (非桌面非pet)
├── SessionSearchModal
└── DefaultCredentialPrompt

CodeModeView.vue
├── div.code-mode-container (flex column, h=100%)
│   ├── header (40px, 显示"OpenCode" + 状态指示灯 + 刷新按钮)
│   ├── content (flex 1)
│   │   ├── 加载态 (spinner + "正在启动 OpenCode 运行时…")
│   │   ├── 运行态 (<webview :src="url"> 或 <iframe>)
│   │   └── 错误态 (icon + 错误信息 + 重试按钮)
│   └── footer (可选, 显示当前注入的 model/provider)
```

## 3. 布局图（ASCII 高保真）

```
┌─────────────────────────────────────────────────────────┐
│ ▢ ▢ ▢  Hermes Studio                        — □ ✕      │ ← TitleBar
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐                      │
│  │ 💬 助理模式  │  │ ⌨  Code 模式 │   ← 底部蓝色下划线   │ ← ModeSwitcher 44px
│  └──────────────┘  └──────────────┘                      │
├────────────┬────────────────────────────────────────────┤
│ ▸ Agent    │  Chat                                       │
│ ▸ Monitor  │  ┌──────────────────────────────────────┐  │
│ ▸ Tools    │  │  AI: 你好，有什么可以帮你？           │  │
│ ▸ System   │  │                                      │  │
│            │  │  You: _______________                │  │
│ [Model ▾]  │  └──────────────────────────────────────┘  │
│ [Profile▾] │                                             │
│ ● Connected│                                             │
│  EN / 🌙   │                                             │
│ v0.9.0     │                                             │
└────────────┴─────────────────────────────────────────────┘

切换到 Code 模式后:
┌─────────────────────────────────────────────────────────┐
│ ▢ ▢ ▢  Hermes Studio                        — □ ✕      │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐                      │
│  │ 💬 助理模式  │  │ ⌨  Code 模式 │                      │
│  └──────────────┘  └──────────────┘                      │
├─────────────────────────────────────────────────────────┤
│  Code Mode                                               │
│  ┌────────────────────────────────────────────────────┐ │
│  │ ● OpenCode 运行中    模型: claude-sonnet-4  [↻]   │ │ ← 40px header
│  ├────────────────────────────────────────────────────┤ │
│  │                                                    │ │
│  │   <webview src="http://127.0.0.1:4096">           │ │ ← flex 1
│  │   (OpenCode 自带 WebUI：文件树/编辑器/终端/AI)    │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 4. ModeSwitcher 视觉规范
- 高度 44px，背景 `var(--bg-secondary)` / SCSS `$bg-secondary`
- 水平排列两个 Tab，Tab 内 padding 12px 24px
- 活跃 Tab：底部 2px accent 线 + 文字色 `$accent-primary` + 字重 600
- 非活跃 Tab：文字色 `$text-secondary`，hover 背景 `rgba(accent, 0.06)`
- Code Tab 在非桌面环境：opacity 0.5，cursor not-allowed，title="Code 模式仅桌面版本可用"
- 暗/亮主题均适配（使用 SCSS 变量）

## 5. 自审 → 修改 → 再截图 迭代记录

### 迭代 1（初稿）
- ModeSwitcher 放在 AppSidebar 内部（sidebar-top-actions 上方）
- ❌ 自审问题：Code 模式下 Sidebar 不该显示助理导航；放 Sidebar 内会导致 Code 模式仍看到 Agent/Monitoring 分组，视觉割裂。

### 迭代 2（调整）
- ModeSwitcher 移到 App.vue 中 TitleBar 下方、app-layout 上方，作为全局 44px 顶栏
- ✅ Code 模式下 Sidebar 隐藏（`v-if="mode==='assistant' && showAppSidebar"`）
- CodeModeView 有自己的 40px 内置 header

### 迭代 3（细节打磨）
- Tab 样式从"按钮组"改为"底部 accent 线"，更像现代 IDE/Tab 栏
- 增加非桌面环境 Code Tab disabled 状态
- 增加 model/provider 信息显示在 CodeModeView header 右侧，强化"配置共享"的视觉提示

### 迭代 4（最终）
- ModeSwitcher 在 login 页 / pet 窗口隐藏（与 AppSidebar 一致）
- 模式切换加 150ms CSS fade 过渡避免白屏感
- 移动端 ≤768px：ModeSwitcher 折叠为紧凑图标按钮（文字仅显示图标）
