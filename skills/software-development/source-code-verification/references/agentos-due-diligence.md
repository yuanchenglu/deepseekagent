# AgentOS 项目尽职调查案例

## 背景

用户机器上跑着一个 `agentos web_ui` 进程占 11.3% CPU，问"这个是啥？"、"这个项目的意义是啥？"

## 执行过程

### 第 1 步：进程溯源

```bash
ps aux --sort=-%cpu | head -10
# 找到 PID 1588: agentos web_ui (11.3% CPU)

ls -la /home/bluth/Code/agentos/
# 确认是一个完整的项目目录

ps -p 1588 -o pid,cmd --no-headers
# -> /home/bluth/Code/agentos/venv/bin/python .../services/web_ui.py
```

### 第 1b 步：systemd 服务检测（扩展溯源）

找到进程后，检查是否有 systemd 服务管理它：

```bash
systemctl list-units --type=service | grep -i agentos
# 发现两个 service:
#   agentos-web.service  — AgentOS Web UI (PID 1588 对应的服务)
#   agentos-llm.service  — AgentOS LLM Service

# 检查是否开机自启
systemctl is-enabled agentos-web.service
# -> enabled（回答了这个进程会否随系统启动）

cat /etc/systemd/system/agentos-web.service
# 看到 ExecStart 指向 venv/bin/python .../services/web_ui.py
```

**为什么这一步重要**：只查 ps 只能看到"当前在跑"，查 systemd 才能回答"重启后还会不会回来"。这两个问题用户都会关心。

### 第 2 步：读源码判断实际功能

`services/web_ui.py`（158 行）：
- 基于 Gradio 的聊天界面
- 直调阿里百炼 API（百炼的 OpenAI 兼容接口）
- 支持 GLM-5 / Qwen3.5 Plus 等 7 个模型切换
- 纯聊天，无自动化、无工具链、无 Agent 能力

`services/llm_service.py`（177 行）：
- FastAPI 代理服务
- 也是调阿里百炼 API
- 无额外功能

### 第 3 步：项目级尽调

> ⚠️ **经验教训：先检查远程版本是否最新！**
> 本例中，本地仓库只有 5 次提交（v1.0.0.3），而远程已有 225+ 次提交（v0.1.0），
> 代码量从 ~14K 行膨胀到 ~438K 行——所有基于本地版本做的结论都被推翻了。
> 详见下方「修正记录」。

#### 基于本地版本（v1.0.0.3，已过时）

```bash
# 统计各语言代码行数
find . -name "*.py" -o -name "*.c" -o -name "*.rs" -o -name "*.go" -o -name "*.ts" \
  | grep -v venv | grep -v .git | grep -v build \
  | xargs wc -l | sort -rn
# C 代码: 13,740 行
# Python: 335 行（仅 web_ui.py + llm_service.py）
# Rust/Go/TS: 0 行

# 识别空文件
find . -name "*.py" -o -name "*.rs" -o -name "*.go" -o -name "*.ts" -o -name "*.c" \
  | grep -v venv | grep -v .git | grep -v build \
  | xargs wc -l | grep "0 "
# 57 个测试文件 = 0 行
# Rust SDK (9个文件) = 0 行
# Go SDK (2个文件) = 0 行
# TS SDK (10个文件) = 0 行
# Python SDK (13个文件) = 0 行
# 所有 Agent 应用 (7个) = 0 行
# 所有脚本 (5个) = 0 行

# 检查 git 活跃度
git log --oneline -5
# 总共 5 次提交
# 最近一次是改 LICENSE
```

#### 基于远程版本（v0.1.0，实际状态）

```bash
# 对比远程
git fetch --dry-run
# 发现: 远程 main 强制推送，落后 225+ 次提交
# 代码量：1858 files changed, 448007 insertions(+), 22445 deletions(-)

# 各语言实际代码量（远程 v0.1.0）
# C: 221,322 行
# Python: 81,819 行
# Go SDK: 9,907 行
# Rust SDK: 7,416 行
# TypeScript SDK: 9,674 行
# 测试: 108,210 行
# 总计: ~438,000 行

# 远程仓库活跃度
# 225+ 次提交，多分支并行开发（feature/official-hubs, hotfix, release）
# 发布 Tags: v0.0.4, v0.0.5
# 有 Docker 镜像 + Desktop 客户端下载
```

### 第 4 步：交叉验证 README vs 代码

#### 过时版本（v1.0.0.3）

| README 声称 | 代码现实 |
|-------------|---------|
| 微内核架构 | ✅ C 代码 13,740 行，有 IPC/内存/任务调度 |
| MemoryRovol 四层记忆 | ✅ C 代码完整 |
| 三层核心运行时 | ✅ C 代码完整 |
| Rust SDK | ❌ 9 个空文件 |
| Go SDK | ❌ 2 个空文件 |
| TypeScript SDK | ❌ 10 个空文件 |
| Python SDK | ❌ 13 个空文件 |
| 应用层 (docgen/commerce) | ❌ 空文件 |
| Agent 市场 | ❌ 空文件 |
| 完整端到端集成测试 | ❌ 57 个空文件 |

#### 实际版本（v0.1.0）

| README 声称 | 代码现实 |
|-------------|---------|
| 微内核架构 | ✅ C 代码 221,322 行 |
| MemoryRovol → 独立仓库 | ✅ 拆分为独立项目，集成测试关联 |
| 三层核心运行时 | ✅ C 代码完整 + 测试 |
| Rust SDK | ✅ 7,416 行，有 agent/client/memory/modules |
| Go SDK | ✅ 9,907 行 |
| TypeScript SDK | ✅ 9,674 行 |
| Docker + Desktop 客户端 | ✅ 有独立发行版本 |
| CI/CD | ✅ 6 个核心工作流，CTest 集成 |
| 多协议支持 | ✅ Claude/OpenClaw/AgntCy 等协议桥接 |

## 关键发现

1. **原始分析基于过时的本地仓库** — 本地 v1.0.0.3（~14K 行）vs 远程 v0.1.0（~438K 行），几乎所有"空壳"结论在远程上不成立
2. **唯一能跑的 web_ui 跟内核无关** — 这在新旧版本中都成立，它只是调阿里百炼 API 的聊天界面
3. **项目并非停更，而是活跃开发中** — 225+ 次提交，多分支，版本发布，生态建设

## 修正记录

| 修正项 | 原始结论 | 修正后 |
|--------|---------|--------|
| 项目状态 | "已停更，共 5 次提交" | **活跃开发中，225+ 次提交，v0.1.0 已发布** |
| SDK 实现 | "Rust/Go/TS SDK 全部空文件" | **各语言 SDK 有 7K-10K 行真代码** |
| 测试 | "57 个空文件" | **108,210 行测试代码** |
| 文档 vs 代码 | "README 远超实际" | **基本匹配（远程版本）** |

## 核心教训

**永远不要假设本地 clone 代表了项目的最新状态。** 在做任何基于代码的分析前，先执行：

```bash
git remote -v
git fetch --dry-run
git log --oneline HEAD..origin/main | wc -l
```

如果远程有大量更新，基于本地版本的结论大概率是错的。用 `git show origin/main:path/to/file` 基于远程版本验证，或者拉取最新代码后重做分析。

## 服务处置记录

用户决定关闭 AgentOS 服务后，实际执行：

```bash
# 1. 停止服务
sudo systemctl stop agentos-web.service agentos-llm.service

# 2. 禁用开机自启
sudo systemctl disable agentos-web.service agentos-llm.service

# 3. 验证效果
top -bn1 | head -4
```

**操作前 vs 操作后：**

| 指标 | 操作前 | 操作后 | 变化 |
|------|--------|--------|------|
| agentos-web CPU | 11.3% | 0% | 释放 |
| agentos-llm CPU | ~10% | 0% | 释放 |
| 可用内存 | 163 MB | 683 MB | +520 MB |
| Load Average | 5.20 | 4.80 | 略降 |

**处置要点**：只是 `kill PID` 不够——systemd 服务会重启进程。必须 `stop + disable` 两条命令才能彻底斩断。

## 对用户的价值

- **web_ui 进程**：跑的是旧版本代码（v1.0.0.3），吃 CPU 但不产生增量价值，建议关闭
- **项目本身**：v0.1.0 认真了很多，有 44 万行代码和完备生态，如果感兴趣可以删掉本地旧版重 clone
- **C 内核架构**：IPC 微内核 + MemoryRovol 多层记忆的设计仍有参考价值
