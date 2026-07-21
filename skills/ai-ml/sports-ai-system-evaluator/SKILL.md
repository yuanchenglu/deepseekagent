---
name: sports-ai-system-evaluator
description: |
  Evaluate open-source sports training/AI systems against specific architectural requirements.
  Conducts systematic GitHub searches, analyzes project capabilities against a 3-tier architecture model
  (data collection → processing → display), identifies gaps, and provides implementation recommendations.
  
  Trigger phrases: "找一下有没有", "GitHub上有没有", "搜索开源项目", "调研一下", 
  "有没有类似的系统", "评估一下", "对比一下", "market research", "find similar projects",
  "evaluate sports AI", "basketball training system", "motion capture comparison"
tags:
  - research
  - sports-ai
  - evaluation
  - github-search
  - architecture-analysis
  - market-research
---

# Sports AI System Evaluator

## Overview

Systematic evaluation methodology for finding and assessing open-source sports training/AI systems against specific architectural requirements. Particularly useful when looking for projects with:
- Multi-tier architecture (mobile app + backend + display)
- Adaptive/self-learning capabilities
- Real-time or near-real-time processing
- Specific domain focus (basketball, fitness, etc.)

## 3-Tier Architecture Model

When evaluating sports training systems, assess against this standard architecture:

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 1: Data Collection (采集端)                          │
│  • Mobile App (iOS/Android)                                 │
│  • Camera/video recording                                    │
│  • Sensor integration (IMU, wearables)                      │
│  • Local preprocessing options                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  TIER 2: Processing (处理端)                                │
│  • Pose estimation (MediaPipe, OpenPose, etc.)              │
│  • Action recognition/classification                         │
│  • ADAPTIVE LEARNING (self-evolving models)                 │
│  • Standard action comparison                                │
│  • Can run: Cloud / Local / Edge (mobile)                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  TIER 3: Display (展示端)                                    │
│  • Mobile App (feedback visualization)                       │
│  • Web Dashboard (coaches/trainers)                        │
│  • Desktop Client (detailed analysis)                       │
│  • Real-time feedback vs post-analysis                      │
└─────────────────────────────────────────────────────────────┘
```

## Evaluation Methodology

### Step 1: Multi-Keyword GitHub Search

Use parallel searches with different keyword combinations to maximize coverage:

**Primary Keywords** (must include):
- `{sport} pose estimation` (e.g., basketball pose estimation)
- `{sport} action recognition`
- `{sport} training AI`
- `{sport} shot analysis`

**Secondary Keywords** (mix and match):
- `machine learning`, `deep learning`, `computer vision`
- `real-time`, `mobile`, `app`
- `openpose`, `mediapipe`, `mmpose`
- `analysis`, `feedback`, `coach`

**Search Pattern**:
```
https://github.com/search?q={keywords}&type=repositories&sort=stars&order=desc
```

### Step 2: Project Scoring Matrix

Score each project on a 0-10 scale across dimensions:

| Dimension | Weight | Criteria |
|-----------|--------|----------|
| **Architecture Match** | 30% | Has all 3 tiers? Mobile support? |
| **Adaptive Learning** | 25% | Self-evolving models? Online learning? |
| **Code Quality** | 15% | Stars, forks, documentation, tests |
| **Domain Fit** | 15% | Specific to target sport? |
| **Activity** | 10% | Recent commits, issues resolved |
| **Extensibility** | 5% | Clean APIs, modular design |

### Step 3: Gap Analysis

For top candidates, identify what's missing:

```
Project: {name}
✅ Has: [list existing capabilities]
❌ Missing: [list gaps vs requirements]
🔧 Can Add: [estimate effort to add missing pieces]
```

### Step 4: Implementation Recommendation

Provide actionable next steps:

**Option A: Extend Existing**
- Best when: Top project scores 7+ and missing pieces are addable
- Effort: Medium (3-6 months)
- Risk: Low

**Option B: Build from Scratch**
- Best when: No project scores 5+ or architecture fundamentally different
- Effort: High (6-12 months)
- Risk: Medium

**Option C: Hybrid Approach**
- Best when: Multiple projects cover different pieces
- Effort: Medium-High (4-8 months)
- Risk: Medium

## ⚠️ Critical Workflow Note

### When User Specifies Search Scope, Obey Strictly

**Pitfall (learned from user correction):** If user explicitly says "search on GitHub", only use GitHub. Do NOT expand to other sources (Baidu, Zhihu, news sites, etc.) on your own.

**Correct approach:**
- User says "搜GitHub" → Use GitHub API/search only
- User says "搜官网" → Prioritize official website
- User says "不要搜其他无用信息" → Strictly limit search scope
- User provides specific source (e.g., Feishu doc link) → Try that source first

**Wrong approach (has been corrected by user):**
- ❌ User says "GitHub上搜", I search elsewhere
- ❌ User provides Feishu link, I search elsewhere anyway

### Typical Gaps in Sports AI Projects

1. **No Adaptive Learning**: 95% of projects use fixed pre-trained models
2. **Missing Mobile App**: Many are backend-only or desktop-only
3. **No Standard Action Evolution**: Static templates, no learning from data
4. **Single-tier Architecture**: Often just pose estimation, no complete system
5. **No Real-time Feedback**: Batch processing only

### Red Flags

- Last commit > 1 year ago
- No documentation beyond README
- Hardcoded paths and parameters
- No tests or CI/CD
- Monolithic codebase (not modular)

## Example Output Format

```markdown
## Top 10 Projects (Ranked by Match Score)

### 🥇 Rank 1: {project-name}
**Match Score**: X/10

| Tier | Support | Notes |
|------|---------|-------|
| T1 Collection | ✅/❌ | {details} |
| T2 Processing | ✅/❌ | {details} |
| T3 Display | ✅/❌ | {details} |

**Key Capabilities**:
- {capability 1}
- {capability 2}

**Critical Gaps**:
- ❌ {missing 1}
- ❌ {missing 2}

**Recommendation**: {Extend/Build/Hybrid}
```

## Technical Architecture Patterns

### Pattern 1: Cloud-First (Heavy Backend)
```
Mobile → Upload Video → Cloud GPU Processing → Results API → Display
```
- Pros: Powerful models, easy updates
- Cons: Latency, bandwidth costs, privacy concerns

### Pattern 2: Edge-First (Mobile ML)
```
Mobile → On-device Inference → Local Feedback → Optional Cloud Sync
```
- Pros: Low latency, works offline, privacy
- Cons: Limited model size, battery drain

### Pattern 3: Hybrid (Recommended)
```
Mobile → Lightweight Local Check → Cloud for Complex Analysis → Sync Results
```
- Pros: Balance of speed and power
- Cons: More complex architecture

## Implementation Roadmap Template

```
Phase 1 (MVP): Basic pose estimation + simple feedback
Phase 2: Standard action library + comparison
Phase 3: User data collection + pattern recognition
Phase 4: Adaptive learning engine + personalization
Phase 5: Real-time feedback + advanced analytics
```

## Related Skills

- `wechat-wiki-archiver`: For archiving research findings
- `khazix-hv-analysis`: For deep competitive analysis
- `github-repo-management`: For forking and extending projects

---

*Created based on evaluation of FreeMoCap and basketball training system requirements*
