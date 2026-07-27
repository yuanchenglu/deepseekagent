# 第一阶段：开源 CLI Alpha

> 状态：执行中  
> 唯一公开入口：https://deepseekagent.starseas.org  
> 唯一支持平台：macOS 15.5，Apple Silicon  
> 阶段产物：公开仓库 + 可从官网安装的 CLI Alpha

## 1. 产品结果

目标用户可以在一台装有 Hermes 和 OpenCode 的 Mac 上执行：

```bash
curl -fsSL https://deepseekagent.starseas.org/install.sh | bash
deepagent --version
deepagent setup
deepagent doctor
deepagent
```

并完成至少一个正式支持模型提供商的真实 Agent 任务。安装、升级、回滚或卸载前后，Hermes 和 OpenCode 的命令、进程、配置与数据均没有非预期变化。

## 2. 冻结范围

包含：Core、CLI、安装器、更新器、安全卸载器、官网安装页、发布 Manifest、SHA-256、开源治理文档。

不包含：`webui/`、旧 Electron、内置 OpenCode、Code Mode 运行包、LAN/公网访问、Intel macOS、Linux、Windows。

公开命令只承诺：

- `deepagent --version`
- `deepagent setup`
- `deepagent doctor`
- `deepagent`
- `deepagent update`
- `deepagent uninstall`

## 3. 不可变发布契约

- `DEEPAGENT_HOME` 是唯一产品根目录，默认 `~/.deepagent`。
- 用户已有 `HERMES_HOME` 不得改变 DeepAgent 根目录；内部兼容值只在 DeepAgent 进程或子进程内映射。
- 唯一全局命令是 `~/.local/bin/deepagent`，不创建 `hermes` 或 `opencode`。
- 安装器不使用 `sudo`，不支持非 `Darwin arm64`。
- 安装器先取得渠道 Manifest，再取得不可变版本 Manifest 和 Core 压缩包；任何缺失、格式错误、大小或 SHA-256 不一致都失败退出。
- 安装使用 `versions/<version>/`，验证成功后再切换 `current`。
- 卸载只处理 `install-manifest.json` 登记的相对路径，并执行 realpath 边界检查。
- `--keep-data` 保留配置和会话；完全卸载也不删除未登记文件。
- CLI Alpha 包不得包含 `webui/`、Electron 和 `embedded/opencode/`。

## 4. 工作包与执行顺序

| 编号 | 工作包 | 实施要求 | 完成证据 | 状态 |
|---|---|---|---|---|
| P1-01 | 凭据止血 | 删除工作树中的发布凭据，轮换外部对象存储/发布/服务凭据 | 新凭据生效、旧凭据失效记录 | 外部操作待完成 |
| P1-02 | Git 历史清理 | 扫描所有 refs；轮换后清除历史秘密；重新扫描 | 全 refs 扫描报告为零 | 待授权改写历史 |
| P1-03 | 许可边界 | 根 README 许可矩阵；Core MIT；`webui/` BSL-1.1；依赖清单 | 人工审查 + 扫描报告 | 已实施，待门禁 |
| P1-04 | 产品目录隔离 | 只认 `DEEPAGENT_HOME`；不读取 Hermes/OpenCode 用户目录 | 单元测试 + VM 基线对比 | 已实施，待 VM |
| P1-05 | 安装/升级/回滚 | 版本目录、渠道/版本 Manifest、SHA-256、失败回滚 | 安装器自动化 + VM 场景 | 已实施，待 VM |
| P1-06 | 安全卸载 | Manifest 所有权、路径边界、保留数据、未知目录拒绝 | 单元测试 + VM 场景 | 已实施，待 VM |
| P1-07 | Core-only 制品 | Release 构建排除 UI/OpenCode，只发布一组校验制品 | tar 内容审计 | 已实施，待 CI |
| P1-08 | 官网入口 | `/install.sh` 返回 Shell；文档只有正式域名 | HTTP 响应与官网 E2E | 已实施，待线上 |
| P1-09 | CLI 闭环 | version/setup/doctor/首次真实任务 | VM 录屏或测试记录 | 待 VM/模型凭据 |
| P1-10 | 发布门禁 | 自动测试、秘密、许可证、制品一致性、P0/P1 | 发布检查表全绿 | 待完成 |

不得跳过依赖顺序：P1-01 → P1-02 → P1-10 → 公开仓库；P1-04/05/06/07/08/09 可并行准备，但必须全部进入 P1-10。

## 5. 发布数据格式

渠道文件 `releases/channels/alpha.json` 只指向已验收版本。版本文件 `releases/manifests/<version>.json` 至少包含：产品名、渠道、版本、操作系统、架构、制品文件名、URL、字节数和 SHA-256。Git tag、Manifest 的 `version` 和压缩包内 `VERSION` 必须完全相同。

发布顺序固定为：构建 → 测试 → 上传不可变制品 → 从对象存储回读验证 → 更新 `channels/alpha.json`。渠道文件失败不能留下半发布状态。

## 6. Parallels 验收剧本

1. 恢复干净快照，创建 `pre-deepagent-coexistence`。
2. 安装并启动 Hermes/OpenCode；记录 `which`、版本、进程、监听端口，并对 `~/.hermes`、`~/.config/opencode`、`~/.opencode` 生成路径/大小/哈希基线。
3. 从正式官网安装，不使用本地脚本或仓库路径。
4. 依次验证 version、setup、doctor、交互 CLI 和首次真实任务。
5. 验证同版本覆盖、升级、故意失败的升级、自动回滚、显式回滚。
6. 验证 `uninstall --keep-data`，重装后确认数据恢复；再验证 `uninstall --full`。
7. 重新启动 Hermes/OpenCode，对比步骤 2 的命令、配置、服务、端口和受保护目录。
8. 分别注入：下载中断、渠道文件缺失、版本 Manifest 缺字段、哈希错误、目标目录无写权限、未知旧目录、恶意 tar 路径和符号链接。

每个场景必须记录：前置快照、命令、退出码、关键日志、目录差异、结论和缺陷编号。

## 7. Go/No-Go 门禁

只有以下条件全部为真才允许公开仓库并提升 `latest-alpha`：

- 所有自动化测试通过；
- 所有 Git refs 无有效秘密，且旧凭据已确认失效；
- 许可证扫描无未声明冲突；
- Core 压缩包内容审计无 UI/OpenCode；
- 安装、覆盖、升级、失败回滚、两种卸载通过；
- Hermes/OpenCode 受保护目录无非预期变化；
- 正式官网 `/install.sh` 的响应类型、内容、下载链路通过；
- 至少一个正式支持模型完成真实任务；
- P0/P1 为零。

任一项缺失时结论必须是 **No-Go**，不得用 warning 或“已知问题”替代失败。
