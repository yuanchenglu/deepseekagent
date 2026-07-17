# DeepAgent Docker — 构建与运行指南

## 构建镜像

```bash
# 从项目根目录构建
docker build -t deepagent .

# 指定构建参数（可选）
docker build -t deepagent:0.9.0-alpha.1 --build-arg VERSION=0.9.0-alpha.1 .
```

## 运行容器

### 基本运行

```bash
# 启动 DeepAgent（交互式）
docker run -it --rm \
  -p 8648:8648 \
  -v ~/.deepagent:/opt/data \
  deepagent

# 启动 WebUI
docker run -d --name deepagent-webui \
  -p 8648:8648 \
  -v ~/.deepagent:/opt/data \
  deepagent webui start
```

### 数据持久化

```bash
# 使用命名卷持久化数据
docker volume create deepagent-data

docker run -d --name deepagent \
  -p 8648:8648 \
  -v deepagent-data:/opt/data \
  deepagent
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEEPAGENT_HOME` | `/opt/data` | 数据目录（配置、日志、skills） |
| `DEEPAGENT_UID` | `10000` | 运行用户 UID（可匹配宿主机） |
| `DEEPAGENT_GID` | `10000` | 运行用户 GID（可匹配宿主机） |
| `PLAYWRIGHT_BROWSERS_PATH` | `/opt/deepagent/.playwright` | Playwright 浏览器路径 |

### 匹配宿主机 UID

```bash
# 获取当前用户 UID/GID
UID_GID="$(id -u):$(id -g)"

# 运行时指定
docker run -d \
  -p 8648:8648 \
  -v ~/.deepagent:/opt/data \
  -e DEEPAGENT_UID=$(id -u) \
  -e DEEPAGENT_GID=$(id -g) \
  deepagent
```

## 健康检查

容器内置 HEALTHCHECK 检测 8648 端口：

```bash
# 查看健康状态
docker inspect --format='{{.State.Health.Status}}' deepagent

# 查看健康检查日志
docker inspect --format='{{json .State.Health.Log}}' deepagent | jq .
```

## Dockerfile 结构

### 多阶段构建

| 阶段 | 基础镜像 | 说明 |
|------|----------|------|
| `builder` | `python:3.12-slim` | 安装构建依赖、uv sync |
| `runtime` | `python:3.12-slim` | 仅复制产物 + 运行时依赖 |

### 运行时依赖

- `curl`：HEALTHCHECK 和下载
- `nodejs` + `npm`：WebUI 和 embedded opencode
- `ripgrep`：代码搜索
- `ffmpeg`：音视频处理
- `gosu`：权限降级

### 端口

| 端口 | 用途 |
|------|------|
| 8648 | WebUI |

## 常用操作

```bash
# 进入容器
docker exec -it deepagent bash

# 查看 WebUI 日志
docker logs -f deepagent

# 重启容器
docker restart deepagent

# 更新镜像
docker pull deepagent:latest
docker stop deepagent && docker rm deepagent
docker run -d --name deepagent ... deepagent:latest
```
