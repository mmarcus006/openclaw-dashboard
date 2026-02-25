# OpenClaw Dashboard — Technical Plan
_Version: 1.0 | Author: COS | Date: 2026-02-25_

## 1. Overview

A standalone web application for managing OpenClaw's multi-agent ecosystem at scale. Personal-use only (single user, localhost). Reads and writes the same files OpenClaw uses — no database, no duplication, no conflicts with OpenClaw updates.

**Problem:** OpenClaw's built-in dashboard is finicky, incomplete config UI, and no way to manage 30+ agents at scale. Managing agents means SSH-ing into workspaces and manually editing Markdown/JSON files.

**Solution:** A companion web app with fleet overview, Monaco file editor, visual config management, and gateway controls.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────┐
│                   Browser (localhost:5173)        │
│  React + TypeScript + Tailwind + Monaco Editor   │
│  Vite dev server (proxies /api → :8400)          │
└──────────────────┬──────────────────────────────┘
                   │ HTTP + WebSocket
┌──────────────────▼──────────────────────────────┐
│              FastAPI Backend (:8400)              │
│  Python 3.12+ | uvicorn | pydantic v2           │
│                                                  │
│  ┌─────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Agents  │ │  Config  │ │    Gateway       │  │
│  │ Router  │ │  Router  │ │    Router        │  │
│  └────┬────┘ └────┬─────┘ └───────┬──────────┘  │
│       │           │               │              │
│  ┌────▼───────────▼───────────────▼──────────┐   │
│  │         File System Layer                 │   │
│  │  ~/.openclaw/  (read/write)               │   │
│  │  /opt/homebrew/lib/node_modules/openclaw/ │   │
│  │  (read-only — bundled skills/docs)        │   │
│  └───────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

### Why No Database

OpenClaw is file-driven. Agent config = JSON. Memory = Markdown. Sessions = JSONL. Adding a database would mean syncing two sources of truth. Instead, we read/write the files directly. OpenClaw picks up changes immediately.

---

## 3. Technology Stack

### Backend
- **Runtime:** Python 3.12+
- **Framework:** FastAPI 0.115+
- **Server:** uvicorn with auto-reload in dev
- **Validation:** Pydantic v2
- **WebSocket:** FastAPI native WebSocket support
- **File watching:** watchfiles (for live reload notifications)
- **Process management:** asyncio.subprocess for `openclaw` CLI calls
- **Dependencies:** fastapi, uvicorn, pydantic, watchfiles, python-dotenv, aiofiles

### Frontend
- **Build tool:** Vite 6+
- **Framework:** React 19 + TypeScript 5.x
- **Styling:** Tailwind CSS v4
- **Editor:** @monaco-editor/react
- **Icons:** lucide-react
- **HTTP client:** Built-in fetch (no axios needed)
- **WebSocket:** Native WebSocket API
- **Routing:** react-router-dom v7
- **State:** React context + useReducer (no Redux — too simple for this)

### Dev Tools
- **Backend:** ruff (lint + format), pytest
- **Frontend:** eslint, prettier, vitest
- **Both:** Just run `make dev` to start both

---

## 4. Directory Structure

```
openclaw-dashboard/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app, CORS, lifespan
│   │   ├── config.py               # Settings (OPENCLAW_HOME, etc.)
│   │   ├── dependencies.py         # Common deps (get_openclaw_home, etc.)
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── agents.py           # /api/agents/*
│   │   │   ├── config.py           # /api/config/*
│   │   │   ├── gateway.py          # /api/gateway/*
│   │   │   ├── skills.py           # /api/skills/*
│   │   │   ├── sessions.py         # /api/sessions/*
│   │   │   ├── memory.py           # /api/memory/*
│   │   │   ├── cron.py             # /api/cron/*
│   │   │   └── files.py            # /api/files/* (generic file ops)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py            # Agent, AgentFile, AgentStatus
│   │   │   ├── config.py           # OpenClawConfig sections
│   │   │   ├── gateway.py          # GatewayStatus
│   │   │   ├── skill.py            # Skill, SkillMeta
│   │   │   ├── session.py          # Session, SessionMessage
│   │   │   └── memory.py           # MemoryFile, MemoryEntry
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── agent_service.py    # Agent discovery, workspace scanning
│   │   │   ├── config_service.py   # openclaw.json read/write
│   │   │   ├── gateway_service.py  # CLI wrapper for gateway commands
│   │   │   ├── skill_service.py    # Skill scanning + ClawHub
│   │   │   ├── session_service.py  # Session/JSONL parsing
│   │   │   ├── file_service.py     # Safe file read/write/list
│   │   │   └── memory_service.py   # Memory file operations
│   │   └── websocket/
│   │       ├── __init__.py
│   │       └── live.py             # WebSocket manager for live updates
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_agents.py
│   │   ├── test_config.py
│   │   ├── test_gateway.py
│   │   └── test_files.py
│   ├── pyproject.toml
│   └── Makefile
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── router.tsx              # React Router config
│   │   ├── api/
│   │   │   ├── client.ts           # Fetch wrapper with error handling
│   │   │   ├── agents.ts           # Agent API calls
│   │   │   ├── config.ts           # Config API calls
│   │   │   ├── gateway.ts          # Gateway API calls
│   │   │   ├── skills.ts           # Skills API calls
│   │   │   ├── sessions.ts         # Session API calls
│   │   │   └── websocket.ts        # WebSocket connection manager
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx     # Navigation sidebar
│   │   │   │   ├── Header.tsx      # Top bar with gateway status
│   │   │   │   └── Layout.tsx      # Main layout wrapper
│   │   │   ├── agents/
│   │   │   │   ├── AgentCard.tsx   # Agent summary card
│   │   │   │   ├── AgentGrid.tsx   # Fleet grid view
│   │   │   │   ├── AgentDetail.tsx # Full agent page
│   │   │   │   └── AgentFiles.tsx  # File list for an agent
│   │   │   ├── editor/
│   │   │   │   ├── FileEditor.tsx  # Monaco editor wrapper
│   │   │   │   ├── FileTree.tsx    # File browser sidebar
│   │   │   │   └── FileTabs.tsx    # Open file tabs
│   │   │   ├── config/
│   │   │   │   ├── ConfigEditor.tsx    # Visual config sections
│   │   │   │   ├── ConfigSection.tsx   # Collapsible section
│   │   │   │   └── JsonEditor.tsx      # Raw JSON toggle
│   │   │   ├── gateway/
│   │   │   │   ├── GatewayPanel.tsx    # Status + controls
│   │   │   │   └── GatewayLog.tsx      # Live log viewer
│   │   │   ├── skills/
│   │   │   │   ├── SkillCard.tsx       # Skill summary
│   │   │   │   └── SkillBrowser.tsx    # Grid of skills
│   │   │   ├── sessions/
│   │   │   │   ├── SessionList.tsx     # Session browser
│   │   │   │   └── SessionViewer.tsx   # Conversation view
│   │   │   └── common/
│   │   │       ├── Badge.tsx
│   │   │       ├── Button.tsx
│   │   │       ├── Card.tsx
│   │   │       ├── Modal.tsx
│   │   │       ├── Toast.tsx
│   │   │       └── Spinner.tsx
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx       # Fleet overview
│   │   │   ├── AgentPage.tsx           # Agent detail
│   │   │   ├── EditorPage.tsx          # File editor (full screen)
│   │   │   ├── ConfigPage.tsx          # Config management
│   │   │   ├── SkillsPage.tsx          # Skills browser
│   │   │   ├── SessionsPage.tsx        # Session viewer
│   │   │   └── GatewayPage.tsx         # Gateway controls
│   │   ├── hooks/
│   │   │   ├── useAgents.ts
│   │   │   ├── useConfig.ts
│   │   │   ├── useGateway.ts
│   │   │   ├── useWebSocket.ts
│   │   │   └── useFileEditor.ts
│   │   ├── context/
│   │   │   └── AppContext.tsx
│   │   ├── types/
│   │   │   └── index.ts               # Shared TypeScript types
│   │   └── styles/
│   │       └── globals.css             # Tailwind imports + custom
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── .eslintrc.cjs
├── Makefile                            # Top-level dev/build/test commands
├── README.md
├── PLAN.md                             # This file
└── .gitignore
```

---

## 5. API Specification

### 5.1 Agents

```
GET    /api/agents                          → AgentListResponse
GET    /api/agents/{agent_id}               → AgentDetailResponse
GET    /api/agents/{agent_id}/files         → FileListResponse
GET    /api/agents/{agent_id}/files/{path}  → FileContentResponse
PUT    /api/agents/{agent_id}/files/{path}  → SaveResponse
DELETE /api/agents/{agent_id}/files/{path}  → DeleteResponse
GET    /api/agents/{agent_id}/sessions      → SessionListResponse
GET    /api/agents/{agent_id}/memory        → MemoryListResponse
```

**Agent Discovery Logic:**
1. Scan `~/.openclaw/agents/` for agent directories
2. Read `openclaw.json → agents` for config (model, workspace, tools, etc.)
3. For each agent, scan its workspace for known files (AGENTS.md, SOUL.md, etc.)
4. Check `~/.openclaw/sessions/sessions.json` for last activity timestamp
5. The "main" agent uses `~/.openclaw/workspace/` (not agents/main/)

**AgentListResponse:**
```json
{
  "agents": [
    {
      "id": "main",
      "name": "COS",
      "model": "anthropic/claude-opus-4-6",
      "workspace": "/Users/miller/.openclaw/workspace",
      "files": ["AGENTS.md", "SOUL.md", "IDENTITY.md", "USER.md", "TOOLS.md", "MEMORY.md", "ACTIVE.md", "HEARTBEAT.md"],
      "lastActivity": "2026-02-25T05:54:00Z",
      "sessionCount": 42,
      "status": "active"
    },
    {
      "id": "coder",
      "name": "Coder",
      "model": "anthropic/claude-sonnet-4-6",
      "workspace": "/Users/miller/.openclaw/workspace-coder",
      "files": ["AGENTS.md", "SOUL.md", "IDENTITY.md", "USER.md", "TOOLS.md"],
      "lastActivity": "2026-02-24T22:50:00Z",
      "sessionCount": 15,
      "status": "idle"
    }
  ]
}
```

### 5.2 Config

```
GET    /api/config                          → Full openclaw.json
GET    /api/config/{section}                → Section of config (e.g., "agents", "models", "cron")
PUT    /api/config                          → Save full config
PUT    /api/config/{section}                → Save section only
POST   /api/config/validate                 → Validate without saving
```

**Safety:** Before writing openclaw.json, always:
1. Create backup at `~/.openclaw/openclaw.json.bak.{timestamp}`
2. Validate JSON structure
3. Write atomically (write to .tmp, then rename)

### 5.3 Gateway

```
GET    /api/gateway/status                  → GatewayStatusResponse
POST   /api/gateway/start                   → CommandResponse
POST   /api/gateway/stop                    → CommandResponse
POST   /api/gateway/restart                 → CommandResponse
GET    /api/gateway/logs                    → Last N lines of gateway log
WS     /ws/gateway                          → Live gateway log stream
```

**GatewayStatusResponse:**
```json
{
  "running": true,
  "pid": 12345,
  "uptime": "2h 15m",
  "channels": {
    "whatsapp": { "status": "connected", "lastPing": "2026-02-25T05:50:00Z" },
    "webchat": { "status": "connected" },
    "telegram": { "status": "disconnected", "error": "auth expired" }
  },
  "sessions": { "active": 3, "total": 142 },
  "model": "anthropic/claude-opus-4-6"
}
```

### 5.4 Skills

```
GET    /api/skills                          → SkillListResponse (installed)
GET    /api/skills/{name}                   → SkillDetailResponse
GET    /api/skills/{name}/files             → Skill file listing
GET    /api/skills/{name}/files/{path}      → Skill file content
GET    /api/skills/available                → ClawHub search results
POST   /api/skills/install                  → Install from ClawHub
```

**Skill Discovery:**
1. Workspace skills: `~/.openclaw/workspace/skills/*/SKILL.md`
2. Bundled skills: `/opt/homebrew/lib/node_modules/openclaw/skills/*/SKILL.md`
3. Per-agent skills: `~/.openclaw/workspace-{agent}/skills/*/SKILL.md`

### 5.5 Sessions

```
GET    /api/sessions                        → SessionListResponse
GET    /api/sessions/{key}                  → SessionDetailResponse
GET    /api/sessions/{key}/messages         → MessageListResponse (paginated)
```

### 5.6 Memory

```
GET    /api/memory/{agent_id}               → List memory files
GET    /api/memory/{agent_id}/{filename}    → Memory file content
PUT    /api/memory/{agent_id}/{filename}    → Update memory file
GET    /api/memory/{agent_id}/search?q=     → Search memory (if search index available)
```

### 5.7 Cron

```
GET    /api/cron                            → CronJobListResponse
POST   /api/cron                            → Create cron job
PUT    /api/cron/{id}                       → Update cron job
DELETE /api/cron/{id}                       → Delete cron job
```

### 5.8 Files (Generic)

```
GET    /api/files/tree?root={path}          → Directory tree
GET    /api/files/read?path={path}          → File content
PUT    /api/files/write                     → Write file content
POST   /api/files/diff                      → Diff two versions
```

**Security:** All file operations are sandboxed to `~/.openclaw/` and agent workspaces. Path traversal blocked. No access outside OpenClaw directories.

---

## 6. Frontend Pages

### 6.1 Dashboard (Fleet Overview)
- Grid of agent cards (name, model badge, status dot, last active, file count)
- Gateway status banner at top (green/red with uptime)
- Quick stats: total agents, active sessions, installed skills
- Click agent card → Agent Detail page

### 6.2 Agent Detail
- Header: agent name, model, workspace path
- Tab bar: Files | Sessions | Memory | Config
- **Files tab:** File tree on left, Monaco editor on right, save button, multi-tab support
- **Sessions tab:** List of recent sessions with timestamps, click to expand messages
- **Memory tab:** Daily logs + MEMORY.md browser with search
- **Config tab:** This agent's section from openclaw.json (visual + raw JSON)

### 6.3 Editor (Full Screen)
- Full-screen Monaco editor with file tree sidebar
- Multi-file tabs (like VS Code)
- Can open any file from any agent workspace
- Syntax highlighting: Markdown, JSON, Python, YAML, TypeScript
- Save with Cmd+S
- Diff view toggle

### 6.4 Config Manager
- Accordion sections for each openclaw.json top-level key
- Visual form fields for common settings (model, fallbacks, workspace path, etc.)
- Raw JSON toggle per section
- "Save" creates backup first, then writes
- Validation errors shown inline
- "Restart Gateway" button after config change

### 6.5 Skills Browser
- Grid of installed skill cards (name, description, location)
- Click to see SKILL.md content + all skill files
- "Available" tab searches ClawHub
- Install button for available skills

### 6.6 Session Viewer
- Filterable list of sessions (by agent, channel, date range)
- Click session → conversation view (user/assistant messages with timestamps)
- Search across all sessions

### 6.7 Gateway Controls
- Status panel: running/stopped, PID, uptime
- Channel status cards (WhatsApp, Telegram, webchat, etc.)
- Start/Stop/Restart buttons
- Live log viewer (WebSocket-fed, auto-scroll, max 500 lines)

---

## 7. Design System

### Colors (matches MRM Advisors palette — professional, dark-mode-first)
```
--bg-primary:    #0f1219    (near-black)
--bg-secondary:  #1a1f2e    (dark navy)
--bg-card:       #232936    (card surface)
--bg-hover:      #2d3548    (hover state)
--border:        #333d52    (subtle borders)
--text-primary:  #e8eaf0    (near-white)
--text-secondary:#8b95a8    (muted)
--accent:        #6366f1    (indigo — primary actions)
--accent-hover:  #818cf8    (lighter indigo)
--success:       #22c55e    (green)
--warning:       #f59e0b    (amber)
--danger:        #ef4444    (red)
--info:          #3b82f6    (blue)
```

### Typography
- Font: Inter (system font stack fallback)
- Monospace: JetBrains Mono (for code/editor)
- Base size: 14px (dashboard density)

### Component Style
- Rounded corners (8px cards, 6px buttons)
- Subtle shadows (no heavy box-shadow)
- Status dots: colored circles (green=active, amber=idle, red=error, gray=offline)
- Badges for models: colored pills with model name
- Toast notifications for save/error/success

---

## 8. Security

- **Bind to 127.0.0.1 only** — not 0.0.0.0
- **No authentication for MVP** — localhost-only makes auth unnecessary
- **File sandboxing** — all paths validated against allowlist:
  - `~/.openclaw/` (read/write)
  - `/opt/homebrew/lib/node_modules/openclaw/` (read-only)
  - Agent workspaces matching `~/.openclaw/workspace*` (read/write)
- **Path traversal protection** — resolve symlinks, reject `..` 
- **Config backup** — every write to openclaw.json creates timestamped backup
- **No secrets in API responses** — redact API keys, tokens from config responses
- **Future: bearer token** — add `Authorization: Bearer <token>` header if remote access needed

---

## 9. Development Workflow

```bash
# First time setup
make setup          # Creates venv, installs deps, sets up frontend

# Development (starts both servers with hot reload)
make dev            # Backend on :8400, Frontend on :5173

# Individual servers
make backend        # uvicorn with --reload
make frontend       # vite dev server

# Testing
make test           # Run all tests
make test-backend   # pytest only
make test-frontend  # vitest only

# Production build
make build          # Builds frontend, copies to backend/static
make serve          # Serves production build from FastAPI
```

---

## 10. MVP Scope (Phase 1)

**In scope:**
- [ ] Fleet dashboard with agent cards
- [ ] Agent detail page with file editor (Monaco)
- [ ] File tree + multi-tab editing
- [ ] openclaw.json config editor (visual + raw)
- [ ] Gateway status + start/stop/restart
- [ ] Dark theme
- [ ] WebSocket live gateway status

**Out of scope (Phase 2+):**
- [ ] Session viewer / conversation history
- [ ] Memory explorer / search
- [ ] Skills browser + ClawHub install
- [ ] Cron manager
- [ ] Diff view in editor
- [ ] Bulk agent operations
- [ ] Agent creation wizard
- [ ] Mobile responsive (desktop-only for MVP)

---

## 11. Agent Assignments

| Agent | Role | Scope |
|-------|------|-------|
| **Planner** (MiniMax-M2.5) | Detailed task breakdown + API contracts | Pre-build, creates implementation tickets |
| **Backend** (Sonnet) | FastAPI app, all routers, services, models | `backend/` directory |
| **Frontend** (Sonnet) | React app, all components, pages, styling | `frontend/` directory |
| **Overseer** (Opus) | Monitors progress, resolves integration issues | Coordinates backend ↔ frontend contracts |
| **Tester** (MiniMax-M2.5) | Writes tests, validates endpoints, UI smoke tests | `backend/tests/` + `frontend/src/**/*.test.ts` |
| **Reviewer** (Opus) | Code review, architecture critique, security audit | Reviews all PRs/outputs before merge |

### Sequencing
```
Phase 0: Planner creates detailed spec → Reviewer critiques → COS finalizes
Phase 1: Backend + Frontend start in parallel (Overseer monitors)
Phase 2: Tester writes tests as endpoints land
Phase 3: Reviewer does final pass
Phase 4: COS integration test + deployment
```

---

## 12. Success Criteria

1. Can view all 30+ agents in a grid with status indicators
2. Can open and edit any agent's AGENTS.md/SOUL.md/etc. in Monaco
3. Can edit openclaw.json visually with section-level saves
4. Can start/stop/restart gateway from the UI
5. Page loads in <500ms, file saves in <200ms
6. No file corruption — atomic writes with backups
7. Works in Chrome and Safari on macOS
