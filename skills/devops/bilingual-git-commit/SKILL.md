---
name: bilingual-git-commit
description: 生成详细的双语 Git commit 信息（英文：简体中文），强调原子化拆分、内容详实、初级开发和非技术 PM 都能看懂
version: 2.0.0
---

# 双语 Git Commit 规范（v2）

## 触发条件

当用户要求提交代码、打 commit、push 代码时自动使用本 Skill。所有 commit 信息必须严格遵循以下三条铁律。

---

## 铁律一：原子化——最小颗粒度

**一个 commit 只做一件事。** 合在一起也能工作的修改，拆开打。别人看 commit log 时 commit 数量越多，代表工作量和思考越深入。

拆分标准：
- 同一个功能的不同逻辑步骤 → 分开 commit
- 数据模型改了 + 读取逻辑改了 + 判断逻辑改了 → 每个步骤各一个 commit
- ❸ ❌ 禁止把 3 个逻辑步骤塞成 1 个 commit 图省事
- 每个 commit 仍然是自洽的（不改坏已有功能、不编译失败）

**拆分流程：**
1. `git status` + `git diff --stat` 查看所有变更
2. 按逻辑步骤将变更拆分为多个细粒度 commit
3. 逐个执行 commit，每步只 add 本次 commit 需要的文件/片段

---

## 铁律二：语言格式——双语强制

### (a) 标题格式

```
English title: 简体中文标题
```

- 英文在前，`：`（全角冒号）或 `: `（半角冒号+空格）分隔，再接简体中文
- 中文版本不是翻译，而是在英文基础上用中文解释这件改动的核心
- 英文用祈使句开头（Add / Fix / Refactor / Remove / Extract / Wire / ...）

示例：
```
Add FEISHU_REQUIRE_MENTION env var to Feishu adapter settings: 在飞书适配器设置中加入 FEISHU_REQUIRE_MENTION 环境变量字段
```

### (b) 正文格式

```
English paragraph 1.  Explain the motivation — why this change is needed.
English paragraph 2.  Describe what exactly changed and how it works.
English paragraph 3.  Mention affected files, env vars, config, and scope.

简体中文段落 1。解释动机——为什么需要这个改动。
简体中文段落 2。描述改动内容和实现方式。
简体中文段落 3。说明影响范围、相关配置和环境变量。
```

- 先全部英文段落，空一行，再全部简体中文段落
- 中文版本是英文的**完整翻译**，不是摘要，不能省略
- 英文和中文不用逐段对应，但信息量必须一致

---

## 铁律三：内容详细——初级开发和非技术 PM 都能看懂

commit 信息要包含以下五要素：

| 要素 | 说明 | 示例 |
|------|------|------|
| 动机（Why） | 为什么有这个改动，解决了什么问题 | "之前 @mention 是硬编码的，群消息没有 @ 机器人就不会处理" |
| 改动（What） | 改了什么文件、什么函数 | "在 `_should_accept_group_message` 中加入 `self._require_mention` 判断" |
| 方式（How） | 怎么实现的 | "读取 FEISHU_REQUIRE_MENTION 环境变量，为 false 时跳过 @ 检查" |
| 范围（Scope） | 影响哪些功能、哪些人 | "影响飞书群聊的消息准入逻辑，DM 不受影响" |
| 配置（Config） | 新增的环境变量/配置项 | "新增环境变量 FEISHU_REQUIRE_MENTION（默认 true）" |

❌ 禁止的写法：
- `fix bug`、`update code`、`minor changes`
- `修复了一个问题`（什么问题？）
- 只说"改了什么"不说"为什么改"

---

## 操作流程

### 单文件的部分变更（staging 指定区块）

```bash
# 对 feishu.py 只 add 前几处改动
git add -p gateway/platforms/feishu.py
# 按 y/n 选择每个 hunk，只 stage 这次 commit 需要的部分
git commit -m "..."
```

### 多行 commit 正文（推荐复杂 commit）

```bash
# 用 write_file 写入临时文件，避免 heredoc 超时
write_file /tmp/commit_msg_N.txt  # 写入完整双语信息
git add <files>
git commit -F /tmp/commit_msg_N.txt
```

### 单行 commit（纯标题）

```bash
git add <files>
git commit -m "English title: 简体中文标题"
```

---

## 常见坑

### 坑1：`git commit -m` 多行信息超时

❌ 用 `git commit -m "$(cat <<'EOF' ...)"` → Hermes 终端会卡死。
✅ 先用 `write_file` 写 `/tmp/commit_msg_N.txt`，再用 `git commit -F`。

### 坑2：漏掉父仓库的未提交文件

❌ 只关注子目录，漏了兄弟目录的改动。
✅ 每次提交前从仓库根目录 `git status --short`，扫一遍 `M` 和 `??` 标记。

### 坑3：子仓库（submodule）提交流程

先提交子仓库本身 commit，再回到父仓库提交指针更新。详见 v1 版本。

### 坑4：`git add -p` 交互式 staging 在终端中不可靠

❌ `yes y | git add -p file` 或 `printf 'y\ny\nn\n' | git add -p` → 
   Hermes 终端可能阻塞，shell 管道和交互式 `git add -p` 之间同步不稳定。

✅ 用 `execute_code`（Python subprocess）执行交互式 staging：

```python
import subprocess, os
os.chdir("/path/to/repo")
proc = subprocess.Popen(
    ["git", "add", "-p", "path/to/file"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
)
# y=accept, n=skip, 按 hunk 顺序排列
stdout, stderr = proc.communicate(input="y\ny\nn\n", timeout=30)
# 用 git diff --cached 验证 staging 结果
result = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True)
```

此方法精准可靠，能逐 hunk 选择要 stage 的改动。
