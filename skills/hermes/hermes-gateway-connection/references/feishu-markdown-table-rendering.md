# Feishu Markdown 表格渲染修复

## 问题

用户在飞书客户端收到的是 Markdown 原始语法（`| col1 | col2 |\n|---|---|`），
而非渲染后的格式。包含表格的消息还会连带丢失其他 Markdown 格式（粗体、标题等）。

## 根因

`plugins/platforms/feishu/adapter.py` 中的 `_build_outbound_payload()` 方法：

```python
# 原始代码（保持至今的官方 main 分支）
if _MARKDOWN_TABLE_RE.search(content):
    text_payload = {"text": content}
    return "text", json.dumps(text_payload, ensure_ascii=False)
if _MARKDOWN_HINT_RE.search(content):
    return "post", _build_markdown_post_payload(content)
```

检测到 Markdown 表格时，**整个消息**被降级为 `msg_type=text`，
Feishu 的 text 类型不渲染 Markdown，用户看到原始管道符和分隔线。

## 官方仓库状态（2026-07-10 调查）

- Bug 存在于 `main` 分支，未修复
- **5+ 个 Issue**：`#9549`（2026-04 最早提出）、`#52786`、`#58269`、`#61643` 等
- **5 个开放 PR**：`#57566`、`#58019`、`#58391`、`#61377`、`#61647`，均为删除 guard 的修复，均**未合并**
- 典型的开源项目积压问题：多人独立发现并提交 PR，维护者标记为 duplicated 后无后续跟进

## 关键发现：Feishu 已原生支持 GFM 表格

Issue #58269 提供了决定性证据：

> 原代码注释称「post-type 'md' elements do not render markdown tables」的假设
> **已经过时**。2026 年 7 月实测 live Feishu API 确认：
> - `msg_type=post` + `{"tag": "md", "text": "| A | B |\n|---|---|\n| 1 | 2 |"}` → Feishu 正确渲染表格（有格线、对齐）
> - 飞书官方文档也写明「md 标签支持 CommonMark 0.31 + GFM 语法，包括**表格**」

## 修复方案

### 方案 A（推荐）：直接删除 guard，利用 Feishu 原生渲染

最简单的修复，两行改动：

1. 删除 `_MARKDOWN_TABLE_RE` 的 force-text 分支
2. 把 `|` 表格检测加入 `_MARKDOWN_HINT_RE`，让纯表格消息也能走 `post(md)` 路径

```python
def _build_outbound_payload(self, content: str) -> tuple[str, str]:
    if _MARKDOWN_HINT_RE.search(content):
        return "post", _build_markdown_post_payload(content)
    text_payload = {"text": content}
    return "text", json.dumps(text_payload, ensure_ascii=False)
```

效果：Feishu 客户端原生渲染表格（格线、列对齐、支持宽表格横向滚动）。

### 方案 B（此前用的方案）：清洗表格为可读文本再发 post

当无法确认 Feishu API 版本是否支持 GFM 表格时使用。

新增 `_convert_table_content_to_readable()` 函数：

```python
def _convert_table_content_to_readable(content: str) -> str:
    """将 Markdown 表格语法转换为可读的纯文本。"""
    lines = content.split("\n")
    result: List[str] = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^\|[-|: ]+\|$", stripped):  # 跳过分隔线
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            inner = stripped[1:-1]
            cells = [cell.strip() for cell in inner.split("|")]
            line = " | ".join(cells)
        result.append(line)
    return "\n".join(result)
```

修改 `_build_outbound_payload`：

```python
if _MARKDOWN_TABLE_RE.search(content):
    content = _convert_table_content_to_readable(content)
    if _MARKDOWN_HINT_RE.search(content):
        return "post", _build_markdown_post_payload(content)
    text_payload = {"text": content}
    return "text", json.dumps(text_payload, ensure_ascii=False)
```

效果：表格变为可读文本（用 ` | ` 分隔），其他 Markdown 正常渲染。

## 跨机器部署

三台机器已通过 Tailscale SSH 并行修复（2026-07-10）：

| 机器 | IP | 备注 |
|------|-----|------|
| MacBook Air (本机) | 本机 | pipx + Python 3.13 |
| AIPC | 100.89.88.88 | Deepin Linux, Python 3.12 |
| ThinkPad (HomeServer) | 100.108.145.79 | Linux, Python 3.12 |

```bash
# 查找 adapter.py 路径
ls ~/.local/share/pipx/venvs/hermes-agent/lib/python3.*/site-packages/plugins/platforms/feishu/adapter.py

# 通过 SSH 修改
ssh bluth@<tailscale-ip> '...'

# 重启 Gateway（kill + KeepAlive 自动重启）
ssh bluth@<tailscale-ip> 'kill $(pgrep -f "hermes.*gateway")'
```

## 改动文件

同一文件：`plugins/platforms/feishu/adapter.py`
- 方案 A：删除 `_MARKDOWN_TABLE_RE` 分支 + 修改 `_MARKDOWN_HINT_RE`
- 方案 B：新增 `_convert_table_content_to_readable()` + 修改 `_build_outbound_payload()`
