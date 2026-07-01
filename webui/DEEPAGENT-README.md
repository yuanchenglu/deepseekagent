# Deep Agent WebUI — 默认工作台

本目录是从 [Hermes Web UI](https://github.com/EKKOLearnAI/hermes-web-ui.git) fork 的版本，作为 **Deep Agent** 的默认 Web 工作台。

## 集成方式

- **数据目录**: `~/.deepagent-webui/`（而非 `~/.hermes-web-ui/`）
- **默认端口**: `8648`
- **品牌**: 页面标题和文案已替换为 "Deep Agent"，但内部包名和路由保持原样以兼容上游更新

## 架构

```
webui/
├── packages/client/    # Vue 3 + Naive UI 前端
├── packages/server/    # Koa 后端
├── bin/                # CLI 入口
└── scripts/            # 构建和部署脚本
```

## 开发

```bash
# 安装依赖并构建
cd webui && npm install && npm run build

# 启动（由 deepagent webui start 触发）
npm run start
```

## 与 DeepAgent 集成

WebUI 通过 agent-bridge 连接到运行中的 DeepAgent IPC，作为其前端界面。
用户可以通过 `deepagent webui` 子命令管理 WebUI 的生命周期。
