# ============================================================================
# DeepAgent Dockerfile — 多阶段构建
# ============================================================================
# 按 31 期任务 31.11 Part B 要求改造：
#   1. 基于 python:3.12-slim
#   2. 多阶段构建：build stage（安装 uv + 依赖）→ runtime stage（仅复制产物）
#   3. EXPOSE 8648（WebUI 端口）
#   4. HEALTHCHECK 检测 8648 端口
#   5. ENTRYPOINT ["deepagent"]
#   6. 安装 curl、uv、nodejs
#   7. 品牌从 hermes → deepagent
#
# 构建命令:
#   docker build -t deepagent .
#
# 运行命令:
#   docker run -p 8648:8648 -v ~/.deepagent:/opt/data deepagent
#   docker run -p 8648:8648 -v ~/.deepagent:/opt/data deepagent webui start
#
# 健康检查:
#   curl -f http://localhost:8648/ || exit 1
# ============================================================================

# ─── Stage 1: Builder（安装依赖、构建产物） ──────────────────────────────
FROM python:3.12-slim AS builder

# 禁用 Python stdout 缓冲，确保日志即时输出
ENV PYTHONUNBUFFERED=1

# 安装构建依赖（build-essential 用于编译 C 扩展，git 用于某些 pip 包）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        procps \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv（Astral 的 Python 包管理器）
COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uvx /usr/local/bin/

# 设置工作目录
WORKDIR /opt/deepagent

# 先复制依赖文件（利用 Docker 层缓存）
COPY pyproject.toml uv.lock requirements.txt ./

# 创建虚拟环境并安装 Python 依赖（仅运行时依赖，不包含开发依赖）
RUN uv venv --python python3.12 && \
    uv sync --no-dev

# ─── Stage 2: Runtime（最终运行镜像） ─────────────────────────────────────
FROM python:3.12-slim AS runtime

# 禁用 Python stdout 缓冲
ENV PYTHONUNBUFFERED=1

# 品牌环境变量（从 hermes → deepagent）
ENV DEEPAGENT_HOME=/opt/data
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/deepagent/.playwright

# 安装运行时系统依赖
# - curl: HEALTHCHECK 和下载用
# - nodejs + npm: WebUI 和 embedded opencode 需要
# - ripgrep: 代码搜索工具
# - ffmpeg: 音视频处理
# - gosu: 权限降级（从 tianon/gosu 镜像复制）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        nodejs \
        npm \
        ripgrep \
        ffmpeg \
        procps \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 阶段复制 uv 二进制
COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uvx /usr/local/bin/

# 从 gosu 镜像复制 gosu 二进制（用于权限降级）
COPY --from=tianon/gosu:1.19-debian /gosu /usr/local/bin/

# 创建非 root 用户（从 hermes → deepagent）
# UID 可通过 DEEPAGENT_UID 环境变量在运行时覆盖
RUN useradd -u 10000 -m -d /opt/data deepagent

# 从 builder 阶段复制已安装的 Python 虚拟环境
COPY --from=builder --chown=deepagent:deepagent /opt/deepagent/.venv /opt/deepagent/.venv

# 复制项目源码（排除 .venv/.git/node_modules/ — 由 .dockerignore 处理）
COPY --chown=deepagent:deepagent . /opt/deepagent

WORKDIR /opt/deepagent

# 安装 Node.js 依赖和 Playwright（需要 apt 安装浏览器依赖）
USER root
RUN npm install --prefer-offline --no-audit && \
    npx playwright install --with-deps chromium --only-shell && \
    cd /opt/deepagent/scripts/whatsapp-bridge && \
    npm install --prefer-offline --no-audit && \
    npm cache clean --force

# 修复 entrypoint 权限
RUN chmod +x /opt/deepagent/docker/entrypoint.sh

# 确保文件归属正确
RUN chown -R deepagent:deepagent /opt/deepagent

# 切换到非 root 用户
USER deepagent

# 设置工作目录
WORKDIR /opt/deepagent

# ─── Docker 标准配置 ──────────────────────────────────────────────────────

# 暴露 WebUI 端口
EXPOSE 8648

# 健康检查：检测 WebUI 端口是否响应
# 间隔 30s，超时 5s，启动宽限 40s，重试 3 次
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8648/ || exit 1

# 数据卷挂载点
VOLUME ["/opt/data"]

# 入口点（从 /opt/hermes → /opt/deepagent）
ENTRYPOINT ["/opt/deepagent/docker/entrypoint.sh"]

# 默认命令
CMD ["deepagent"]
