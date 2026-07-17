#!/bin/bash
# ============================================================================
# DeepAgent Docker/Podman Entrypoint
# ============================================================================
# 启动时将配置文件引导到挂载的卷中，然后以 deepagent 用户运行。
#
# 功能：
#   1. 权限降级：root → deepagent 用户（通过 gosu）
#   2. 创建必要的目录结构
#   3. 初始化 .env / config.yaml / SOUL.md（仅首次）
#   4. 同步内置 Skills（manifest-based，保留用户自定义）
#   5. 执行 deepagent 命令
# ============================================================================
set -e

# 安装根目录（从 hermes → deepagent）
DEEPAGENT_HOME="${DEEPAGENT_HOME:-/opt/data}"
INSTALL_DIR="/opt/deepagent"

# --- 权限降级（通过 gosu） ---
# 当以 root 启动时（Docker 默认），可选地重新映射 deepagent 用户/组
# 以匹配宿主机 UID/GID，修复卷权限，然后以 deepagent 用户重新执行。
if [ "$(id -u)" = "0" ]; then
    if [ -n "$DEEPAGENT_UID" ] && [ "$DEEPAGENT_UID" != "$(id -u deepagent)" ]; then
        echo "Changing deepagent UID to $DEEPAGENT_UID"
        usermod -u "$DEEPAGENT_UID" deepagent
    fi

    if [ -n "$DEEPAGENT_GID" ] && [ "$DEEPAGENT_GID" != "$(id -g deepagent)" ]; then
        echo "Changing deepagent GID to $DEEPAGENT_GID"
        # -o 允许非唯一 GID（例如 macOS GID 20 "staff" 在 Debian 镜像中
        # 可能已作为 "dialout" 存在）
        groupmod -o -g "$DEEPAGENT_GID" deepagent 2>/dev/null || true
    fi

    actual_uid=$(id -u deepagent)
    if [ "$(stat -c %u "$DEEPAGENT_HOME" 2>/dev/null)" != "$actual_uid" ]; then
        echo "$DEEPAGENT_HOME is not owned by $actual_uid, fixing"
        # 在 rootless Podman 中，容器的 "root" 映射到非特权宿主 UID —
        # chown 会失败。这没关系：卷在宿主端已由映射用户拥有。
        chown -R deepagent:deepagent "$DEEPAGENT_HOME" 2>/dev/null || \
            echo "Warning: chown failed (rootless container?) — continuing anyway"
    fi

    echo "Dropping root privileges"
    exec gosu deepagent "$0" "$@"
fi

# --- 以下以 deepagent 用户运行 ---
source "${INSTALL_DIR}/.venv/bin/activate"

# 创建必要的目录结构。
# 缓存和平台目录（cache/images, cache/audio, platforms/whatsapp 等）
# 由应用按需创建 — 不在此预创建，以便新安装获得统一布局。
# "home/" 子目录是子进程（git, ssh, gh, npm…）的 per-profile HOME。
# 没有它，这些工具会写入 /root，这是临时的且跨 profile 共享的。
mkdir -p "$DEEPAGENT_HOME"/{cron,sessions,logs,hooks,memories,skills,skins,plans,workspace,home}

# .env — 仅首次安装时复制模板
if [ ! -f "$DEEPAGENT_HOME/.env" ]; then
    cp "$INSTALL_DIR/.env.example" "$DEEPAGENT_HOME/.env"
fi

# config.yaml — 仅首次安装时复制模板
if [ ! -f "$DEEPAGENT_HOME/config.yaml" ]; then
    cp "$INSTALL_DIR/cli-config.yaml.example" "$DEEPAGENT_HOME/config.yaml"
fi

# SOUL.md — 仅首次安装时复制模板
if [ ! -f "$DEEPAGENT_HOME/SOUL.md" ]; then
    cp "$INSTALL_DIR/docker/SOUL.md" "$DEEPAGENT_HOME/SOUL.md"
fi

# 同步内置 Skills（基于 manifest，保留用户自定义编辑）
if [ -d "$INSTALL_DIR/skills" ]; then
    python3 "$INSTALL_DIR/tools/skills_sync.py"
fi

# 执行 deepagent 命令
exec deepagent "$@"
