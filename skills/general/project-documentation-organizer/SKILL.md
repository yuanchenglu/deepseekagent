---
name: project-documentation-organizer
description: Organize scattered project documentation into a structured docs/ directory with proper categorization, README index, and version control
version: 1.0.0
trigger: When user needs to organize project docs, create documentation structure, or archive project materials
---

# Project Documentation Organizer

Organize scattered project documentation into a well-structured, maintainable documentation system.

## Purpose
Transform unstructured project materials (links, notes, scattered files) into a professional documentation structure suitable for team collaboration and long-term maintenance.

## When to Use
- Project handover/sunset documentation
- Converting scattered notes into structured docs
- Creating documentation for legacy projects
- Organizing materials from multiple sources (Feishu, Wiki, emails, etc.)

## Directory Structure Template

```
docs/
├── README.md                    # Documentation hub and entry point
├── PROJECT_STATUS.md            # Current state, blockers, next steps
├── requirements/                # 📋 Requirements and specifications
│   ├── PRD_v{version}.md       # Product Requirements Document
│   ├── user_stories.md         # User stories and use cases
│   └── changelog.md            # Version history and changes
├── technical/                   # 🔧 Technical documentation
│   ├── architecture.md         # System architecture and design
│   ├── api_reference.md        # API documentation
│   ├── database_schema.md      # Database design
│   └── development_guide.md    # Development standards
├── deployment/                  # 🚀 Deployment and operations
│   ├── deployment_guide.md     # Step-by-step deployment
│   ├── environment_setup.md    # Environment configuration
│   └── migration_guide.md      # Migration procedures
├── operation/                   # 📖 User and admin guides
│   ├── user_manual.md          # End-user documentation
│   ├── admin_manual.md         # Administrator guide
│   ├── troubleshooting.md      # Common issues and fixes
│   └── faq.md                  # Frequently asked questions
└── archive/                     # 📦 Historical materials
    ├── meeting_records/
    ├── design_artifacts/
    └── temp/
```

## Workflow

### Phase 1: Information Gathering
1. **Collect all sources**:
   - Feishu/Lark documents (use `lark-cli` to fetch content)
   - Wiki pages
   - Code repository READMEs
   - Meeting notes
   - Email threads
   - Chat logs

2. **Identify document types**:
   - User-facing guides → `operation/`
   - Technical specs → `technical/`
   - Deployment info → `deployment/`
   - Requirements → `requirements/`

### Phase 2: Content Creation

#### README.md Template
```markdown
# {Project Name} Documentation

> **Version**: {X.Y.Z}  
> **Last Updated**: {YYYY-MM-DD}  
> **Maintainer**: {Name}

---

## 📁 Document Index

| Category | Documents | Purpose |
|----------|-----------|---------|
| Requirements | [PRD](requirements/PRD.md) | Product specifications |
| Technical | [Architecture](technical/architecture.md) | System design |
| Deployment | [Guide](deployment/deployment_guide.md) | Deployment steps |
| Operation | [User Manual](operation/user_manual.md) | User guides |

## 🎯 Quick Links

- **Project Status**: [Current State](PROJECT_STATUS.md)
- **Deployment Checklist**: [Checklist](../DEPLOYMENT_CHECKLIST.md)
- **Code Repository**: {repo_url}

## 👥 Team

| Role | Name | Contact |
|------|------|---------|
| PM | {name} | {contact} |
| Tech Lead | {name} | {contact} |
```

#### PROJECT_STATUS.md Template
```markdown
# Project Status

> **Status**: {🟢 Active / 🔶 Blocked / 🔴 Sunset}  
> **Last Updated**: {YYYY-MM-DD}

---

## 📋 Project Overview

| Attribute | Value |
|-----------|-------|
| **Name** | {project_name} |
| **Repository** | {repo_url} |
| **Tech Stack** | {stack} |

## ✅ Completed Work

- [x] {completed_item_1}
- [x] {completed_item_2}

## 🔴 Current Blockers

| Blocker | Impact | Owner | ETA |
|---------|--------|-------|-----|
| {issue} | {impact} | {owner} | {eta} |

## ⏳ Next Steps

1. {next_step_1}
2. {next_step_2}

## 📞 Contacts

- **PM**: {name} - {contact}
- **Tech Lead**: {name} - {contact}
```

### Phase 3: Git Integration

```bash
# Create docs directory structure
mkdir -p docs/{requirements,technical,deployment,operation,archive}

# Add all documentation
git add docs/
git add DEPLOYMENT_CHECKLIST.md  # if applicable

# Commit with descriptive message
git commit -m "DOCS: Initialize project documentation

【新增文档】
- docs/README.md: Documentation hub
- docs/PROJECT_STATUS.md: Project status and blockers
- docs/requirements/PRD_v{X.Y}.md: Product requirements
- docs/technical/architecture.md: System architecture
- docs/deployment/deployment_guide.md: Deployment guide
- docs/operation/user_manual.md: User manual

【内容来源】
- Feishu Wiki: {url}
- Code repository: {repo}
- Meeting notes: {date}}"

# Push to remote
git push origin {branch}
```

## Key Principles

1. **Single Source of Truth**: All project info in one place
2. **Clear Ownership**: Each doc has a maintainer
3. **Status Visibility**: PROJECT_STATUS.md shows current state
4. **Actionable Next Steps**: Clear task list with owners
5. **Version Control**: Docs live with code in git

## Common Patterns

### For Blocked Projects
- Clearly document blockers in PROJECT_STATUS.md
- Include contact info for unblock
- Document what IS working vs what's blocked

### For Multi-Stakeholder Projects
- Separate docs by audience (user/admin/dev)
- Include role-based quick start guides
- Clear contact matrix

### For Legacy/Handover Projects
- Archive historical decisions in `archive/`
- Document "why" not just "what"
- Include migration/decommission plans

## Quality Checklist

- [ ] All scattered docs consolidated
- [ ] README.md provides clear navigation
- [ ] PROJECT_STATUS.md shows current state
- [ ] Documents categorized by audience
- [ ] Git commit with descriptive message
- [ ] Links between documents work
- [ ] Contact information included
