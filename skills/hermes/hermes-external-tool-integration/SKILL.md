---
name: hermes-external-tool-integration
description: 将外部工具/Skill 集成到 Hermes。两种模式：A) 外部 Python 工具（browser-harness、cc-connect 等）安装到 Hermes venv；B) 外部平台 Skill 仓库（Claude Code 插件、Codex CLI 技能等）提取 SKILL.md 注册到 Hermes。覆盖 pip 包安装和纯 Skill 适配两大场景。
version: 1.1.0
author: Hermes Agent
metadata:
  hermes:
    tags: [hermes, uv, venv, skill, integration, pip, claude-code, plugin-adaptation, pm-skills]
    related_skills: [hermes-agent, claude-code, codex, opencode]
---

# 将外部工具集成到 Hermes

当用户要求把某个 GitHub 上的项目"安装给 Hermes 使用"时，有两种情景：

## 核心发现

- **Hermes 的 venv 是用 `uv` 管理的**，`bin/` 目录下没有 `pip`，只有 `python` 和 `uv`
- 必须使用 `uv pip install --python <venv-python>` 来指定目标 venv，否则可能装到系统环境
- 外部工具的 **SKILL.md** 需要通过**软链接**注册到 `~/.hermes/skills/<name>/`，Hermes 新会话会自动加载

## 操作步骤

### 1. 定位 Hermes 的 venv Python

```bash
# 找到 hermes 可执行文件，反推 venv 路径
which hermes
# 输出示例：/home/user/.hermes/hermes-agent/venv/bin/hermes

# 确认 python 存在
ls -la /home/user/.hermes/hermes-agent/venv/bin/python*
```

### 2. 克隆仓库到稳定路径

```bash
cd ~/Code  # 或用户指定的目录
git clone <仓库地址>
cd <仓库名>
```

### 3. 用 uv 安装到 Hermes venv（editable 模式）

```bash
# 关键：--python 参数指定 Hermes 的 venv python，确保装到正确环境
uv pip install -e . --python /home/user/.hermes/hermes-agent/venv/bin/python
```

**为什么用 editable (`-e`)：** 这样 agent 后续修改仓库里的代码（如 browser-harness 的 `agent_helpers.py`）会立即生效，无需重新安装。

### 4. 验证安装

```bash
# 直接调用 CLI（通过 venv 的 python）
/home/user/.hermes/hermes-agent/venv/bin/<工具命令> --version

# 或 source activate 后调用
source /home/user/.hermes/hermes-agent/venv/bin/activate
<工具命令> --version
```

### 5. 注册 SKILL.md（如果有）

如果仓库提供了 `SKILL.md`，将其软链接到 Hermes skills 目录，让 Hermes 自动加载：

```bash
mkdir -p ~/.hermes/skills/<tool-name>
ln -sf ~/Code/<repo>/SKILL.md ~/.hermes/skills/<tool-name>/SKILL.md
```

**用软链接而非复制**：这样当仓库 `git pull` 更新后，skill 内容自动同步。

### 6. 最终验证

```bash
# 检查 skill 是否注册成功
ls -la ~/.hermes/skills/<tool-name>/

# 运行工具的诊断命令（如有）
<工具命令> --doctor
```

## 常见坑点

| 问题 | 原因 | 解决 |
|------|------|------|
| `pip: command not found` | Hermes venv 由 uv 创建，不含 pip | 用 `uv pip` 代替 |
| 装到了系统环境 | 没指定 `--python` | 始终加 `--python <venv-path>/bin/python` |
| skill 未生效 | 复制而非软链接，或路径不对 | 检查 `~/.hermes/skills/` 下是否有软链接 |
| 工具命令找不到 | 未安装到正确 venv，或没 source activate | 用全路径调用，或确认 `--python` 参数正确 |

## 示例：安装 browser-harness

```bash
# 1. 克隆
cd ~/Code && git clone https://github.com/browser-use/browser-harness.git

# 2. 安装到 Hermes venv
cd browser-harness
uv pip install -e . --python /home/bluth/.hermes/hermes-agent/venv/bin/python

# 3. 验证
/home/bluth/.hermes/hermes-agent/venv/bin/browser-harness --version

# 4. 注册 skill
mkdir -p ~/.hermes/skills/browser-harness
ln -sf ~/Code/browser-harness/SKILL.md ~/.hermes/skills/browser-harness/SKILL.md

# 5. 运行诊断
source /home/bluth/.hermes/hermes-agent/venv/bin/activate
browser-harness --doctor
```

## 适用场景

- browser-use/browser-harness
- anthropics/cc-connect
- 任何自带 CLI + SKILL.md 的 agent 工具
- 用户说 "clone 到 ~/Code/ 并安装给 hermes 使用"

## 情景 B：外部平台 Skill 仓库（非 Python 包）

当仓库是其他平台（Claude Code, Codex CLI, Gemini CLI 等）的纯 Skill 集合、没有 `pyproject.toml`/`setup.py` 时，操作流程不同。

### 典型场景

- Claude Code 插件市场（如 PM Skills Marketplace：`phuryn/pm-skills`）
- Codex CLI 插件包
- Gemini CLI 的 SKILL.md 集合

这些仓库的结构通常是：
```
repo/
├── plugin-1/
│   ├── skills/
│   │   ├── skill-a/SKILL.md
│   │   └── skill-b/SKILL.md
│   └── commands/          ← Claude Code 工作流定义，非 Hermes 原生格式
├── plugin-2/
│   └── ...
```

### 操作步骤

```bash
# 1. 克隆
cd ~/Code && git clone --depth 1 <仓库地址> <目录名>

# 2. 创建分类目录（建议用 pm-skills/ 等有意义的域名）
mkdir -p ~/.hermes/skills/<category>

# 3. 复制 Skill 目录（批量提取所有 SKILL.md）
for plugin in <目录名>/plugin-*/; do
  if [ -d "$plugin/skills" ]; then
    cp -r "$plugin/skills/"* ~/.hermes/skills/<category>/
  fi
done

# 4. （可选）创建分类 DESCRIPTION.md
cat > ~/.hermes/skills/<category>/DESCRIPTION.md << 'EOF'
---
description: ...
source: <仓库地址>
---
EOF

# 5. 验证
find ~/.hermes/skills/<category> -name "SKILL.md" | wc -l
ls ~/.hermes/skills/<category>/
```

### 注意事项

| 问题 | 说明 |
|------|------|
| **命令文件不兼容** | Claude Code 的 `commands/*.md` 是工作流编排文件，Hermes 不原生支持 `/command-name` 风格。可作为参考阅读，不需要复制 |
| **命名冲突** | 安装前检查 `ls ~/.hermes/skills/` 是否有同名目录。如果冲突，可在技能名前加前缀或选择不同分类目录 |
| **分类组织** | 用域名分组（如 `pm-skills/`、`codex-plugins/`），避免 60+ 个技能平铺在 skills/ 根目录 |
| **软链接 vs 复制** | 此类仓库通常只有 SKILL.md 无 Python 代码，用复制即可。若需跟踪上游更新才用 `ln -sf` |
| **Hermes 加载** | 新技能会被 Hermes 自动发现。如想立即在当前会话使用，执行 `/reload-skills` |

### 示例：安装 PM Skills Marketplace（68 个技能）

```bash
# 1. 克隆
cd ~/Code && git clone --depth 1 https://github.com/phuryn/pm-skills.git

# 2. 创建分类目录
mkdir -p ~/.hermes/skills/pm-skills

# 3. 提取所有 SKILL.md
for plugin in ~/Code/pm-skills/pm-*/; do
  if [ -d "$plugin/skills" ]; then
    cp -r "$plugin/skills/"* ~/.hermes/skills/pm-skills/
  fi
done

# 4. 创建 DESCRIPTION.md
cat > ~/.hermes/skills/pm-skills/DESCRIPTION.md << 'EOF'
---
description: 68 product management skills covering the full PM lifecycle.
source: https://github.com/phuryn/pm-skills
---
EOF

# 5. 验证
find ~/.hermes/skills/pm-skills -name "SKILL.md" | wc -l
# 输出：68
```

## 反向集成：外部 Agent 使用 Hermes 模型基础设施

当外部 AI Agent 工具（如 Agent TARS、Claude Computer Use 等）需要一个视觉语言模型（VLM）作为大脑，而我们已经通过 Hermes/OpenCode 拥有了多模态模型时，可以将该工具配置为使用 Hermes 的模型链路。

### 适用场景

- 用户安装了 Agent TARS / UI-TARS Desktop / 其他 GUI Agent 工具
- 该工具需要配置一个 VLM（视觉语言模型）用于截图理解
- Hermes 已经通过 `opencode-go` provider 拥有多模态模型（mimo-v2.5、kimi-k2.6 等）

### 通用架构

```
外部 Agent Tool                     Hermes 模型链路
───────────────                     ──────────────
Agent TARS                          OpenCode CLI
  ↓                                     ↓
OpenAI 兼容 API ──→ opencode.ai/zen/go/v1
  (model, apiKey, baseURL)
                      或者
OpenAI 兼容 API ──→ AIPC:41428 (本地 passthrough)
                    → opencode.ai/zen/go/v1
```

### 核心原则

| 原则 | 说明 |
|------|------|
| **优先用 OpenAI 兼容 API** | 大多数现代 Agent 工具都支持 `--provider openai` 或等价配置，是最通用的集成方式 |
| **选对的多模态模型** | 测试两个关键行为：① 是否接受 image_url 输入 ② 是否在 content 字段输出，而非仅 reasoning_content |
| **API Key 共享** | `OPENCODE_API_KEY` 环境变量是共享凭证。确保目标机器上已设置 |
| **跨机器考虑** | MacBook 可直接调用远程 endpoint；Linux server 可跑本地 passthrough proxy 降低延迟 |

### 常见多模态模型对比

| 模型 | 支持图片输入 | 标准 content 输出 | 适合作 Agent VLM |
|------|:----------:|:---------------:|:--------------:|
| `kimi-k2.6` | ✅ | ✅ content | ✅ **推荐** |
| `mimo-v2.5` | ✅ | ❌ 仅 reasoning_content | ⚠️ 不兼容标准格式 |
| `mimo-v2.5-pro` | ✅ | ❌ 仅 reasoning_content | ⚠️ 不兼容标准格式 |

### 详细记录

见 `references/external-agent-model-config.md` 获取完整的会话记录、配置模板和故障排查。

## 不适用场景（更新版）

以下场景请改用对应技能：

| 场景 | 改用技能 |
|------|---------|
| 项目只是一堆独立脚本，无结构 | `project-clone-analysis` |
| 项目无 `pyproject.toml`/`setup.py`，但仍是独立 Python 工具 | 按情景 B 处理（纯 Skill 仓库），或 `project-clone-analysis` |
| 需要分析/克隆 GitHub 项目结构 | `project-clone-analysis` |
| 需要安装 Node.js 工具 | `nodejs-portable-packaging` |
