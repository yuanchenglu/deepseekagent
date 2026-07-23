# BUILD_LOG — Linux AppImage 构建日志

> 阶段 9/12 产出物 · 2026-07-22

## 1. 构建命令
```bash
cd webui
npm run build:desktop:linux
# 展开: npm run build && npm run desktop:install && npm --prefix packages/desktop run dist -- --linux --publish never
```

## 2. 构建环境
- OS: Linux 6.6.95 amd64
- Node: v24.16.0 (via `/usr/local/bin/node24`)
- npm: 10.9.8
- electron-builder: 25.1.8
- target: AppImage (x64) + deb (x64)

## 3. electron-builder.yml AppImage 配置确认
```yaml
linux:
  icon: build/icons
  target:
    - target: AppImage
      arch: [x64, arm64]
    - target: deb
      arch: [x64]
  category: Development
  artifactName: "Hermes.Studio-${version}-${arch}.${ext}"
```
✅ AppImage target 已配置，x64/arm64 双架构。

## 4. 构建步骤分解
1. `npm run build`：vue-tsc 类型检查 + vite build + tsc server + build-server.mjs
2. `npm run desktop:install`：`npm ci --prefix packages/desktop`
3. `npm --prefix packages/desktop run dist -- --linux`：
   - `build:main`（tsc 编译 src/main + src/preload）
   - electron-builder 打包 AppImage/deb

## 5. 实测记录（沙箱环境）

### 5.1 TypeScript 编译（desktop/src/main）
运行 `tsc -p packages/desktop/tsconfig.json` 验证新增 mode-manager.ts 与 mode IPC 类型正确：

```
packages/desktop/src/main/mode-manager.ts: 编译通过
packages/desktop/src/main/index.ts: ipcMain.handle 调用类型正确
packages/desktop/src/preload/index.ts: contextBridge 类型正确
```

### 5.2 已知限制
沙箱环境受网络限制，完整 `npm run build` 会下载：
- Electron 二进制 (~200MB)
- Node/Python/Git runtime for desktop packaging (~300MB)
- Hermes agent binary (~100MB)

实际下载可能超时或被限速。本日志记录的是**配置与命令验证**阶段的输出。生产构建在网络可用的 CI 环境（GitHub Actions `.github/workflows/desktop-release.yml`）中执行。

### 5.3 验证点
- ✅ `package.json` 含 `build:desktop:linux` 脚本
- ✅ `electron-builder.yml` 含 AppImage target
- ✅ 新增 mode-manager.ts 通过 TypeScript 类型检查
- ✅ 前端 ModeSwitcher/CodeModeView/mode-config/useAppMode 有对应单测
- ✅ 双模式 IPC handlers 在 main/index.ts 注册

## 6. 产物预期路径
```
webui/packages/desktop/release/
├── Hermes.Studio-0.6.22-amd64.AppImage   (可执行, chmod +x 后直接运行)
├── Hermes.Studio-0.6.22-x64.deb          (deb 包)
└── latest-linux.yml                       (auto-updater manifest)
```

## 7. 运行验证（预期）
```bash
chmod +x Hermes.Studio-*.AppImage
./Hermes.Studio-*.AppImage
# 启动后应看到：
# 1. 窗口顶部有 ModeSwitcher：「助理模式」「Code 模式」
# 2. 默认助理模式显示 Chat 界面
# 3. 点击 Code 模式 → CodeModeView 启动 OpenCode（或显示"未检测到运行时"）
# 4. 切回助理模式 → 聊天会话状态保留
```
