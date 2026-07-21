---
name: article-synthesis-workflow
title: Article Synthesis & Integration Workflow
description: Synthesize multiple articles into a comprehensive guide, creating original content that integrates insights from multiple sources
version: 1.0
triggers:
  - User provides multiple articles or sources to synthesize
  - User asks to integrate or combine multiple pieces of content
  - User requests a comprehensive guide based on multiple references
---

# Article Synthesis & Integration Workflow

## Trigger Conditions
- User provides multiple articles, documents, or sources to synthesize
- User asks to "integrate", "combine", "synthesize" multiple pieces of content
- User requests a comprehensive guide based on multiple references
- User wants to create original content that builds upon existing sources

## Key Differences from Article Extraction

| Aspect | Article Extraction | Article Synthesis |
|--------|-------------------|-------------------|
| Input | Single URL | Multiple sources (text, URLs, files) |
| Output | Preserved original | Original integrated content |
| Goal | Archive existing | Create new comprehensive guide |
| Content | Unchanged | Transformed and expanded |

## Workflow Steps

### Phase 1: Source Analysis
1. **Read and analyze all sources** - Extract key insights, frameworks, approaches from each
2. **Identify complementary elements** - What does each source contribute uniquely?
3. **Find gaps and conflicts** - What needs reconciliation? What needs expansion?
4. **Determine target audience** - Who is the synthesized content for?

### Phase 2: Framework Design
1. **Design unified structure** - Create a coherent framework that integrates all sources
2. **Define the synthesis angle** - What's the unique value of the combined perspective?
3. **Map content flow** - How do concepts from different sources connect?
4. **Identify expansion points** - Where should original analysis be added?

### Phase 3: Content Creation
1. **Write integrated content** - Original writing that weaves together insights
2. **Add original analysis** - New frameworks, diagrams, examples not in sources
3. **Create practical applications** - How-to guides, checklists, templates
4. **Maintain attribution** - Credit sources while creating original work

### Phase 4: Three-Stage Optimization (MANDATORY)
1. **Title Optimization**: Create engaging title that captures the synthesis value
2. **Cover Generation**: Generate 900x500 PNG with tech-focused minimalist style
   - Deep navy backgrounds, electric cyan accents
   - NO large color blocks or "blackboard poster" style
   - NO text on image
   - Asymmetric composition with 40%+ negative space
3. **Content Calibration**: Optimize readability, structure, and flow

### Phase 5: Multi-Format Generation
Generate three formats:
- `article_optimized.md` - Full comprehensive guide (Markdown)
- `feishu_archive.md` - Feishu knowledge base summary format
- `wechat_format.txt` - WeChat official account format (shorter)

### Phase 6: Storage & Archiving
1. Create folder: `~/Documents/article/{article_title}/`
2. Place ALL files inside:
   - `article_optimized.md`
   - `cover_900x500.png` (or `cover_note.txt` if generation fails)
   - `feishu_archive.md`
   - `wechat_format.txt`
3. Upload to Feishu Wiki with appropriate classification
4. Classify according to strict 6-category system:
   - 袁老师自用经验
   - AI+自媒体创作
   - AI+教育
   - 网上干货整理 (Claude Code, OpenClaw, Hermes, OpenCode, Skill subcategories)
   - 了解AI底层技术
   - 其他

## Synthesis Patterns

### Pattern 1: Complementary Integration
When sources cover different aspects of the same topic:
- Source A: Conceptual framework
- Source B: Practical implementation
- Source C: Case studies
- **Synthesis**: Unified guide with theory → practice → examples

### Pattern 2: Conflict Resolution
When sources have conflicting approaches:
- Identify the context where each applies
- Create decision framework for choosing
- Add original analysis of trade-offs
- **Synthesis**: Comparative guide with decision tree

### Pattern 3: Expansion & Specialization
When sources are general and user needs specific application:
- Take general frameworks from sources
- Add domain-specific adaptations
- Create specialized examples
- **Synthesis**: Domain-specific implementation guide

### Pattern 4: Multi-Tool Integration
When sources describe tools that work together:
- Map tool interactions and dependencies
- Design integrated workflow
- Create unified command reference
- **Synthesis**: Multi-tool orchestration guide

## Quality Standards

### Original Content Threshold
- At least 30% original analysis, examples, or frameworks
- New insights not present in any single source
- Practical applications and templates
- Visual diagrams or structured frameworks

### Attribution Balance
- Credit sources for their specific contributions
- Don't over-quote (max 20% direct content)
- Transform ideas into original expression
- Add value through synthesis and expansion

### Structural Quality
- Clear progression from concept to implementation
- Consistent terminology and notation
- Actionable takeaways at each section
- Comprehensive troubleshooting

## Cover Image Style Guide
- Tech-focused, minimalist, sophisticated
- NO rainbow colors or neon explosions
- Muted professional palette: deep navy, electric cyan, soft purple
- Asymmetric balance, generous negative space
- Visual metaphor as "hook"
- NO text on image
- Thin lines, subtle gradients, geometric shapes
- Professional, innovative, trustworthy mood
- 16:9 or 2.35:1 cinematic widescreen

## User Role
- DISCOVERER perspective ("I discovered" not "I developed")
- Pain-point-first structure
- NO title-gimmick style
- 120-character digest for CTR

## Pitfalls
- DO NOT simply concatenate sources
- DO NOT lose original insights in over-summarization
- DO NOT create new categories without explicit permission
- DO NOT store cover images in separate directory
- DO NOT include original source links in drafts
- ALWAYS add original analysis and frameworks
- ALWAYS maintain practical applicability
- ALWAYS verify synthesized information is coherent

## Example Outputs

### Example 1: Multi-Agent Development Framework
**Sources**: 
- Article about oh-my-openagent (multi-agent orchestration)
- Article about superpowers (TDD and code review)
- Article about OpenSpec (specification-driven development)

**Synthesis**: 
Three-layer virtual team architecture (Strategic/Tactical/Execution) + 
Six-phase workflow integrating all three tools + 
Extended Wave model for complex projects +
Original checklists and decision frameworks

**Result**: Comprehensive guide for AI agent team management in OS-level projects

## Verification Checklist

Before completing synthesis:
- [ ] All sources analyzed and key insights extracted
- [ ] Original framework or structure created
- [ ] At least 30% original content added
- [ ] Practical applications included
- [ ] Multi-format outputs generated
- [ ] Properly classified in Feishu Wiki
- [ ] Cover image generated or fallback documented