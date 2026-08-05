# DeepAgent WebUI

DeepAgent WebUI 是第二阶段发布的浏览器界面。本目录采用 BSL-1.1，是源码可见软件，不属于 MIT 许可的 DeepAgent Core。

## 首发支持范围

首轮公开 Beta 只支持 macOS Apple Silicon。先从官网安装 Core，再安装并打开 WebUI：

```bash
curl -fsSL https://deepseekagent.starseas.org/install.sh | bash
deepagent webui install
deepagent webui open
```

生命周期命令：

```bash
deepagent webui start
deepagent webui open
deepagent webui status
deepagent webui stop
```

`open` 会创建一个短时、一次性的登录 Ticket。DeepAgent 不提供固定默认密码，也不会把浏览器会话 JWT 持久化到本地存储。

## 隔离与安全契约

- HTTP 默认只监听 `127.0.0.1`。
- LAN 发现、局域网和公网访问默认关闭。
- 配置和会话统一存放在 `~/.deepagent/data/`。
- PID、端口、锁和 Ticket 存放在 `~/.deepagent/runtime/webui/`。
- 启动器不会因为端口被占用就杀死或接管其他进程。
- 子进程只接收明确的环境变量白名单，不继承无关 API Key。
- 不读取、迁移或删除 Hermes 数据（`~/.hermes`）和用户 OpenCode 数据（`~/.config/opencode`、`~/.opencode`）。

旧 Electron 壳使用独立名称 `DeepAgent Legacy Preview` 和标识 `org.starseas.deepagent.legacy`，不作为官网主下载入口，只接受安全、路径和启动修复。

## 开发

```bash
npm install
npm run build
npm test
```

正式制品必须来自版本一致的 Git tag 和发布 Manifest。`deepagent webui install` 会拒绝缺失校验、大小或哈希不匹配、不安全压缩包，以及来源不明的既有目录。

## 许可

见 [LICENSE](./LICENSE)。仓库根目录的 DeepAgent Core 使用 MIT；本 WebUI/Desktop 目录使用 BSL-1.1。
