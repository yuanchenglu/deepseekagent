---
name: hermes-consolidation
description: Cross-machine Hermes consolidation — centralized `.agents/skills/` store, symlink switching, memory merging, profile consolidation, and daily sync cron. Use when setting up a multi-machine Hermes fleet or migrating from flat skills to centralized store.
version: 1.0.0
category: hermes
---

# Hermes Multi-Machine Consolidation

完整的跨机器 Hermes 整合流程。适用于：新设备加入、从扁平 skills 切换为中心化 `.agents/skills/` 存储、多 profile 合并为单 profile、记忆融合。

## Architecture

```
每个机器:
  ~/.agents/skills/   ← 所有自定义技能的物理存储（单个扁平目录，无 category 嵌套）
  ~/.hermes/skills/   ← 软链指向 ~/.agents/skills/
  
同步方向:
  AuthoritativeSource (技能权威源)
    ↓ rsync --delete 每天凌晨 4:00
  CentralNode (主节点, 记忆权威)
    ↓ rsync
  Replica (从节点)
```

## 1. 跨机器预备：免密 SSH + Tailscale

```bash
# 用户名可能不同，先探测
for user in bluth ycl_pj root; do
  ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 \
    -o NumberOfPasswordPrompts=0 "$user@<target-ip>" "hostname" 2>&1 || true
done

# 使用 tailscale ssh（自动处理 host key）
tailscale ssh <user>@<tailscale-ip>
```

## 2. 建立中心化 Skills 存储

### 2.1 在目标机器上创建 `.agents/skills/`

```bash
ssh <user>@<target-ip> 'mkdir -p ~/.agents/skills'
```

### 2.2 从权威源同步

```bash
rsync -av --delete ~/.agents/skills/ <user>@<target-ip>:~/.agents/skills/
```

`--delete` 保证目标机器跟上权威源的增删。

### 2.3 切换为软链

```bash
ssh <user>@<target-ip> '
  mv ~/.hermes/skills ~/.hermes/skills.bak
  ln -s ~/.agents/skills ~/.hermes/skills
'
```

### 2.4 复制 Hermes 管理文件

旧 skills 目录中有 Hermes 需要的隐藏管理文件：

```bash
ssh <user>@<target-ip> '
  cp ~/.hermes/skills.bak/.bundled_manifest ~/.agents/skills/ 2>/dev/null
  cp ~/.hermes/skills.bak/.curator_state ~/.agents/skills/ 2>/dev/null
  cp ~/.hermes/skills.bak/.usage.json ~/.agents/skills/ 2>/dev/null
  cp ~/.hermes/skills.bak/.webui-managed-skills.json ~/.agents/skills/ 2>/dev/null
  cp ~/.hermes/skills.bak/.usage.json.lock ~/.agents/skills/ 2>/dev/null
'
```

### 2.5 检查 Mac 带来的无效软链并清理

从 macOS rsync 过来的 skills 可能包含指向 Mac 本地路径的符号链接：

```bash
ssh <user>@<target-ip> '
  find ~/.agents/skills -type l ! -exec test -e {} \; -delete
'
```

### 2.6 补充差异技能

对比 `~/.hermes/skills/`（旧）和 `.agents/skills/`（新），找出缺失的独立技能：

```bash
# 在权威源机器上
for d in ~/.hermes/skills.original/*/; do
  name=$(basename "$d")
  # 排除 category 目录（包含 DESCRIPTION.md 而非 SKILL.md）
  [ -f "$d/SKILL.md" ] || [ -f "$d/SKILL.yaml" ] || continue
  [ -d "$HOME/.agents/skills/$name" ] || echo "MISSING: $name"
done

# 复制缺失技能
cp -R ~/.hermes/skills.original/$missing_skill ~/.agents/skills/
```

## 3. 记忆（Memory）合并

### 3.1 收集三份 MEMORY.md + USER.md

```bash
mkdir -p ~/merge_temp
cp ~/.hermes/memories/MEMORY.md ~/merge_temp/MEMORY_A.md
scp <machine-B>:~/.hermes/memories/MEMORY.md ~/merge_temp/MEMORY_B.md
scp <machine-C>:~/.hermes/memories/MEMORY.md ~/merge_temp/MEMORY_C.md
```

### 3.2 对比合并

三台机器的记忆往往各有侧重，不要简单覆盖：

| 源 | MEMORY.md 侧重 |
|----|---------------|
| 主工作站 | CTO 运营、方舟众测打分、Commit 规范、协作模式 |
| 服务器 | 写作风格、飞书 Wiki 结构、Obsidian 路径、自媒体规则 |
| 开发机 | X 发文铁律、模型架构参数、本地环境配置 |

合并原则：按主题重组，保留独特内容，去重共同内容。

### 3.3 备份并写入

```bash
# 备份旧记忆
cp ~/.hermes/memories/MEMORY.md ~/.hermes/memories/MEMORY.md.pre-merge
cp ~/.hermes/memories/USER.md ~/.hermes/memories/USER.md.pre-merge

# 写入合并版
cp ~/merge_temp/MEMORY_merged.md ~/.hermes/memories/MEMORY.md
cp ~/merge_temp/USER_merged.md ~/.hermes/memories/USER.md
```

### 3.4 推送到其他机器

```bash
rsync -av ~/.hermes/memories/ <target>:~/.hermes/memories/
```

## 4. Profile 精简（多 Profile → 单 Default）

### 4.1 备份有价值内容

每个 profile 的 SOUL.md（角色定义和原则）可能有独特价值：

```bash
mkdir -p ~/profile_backup
cp ~/.hermes/profiles/course-designer/SOUL.md ~/profile_backup/
cp ~/.hermes/profiles/course-designer/profile.yaml ~/profile_backup/
cp ~/.hermes/profiles/cto/SOUL.md ~/profile_backup/
cp ~/.hermes/profiles/yunying/SOUL.md ~/profile_backup/
```

### 4.2 提取独有 Skills

检查每个 profile 的独立 skills 目录（如果 profile 使用独立 skills 而非软链共享）：

```bash
for s in ~/.hermes/profiles/<name>/skills/*/; do
  name=$(basename $s)
  [ "$name" = "skills" ] && continue  # 跳过 symlink
  [ -d "$HOME/.agents/skills/$name" ] || [ -e "$HOME/.agents/skills/$name" ] || \
    echo "UNIQUE IN PROFILE: $name"
done
```

### 4.3 停止多余 Gateway

每个 profile 独立运行自己的 `gateway run` 进程。必须通过 systemd 禁用和停止：

```bash
# 查找服务
systemctl --user list-units --type=service | grep hermes

# 禁用并停止多余服务
systemctl --user disable hermes-gateway-<name>
systemctl --user stop hermes-gateway-<name>
```

如果 systemd 命令也被网关阻塞，直接 `kill -9 <PID>` 然后快速 `systemctl --user stop`（systemd 自动重启有时间窗口）。

### 4.4 删除 Profile 目录

```bash
# 先删大文件（state.db 可能几百 MB）
rm -f ~/.hermes/profiles/<name>/state.db
rm -f ~/.hermes/profiles/<name>/state.db-shm
rm -f ~/.hermes/profiles/<name>/state.db-wal

# 再删整个目录
rm -rf ~/.hermes/profiles/<name>
```

### 4.5 删除快捷命令（如果有）

```bash
rm -f ~/.local/bin/cto ~/.local/bin/course-designer ~/.local/bin/yunying 2>/dev/null
```

## 5. 建立每日同步 Cron

### 5.1 创建同步脚本

在中央节点上创建 `~/sync_hermes.sh`：

```bash
#!/bin/bash
# Hermes 三机同步：权威源(技能) → 中央节点(主) → 副本(从)

LOG="/tmp/hermes-sync-$(date +%Y%m%d-%H%M).log"
exec > "$LOG" 2>&1

echo "=== Sync $(date) ==="

# 从权威源拉取 skills
rsync -av --delete bluth@<authoritative-ip>:~/.agents/skills/ ~/.agents/skills/

# 从权威源拉取 memory
rsync -av bluth@<authoritative-ip>:~/.hermes/memories/ ~/.hermes/memories/

# 推送到从节点
rsync -av --delete ~/.agents/skills/ bluth@<replica-ip>:~/.agents/skills/
rsync -av ~/.hermes/memories/ bluth@<replica-ip>:~/.hermes/memories/

# 推回权威源（如果记忆有合并更新）
rsync -av ~/.hermes/memories/ bluth@<authoritative-ip>:~/.hermes/memories/

echo "=== Sync complete ==="
```

### 5.2 设置 crontab

```bash
chmod +x ~/sync_hermes.sh
(crontab -l 2>/dev/null | grep -v "sync_hermes"
 echo "0 4 * * * /home/bluth/sync_hermes.sh > /tmp/hermes-sync-cron.log 2>&1") | crontab -
```

## 6. Gateway 重启受阻的临时方案

当 SSH 连接到运行 Hermes Gateway 的机器时，`hermes gateway restart` 和 `systemctl --user stop` 都会被网关拦截（检测到同一用户 session 发起的命令，发送 SIGTERM 中断 SSH）。

**方案：直接 `kill <PID>`**

```bash
GATEWAY_PID=$(ps aux | grep "python.*hermes_cli.main gateway run" | \
  grep -v grep | head -1 | awk '{print $2}')
kill "$GATEWAY_PID"
sleep 5
systemctl --user status hermes-gateway.service
```

systemd 的 `Restart=on-failure` 会自动重启新进程，本次会使用更新后的 pipx 版本。

## 7. 验证清单

- [ ] `~/.hermes/skills` → 软链指向 `~/.agents/skills/`
- [ ] `.agents/skills/` 中的技能数三台一致
- [ ] 无损坏软链（`find ~/.agents/skills -xtype l` 为空）
- [ ] MEMORY.md + USER.md 三台一致
- [ ] 只有 1 个 default profile
- [ ] Hermes 管理文件（`.bundled_manifest`, `.usage.json` 等）在 `.agents/skills/` 中
- [ ] crontab 已设置，脚本语法正确
- [ ] Gateway 正常运行，飞书已连接

## Pitfalls

- **macOS→Linux rsync 会把 Mac 软链带过去** — `/Users/bluth/...` 路径在 Linux 上无效，需要 `find -xtype l -delete`。
- **`systemctl --user stop` 也可能被网关拦截** — 如果被拦，直接 `kill -9 <PID>`，systemd 会在短暂延迟后重启。利用这段时间窗口用 `systemctl --user stop` 或 `disable`。
- **profile 目录很大** — state.db 可能几百 MB，先删 db 文件再删目录，避免 `rm -rf` 超时。
- **yunying profile 的 SOUL.md 可能错放** — 检查是否跟 course-designer 的 SOUL.md 内容一样（复制粘贴错误）。yunying 的独立 memories 可能为空。
- **软链切换后 Hermes 管理文件丢失** — `.bundled_manifest`, `.curator_state`, `.usage.json` 等文件在原 `~/.hermes/skills/` 目录中，软链后不自动迁移。必须手动复制。
- **gateway_state.json 更新延迟** — 新 gateway 进程可能不会立即更新 gateway_state.json 的 PID 和连接状态。检查 `~/.hermes/logs/gateway.log` 确认真实状态，不要只依赖 gateway_state.json。
