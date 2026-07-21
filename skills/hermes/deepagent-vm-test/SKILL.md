---
name: deepagent-vm-test
description: DeepAgent 的测试/验收任务（install-verify、docker build、pytest 等）必须在本机之外的专用 macOS 虚拟机 deepagent-vm 中执行，禁止在 localhost 跑。包含 SSH 密钥连接、环境引导、项目同步与验收命令。
---

# DeepAgent 测试虚拟机（deepagent-vm）

## 铁律（务必遵守）

> **DeepAgent 的所有测试、构建验证、安装验收，一律在虚拟机 `deepagent-vm` 中执行，绝不在本机（localhost）跑。**
> 本机只负责编写/编辑代码、git 操作、写文档。任何需要"跑起来验证"的动作都放到 VM。

小路明确要求：不要每次都提醒他"在 VM 里测"，这个约定写进 Skill，默认遵守。

## 测试虚拟机规格

| 项 | 值 |
|----|----|
| 主机地址 | `192.168.64.6` |
| 系统 | macOS（Apple Silicon / arm64，VMAPPLE 虚拟机的 macOS guest） |
| 用户 | `bluth` |
| 内存 | 8 GB |
| 磁盘 | ~474 GB 可用 |
| SSH 别名 | `deepagent-vm`（已写入本机 `~/.ssh/config`） |

## 连接方式（密钥，非密码）

- 本机 `~/.ssh/id_ed25519` 公钥已加入 VM 的 `~/.ssh/authorized_keys`（一次性配置）。
- 日常连接直接用别名，无需密码：
  ```bash
  ssh deepagent-vm                       # 交互
  ssh deepagent-vm 'uname -a'            # 单行命令
  ```
- 若提示 host key 警告，确认 `~/.ssh/config` 中 `deepagent-vm` 段含 `StrictHostKeyChecking no` + `UserKnownHostsFile ~/.ssh/known_hosts`，且 `ssh-keyscan -H 192.168.64.6 >> ~/.ssh/known_hosts` 已执行。
- **首次配置（仅当密钥丢失时）**：用密码 `0227` 通过 `sshpass` 注入公钥：
  ```bash
  sshpass -p 0227 scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ~/.ssh/id_ed25519.pub bluth@192.168.64.6:/tmp/id.pub
  sshpass -p 0227 ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null bluth@192.168.64.6 'mkdir -p ~/.ssh && cat /tmp/id.pub >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys && rm /tmp/id.pub'
  ```

## VM 环境引导（首次/缺失时执行）

VM 出厂是裸 macOS：**没有 Homebrew、Docker，python 仅是 3.9.6（项目需要 3.12）**。每次要做测试前先确认依赖齐备。

```bash
# 1) Homebrew（CI=1 非交互）
CI=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv)"

# 2) 运行时依赖（与 Homebrew Formula 一致）
brew install python@3.12 uv node@23

# 3) Docker（headless，适合 VM）
brew install docker colima
colima start --cpu 4 --memory 6
# 验证
docker info
```

> ⚠️ 注意：VM 内再跑 Linux 虚拟机（Colima）依赖嵌套虚拟化；若 `colima start` 失败，
> 改为安装 Docker Desktop for Mac（GUI，需人工确认），或上报限制给用户。
> 8 GB 内存下给 Colima 分配 6 GB 较紧，如 OOM 降到 4 GB。

## 项目同步（本机 → VM）

VM 没有项目代码，需从本机同步。用 `rsync` 排除大目录，避免每次全量拷贝：

```bash
rsync -az --delete \
  --exclude='.git' --exclude='node_modules' --exclude='.venv' \
  --exclude='dist/releases' --exclude='__pycache__' --exclude='*.pyc' \
  /Volumes/Doc/Code/deepseekagent/ \
  deepagent-vm:/Users/bluth/Code/deepseekagent/
```

- 源路径末尾的 `/` 表示同步目录内容。
- 首次同步约 2–3 GB（含 webui/dist、embedded opencode 二进制），耗时数分钟；后续增量很快。
- 若只想验证 tarball（不装依赖），可只传 `dist/releases/*.tar.gz` + `scripts/` + `tests/`。

## 在 VM 中执行验收

```bash
# 登录 VM
ssh deepagent-vm

# —— 安装/结构验收（对应 31 期任务）——
cd ~/Code/deepseekagent
bash scripts/install-verify.sh                 # 完整三阶段（含 Phase 3 实际安装）
# bash scripts/install-verify.sh --skip-install  # 仅结构检查（快）

# —— Docker 构建验证（对应 31 期 31.11）——
# 确保 colima 已启动
colima status || colima start --cpu 4 --memory 6
docker build -t deepagent .

# —— pytest（Harness 回归）——
source .venv/bin/activate 2>/dev/null || uv venv && uv sync
pytest tests/test_harness_*.py -q
```

## 本机 vs VM 职责对照

| 动作 | 在哪里做 |
|------|---------|
| 写代码 / 改文档 / git commit / 生成 banner | 本机 localhost |
| `scripts/install-verify.sh` | **VM** |
| `docker build` | **VM** |
| `pytest` 回归 | **VM** |
| `git push` | 本机（push 到远程，不依赖 VM） |
| 生成 release tarball（`build-release.sh`） | 本机即可，产物随项目同步到 VM |

## 自检清单（每次测试前）

- [ ] `ssh deepagent-vm 'echo ok'` 无需密码即可连通
- [ ] VM 上 `python3.12 --version` 存在（≥3.12）
- [ ] 需要 Docker 时 `colima status` 正常 / `docker info` 可用
- [ ] 项目已 `rsync` 到 `~/Code/deepseekagent`（且含最新改动）
- [ ] 测试命令在 `ssh deepagent-vm '...'` 中执行，不在本机
