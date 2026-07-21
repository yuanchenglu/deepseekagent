---
name: modular-ai-analysis-document
description: Create modular business analysis documents with AI prompts for multi-model validation. Supports critical logic analysis, first-person perspective writing, and structured critique format.
version: 1.0.0
trigger: When user needs to create business analysis documents with AI prompts for validation, critical logic analysis, or multi-model review
---

# Modular AI Analysis Document Creator

## Purpose
Create structured business analysis documents that can be fed to multiple AI models for validation and critique. Documents are split into modular sections with specific AI prompts for each analysis dimension.

## When to Use
- Business model analysis requiring critical evaluation
- Logic hole identification in proposals
- Multi-model validation (GPT 5.5, Gemini 3.1 Pro, Claude Code 4.7, etc.)
- First-person perspective business writing
- Structured critique with step-by-step analysis

## Key Features
1. **Modular Structure**: Split content into independent modules to avoid context overflow
2. **AI Prompts per Module**: Each module has tailored prompts for specific analysis angles
3. **Critical Analysis Format**: "漏洞X：描述→分析→结论" (Hole X: Description→Analysis→Conclusion)
4. **First-Person Perspective**: Write as if the user authored it directly
5. **Multi-Model Ready**: Optimized for GPT 5.5, Gemini 3.1 Pro, Claude Code 4.7, Kimi 3.0, DeepSeek V4, Qwen 3.6

## Workflow

### Step 1: Define Analysis Modules
Split the analysis into logical modules:
- Module 1: Original Proposal/Scheme
- Module 2: Logic Hole Analysis (Area A)
- Module 3: Logic Hole Analysis (Area B)
- Module 4: AI Prompts Collection
- Module 5: Summary & Index

### Step 2: Create Module Documents

**For each module, create:**
```markdown
# AI Analysis Prompt - [Module Name]

> **Instructions**: 
> Use this document for AI analysis. Each module has specific prompts.
> Current time: [YYYY年M月]
> Latest models: GPT 5.5, Gemini 3.1 Pro, Claude Code 4.7, Kimi 3.0, DeepSeek V4, Qwen 3.6

---

## [AI Prompt Section]

```
[Role definition with specific expertise]
Current time: [Date]
Latest knowledge: [2026 market data, industry benchmarks]

Please analyze [specific aspect]:
- Dimension 1
- Dimension 2
- Dimension 3

Use format: "漏洞X：描述→分析→结论"
```

### [Content Section]
[Actual content for analysis]
```

### Step 3: Critical Analysis Format

**Standard Logic Hole Format**:
```markdown
**漏洞[N]: [标题]**

**描述**: [What is the assumption]

**分析**: 
- Evidence 1
- Evidence 2
- Calculation/data

**结论**: [Does not hold / Market capacity insufficient / etc.]
```

### Step 4: First-Person Perspective

**Write as if user authored directly**:
- Use "我的判断" (My judgment)
- Use "我的方案" (My proposal)
- Use "我的洞察" (My insight)
- NOT "我们讨论得出" (We discussed and concluded)
- NOT "AI分析显示" (AI analysis shows)

### Step 5: Save to Proper Location

**Save analysis documents to**: `~/Code/[project]/analysis/`

**Structure**:
```
~/Code/[project]/analysis/
├── README.md                    # Document index
├── 01_original_proposal.md      # Original scheme
├── 02_[area]_logic_check.md     # Logic analysis area 1
├── 03_[area]_logic_check.md     # Logic analysis area 2
├── 04_ai_prompts_collection.md  # All AI prompts
└── ...
```

### Step 6: Upload to Feishu (Optional)

Use `npx @larksuite/cli` to upload:
```bash
cat document.md | npx @larksuite/cli docs +update --doc "[url]" --markdown - --mode overwrite
```

## Critical Analysis Dimensions

### Dimension 1: Market Capacity
- Calculate: [Number of creators] × [Users per creator] vs [Total users]
- Check: Is the market big enough?
- Format: Table with assumptions vs reality

### Dimension 2: Cost-Benefit
- Calculate: Development cost + Maintenance cost + Team cost
- Compare: Revenue projections vs costs
- Format: Financial model table

### Dimension 3: Matthew Effect
- Analyze: Will resources concentrate at the top?
- Check: Can 100 people all survive, or only 10-20?
- Format: Distribution analysis

### Dimension 4: Role Division
- Analyze: Are strict role divisions realistic?
- Check: Do full-stack individuals exist?
- Format: Capability overlap matrix

### Dimension 5: Necessity
- Analyze: Is this role/component really needed?
- Compare: Simpler alternatives
- Format: With vs without comparison

## Example AI Prompts

### Prompt for Business Model Analysis
```
你是一位资深的商业模式分析师，拥有20年互联网产品经验。

当前时间：2026年5月
最新AI模型参考：GPT 5.5、Gemini 3.1 Pro、Claude Code 4.7、Kimi 3.0、DeepSeek V4、Qwen 3.6

请分析以下方案：
- 保持客观中立，既不完全赞同也不完全否定
- 识别创新点和潜在价值
- 找出逻辑漏洞或执行难点
- 评估可行性和市场规模
- 给出改进建议

分析维度：
1. 产品定位是否清晰
2. 商业模式是否可持续
3. 用户价值主张是否成立
4. 竞争壁垒是否足够
5. 执行路径是否可行

请用结构化方式输出。
```

### Prompt for Logic Hole Identification
```
你是一位资深的商业逻辑检验专家。

当前时间：2026年5月
最新知识：
- [Relevant market 2026 data]
- [Industry benchmarks]

请进行严格的逻辑检验：
- 找出所有假设与现实的差距
- 识别数学计算错误
- 分析市场容量、用户行为、成本结构
- 指出执行难点和风险
- 用数据说话

检验重点：
1. [Specific area 1]
2. [Specific area 2]
3. [Specific area 3]

请用"漏洞X：描述→分析→结论"格式输出。
```

## Common Patterns

### Pattern 1: Flywheel Analysis
```
[Current flywheel]
    ↓
[Step 1: Check assumption]
    ↓
[Step 2: Check reality]
    ↓
[Step 3: Identify break point]
    ↓
[Conclusion: Why it won't work]
```

### Pattern 2: Comparison Table
```markdown
| 假设 | 漏洞 | 更可能的现实 |
|------|------|------------|
| 100人存活 | 马太效应 | 10-20人存活 |
| 900人垂直 | 市场容量 | 100-200人 |
```

### Pattern 3: Simpler Alternative
```markdown
Your scheme (complex):
A → B → C → D → E

Simpler scheme:
A → B' → D

Question: Is C and E necessary?
```

## Quality Checklist

- [ ] Content is in first-person perspective
- [ ] Each module has specific AI prompt
- [ ] Logic holes use standard format
- [ ] Data/calculations support claims
- [ ] Simpler alternatives proposed
- [ ] Model references are current (2026)
- [ ] Documents saved to ~/Code/[project]/analysis/
- [ ] README.md created as index
- [ ] Feishu links verified (if uploaded)

## Example Output

See `~/Code/lazycat/analysis/` for complete example:
- 01_original_proposal.md
- 02_trainer_ecology_logic_check.md
- 03_scene_sales_logic_check.md
- 04_ai_prompts_collection.md
- README.md

## Pitfalls to Avoid

1. **Don't use outdated model references**: Always update to latest (GPT 5.5 not GPT 4)
2. **Don't mix discussion with proposal**: Keep first-person perspective clean
3. **Don't skip the simpler alternative**: Always compare with simpler approach
4. **Don't forget data verification**: Every claim needs data support
5. **Don't create overly long modules**: Keep under 500 lines for context efficiency

## Related Skills
- `feishu-wiki-document-creator`: For uploading to Feishu
- `zhuyu-writer`: For CEO-style business writing
- `business-model-critique`: For structured business critique