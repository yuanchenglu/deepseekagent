# 完整记忆重构执行示例（2026-07-14）

## 背景
本机 Hermes 的 MEMORY 满了：9,721/10,000 chars（97%）。用户反映近期幻觉率飙升，
要求对记忆体系做分类和整合。

## 目标
- MEMORY: 9,721 chars → 538 chars（8条，每条 ≤200 chars）
- SOUL.md: 从 513B 官方模板 → 4,264B 自定义灵魂定义
- memories/*.md: 不存在 → 3 个参考文档
- USER.md: 从 AIPC 吸了 3 个条目（代码注释、决策原则、沟通定位）

## 执行步骤

### Step 1: 确定分类方案
先问用户 WHY（为什么做这件事？遇到了什么痛？），再问 WHAT（最终目标状态是什么？）。
不要跳过问题定义直接画架构。

### Step 2: 写 SOUL.md
```markdown
# 数字分身灵魂定义
## 一、我的角色
## 二、三层认知框架（L1/L2/L3）
## 三、方法论铁律 + Token 纪律
## 四、沟通方法论 + 先内后外探索模式
## 五、核心洞察（Scene ≠ Data）
## 六、版本信息
```
文件位置：~/.hermes/SOUL.md（自动加载，无需配置）

### Step 3: 精简 MEMORY
移除的条目类别：
- ✅ 已移入 SOUL.md 的：方法论铁律、Token 纪律、三层认知框架、沟通方法论
- ✅ 已移入 memories/*.md 的：Cloudflare 凭证（引用 $VAR_NAME）、机器配置、用户纠正史
- ✅ 已移入 skill 的：方舟众测规则体系（fangzhou-testing-guide 已有）、方舟整合流程
- ✅ 删除的过时条目：DeepAgent 项目状态、旧 session 管理规则（非通用）

留下的 8 条（示例）：
```
【生产流程】PRD→源码审计→OpenCode 审查设计→审查计划(9.5+)→OMO执行→截图验收→签字交付
【铁律】禁止写代码❌ 指挥 OMO/OpenCode 完成。禁止造轮子❌ 先搜开源库。端口永不篡改
【方舟导航】fangzhouzhongce/ 下是全部评测材料 ...
...（共 8 条，538 chars）
```

### Step 4: 创建 memories/*.md
文件列表：
- cloudflare-ref.md（Zone IDs + 认证方式引用 $VAR_NAME）
- machine-configs.md（AIPC/MacBook/Lenovo 各机配置）
- feedback-lessons.md（用户纠正史，逐条记录）

### Step 5: 更新 USER.md
从 AIPC 吸收：
- 「代码必须写简体中文注释」
- 「能决策的，就你决策」
- 「我是 PM/非技术人员，解释用大白话」
- 「面试/评估客观不迎合」

## 结果
- MEMORY 占用率: 97% → 5%
- 条目数: ~70 → 8
- SOUL.md: 有自定义内容 ✅
- 参考文档: 有 3 个 ✅
- AIPC 差异吸收: 4 条 ✅

## 注意事项
- memory 工具的操作是 all-or-nothing batch — 一个 remove 失败整个 batch 回滚
- SOUL.md 由 Hermes 自动加载（load_soul_md），不需要改任何配置
- 文件级 MEMORY.md（~/.hermes/memories/MEMORY.md）和 memory 工具的内容应保持一致
