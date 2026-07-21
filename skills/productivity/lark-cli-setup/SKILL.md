---
name: lark-cli-setup
description: Install and configure the Lark/Feishu CLI tool (@larksuite/cli) with all 23 official skills for document, sheet, calendar, IM, and workflow automation.
version: 1.0.0
metadata:
  hermes:
    tags: [lark, feishu, cli, productivity, collaboration, 飞书]
---

# Lark/Feishu CLI Setup

Install and configure the official Lark (Feishu) CLI tool with all 23 skills for comprehensive workspace automation.

## Overview

The Lark CLI provides command-line access to Feishu/Lark workspace features including:
- **IM (即时消息)** - Send/receive messages, manage groups
- **Docs (文档)** - Create and edit documents
- **Sheets (表格)** - Manage spreadsheets
- **Calendar (日历)** - Schedule and manage events
- **Drive (云盘)** - File storage and sharing
- **Wiki (知识库)** - Knowledge base management
- **Tasks (任务)** - Task and project management
- **Minutes (妙记)** - Meeting recordings and transcripts
- **Approval (审批)** - Workflow approvals
- **And more...**

## Prerequisites

- Node.js and npm installed
- npx available (comes with npm)
- Active Feishu/Lark account

## Installation Steps

### 1. Install Lark CLI

```bash
npm install -g @larksuite/cli
```

Verify installation:
```bash
lark-cli --version
# Expected: lark-cli version 1.0.11 (or later)
```

**Note:** The binary may be installed to `~/.npm-global/bin/lark-cli`. Add to PATH if needed:
```bash
export PATH="$HOME/.npm-global/bin:$PATH"
```

### 2. Install Official Skills

Install all 23 official Lark skills:

```bash
npx skills add larksuite/cli -g -y
```

This installs skills for:
- `lark-approval` - Approval workflows
- `lark-attendance` - Attendance management
- `lark-base` - Base/database operations
- `lark-calendar` - Calendar management
- `lark-contact` - Contact management
- `lark-doc` - Document operations
- `lark-drive` - Drive/cloud storage
- `lark-event` - Event management
- `lark-im` - Instant messaging
- `lark-mail` - Email management
- `lark-minutes` - Meeting minutes
- `lark-openapi-explorer` - API exploration
- `lark-shared` - Shared resources
- `lark-sheets` - Spreadsheet operations
- `lark-skill-maker` - Custom skill creation
- `lark-slides` - Presentation management
- `lark-task` - Task management
- `lark-vc` - Video conferencing
- `lark-whiteboard` - Whiteboard operations
- `lark-whiteboard-cli` - Whiteboard CLI
- `lark-wiki` - Wiki management
- `lark-workflow-meeting-summary` - Meeting summaries
- `lark-workflow-standup-report` - Standup reports

### 3. Initialize Configuration

```bash
lark-cli config init --new
```

This will:
1. Generate a QR code
2. Provide a configuration URL
3. Wait for you to complete authorization

**Example output:**
```
打开以下链接配置应用:
  https://open.feishu.cn/page/cli?user_code=XXXX-XXXX&lpv=1.0.11

等待配置应用...
```

### 4. Complete Authorization

1. Open the provided URL in your browser
2. Log in with your Feishu account
3. Create or select an existing app
4. Grant necessary permissions
5. Return to the terminal - the CLI will detect completion

### 5. Verify Setup

```bash
# Check CLI status
lark-cli auth status

# List available skills
lark-cli skills list

# Test with a simple command
lark-cli im list-chats
```

## Common Commands

### IM (即时消息)

```bash
# List recent chats
lark-cli im list-chats

# Send a message
lark-cli im send --chat-id "oc_xxx" --content "Hello from CLI"

# Get chat history
lark-cli im history --chat-id "oc_xxx"
```

### Documents

```bash
# Create a document (v1 — deprecated, prefer v2)
lark-cli doc create --title "My Document" --content "Document body"

# List documents
lark-cli doc list

# Get document content
lark-cli doc get --doc-token "docxxx"

# Fetch document content from URL (works when browser hits auth wall)
lark-cli docs +fetch --doc "https://7colortech.feishu.cn/wiki/XXXXX" --format pretty

# Fetch with outline mode (headings only) — useful for structure checks
lark-cli docs +fetch --doc <token> --api-version v2 --scope outline

# Update existing document — PITFALL: v1 and v2 use different flag names!
#   v1: --mode append --markdown "content"
#   v2: --command append --content "content"
# Always --help the specific API version first:
lark-cli docs +update --help --api-version v2

# v2 overwrite entire document (replaces all content)
lark-cli docs +update --doc <token> --api-version v2 --command overwrite --content @./content.html

# v2 append to end of document
lark-cli docs +update --doc <token> --api-version v2 --command append --content @./content.md

# @file references MUST be relative paths (e.g. ./file.md), NOT absolute (/tmp/file.md)
# stdin works too:  cat content.md | lark-cli docs +update ... --content -

# v2 other commands: str_replace, block_delete, block_insert_after, block_copy_insert_after, block_replace, block_move_after

# v2 create document from markdown file (relative path required!)
lark-cli docs +create --api-version v2 --content @./resume.md --doc-format markdown

# v2 create with parent folder/wiki-node (--parent-token or --parent-position)
lark-cli docs +create --api-version v2 --content @./doc.md --doc-format markdown --parent-token <folder_token>

# PITFALL: bot-created docs may show "permission_grant skipped" warning.
# The current user won't get auto-granted full_access if no open_id mapping exists.
# Fix: the user can manually grant themselves access via the Feishu web UI,
# or run `lark-cli auth login --recommend` to establish the open_id mapping.
```

### Sheets

```bash
# Create a spreadsheet
lark-cli sheets create --title "My Sheet"

# Read cell values
lark-cli sheets get-values --spreadsheet-token "shtxxx" --range "Sheet1!A1:D10"

# Update cells
lark-cli sheets update-values --spreadsheet-token "shtxxx" --range "Sheet1!A1" --values "[[\"Hello\", \"World\"]]"
```

### Calendar

```bash
# List events
lark-cli calendar list-events --start-date "2024-01-01" --end-date "2024-12-31"

# Create an event
lark-cli calendar create-event --title "Team Meeting" --start-time "2024-01-15T10:00:00" --end-time "2024-01-15T11:00:00"
```

### Tasks

```bash
# List tasks
lark-cli task list

# Create a task
lark-cli task create --title "Review PR" --due-date "2024-01-20"

# Complete a task
lark-cli task complete --task-id "xxx"
```

## Security Considerations

The skills installation shows security risk assessments:
- Most skills are rated "Safe" or "Low Risk"
- Some skills (doc, sheets, drive) are rated "High Risk" by Snyk - review before use
- Skills run with full agent permissions - use with caution

## Troubleshooting

### Accessing Feishu Drive Folders (云盘文件夹)

### Drive (云盘)

```bash
# List files in a folder
lark-cli drive files list --params '{"folder_token": "FOLDER_TOKEN"}'

# Create a folder
lark-cli drive +create-folder --name "New Folder"

# Upload a file
lark-cli drive +upload --file "/path/to/file.pdf"

# Download a file
lark-cli drive +download --file-token "FILE_TOKEN" --output "/path/to/save/"

# Move a file
lark-cli drive +move --file-token "FILE_TOKEN" --target-folder-token "TARGET_FOLDER"
```

**Note:** Drive folders require the `space:document:retrieve` scope. If you get a permission error:

```bash
# Request additional scope (run in background, it will block)
lark-cli auth login --scope "space:document:retrieve" --no-wait
# This outputs a verification_url - show it to the user to complete authorization
```

**Important:** The folder token from the URL (e.g., `WnPSfOtWklxfImdqmPEcTv97nIo`) is for **Drive**, not Wiki. Don't confuse:
- **Wiki nodes** - Use `lark-cli wiki nodes list`
- **Drive folders** - Use `lark-cli drive files list`

### Accessing Feishu Documents (Hermes Built-in vs Lark CLI)

**PITFALL: Hermes's `feishu_doc_read` tool** only works when the session originates from a Feishu comment context (e.g., replying to a document comment). When called outside that context, it fails with:

```
error: "Feishu client not available (not in a Feishu comment context)"
```

**Resolution: fall back to `lark-cli docs +fetch`** — it uses stored OAuth tokens and works regardless of the session origin. This is the most reliable way to read Feishu documents programmatically.

### Accessing Feishu Documents (Browser vs CLI)

When you encounter Feishu wiki/document links that require login (browser redirects to login page), **use the CLI instead of browser automation**:

```bash
# Check if CLI is already authenticated
lark-cli auth status

# If authenticated, fetch document content directly
lark-cli docs +fetch --doc "https://7colortech.feishu.cn/wiki/XXXXX" --format pretty

# For shorter output, use json format
lark-cli docs +fetch --doc "<url>" --format json
```

**Why this works:** The CLI uses stored OAuth tokens that bypass the web login flow, while browser automation hits the login wall.

### Analyzing Feishu Base (多维表格) Data

For comprehensive Base data analysis and summary generation:

**Step 1: Understand the schema first**
```bash
lark-cli base +field-list --base-token <BASE_TOKEN> --table-id <TABLE_ID>
```
This returns field definitions including types (text, select, multi-select, attachment, datetime, etc.) and options for select fields.

**Step 2: Fetch all records with pagination**
```bash
# Start with first page
lark-cli base +record-list --base-token <BASE_TOKEN> --table-id <TABLE_ID> \
  --view-id <VIEW_ID> --limit 100 --offset 0

# Continue with offset until no more records
lark-cli base +record-list --base-token <BASE_TOKEN> --table-id <TABLE_ID> \
  --view-id <VIEW_ID> --limit 100 --offset 100
```

**Step 3: Parse and analyze the data**
The response is an array of arrays. Map fields by index based on the field-list output:
- Index 0 = first field from field-list
- Index 1 = second field, etc.

**Data type handling:**
- `null` = empty cell
- `string` = text/URL fields
- `array` = multi-select or attachments (check if items have "name" key for attachments)
- `array with single item` = single-select fields

**Step 4: Generate categorical statistics**
Count distributions for:
- Single-select fields (e.g., status, priority)
- Multi-select fields (e.g., tags, categories)
- Date ranges (for time-based analysis)

**Step 5: Produce executive summary**
Include:
- Total record count
- Distribution breakdowns by key dimensions
- Highlights of high-priority or completed items
- Trends and patterns

**Example workflow for a project tracker Base:**
1. Get fields: 项目名称, 进度反馈, 优先级, 类别, 添加日期
2. Fetch all 128 records across 2 pages (100 + 28)
3. Parse into structured dicts with field names as keys
4. Count: 36条"评估中", 17条"准备中", 1条"已验证成功"
5. Count by priority: P1(41), P2(25), P0(24)
6. Group by category: AI视频(43), 教育应用(19), 其他(18)
7. Generate summary with top projects and insights

### Reading Historical Commits with Special Characters

When retrieving historical commits that contain files with special characters (Chinese filenames, etc.), the git show command may fail with "path not in commit" errors. Use this approach:

```bash
# List files in the commit first to see exact paths
git show <commit_hash> --name-only

# For files with special characters, use git show with the exact path from --name-only
# If the filename shows as escaped octal (e.g., \\350\\277\...), use the -- encoding:
git show <commit_hash>:"docs/实际文件名.md"

# Alternative: use git show with the raw path from --name-only output
git show <commit_hash> -- "docs/*"
```

**Note:** Git stores filenames in octal-escaped format internally. When accessing historical commits, you may need to work with the escaped representation or use wildcards.

### Command not found

```bash
# Find the binary
which lark-cli || find ~ -name "lark-cli" 2>/dev/null

# Add to PATH
export PATH="$HOME/.npm-global/bin:$PATH"
```

### Authentication fails

1. Ensure you're using a Feishu account with proper permissions
2. Check that the app has been approved by your organization admin
3. Try re-authenticating: `lark-cli auth login --recommend`

### Skills not working

1. Verify skills are installed: `ls ~/.agents/skills/ | grep lark`
2. Check skill documentation: `cat ~/.agents/skills/lark-im/README.md`
3. Update skills: `npx skills update larksuite/cli -g`

### Permission Management (权限管理)

When bot-created documents need to be shared with the user:

**Schema-first approach** — always inspect the API schema before calling:
```bash
lark-cli schema drive.permission.members.create   # member-level permissions
lark-cli schema drive.permission.public.patch      # public sharing settings
```

**PITFALL: `permission.members create` with email fails** — Adding a member by email (`member_type: "email"`) returns error `[1063001] Invalid parameter` when the user is not in the same enterprise tenant as the bot. The bot cannot resolve external emails to user IDs.

**WORKAROUND: Use `permission.public patch`** to make the doc editable by anyone with the link:
```bash
lark-cli drive permission.public patch \
  --params '{"token":"<doc_token>","type":"docx"}' \
  --data '{"external_access":true,"security_entity":"anyone_can_view","comment_entity":"anyone_can_view","share_entity":"anyone","link_share_entity":"anyone_editable","invite_external":true}' \
  --yes
```

Key fields:
- `link_share_entity`: `"anyone_readable"` (view only) or `"anyone_editable"` (edit)
- `external_access`: `true` — allows sharing outside the organization
- `invite_external`: `true` — non-managers can invite external users
- `share_entity`: `"anyone"` — anyone can add collaborators

**Response format differences** — `permission.public patch` returns `{"code": 0, "msg": "Success"}` (not `{"ok": true}` like docs commands). Check `code == 0` for success, not `ok`.

**Note**: `permission.public` cannot be used with `type: "wiki"` (knowledge base nodes) — several fields are unsupported for wiki-type resources.

**For true member-level ownership**: the user should open the doc in the Feishu web UI and make a copy to their own space, which grants them full ownership. Alternatively, run `lark-cli auth login --recommend` to establish the open_id mapping so `permission.members create` can use `member_type: "openid"`.

### docs +update append silently truncates large content

If `--command append` produces a truncated result (document shows only the first `<hr/>` but the rest is missing), fall back to `--command overwrite`: fetch the existing content, concatenate the new content to it, and overwrite the entire document. This is reliable for large markdown/HTML payloads.

```bash
# 1. Fetch current content
lark-cli docs +fetch --doc <token> --api-version v2 > current.json

# 2. Build combined content file (original + new analysis)
# 3. Overwrite
lark-cli docs +update --doc <token> --api-version v2 --command overwrite --content @./combined.html
```

## Resources

- **Skills Hub:** https://skills.sh/larksuite/cli
- **Feishu Open Platform:** https://open.feishu.cn/
- **CLI Documentation:** Included in each skill's README

## Notes

- The CLI uses the Feishu Open API - requires internet connectivity
- Some features may require specific app permissions granted by organization admins
- Skills are installed to `~/.agents/skills/` and symlinked to various AI assistants
- The 23 skills provide comprehensive coverage of Feishu/Lark workspace features
