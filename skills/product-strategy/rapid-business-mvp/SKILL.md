---
name: rapid-business-mvp
title: Rapid Business MVP Development
description: Build minimal viable products for small business workflows - mobile-first, WeChat-optimized, single-file database, deployable to single VPS.
triggers:
  - keywords: ["mvp", "small business", "workflow", "digitization", "excel replacement", "手机", "微信", "简单系统", "小工具"]
    description: User wants to digitize a manual business process (often Excel-based) into a simple web app
  - keywords: ["inventory", "进销存", "库存", "记账"]
    description: Inventory/stock management or accounting workflows
  - keywords: ["quick prototype", "fastest way", "最简单"]
    description: User emphasizes speed and simplicity over comprehensive features
prerequisites:
  - User describes a manual workflow (often Excel-based)
  - Small team (3-10 people)
  - Mobile access required
  - Limited budget/timeline
---

# Rapid Business MVP Development

Build minimal viable products for small business workflow digitization.

## When to Use

- User describes a manual workflow (often Excel/paper-based)
- Small team (3-10 people) needs simple digital solution
- Mobile/WeChat access is primary requirement
- Limited budget and timeline (days to weeks, not months)
- User initially asks for "existing solutions" but actually needs custom MVP

## Key Principles

### 1. Start with "Excel Replacement" Mindset

Most small business users are migrating from Excel. Don't over-engineer:
- Match their current mental model
- Add automation (calculations, sync) but keep familiar workflows
- One-screen-per-task principle

### 2. Mobile-First, WeChat-Optimized

```
Technical Stack:
├── Frontend: Pure HTML + Tailwind CSS (CDN)
│   └── No build step, no framework, instant preview
│   └── Optimized for WeChat built-in browser
│   └── Touch-friendly inputs, prevent iOS zoom
├── Backend: Node.js + Express
│   └── Single-file SQLite database
│   └── REST API (5-8 endpoints maximum)
└── Deployment: Single VPS/ECS
    └── PM2 process management
    └── Optional: Nginx reverse proxy
```

### 3. Single-File Database Pattern

**Why SQLite:**
- Zero configuration
- Backup = copy one file
- Perfect for MVP scale (<10GB, <10 concurrent users)
- Easy to migrate to PostgreSQL later if needed

**Database Schema Pattern:**
```sql
-- Core entities only
CREATE TABLE products (id, name, stock, avg_cost);
CREATE TABLE transactions (id, product_id, type, qty, price, profit, user, created_at);
CREATE TABLE users (id, username, password_hash, role);
```

### 4. Three-Page Architecture

```
Page 1: Dashboard
├── Today's key metrics (profit, sales, purchases)
├── Quick action buttons (big, thumb-friendly)
└── Recent activity list

Page 2: Data Entry
├── Minimal form fields (3-5 max per action)
├── Real-time calculation preview
├── One-tap submit
└── Immediate feedback (toast notification)

Page 3: Records/Reports
├── Searchable list
├── Simple filters (today/week/month)
└── Export to Excel (CSV download)
```

## Workflow

### Phase 1: Requirements Extraction (30 min)

1. **Identify the pain point**
   - What takes most time in current manual process?
   - What errors happen frequently?
   - Who needs access to what data?

2. **Map the workflow**
   ```
   Input → Process → Output
   (e.g., Purchase → Inventory Update → Profit Calculation)
   ```

3. **Define MVP scope**
   - Core loop: What single workflow delivers 80% value?
   - Cut features ruthlessly
   - "Nice to have" = V1.1

### Phase 2: Technical Decisions (15 min)

**Decision Tree:**

```
User asks for "existing open source solutions"?
├── Evaluate: Does any match 90%+ of needs?
│   ├── YES → Recommend + customization estimate
│   └── NO  → Build custom MVP (this skill)
│
Need real-time collaboration?
├── YES → WebSocket or polling (add complexity)
└── NO  → Simple REST API (recommended for MVP)
│
Multiple locations/warehouses?
├── YES → Add location_id to schema
└── NO  → Single location, hardcode if needed
```

### Phase 3: Rapid Implementation (2-4 hours)

**File Structure:**
```
project/
├── server.js          # Express + SQLite (200-300 lines)
├── package.json       # 4 deps: express, sqlite3, cors, body-parser
├── README.md          # Setup + deployment guide
├── DEPLOY.md          # VPS/ECS specific instructions
└── public/
    └── index.html     # Single-page app (300-500 lines)
```

**Backend Checklist:**
- [ ] Express server with CORS
- [ ] SQLite initialization (auto-create tables)
- [ ] CRUD endpoints for core entities
- [ ] Simple auth (session or JWT-lite)
- [ ] Health check endpoint

**Frontend Checklist:**
- [ ] Mobile viewport meta tags
- [ ] Touch-friendly button sizes (min 44px)
- [ ] Input font-size: 16px (prevents iOS zoom)
- [ ] Loading states for all async actions
- [ ] Toast notifications for feedback
- [ ] Offline detection (optional but nice)

### Phase 4: Deployment (30 min)

**Target: Single VPS/ECS**

```bash
# One-command deployment
npm install
npm start  # or pm2 start
```

**Required Documentation:**
- Environment setup (Node.js version)
- Port configuration
- Database backup commands
- Default login credentials

## Common Patterns

### Pattern: Inventory/Stock Management

**Core Loop:**
1. Purchase Entry → Update stock + avg_cost
2. Sale Entry → Deduct stock + calculate profit
3. Dashboard → Show current stock + today's profit

**Key Calculation:**
```javascript
// Average cost method
newAvgCost = (oldStock * oldAvgCost + newQty * newPrice) / (oldStock + newQty)
profit = (salePrice - avgCost) * saleQty
```

### Pattern: Approval Workflow

**Simple state machine:**
```javascript
status: draft → submitted → approved → completed
```

**Notification:**
- In-app only for MVP
- WeChat notifications in V1.1

### Pattern: Multi-User Permissions

**Roles:**
- admin: full access
- staff: create only, read own
- viewer: read only

**Implementation:**
- Middleware check on API routes
- UI hides buttons based on role

## Anti-Patterns

❌ **Don't:**
- Use React/Vue for MVP (build step overhead)
- Use MySQL/PostgreSQL (deployment complexity)
- Build native apps (distribution friction)
- Add real-time sync (WebSocket complexity)
- Implement complex RBAC (2-3 roles max)

✅ **Do:**
- Use SQLite, migrate to PostgreSQL later if needed
- Deploy to single VPS, scale horizontally later
- Use WeChat web, build mini-program later if needed
- Start with single user type, add roles later

## Example Output Structure

```
~/Code/business-mvp/
├── server.js              # Working backend
├── package.json           # Dependencies
├── inventory.db           # SQLite database (auto-created)
├── README.md              # Quick start
├── DEPLOY.md              # Production deployment
└── public/
    └── index.html         # Mobile-optimized frontend
```

## Success Metrics

- [ ] User can complete core workflow in < 30 seconds
- [ ] Works smoothly on 3-year-old Android phones
- [ ] Loads in < 3 seconds on 4G network
- [ ] No training required (self-explanatory UI)
- [ ] Deploys in < 10 minutes to fresh VPS

## Post-MVP Roadmap

**V1.1 (Week 2):**
- Data export (Excel/CSV)
- Simple reports/charts
- User password change

**V1.2 (Month 2):**
- Image upload (receipts/photos)
- Push notifications
- Basic analytics

**V2.0 (Month 3+):**
- Consider migrating to proper framework
- Add features based on actual usage data
- Scale infrastructure if needed

---

Remember: The goal is **working software in user's hands today**, not perfect architecture tomorrow.
