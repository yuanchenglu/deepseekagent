# 源码验证速查

## 四步法

```
1. 读项目自述文档（README / ARCHITECTURE / AGENTS.md）
   → 了解项目自称做了什么
   命令: read_file(path, limit=200)
   成本: ~3K Token

2. search_files 定位关键实现
   → 用关键字找到具体文件和行号
   命令: search_files(pattern="关键字", target="content", path="源码目录")
   成本: ~0（不读文件内容，只看匹配行）

3. read_file + offset + limit 读片段
   → 只看相关的 50-200 行，不全量读
   命令: read_file(path, offset=行号-20, limit=100)
   成本: ~2K Token/次

4. 输出时标注来源
   → "[来源: src/agents/metis.ts, L35-48]"
   成本: 0
```

## 决策树

| 代码规模 | 做法 |
|---------|------|
| 单文件 < 500 行 | 全读 |
| 中等 500-2000 行 | 读关键部分 50-200 行 |
| 大型 > 2000 行 | 只搜索关键词 + 读匹配片段 |
| 仓库 > 100MB | 不 clone，用 GitHub API 浏览 |

## Clone 策略

```bash
# 公开仓库 → 浅克隆
git clone --depth 1 <url>

# 大型仓库 → 只浏览，不 clone
# 用 GitHub API 或 raw.githubusercontent.com 读单文件

# 本地已有 → 直接用，增量更新
cd ~/Code/<repo> && git pull --depth 1
```

## 反例：本次会话的教训

初版 Plan 架构文档写了"Momus 按 4 标准审查"，源码实际是 3 标准 + APPROVAL BIAS。
初版写了"First Principles 正好相反"，实际是正好匹配。
→ 两个错误都是"没看源码就写结论"造成的。

## 输出格式

```
✅ 已验证: "Momus 核心原则是 APPROVAL BIAS" (src/agents/momus.ts, L45-52)

⚠️ 推断（需标注）: "Atlas Wisdom 在 prompt 中无显式实现 (18KB prompt 中无 Wisdom 分类)"

❌ 错误（已修正）: "Momus 按 4 标准审查" → 实际是 Reference/Executability/Blockers 3 标准
```
