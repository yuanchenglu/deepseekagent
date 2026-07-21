---
name: business-model-critique
description: Critically analyze business models with structured documentation for external AI validation. Supports deep logical reasoning, self-examination, and modular documentation with AI prompts.
trigger: When user asks to analyze a business model, find holes in logic, create structured analysis docs, or prepare documents for external AI review
version: 1.0.0
---

# Business Model Critique & Structured Analysis

## Purpose

Guide users through a rigorous business model analysis that:
1. Examines the original business model and identifies logical flaws
2. Proposes improvements with step-by-step reasoning
3. Critically examines the proposed solution (finding holes in user's own logic)
4. Structures documentation for external AI validation
5. Creates modular documents with specific AI prompts for different analysis angles

## When to Use

- Analyzing startup business models (especially platform/ecosystem plays)
- Examining go-to-market strategies
- Evaluating revenue model assumptions
- Assessing competitive positioning
- Preparing investment/deck materials
- Creating documentation for founder discussions

## Workflow

### Phase 1: Understand the Business Model

**Ask clarifying questions:**
- What is the core value proposition?
- Who are the target users/customers?
- What is the revenue model?
- What is the growth flywheel (if any)?
- What are the key assumptions?

**Document the original model:**
- Preserve ALL details (even seemingly unimportant ones)
- Capture the founder's intent and constraints
- Note any stated "must-haves" (e.g., "must be ToC not ToB")

### Phase 2: Logical Analysis (Step-by-Step)

**For each component of the business model:**

1. **Identify assumptions**
   - What must be true for this to work?
   - What is the evidence for/against?

2. **Mathematical validation**
   - Calculate unit economics
   - Model customer acquisition costs
   - Project lifetime value
   - Assess market sizing

3. **Competitive benchmarking**
   - Compare to successful/failed similar models
   - Identify differentiating factors
   - Assess moats and barriers

4. **Risk identification**
   - What could go wrong?
   - What are the single points of failure?
   - What external dependencies exist?

### Phase 3: Propose Improvements

**Structure the improved model:**
- Keep original intent/constraints
- Address identified flaws
- Provide step-by-step reasoning for each change
- Show how the new flywheel works

### Phase 4: Critical Self-Examination (CRITICAL)

**This is the key differentiator - find holes in the proposed solution:**

Ask the user: *"Now find the holes in my logic. Step-by-step."*

**For the proposed solution, examine:**

| Aspect | Questions to Ask |
|--------|----------------|
| Scale assumptions | Is the assumed user/developer/creator count realistic? |
| Revenue sustainability | Will revenue recur, or is it one-time? |
| Cost underestimation | Are hidden costs (compliance, maintenance, support) accounted for? |
| Market timing | Why now? What's changed? |
| Competitive response | What stops incumbents from copying? |
| User behavior | Do users actually want this? Evidence? |
| Platform risk | Dependencies on other platforms? |
| Incentive alignment | Are all parties incentivized to participate? |

**Common logical holes to check:**
1. **Matthew Effect**: Will the "long tail" actually survive, or just the top 10%?
2. **Cold start problem**: Who comes first when nothing exists yet?
3. **Chicken-and-egg**: Which side of the market starts?
4. **Misattributed causality**: Did X cause Y, or just correlate?
5. **Survivorship bias**: Only looking at successes, not failures
6. **Underestimated CAC**: Acquisition costs often 3-5x initial estimates
7. **Overestimated LTV**: Churn often higher than expected

### Phase 5: Structured Documentation

**Create modular documents:**

```
analysis/
├── README.md                    # Index and navigation guide
├── 01_original_model.md         # Original business model (user's perspective)
├── 02_improved_proposal.md      # Your proposed improvements
├── 03_component_A_logic_check.md # Detailed analysis of specific component
├── 04_component_B_logic_check.md # (e.g., trainer ecosystem, sales channels)
└── 05_counter_arguments.md      # Your critique of your own proposal
```

**Each document should include:**

1. **AI Prompt Section** at the top:
```markdown
## AI Analysis Prompt

```
You are a [role: business analyst/market researcher/etc.] with [X years] experience in [domain].

Please analyze the following business model component:
- Identify logical flaws and unstated assumptions
- Validate mathematical calculations
- Assess market feasibility
- Compare to successful/failed precedents
- Evaluate execution difficulty

Output format: Structured analysis with specific recommendations.
```
```

2. **Content Section** with:
   - Clear headers and structure
   - Tables for comparisons
   - ASCII diagrams for flows/flywheels
   - Step-by-step reasoning
   - Explicit assumptions

### Phase 6: Validation Preparation

**Prepare for external AI review:**

1. **Create summary of key controversies:**
   | Assumption | User's View | Counter-View | Evidence Needed |

2. **Identify data gaps:**
   - What metrics would validate/invalidate this?
   - What experiments could be run?

3. **Prepare founder discussion points:**
   - Questions to ask
   - Hypotheses to test
   - Risks to acknowledge

## Key Principles

### 1. Preserve User Intent
- Never dismiss constraints ("must be ToC", "won't do ToB")
- Work within stated boundaries
- If a constraint seems problematic, flag it but don't override

### 2. First-Person Documentation
- Write as if the user wrote it ("My analysis shows...")
- Not "We discussed and concluded..."
- This is for the user to share with stakeholders

### 3. Find Holes Aggressively
- After proposing improvements, MUST critique them
- Look for counter-examples
- Calculate worst-case scenarios
- Question every "obviously"

### 4. Modular Structure
- Each document should be independently analyzable
- AI prompts should be specific to the content
- Avoid overwhelming context windows

### 5. Visual Clarity
- Use tables for comparisons
- Use ASCII art for flows
- Use headers for scanability
- Bold key conclusions

## Example Output Structure

### For a Platform Business Model Analysis

**01_original_model.md:**
- Founder's original flywheel
- Revenue assumptions
- User/developer projections

**02_improved_proposal.md:**
- Modified flywheel
- New pricing tiers
- Revised projections

**03_trainer_ecosystem_logic.md:**
- Analysis of "1000 trainers" assumption
- AI prompt for trainer market sizing
- Mathematical validation

**04_sales_channel_logic.md:**
- Analysis of "livestream sales" assumption
- AI prompt for channel effectiveness
- Conversion funnel critique

**05_self_critique.md:**
- Your critique of your own proposal
- Alternative simpler models
- Recommendation on which path to pursue

## Common Pitfalls to Avoid

1. **Accepting stated assumptions at face value** - Always validate
2. **Ignoring opportunity costs** - What else could resources do?
3. **Underestimating time to market** - Everything takes 2-3x longer
4. **Overestimating user enthusiasm** - Users are lazy and busy
5. **Neglecting competitive response** - Incumbents won't sit still
6. **Forgetting about incentives** - Why would each party participate?
7. **Assuming linear scaling** - Growth usually hits plateaus

## Success Metrics

A successful analysis should:
- Identify 3-5 major logical flaws in original model
- Propose concrete, implementable improvements
- Find 2-3 holes in the proposed improvements
- Provide structured docs ready for external review
- Give the user confidence in next steps (pivot, persevere, or abandon)

## Final Output Checklist

- [ ] Original model fully documented (no omissions)
- [ ] Improvements proposed with step-by-step reasoning
- [ ] Self-critique performed (found holes in own logic)
- [ ] Modular docs created with AI prompts
- [ ] README/index created for navigation
- [ ] Key controversies identified
- [ ] Data gaps noted
- [ ] Founder discussion points prepared