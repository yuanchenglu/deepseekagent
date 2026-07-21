---
name: product-marketing-content
description: Create high-converting product marketing content for WeChat articles and landing pages. Focuses on scenario-based storytelling, visual comparison charts, and purchase decision frameworks.
triggers:
  - User wants to create product marketing content
  - User needs to write sales copy for a product
  - User asks for scenario-based product descriptions
  - User needs version comparison charts
  - User wants landing page content
---

# Product Marketing Content Creator

## Overview

Create compelling product marketing content that drives purchase decisions. This skill focuses on user-centric storytelling rather than feature lists, with emphasis on scenarios, pain points, and clear value propositions.

## Key Principles

### 1. Scenario-Based Opening

**Never start with features. Start with a relatable scenario.**

```
❌ WRONG: "U-Color AI is a U盘 with built-in AI tools..."
✅ RIGHT: "上周三凌晨1点，我在酒店赶一份明天要用的方案。电脑是酒店的，里面什么都没有。但我插上一个U盘，30分钟后..."
```

**Structure**:
1. Real story/time/place (creates credibility)
2. The problem/pain point
3. The solution in action
4. The result

### 2. Visual Version Comparison

**Critical for purchase decisions. Must be visual, not text-only.**

**Requirements**:
- Large vertical image (900x2000+ px)
- Color-coded versions (e.g., red/yellow/blue/purple)
- Clear checkmarks (✓) vs dashes (—)
- "Recommended" badge on best value option
- Bottom section explaining WHY it's recommended

**Implementation**:
```python
# Use PIL to create comparison chart
# Each version gets distinct color theme
# Features listed vertically, versions horizontally
# Include price prominently
# Add recommendation rationale at bottom
```

### 3. User-Centric Version Descriptions

**Each version must answer**:
- **Who is this for?** (specific persona)
- **What do you get?** (concrete deliverables)
- **Why choose this over others?** (value proposition)
- **Limitations** (if any, be honest)

**Template**:
```
[Version Name] [Price]

适合谁：[Specific persona]

你能得到：
- [Concrete benefit 1]
- [Concrete benefit 2]
- [Concrete benefit 3]

局限：[Honest limitation, if any]

为什么选这个：[Value proposition]
```

### 4. Feature Explanations (作用-场景-提升)

**Every feature needs three parts**:

1. **作用 (Role)**: What does it do?
2. **场景 (Scenario)**: When would you use it?
3. **提升 (Improvement)**: How much better/faster?

**Template**:
```
[Feature Name] - [Role]

场景：[Specific usage scenario]
提升：[Quantified improvement]
```

### 5. Address Objections Proactively

**Common concerns to address**:
- Data security/privacy
- Learning curve
- Compatibility
- Value for money

**Format**: State concern → Explain solution → Provide proof

## Content Structure

### WeChat Article Structure

```
1. Scenario Opening (真实故事)
   - Time, place, situation
   - Problem/pain
   - Solution preview

2. "When You Need It" Section
   - 4 specific scenarios
   - Each: Pain → Solution

3. Version Comparison
   - Visual chart (image)
   - Detailed breakdown per version
   - Clear recommendation

4. Feature Deep Dive
   - 作用-场景-提升 for each key feature
   - Real examples, not abstract descriptions

5. Objection Handling
   - Security
   - Privacy
   - Value

6. CTA
   - Summary of value
   - Purchase link/QR code
```

### Landing Page Structure

```
1. Hero Section
   - Product name + tagline
   - Scenario story (condensed)

2. Scenario Cards (4 cards)
   - Pain point
   - Solution

3. Version Comparison
   - Visual chart
   - Detailed cards

4. Feature Details
   - 作用-场景-提升 structure

5. Trust/Security
   - Objection handling

6. CTA
   - Final value prop
   - Purchase button
```

## Implementation Guide

### Creating Visual Comparison Charts

```python
from PIL import Image, ImageDraw

# Canvas size
width = 900
total_height = 2400

# Color scheme per version
version_colors = {
    "manager": (254, 242, 242),      # Light red
    "director": (254, 252, 232),     # Light yellow  
    "ceo": (239, 246, 255),          # Light blue (recommended)
    "chairman": (250, 245, 255)      # Light purple
}

# Structure
# - Header with title
# - Version header row (colored backgrounds)
# - Feature rows (alternating backgrounds)
# - Recommendation section at bottom
```

### Writing Scenario Content

**Checklist**:
- [ ] Is the scenario specific? (time, place, situation)
- [ ] Is the pain point relatable?
- [ ] Is the solution clear?
- [ ] Is the result quantified?

**Example**:
```
❌ "You can use this for content creation"
✅ "周三凌晨1点，我在酒店赶明天要用的方案。电脑是酒店的，里面什么都没有。但我插上一个U盘，30分钟后，一份带数据分析、排版精美的PPT就搞定了。"
```

### Version Selection Guidance

**Help users choose by asking**:
1. What's your primary use case?
2. Do you need Mac support?
3. Do you need the AI OS?
4. What's your budget?

**Then recommend**:
- "Based on your needs, I recommend CEO版 because..."
- Always explain the value calculation

## Common Mistakes to Avoid

1. **Feature dumping**: Listing features without context
2. **No visual comparison**: Expecting users to read text tables
3. **Missing "why"**: Not explaining why each version exists
4. **Ignoring objections**: Not addressing security/concerns
5. **Weak CTA**: Not pushing for the sale

## Output Files & Visual Design (consolidated from v2)

### Output Files
- `*_wechat.md`: WeChat article with HTML-rich formatting
- `*_comparison.png`: Feature comparison visualization (900x2400px)
- `*_landing.html`: Landing page with same content structure

### Visual Design Requirements (from product-marketing-content-v2)
- Comparison table: 900x2400px vertical, color-coded tiers
- Recommended tier: 3px border + badge
- WeChat styling: section dividers with gradient underlines, feature cards with left accent borders
- Clean grid layout, easy to scan

## Version Comparison Guide (consolidated from product-marketing-comparison-guide)

### Workflow for Version Comparisons
1. Identify all product versions/tiers with prices
2. Map features to each version
3. Understand target user segments for each tier
4. Create visual table with ✓/✗
5. Write user-centric explanations for each feature (what it is, why you need it, daily work improvement, specific scenarios)

### Purchase Decision Framework
- "Why buy this product?" (overall value)
- "Why this version vs another?" (version selection guide)
- ROI/time savings calculations if applicable
- Real user scenarios/stories

### Deliverables for Comparison Content
- Complete version: Feishu cloud doc with full details
- Landing page: HTML with responsive comparison cards
- Social article: Mobile-optimized shorter version

- ✅ Opens with relatable scenario
- ✅ Visual comparison chart included
- ✅ Each version has "who it's for"
- ✅ Each feature has "作用-场景-提升"
- ✅ Objections addressed proactively
- ✅ Clear recommendation made
- ✅ Strong CTA with purchase path

## Examples

### Good Scenario Opening
```
上周三凌晨1点，我在酒店赶一份明天要用的方案。电脑是酒店的，里面什么都没有。但我插上一个U盘，30分钟后，一份带数据分析、排版精美的PPT就搞定了。

这个U盘里装着的，是我这8个月来每天都在用的U-Color AI。
```

### Good Version Description
```
CEO版 1888元 ⭐ 推荐

适合谁：真正把AI当生产力工具的人，创业者、自媒体人、技术负责人

你能得到：
- 128G大容量，存资料、存项目、存知识库
- 完整虚拟研发团队（非限时，永久拥有）
- Color AIOS完整版
- 6个月知识星球（价值750元）
- 1次付费提问（价值288元）

为什么推荐：光是赠送的知识星球+提问就值1038元，相当于U盘只要850元。
```

### Good Feature Explanation
```
👥 虚拟软件研发团队 - OpenCode

作用：10个虚拟员工组成的完整研发团队：产品经理、架构师、前端、后端、测试、运维。

场景：你说"我想做一个记账小程序"，团队自动分工，从需求文档到上线代码，全流程交付。

提升：不会代码也能做产品。我已经用它开发了15个软件。
```
