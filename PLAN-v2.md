# OpenClaw Dashboard — Technical Plan v2
_Version: 2.0 | Author: COS | Date: 2026-02-25_
_Incorporates all 12 recommendations from architecture review._

## 1. Overview

A standalone web application for managing OpenClaw's multi-agent ecosystem at scale. Personal-use only (single user, localhost). Reads and writes the same files OpenClaw uses — no database, no duplication, no conflicts with OpenClaw updates.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────┐
│                   Browser (localhost:5173)        │
│  React + TypeScript + Tailwind + Monaco (lazy)   │
│  Vite dev server (proxies /api → :8400)          │
└──────────────────┬──────────────────────────────┘
                   │ HTTP + WebSocket
┌──────────────────▼──────────────────────────────┐
│              FastAPI Backend (:8400)              │
│  Python 3.12+ | uvicorn | pydantic v2           │
│  Host validation middleware (R5)                 │
│  ETag/If-Match concurrency control (R7)          │
│                                                  │
│  ┌─────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Agents  │ │  Config  │ │    Gateway       │  │
│  │ Router  │ │  Router  │ │    Router        │  │
│  └────┬────┘ └────┬─────┘ └───────┬──────────┘  │
│       │           │               │              │
│  ┌────▼───────────▼───────────────▼──────────┐   │
│  │         File System Layer                 │   │
│  │  Path sandboxing + symlink resolution     │   │
│  │  ~/.openclaw/ (read/write)                │   │
│  │  /opt/homebrew/.../openclaw/ (read-only)  │   │
│  └───────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

### Why No Database
OpenClaw is file-driven. Adding a database means syncing two sources of truth. We read/write files directly. OpenClaw picks up changes immediately.

---

## 3. Technology Stack

### Backend
- **Runtime:** Python 3.12+
- **Framework:** FastAPI 0.115+
- **Server:** uvicorn with auto-reload in dev
- **Validation:** Pydantic v2 (with `json_schema_extra` examples on all models)
- **Subprocess:** `asyncio.create_subprocess_exec` ONLY — never `_shell` (R6)
- **Logging:** `structlog` with JSON output, log every file write
- **Rate limiting:** `slowapi` — 1 config write/sec, 1 gateway cmd/5sec
- **Dependencies:** fastapi, uvicorn, pydantic, watchfiles, python-dotenv, aiofiles, structlog, slowapi

### Frontend
- **Build tool:** Vite 6+
- **Framework:** React 19 + TypeScript 5.x
- **Styling:** Tailwind CSS v4
- **Editor:** @monaco-editor/react — LAZY LOADED (R4)
- **State:** Zustand with selectors (R3) — NOT single React context
- **Icons:** lucide-react
- **HTTP:** Built-in fetch with typed wrapper
- **Routing:** react-router-dom v7
- **Types:** Auto-generated from OpenAPI spec via `openapi-typescript` (R10)

### Type Contract (R10)
```bash
# After any backend model change:
make types
# Runs: npx openapi-typescript http://localhost:8400/openapi.json -o frontend/src/types/generated.ts
```
The Overseer agent MUST run `make types` after any backend model change.

---

## 4. Directory Structure

```
openclaw-dashboard/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app, CORS, lifespan, startup validation (R12)
│   │   ├── config.py               # Settings (OPENCLAW_HOME, etc.)
│   │   ├── dependencies.py         # Common deps
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── host_validation.py  # DNS rebinding protection (R5)
│   │   │   └── error_handler.py    # Global exception → error envelope
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── agents.py           # /api/agents/*
│   │   │   ├── config.py           # /api/config/*
│   │   │   ├── gateway.py          # /api/gateway/*
│   │   │   └── health.py           # /api/health
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   ├── config.py
│   │   │   ├── gateway.py
│   │   │   └── common.py           # ErrorResponse envelope, ETag types
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── agent_service.py    # Agent discovery + resolve_agent_workspace() (R1.4)
│   │   │   ├── config_service.py   # openclaw.json read/write with backup rotation
│   │   │   ├── gateway_service.py  # CLI wrapper — exec only, enum-validated actions (R6)
│   │   │   └── file_service.py     # Sandboxed read/write with ETags (R7)
│   │   └── websocket/
│   │       ├── __init__.py
│   │       └── live.py             # WebSocket with defined protocol (R11)
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py             # mock_openclaw_home fixture
│   │   ├── test_agents.py
│   │   ├── test_config.py
│   │   ├── test_gateway.py
│   │   ├── test_files.py
│   │   └── test_security.py        # Symlink, path traversal, Host validation tests
│   ├── pyproject.toml
│   └── Makefile
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   ├── api/
│   │   │   ├── client.ts           # Fetch wrapper — parses error envelope, handles ETags
│   │   │   ├── agents.ts
│   │   │   ├── config.ts
│   │   │   └── gateway.ts
│   │   ├── stores/                  # Zustand stores (R3)
│   │   │   ├── agentStore.ts
│   │   │   ├── editorStore.ts
│   │   │   ├── gatewayStore.ts
│   │   │   ├── configStore.ts
│   │   │   └── toastStore.ts
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   └── Layout.tsx
│   │   │   ├── agents/
│   │   │   │   ├── AgentCard.tsx
│   │   │   │   ├── AgentGrid.tsx
│   │   │   │   └── AgentDetail.tsx
│   │   │   ├── editor/
│   │   │   │   └── FileEditor.tsx  # Single-file Monaco editor (R8)
│   │   │   ├── config/
│   │   │   │   └── ConfigEditor.tsx # Monaco for JSON (R9)
│   │   │   ├── gateway/
│   │   │   │   └── GatewayPanel.tsx
│   │   │   └── common/
│   │   │       ├── Badge.tsx
│   │   │       ├── Button.tsx
│   │   │       ├── Card.tsx
│   │   │       ├── Modal.tsx
│   │   │       ├── Toast.tsx
│   │   │       ├── ErrorBoundary.tsx
│   │   │       └── Spinner.tsx
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── AgentPage.tsx
│   │   │   ├── EditorPage.tsx      # Lazy-loaded (R4)
│   │   │   ├── ConfigPage.tsx
│   │   │   └── GatewayPage.tsx
│   │   ├── hooks/
│   │   │   ├── useAgents.ts
│   │   │   ├── useGateway.ts
│   │   │   └── useWebSocket.ts     # With reconnection + backoff
│   │   ├── types/
│   │   │   ├── generated.ts        # Auto-generated from OpenAPI (R10)
│   │   │   └── index.ts            # Re-exports + any manual types
│   │   └── styles/
│   │       └── globals.css
│   ├── index.html
│   ├── vite.config.ts              # Proxy /api→:8400, /ws→:8400
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
├── Makefile                         # Top-level: dev, build, test, types, serve
├── README.md
├── PLAN-v2.md
├── REVIEW.md
└── .gitignore
```

---

## 5. API Specification (MVP Only)

### 5.0 Standard Error Envelope (R2.3)

All error responses use this shape:
```json
{
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "File not found: SOUL.md",
    "detail": {"agent_id": "coder", "path": "SOUL.md"},
    "timestamp": "2026-02-25T06:00:00Z"
  }
}
```

Error code mapping:
- `FileNotFoundError` → 404 / `FILE_NOT_FOUND`
- `PermissionError` → 403 / `ACCESS_DENIED`
- `JSONDecodeError` → 422 / `INVALID_JSON`
- `ETag mismatch` → 409 / `CONFLICT`
- `Rate limited` → 429 / `RATE_LIMITED`
- `Subprocess timeout` → 504 / `GATEWAY_TIMEOUT`
- Everything else → 500 / `INTERNAL_ERROR`

### 5.1 Health

```
GET /api/health → HealthResponse
```
```json
{
  "status": "ok",
  "version": "1.0.0",
  "openclaw_home": "/Users/miller/.openclaw",
  "subsystems": {
    "config": true,
    "workspaces": true,
    "gateway_cli": true,
    "sessions": true
  }
}
```

### 5.2 Agents

```
GET    /api/agents                              → AgentListResponse
GET    /api/agents/{agent_id}                   → AgentDetailResponse
GET    /api/agents/{agent_id}/files?path=X      → FileContentResponse (includes ETag header)
PUT    /api/agents/{agent_id}/files?path=X      → SaveResponse (requires If-Match header)
```

**File path via query parameter (R1).** No generic file endpoints (R2).

**Agent Discovery:**
1. Scan `~/.openclaw/agents/` for agent directories
2. Read `openclaw.json → agents` for config
3. For each agent, call `resolve_agent_workspace(agent_id)` (R1.4)
4. The "main" agent → `~/.openclaw/workspace/` (encapsulated in ONE function)
5. Scan workspace for known files
6. Check sessions.json for last activity

**ETag flow (R7):**
- GET returns `ETag: "{mtime}:{size}"` header
- PUT requires `If-Match: "{mtime}:{size}"` header
- If file changed since GET → 409 Conflict with current ETag in response
- Frontend shows "File changed externally. Reload?" dialog

**AgentDetailResponse:**
```json
{
  "id": "main",
  "name": "COS",
  "model": "anthropic/claude-opus-4-6",
  "workspace": "/Users/miller/.openclaw/workspace",
  "files": [
    {"name": "AGENTS.md", "size": 12400, "mtime": "2026-02-25T05:53:00Z"},
    {"name": "SOUL.md", "size": 3800, "mtime": "2026-02-25T05:55:00Z"}
  ],
  "lastActivity": "2026-02-25T05:54:00Z",
  "status": "active"
}
```

**FileContentResponse:**
```json
{
  "path": "AGENTS.md",
  "content": "# AGENTS.md - Your Workspace\n...",
  "size": 12400,
  "mtime": "2026-02-25T05:53:00Z",
  "language": "markdown"
}
```
Plus `ETag` header.

### 5.3 Config

```
GET    /api/config                              → Full openclaw.json (secrets redacted)
PUT    /api/config                              → Save full config (requires If-Match)
POST   /api/config/validate                     → Validate JSON without saving
```

**Safety on write:**
1. Validate JSON structure
2. Check If-Match ETag
3. Create backup: `openclaw.json.bak.{timestamp}` (keep max 10, prune older)
4. Write atomically (write .tmp → rename)

**Secret redaction:** Replace values matching `*KEY*`, `*TOKEN*`, `*SECRET*`, `*PASSWORD*` patterns with `"__REDACTED__"`. On PUT, if a value is `"__REDACTED__"`, preserve the original value from the existing file.

### 5.4 Gateway

```
GET    /api/gateway/status                      → GatewayStatusResponse
POST   /api/gateway/{action}                    → CommandResponse
```

**Action enum:** `start | stop | restart` — validated server-side, reject anything else (R6).

**Subprocess rules:**
- `create_subprocess_exec("openclaw", "gateway", action)` — NEVER shell (R6)
- 10-second timeout on all calls
- If parsing fails → degraded response: `{"running": "unknown", "error": "..."}`

**GatewayStatusResponse:**
```json
{
  "running": true,
  "pid": 12345,
  "uptime": "2h 15m",
  "channels": {},
  "error": null
}
```

### 5.5 WebSocket Protocol (R11)

```
WS /ws/live
```

**Message envelope:**
```json
{
  "type": "gateway_status" | "file_changed" | "error" | "ping",
  "timestamp": "2026-02-25T06:00:00Z",
  "payload": { ... }
}
```

**Event types:**
- `gateway_status` — periodic gateway health (every 10s)
- `file_changed` — workspace file modified (debounced 500ms)
- `error` — server-side error notification
- `ping` — keepalive (every 30s)

**Client behavior:**
- On message type `ping` → respond with `{"type": "pong"}`
- On connection drop → reconnect with exponential backoff (1s → 2s → 4s → ... → 30s max)
- Show "Reconnecting..." indicator in UI during backoff

**File watching scope (R1.2):**
Watch ONLY specific files per agent (not recursive):
- `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, `MEMORY.md`, `ACTIVE.md`, `HEARTBEAT.md`
- `~/.openclaw/openclaw.json`
- `~/.openclaw/sessions/sessions.json`
- Debounce: 500ms

---

## 6. Frontend Pages (MVP)

### 6.1 Dashboard (Fleet Overview)
- Grid of agent cards: name, model badge, status dot, last active, file count
- Gateway status banner at top
- Quick stats: total agents, active sessions
- Click card → Agent Detail
- **Data:** Poll `GET /api/agents` every 5 seconds (no WebSocket for MVP agent list)

### 6.2 Agent Detail
- Header: name, model, workspace path
- Flat file list (not tree) with name, size, last modified (R8)
- Click file → opens in EditorPage
- Back button to dashboard

### 6.3 Editor Page (Lazy-loaded) (R4, R8)
- Single-file Monaco editor (no tabs, no file tree)
- File path shown in header
- Save button + Cmd+S binding
- Dirty indicator (dot in title)
- ETag conflict handling: if 409 → show "File changed externally" dialog with options: Reload / Force Save / Diff (Phase 2)
- `beforeunload` warning if dirty
- Error boundary around Monaco (R4.5)

### 6.4 Config Page (R9)
- Monaco editor showing `openclaw.json` with JSON language mode
- Syntax highlighting, validation, formatting
- Save button with ETag conflict handling
- "Restart Gateway" button after save
- NOT a visual form editor — that's Phase 2

### 6.5 Gateway Page
- Status card: running/stopped, PID, uptime
- Start / Stop / Restart buttons
- Channel status if available
- Last command output display

---

## 7. Design System

### Colors (dark-mode-first)
```css
--bg-primary:    #0f1219;
--bg-secondary:  #1a1f2e;
--bg-card:       #232936;
--bg-hover:      #2d3548;
--border:        #333d52;
--text-primary:  #e8eaf0;
--text-secondary:#8b95a8;
--accent:        #6366f1;
--accent-hover:  #818cf8;
--success:       #22c55e;
--warning:       #f59e0b;
--danger:        #ef4444;
--info:          #3b82f6;
```

### Typography
- UI: Inter (system stack fallback)
- Code: JetBrains Mono
- Base: 14px

### Accessibility (minimum for MVP)
- All buttons/links have accessible names
- Status dots include `aria-label` (not just color)
- Modal focus traps
- Keyboard-navigable sidebar

---

## 8. Security

- **Bind to 127.0.0.1:8400 only**
- **Host header validation middleware** (R5) — reject if Host ≠ `localhost` / `127.0.0.1`
- **CORS:** `http://localhost:5173` in dev, same-origin in prod — NEVER `*`
- **File sandboxing:** `Path.resolve()` THEN check against allowlist (R3.3)
- **Subprocess:** `create_subprocess_exec` with argument lists ONLY (R6)
- **ETag concurrency** on all file writes (R7)
- **Config backups:** max 10, auto-prune older
- **Rate limiting:** 1 config write/sec, 1 gateway cmd/5sec
- **No auth for MVP** — localhost-only. Phase 2: optional bearer token

---

## 9. Error Handling

### Backend
- Global exception handler: all exceptions → standard error envelope
- Map: FileNotFoundError→404, PermissionError→403, JSONDecodeError→422, ETag mismatch→409
- Log all 500s with full traceback via structlog
- Log every file write: who/what/when/bytes
- All subprocess calls: 10s timeout, parse defensively

### Frontend
- `client.ts` fetch wrapper: parse error envelope, dispatch to toast
- Network errors → "Backend unreachable" banner (not toast)
- Error boundaries around: Monaco editor, each page route, gateway panel
- `beforeunload` on dirty editor state

### Graceful Degradation
- No agents found → empty dashboard with "No agents configured" message
- Agent workspace missing → show agent with "Workspace not found" badge
- Config malformed → show raw text with error banner
- Gateway CLI missing → `{"installed": false}` — disable gateway controls
- Subprocess hangs → timeout after 10s, return degraded response

---

## 10. Testing Strategy

### Backend (pytest)
```python
@pytest.fixture
def mock_openclaw_home(tmp_path):
    """Creates realistic ~/.openclaw/ in temp dir."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "AGENTS.md").write_text("# Agents")
    (workspace / "SOUL.md").write_text("# Soul")
    agents = tmp_path / "agents" / "coder"
    agents.mkdir(parents=True)
    coder_ws = tmp_path / "workspace-coder"
    coder_ws.mkdir()
    (coder_ws / "AGENTS.md").write_text("# Coder")
    config = {"agents": {"defaults": {"workspace": str(workspace)}}}
    (tmp_path / "openclaw.json").write_text(json.dumps(config))
    return tmp_path
```

**Tests must cover:**
- Agent list returns main + configured agents
- Main agent workspace resolution special case
- File read/write with ETags
- ETag conflict returns 409
- Path traversal blocked
- Symlink outside sandbox blocked
- Host header validation rejects non-localhost
- Gateway action enum validation
- Config backup rotation (max 10)
- Subprocess timeout handling

**Coverage target:** 80%+ on services

### Frontend (vitest)
- Component rendering tests for AgentCard, AgentGrid, GatewayPanel
- Store tests for Zustand stores
- API client tests with mocked fetch
- Error boundary tests

---

## 11. Development Workflow

```bash
make setup          # Creates venv, npm install, installs all deps
make dev            # Starts backend (:8400) + frontend (:5173)
make backend        # uvicorn --reload
make frontend       # vite dev
make types          # Generate TS types from OpenAPI schema (R10)
make test           # Run all tests
make test-backend   # pytest
make test-frontend  # vitest
make build          # Build frontend, copy to backend/static
make serve          # Serve production build from FastAPI
make lint           # ruff + eslint
```

---

## 12. MVP Scope

### ✅ In Scope
- Fleet dashboard with agent cards + status
- Agent detail with flat file list
- Single-file Monaco editor with save + ETag conflicts
- Config editor (Monaco for JSON + validation)
- Gateway status + start/stop/restart
- Dark theme
- Health check endpoint
- Host header validation + file sandboxing
- Standard error envelope + error boundaries
- TypeScript types auto-generated from OpenAPI
- 80%+ backend test coverage

### 📋 Phase 2
- Multi-tab file editing
- File tree sidebar
- Visual config editor (forms for common settings)
- WebSocket live updates (replace 5s polling)
- Session viewer / conversation history
- Memory explorer / search
- Skills browser + ClawHub install
- Cron manager
- Diff view in editor
- Agent creation wizard
- Mobile responsive
- `launchctl` plist for auto-start
- Accessibility WCAG 2.1 AA

---

## 13. Agent Assignments

| Agent | Model | Role | Scope |
|-------|-------|------|-------|
| **Planner** | MiniMax-M2.5 | Task breakdown, API contracts, file stubs | Creates implementation checklist + skeleton files |
| **Backend** | Sonnet | FastAPI app — all routers, services, models, middleware | `backend/` directory |
| **Frontend** | Sonnet | React app — all components, pages, stores, styling | `frontend/` directory |
| **Overseer** | Opus | Integration monitor, type generation, conflict resolution | Runs `make types`, checks contracts, unblocks |
| **Tester** | MiniMax-M2.5 | Tests + validation | `backend/tests/` + `frontend/**/*.test.ts` |
| **Reviewer** | Opus | Final code review, security audit | Reviews all outputs before declaring done |

### Sequencing
```
Phase 0: Planner → creates skeleton + checklist (solo)
Phase 1: Backend + Frontend in parallel (Overseer monitors, runs make types)
Phase 2: Tester writes + runs tests
Phase 3: Reviewer final pass
Phase 4: COS integration test + ship
```

### Concurrency: Backend + Frontend + Overseer = 3 (within limit). Tester + Reviewer sequential after.

---

## 14. Success Criteria

1. View all 30+ agents in a grid with status indicators
2. Open and edit any agent file in Monaco with save
3. Edit openclaw.json with validation and backup
4. Start/stop/restart gateway from the UI
5. Page load <500ms (non-editor pages), <2s (editor page, first load)
6. No data loss — ETags prevent overwrite conflicts
7. No security holes — Host validation, sandboxing, exec-only subprocess
8. 80%+ backend test coverage
9. Works in Chrome + Safari on macOS
