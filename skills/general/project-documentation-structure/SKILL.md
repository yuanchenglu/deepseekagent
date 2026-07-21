---
name: project-documentation-structure
description: Create a comprehensive documentation structure for software projects with organized folders for requirements, technical docs, deployment guides, and operation manuals.
version: 1.0.0
metadata:
  hermes:
    tags: [documentation, project-management, docs, organization, templates]
---

# Project Documentation Structure

Create a well-organized documentation structure for software projects that separates concerns and makes information easy to find.

## Overview

A good documentation structure helps team members quickly find what they need:
- **New developers** → Technical docs and setup guides
- **DevOps engineers** → Deployment and infrastructure docs
- **End users** → Operation manuals and FAQs
- **Project managers** → Requirements and status docs

## Directory Structure

```
docs/
├── README.md                    # Documentation center entry point
├── PROJECT_STATUS.md            # Current project status and blockers
├── requirements/                # 📋 Requirements and planning
│   ├── PRD_v{version}.md       # Product Requirements Document
│   ├── user_stories.md         # User stories and use cases
│   ├── changelog.md            # Version history and changes
│   └── roadmap.md              # Future plans and milestones
├── technical/                   # 🔧 Technical documentation
│   ├── architecture.md         # System architecture and design
│   ├── api_reference.md        # API documentation
│   ├── database_schema.md      # Database design
│   ├── development_guide.md    # Development standards
│   └── security.md             # Security considerations
├── deployment/                  # 🚀 Deployment documentation
│   ├── deployment_guide.md     # Step-by-step deployment
│   ├── environment_setup.md    # Environment configuration
│   ├── migration_guide.md      # Data migration procedures
│   └── rollback_procedures.md  # Emergency rollback steps
├── operation/                   # 📖 Operation and support
│   ├── user_manual.md          # End-user guide
│   ├── admin_manual.md         # Administrator guide
│   ├── troubleshooting.md      # Common issues and solutions
│   └── faq.md                  # Frequently asked questions
└── archive/                     # 📦 Historical documents
    ├── meeting_records/        # Meeting notes and decisions
    ├── design_artifacts/       # Design mockups and diagrams
    └── temp/                   # Temporary working documents
```

## Quick Start

### 1. Create Directory Structure

```bash
mkdir -p docs/{requirements,technical,deployment,operation,archive/{meeting_records,design_artifacts,temp}}
touch docs/README.md
touch docs/PROJECT_STATUS.md
```

### 2. Create Main Entry Point (README.md)

```markdown
# {Project Name} Documentation Center

> **Version**: {version}  
> **Last Updated**: {date}  
> **Maintainer**: {name}

---

## 📁 Documentation Index

### For Developers
- [System Architecture](technical/architecture.md)
- [Development Guide](technical/development_guide.md)
- [API Reference](technical/api_reference.md)

### For DevOps
- [Deployment Guide](deployment/deployment_guide.md)
- [Environment Setup](deployment/environment_setup.md)

### For Users
- [User Manual](operation/user_manual.md)
- [FAQ](operation/faq.md)

### Project Management
- [Project Status](PROJECT_STATUS.md)
- [Requirements](requirements/PRD_v1.0.md)
- [Changelog](requirements/changelog.md)

---

## 🚀 Quick Links

- **Production**: {url}
- **Staging**: {url}
- **Repository**: {git_url}
- **Issue Tracker**: {issues_url}
```

### 3. Create Project Status Document

```markdown
# Project Status

> **Status**: 🟢 Active / 🟡 In Progress / 🔴 Blocked  
> **Last Updated**: {date}

---

## 📊 Current Status

### ✅ Completed
- [Feature 1]
- [Feature 2]

### 🚧 In Progress
- [Task 1]
- [Task 2]

### 🔴 Blockers
| Issue | Impact | Owner | ETA |
|-------|--------|-------|-----|
| [Blocker] | High | [Name] | [Date] |

---

## 📅 Timeline

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| v1.0 Release | 2024-01-15 | 🟡 In Progress |
| v1.1 Release | 2024-02-01 | ⚪ Not Started |

---

## 👥 Team

| Role | Name | Contact |
|------|------|---------|
| PM | [Name] | [email] |
| Tech Lead | [Name] | [email] |
| DevOps | [Name] | [email] |
```

## Document Templates

### Product Requirements Document (PRD)

```markdown
# PRD v{version} - {Project Name}

## 1. Overview

### 1.1 Background
{Context and problem statement}

### 1.2 Goals
- Goal 1
- Goal 2

### 1.3 Non-Goals
- Out of scope item 1
- Out of scope item 2

## 2. User Personas

### Persona 1: {Name}
- **Role**: {Role}
- **Pain Points**: {Problems}
- **Needs**: {Requirements}

## 3. Requirements

### Functional Requirements
| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-001 | {Description} | P0 | {Criteria} |

### Non-Functional Requirements
| ID | Requirement | Target |
|----|-------------|--------|
| NFR-001 | Performance | < 2s response |

## 4. Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1 | 2 weeks | MVP |
| Phase 2 | 1 week | Polish |
```

### Architecture Document

```markdown
# System Architecture

## Overview
{High-level description}

## Architecture Diagram
```
[Diagram or ASCII art]
```

## Components

### Component 1: {Name}
- **Purpose**: {What it does}
- **Technology**: {Stack}
- **Interfaces**: {APIs/connections}

## Data Flow
1. Step 1
2. Step 2
3. Step 3

## Technology Stack
| Layer | Technology | Version |
|-------|------------|---------|
| Frontend | React | 18.x |
| Backend | Node.js | 20.x |
| Database | PostgreSQL | 15.x |
```

### Deployment Guide

```markdown
# Deployment Guide

## Prerequisites
- [ ] Requirement 1
- [ ] Requirement 2

## Environment Setup

### Development
```bash
# Commands
```

### Production
```bash
# Commands
```

## Deployment Steps

### Step 1: {Action}
```bash
# Commands
```

### Step 2: {Action}
```bash
# Commands
```

## Verification
- [ ] Check 1
- [ ] Check 2

## Rollback
If deployment fails:
```bash
# Rollback commands
```
```

### User Manual

```markdown
# User Manual

## Quick Start
1. Step 1
2. Step 2
3. Step 3

## Features

### Feature 1: {Name}
**Purpose**: {What it does}

**Steps**:
1. Step 1
2. Step 2

**Screenshot**: [Image]

## Troubleshooting

### Problem 1: {Issue}
**Solution**: {Steps to resolve}

## FAQ

**Q**: Question?
**A**: Answer.
```

## Best Practices

### 1. Keep Documents Updated
- Update `PROJECT_STATUS.md` weekly
- Update `changelog.md` with each release
- Review docs quarterly for accuracy

### 2. Use Consistent Formatting
- Markdown for all documents
- Tables for structured data
- Code blocks for commands
- Headers for hierarchy

### 3. Include Metadata
Every document should have:
```markdown
> **Version**: x.y.z  
> **Last Updated**: YYYY-MM-DD  
> **Author**: Name  
> **Reviewers**: Name1, Name2
```

### 4. Cross-Reference
- Link related documents
- Use relative paths: `[Link](../technical/architecture.md)`
- Maintain a master index in README.md

### 5. Version Control
- Commit docs with code changes
- Use meaningful commit messages: `DOCS: Update deployment guide`
- Review docs in PRs

## Automation

### Generate Structure Script

```bash
#!/bin/bash
# init-docs.sh

PROJECT_NAME="$1"

mkdir -p docs/{requirements,technical,deployment,operation,archive/{meeting_records,design_artifacts,temp}}

cat > docs/README.md << EOF
# $PROJECT_NAME Documentation

## Quick Links
- [Project Status](PROJECT_STATUS.md)
- [Requirements](requirements/)
- [Technical Docs](technical/)
- [Deployment](deployment/)
- [Operations](operation/)
EOF

cat > docs/PROJECT_STATUS.md << EOF
# Project Status

> **Status**: 🟡 In Progress  
> **Last Updated**: $(date +%Y-%m-%d)

## Overview
{Project description}

## Current Status
- ✅ Completed: 
- 🚧 In Progress: 
- 🔴 Blockers: 

## Team
- PM: 
- Tech Lead: 
- DevOps: 
EOF

echo "Documentation structure created for $PROJECT_NAME"
```

Usage:
```bash
chmod +x init-docs.sh
./init-docs.sh "My Project"
```

## Integration with Tools

### MkDocs (Static Site Generator)

```yaml
# mkdocs.yml
site_name: Project Documentation
nav:
  - Home: index.md
  - Requirements:
    - PRD: requirements/PRD.md
  - Technical:
    - Architecture: technical/architecture.md
plugins:
  - search
```

### GitHub/GitLab Pages

Host your docs as a static website:

```yaml
# .github/workflows/docs.yml
name: Deploy Docs
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install mkdocs
      - run: mkdocs gh-deploy --force
```

## Examples

### Well-Structured Projects
- [Kubernetes](https://github.com/kubernetes/community/tree/master/contributors/guide)
- [React](https://github.com/facebook/react/tree/main/docs)
- [Terraform](https://github.com/hashicorp/terraform/tree/main/docs)

## Resources

- [Documentation as Code](https://www.writethedocs.org/guide/docs-as-code/)
- [Markdown Guide](https://www.markdownguide.org/)
- [MkDocs](https://www.mkdocs.org/)
- [Docusaurus](https://docusaurus.io/)

## Notes

- Start simple, expand as needed
- Don't over-document - focus on what's useful
- Keep docs close to code (same repo)
- Make docs searchable
- Regular reviews prevent staleness
