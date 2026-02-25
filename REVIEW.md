# OpenClaw Dashboard — Architecture Review
_Reviewer: Plan Reviewer (Senior Architect) | Date: 2026-02-25_
_Verdict: **Proceed with significant revisions.** The plan has a solid high-level vision but critical gaps in concurrency, security, and scope estimation that will cause rework if not addressed before agents start building._

---

## 1. Architecture Gaps

### 1.1 No Concurrency Control on File Writes (Critical)

**Section 5.1, 5.2, 5.8 — all PUT endpoints.**

The plan mentions atomic writes for `openclaw.json` only (§5.2: "write to .tmp, then rename"). Every other file write — agent workspace files via `PUT /api/agents/{agent_id}/files/{path}` and generic `PUT /api/files/write` — has no concurrency strategy.

**The failure scenario:** Miller opens `AGENTS.md` in Monaco. COS's heartbeat fires and writes to the same file 3 seconds later via OpenClaw. Miller hits Cmd+S. COS's changes are silently obliterated. No conflict detection, no warning, no merge.

**Recommendation:** Add optimistic concurrency control using `If-Match` / `ETag` headers. On every `GET`, return the file's mtime + size as an ETag. On `PUT`, require `If-Match` with the ETag from the `GET`. Return `409 Conflict` if the file changed since it was read. This is 20 lines of code in the service layer and prevents the most common data loss scenario.

### 1.2 File Watching is Underspecified

**Section 3 (Backend):** "watchfiles (for live reload notifications)" — watching what? How many watchers?

With 30+ agents, each with a workspace containing `memory/`, `skills/`, `reference/`, you're looking at 150+ directories. macOS kqueue has a per-process file descriptor limit (default ~10,240), but each watched directory and file consumes one. More critically, `watchfiles` uses a Rust-based watcher that by default does recursive watching — meaning you'll watch every file in every workspace recursively.

**Problems:**
1. A runaway agent creating temp files in a workspace will generate a flood of WebSocket events
2. Large `reference/` directories with hundreds of files will spike watcher overhead
3. No mention of debouncing — a single `git pull` touching 50 files will fire 50 events

**Recommendation:** Watch only specific files, not entire directory trees. Watch: `~/.openclaw/openclaw.json`, `~/.openclaw/sessions/sessions.json`, and each agent's `AGENTS.md`, `SOUL.md`, `ACTIVE.md`, `MEMORY.md`. That's ~6 files per agent × 30 agents = ~180 files. Debounce events by 500ms. Do NOT recursively watch workspaces.

### 1.3 No In-Memory Cache or ETag Strategy

**Section 5.1 — Agent Discovery Logic (steps 1-5).**

Every call to `GET /api/agents` will:
1. `listdir` on `~/.openclaw/agents/`
2. Read + parse `openclaw.json` (could be 500+ lines)
3. For each of 30+ agents, `listdir` on their workspace
4. Read + parse `sessions.json`
5. Compute status for each agent

That's ~65 filesystem operations per dashboard load. At the "page loads in <500ms" target (§12), this is tight even on an M1 with SSD.

**Recommendation:** Add a simple TTL cache (e.g., `cachetools.TTLCache` or a manual dict with timestamps). Cache agent list for 5 seconds. Invalidate on file watcher events for `openclaw.json` or agent directory changes. Return `Last-Modified` header so the frontend can use conditional requests.

### 1.4 Main Agent Special-Casing Will Leak Everywhere

**Section 5.1:** "The 'main' agent uses `~/.openclaw/workspace/` (not `agents/main/`)."

This means `agent_service.py` needs an `if agent_id == "main"` branch in every path-resolution function. This will propagate to the frontend (special URL handling), the file service (different base paths), and the config service (main agent's config is the top-level, not under `agents.main`).

**Recommendation:** Encapsulate this in a single `resolve_agent_workspace(agent_id: str) -> Path` function in `agent_service.py` and document it as THE ONLY place this logic lives. Add a test specifically for the main agent path resolution. Every other service must call this function — never construct agent paths manually.

### 1.5 Missing Health Check

No `/api/health` endpoint. This is a one-liner in FastAPI but critical for:
- Vite proxy knowing the backend is up
- Any future process supervisor
- Frontend showing "backend disconnected" state

**Recommendation:** Add `GET /api/health → {"status": "ok", "version": "1.0.0", "openclaw_home": "~/.openclaw"}`.

### 1.6 No Startup Validation

What happens when the dashboard starts and:
- `~/.openclaw/` doesn't exist?
- `openclaw.json` is malformed?
- No agents are configured?
- The `openclaw` CLI isn't in `$PATH`?

The plan has no startup validation or graceful error states for any of these.

**Recommendation:** Add a startup check in `main.py`'s lifespan handler that validates: (1) OPENCLAW_HOME exists, (2) `openclaw.json` is valid JSON, (3) at least the main workspace exists. Log warnings for anything missing. Return a structured error from `/api/health` if the environment is broken so the frontend can show an appropriate screen.

---

## 2. API Design Issues

### 2.1 File Path as URL Path Parameter is Broken (Critical)

**Section 5.1:** `GET /api/agents/{agent_id}/files/{path}`

If the file is `memory/2026-02-25.md`, the URL becomes `/api/agents/main/files/memory/2026-02-25.md`. FastAPI will try to match `memory` as a route segment, `2026-02-25.md` as another. This requires Starlette's `path` converter (`{path:path}`), which works but has edge cases with URL-encoded slashes, query parameters, and characters like `#`, `?`, `%`.

**Recommendation:** Use a query parameter instead: `GET /api/agents/{agent_id}/files?path=memory/2026-02-25.md`. This is unambiguous, doesn't fight URL routing, and handles special characters naturally. Apply this to PUT and DELETE as well.

### 2.2 Inconsistent File Access Patterns

The plan defines TWO file access APIs:
1. `/api/agents/{agent_id}/files/{path}` — agent-scoped (§5.1)
2. `/api/files/read?path={path}` — generic, any path (§5.8)

These overlap. An agent's file can be accessed via either endpoint. This creates confusion about which to use, different auth/sandboxing rules, and duplicate code paths.

**Recommendation:** Delete the generic `/api/files/*` endpoints entirely. All file access goes through agent-scoped routes. If you need to access a file outside an agent workspace (e.g., bundled skills), add a `/api/skills/{name}/files/{path}` route instead. One file access pattern, one sandboxing implementation.

### 2.3 No Standard Error Envelope

No error response schema is defined anywhere. What does a 404 look like? A validation error? A file permission error?

**Recommendation:** Define a standard error response:
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
Use FastAPI exception handlers to enforce this globally. The frontend's `client.ts` fetch wrapper should expect and parse this shape.

### 2.4 Pagination Not Specified for Sessions

**Section 5.5:** `GET /api/sessions/{key}/messages → MessageListResponse (paginated)` — paginated HOW?

- Cursor-based or offset-based?
- Default page size?
- Response envelope with `total`, `hasMore`, `nextCursor`?
- Session JSONL files can be megabytes — what's the max response size?

**Recommendation:** Use cursor-based pagination (JSONL line offset). Default 50 messages. Response:
```json
{
  "messages": [...],
  "cursor": "line:2450",
  "hasMore": true,
  "total": 3200
}
```

### 2.5 DELETE and PATCH Missing or Undefined

- `DeleteResponse` (§5.1) is listed but never defined
- No PATCH support for config — can only PUT full sections
- No way to add a single cron job field without sending the entire cron config

**Recommendation:** Define `DeleteResponse` as `{"deleted": true, "path": "..."}`. Add `PATCH /api/config/{section}` with JSON Merge Patch (RFC 7396) for partial updates. This is especially important for config where a visual form toggles one field — you don't want to send the entire agents object.

### 2.6 Cron Endpoints Specified but Out of MVP Scope

**Section 5.7** fully specifies CRUD for cron jobs. **Section 10** explicitly puts cron in "Out of scope (Phase 2+)."

This is wasted specification and will confuse the Backend agent about what to build.

**Recommendation:** Move §5.7 to an appendix or label it `[PHASE 2]` clearly. Same for §5.5 (Sessions) and §5.6 (Memory) — these are all Phase 2 features with Phase 1 API specs.

---

## 3. Security Concerns

### 3.1 DNS Rebinding Attack (Critical)

**Section 8:** "Bind to 127.0.0.1 only."

Binding to localhost does NOT prevent DNS rebinding attacks. An attacker's website can set up a DNS record for `evil.com` that resolves to `127.0.0.1`. The browser makes a request to `evil.com:8400/api/config` — which hits your local FastAPI server. The request passes CORS (if `Access-Control-Allow-Origin` is misconfigured or the request is "simple") and the attacker reads your entire OpenClaw config, including API keys.

**Recommendation:** Add Host header validation middleware. Reject any request where the `Host` header is not `localhost`, `127.0.0.1`, or `localhost:8400`. This is 10 lines of middleware and closes the DNS rebinding vector completely. Example:

```python
@app.middleware("http")
async def validate_host(request: Request, call_next):
    host = request.headers.get("host", "").split(":")[0]
    if host not in ("localhost", "127.0.0.1"):
        return JSONResponse(status_code(403), {"error": "Invalid host"})
    return await call_next(request)
```

### 3.2 CORS Policy Not Specified

**Section 4:** `main.py` mentions "CORS" but the actual CORS policy is never defined.

If the policy is `Access-Control-Allow-Origin: *`, every website Miller visits can read his agent configs, API keys (if redaction fails), and workspace files.

**Recommendation:** Set CORS to `Access-Control-Allow-Origin: http://localhost:5173` in dev and remove CORS entirely in production (same-origin). Never use `*`.

### 3.3 Symlink Following Defeats Sandboxing

**Section 8:** "resolve symlinks, reject `..`"

This is contradictory. If you resolve symlinks, a symlink at `~/.openclaw/workspace/evil → /etc/` would resolve to `/etc/`, which is outside the sandbox. But you "resolved" it, so the `..` check passes.

**Recommendation:** Resolve the path to its real path via `Path.resolve()`, THEN check if the resolved path starts with an allowed prefix. The order matters:
```python
real_path = requested_path.resolve()
if not any(real_path.is_relative_to(allowed) for allowed in ALLOWED_ROOTS):
    raise PermissionError(f"Access denied: {real_path}")
```
Add explicit tests for symlinks pointing outside the sandbox.

### 3.4 Command Injection via CLI Subprocess

**Section 3 (Backend):** "asyncio.subprocess for `openclaw` CLI calls."

If `gateway_service.py` constructs commands like:
```python
await asyncio.create_subprocess_shell(f"openclaw gateway {action}")
```
And `action` comes from the API request, this is command injection.

**Recommendation:** Always use `create_subprocess_exec` (not `_shell`) with explicit argument lists:
```python
await asyncio.create_subprocess_exec("openclaw", "gateway", "start")
```
Never interpolate user input into shell strings. Validate `action` against an enum: `{"start", "stop", "restart", "status"}`.

### 3.5 Backup File Accumulation

**Section 5.2:** "Create backup at `~/.openclaw/openclaw.json.bak.{timestamp}`" on every write.

If the config page auto-saves or a user saves frequently, this creates unbounded backup files. 100 saves = 100 backup files in `~/.openclaw/`.

**Recommendation:** Keep only the last 10 backups. After writing a new backup, delete any beyond the 10 most recent. Add a cleanup step to the config write service.

### 3.6 Secrets in Workspace Files Not Addressed

**Section 8:** "redact API keys, tokens from config responses."

This handles `openclaw.json`, but agent workspace files like `TOOLS.md`, `.env`, and `reference/` files often contain API keys, passwords, and tokens. The file editor will serve these raw.

**Recommendation:** Accept this as a known risk for MVP (localhost-only). Document it in the README: "This dashboard serves workspace files as-is. Do not expose port 8400 to the network." Add a warning banner if the server is ever bound to 0.0.0.0.

---

## 4. Frontend Concerns

### 4.1 Single Context Will Cause Performance Death (Critical)

**Section 3 (Frontend):** "React context + useReducer (no Redux — too simple for this)."

This is wrong. The state this app manages includes:
- 30+ agents with status, files, last activity
- Multiple open editor tabs with content, dirty state, cursor position
- Gateway status updated every few seconds via WebSocket
- Config state (large nested object)
- Toast notifications
- WebSocket connection state

A single `AppContext` means every WebSocket gateway status update triggers a re-render of every agent card, every editor tab, and every other component consuming the context. With Monaco editors open (which are expensive to re-render), this will cause visible jank.

**Recommendation:** Split into 4-5 focused contexts:
1. `AgentContext` — agent list, selected agent
2. `EditorContext` — open tabs, active tab, dirty state
3. `GatewayContext` — gateway status, WebSocket connection
4. `ConfigContext` — config state
5. `ToastContext` — notifications

Each context only re-renders its consumers. Or use Zustand (3KB gzipped, simpler than Redux) with selectors for surgical re-renders.

### 4.2 Monaco Bundle Size vs. Performance Target Conflict

**Section 12:** "Page loads in <500ms."
**Section 3:** "@monaco-editor/react."

Monaco editor's JavaScript alone is ~2.5MB gzipped. On first load (cold cache), downloading + parsing this will take 1-3 seconds even on localhost. The 500ms target is impossible on first load with Monaco.

**Recommendation:** Either:
- (A) Lazy-load Monaco only on the EditorPage route (React.lazy + Suspense). Dashboard/agent pages load fast. Editor page takes longer but that's acceptable.
- (B) Change the success criterion to "<500ms for non-editor pages, <2s for editor page (first load)."

Option A is strongly preferred. It also reduces memory usage when the editor isn't open.

### 4.3 No Dirty State / Unsaved Changes Tracking

The plan mentions "multi-tab support" and "Save with Cmd+S" but nothing about:
- Tracking which tabs have unsaved changes
- Warning before closing a tab with unsaved content
- Warning before navigating away with unsaved content
- Visual indicator (dot/icon) on dirty tabs

**Recommendation:** Add a `modified: boolean` flag per tab in `EditorContext`. Show a dot on dirty tabs. Use `beforeunload` event to warn on page close. Warn on tab close via the close button. This is table stakes for any editor.

### 4.4 Zero Accessibility

No mention of:
- ARIA labels on interactive elements
- Keyboard navigation for the sidebar, agent grid, file tree
- Focus management when modals open/close
- Screen reader support for status indicators
- Color contrast ratios (the dark theme colors need verification)
- Skip navigation links

**Recommendation:** At minimum for MVP:
- All buttons and links must have accessible names
- Status dots need `aria-label` (not just color)
- Modal focus trap
- Keyboard-navigable sidebar

Add an "Accessibility" section to the plan with at least WCAG 2.1 Level A compliance targets.

### 4.5 No Error Boundaries

If Monaco throws an exception (which it does, especially with malformed files or memory pressure), the entire React app crashes to a white screen.

**Recommendation:** Add React error boundaries around: (1) the Monaco editor, (2) each page route, (3) the WebSocket-connected gateway panel. Each boundary shows a "Something went wrong — reload" message instead of crashing the whole app.

### 4.6 File Tree Performance

30+ agent workspaces × 10-50 files each = 300-1500 tree nodes. The file tree needs:
- Lazy loading (don't expand all directories on mount)
- Virtualization for large directories (react-window or similar)
- Expand/collapse state persistence

The plan specifies a `FileTree.tsx` component but doesn't address any of this.

**Recommendation:** Use a proven tree component like `react-arborist` (virtualized tree with keyboard nav) rather than building one from scratch. It handles virtualization, keyboard navigation, and accessibility out of the box.

### 4.7 WebSocket Reconnection Strategy Missing

**Section 3:** "Native WebSocket API."

Native WebSocket has no auto-reconnect. When the backend restarts (which happens on every code change with `--reload`), the WebSocket dies and the gateway status panel goes dark with no recovery.

**Recommendation:** Implement reconnection with exponential backoff in `useWebSocket.ts`:
- Initial retry: 1s
- Max retry: 30s
- Backoff factor: 2×
- Show "Reconnecting..." indicator in the UI
- Or use a tiny library like `reconnecting-websocket` (1KB).

---

## 5. Scope Creep Risk

### 5.1 Monaco Multi-Tab Editor is a Whole Project (High Risk)

**Section 10 (MVP):** "File tree + multi-tab editing."

Building a multi-tab code editor with:
- File tree with expand/collapse
- Tab bar with close, dirty indicators
- Cmd+S save to backend
- Syntax highlighting for 5+ languages
- Multiple files open simultaneously

...is not one checkbox item. This is the hardest frontend feature in the entire plan. VS Code itself is a Monaco app, and it took a team years. Even a stripped-down version is easily 40+ hours of frontend work.

**Recommendation:** MVP should be **single-file editor**. Click a file in the agent detail page → opens Monaco with that file → save → done. No tabs, no file tree, no multi-file. Add tabs and file tree in Phase 2. This cuts frontend complexity by ~40%.

### 5.2 Visual Config Editor is Deceptively Hard (High Risk)

**Section 6.4:** "Accordion sections for each openclaw.json top-level key. Visual form fields for common settings."

`openclaw.json` has deeply nested, heterogeneous structure. The `agents` key is a map of agent objects, each with different fields. The `models` key has fallback chains. The `cron` key has schedule expressions. Building visual form components that correctly handle every type — strings, numbers, booleans, arrays of strings, nested objects, model references — is a massive frontend effort.

**Recommendation:** For MVP, the config editor should be **Monaco editing openclaw.json directly** with validation on save. You already have Monaco — use it. Add visual form sections for the 3-4 most common settings (default model, agent model, workspace path) in Phase 2.

### 5.3 What Should Be Cut from MVP

Cutting these brings the MVP from ~3 weeks to ~1 week for the 6-agent team:

| Feature | Effort | Cut? | Replacement |
|---------|--------|------|-------------|
| Multi-tab file editing | High | ✂️ Yes | Single-file editor |
| File tree sidebar | Medium | ✂️ Yes | Flat file list in agent detail |
| Visual config editor | High | ✂️ Yes | Monaco for openclaw.json |
| WebSocket live updates | Medium | ✂️ Yes | Poll every 5s (3 lines of code) |
| Config section-level save | Medium | ✂️ Yes | Full-file save only |

### 5.4 What's Harder Than Estimated

| Feature | Estimated | Actual | Why |
|---------|-----------|--------|-----|
| Agent discovery | Simple scan | Medium | Error handling for missing/malformed files, main agent special case, session file parsing |
| Gateway start/stop | CLI wrapper | Medium | Async subprocess, timeout handling, output parsing, state polling after command |
| File sandboxing | Path check | Medium | Symlink resolution, encoding issues, race conditions (TOCTOU) |
| Dark theme | CSS | Easy | It's actually easy IF you use Tailwind's dark mode classes consistently from the start |

---

## 6. Integration Risks

### 6.1 No Shared Type Contract (Critical)

**Section 4:** Backend has `models/agent.py` (Pydantic). Frontend has `types/index.ts` (TypeScript).

These are manually maintained copies of the same types. They WILL drift. The Backend agent adds a field to `AgentDetailResponse`, the Frontend agent doesn't know, and the field is silently ignored or causes a runtime error.

**Recommendation:** Use FastAPI's automatic OpenAPI schema generation + `openapi-typescript` or `openapi-fetch` to auto-generate TypeScript types from the Pydantic models. Run this as a build step: `make types` generates `frontend/src/types/generated.ts`. The Overseer agent should enforce that types are regenerated after any backend model change.

### 6.2 WebSocket Message Protocol Undefined

**Section 5.3:** `WS /ws/gateway → Live gateway log stream`

What is the message format? Raw text lines? JSON events? Is there a message type field? What about:
- Connection handshake
- Heartbeat/ping-pong
- Error messages
- Backpressure (client can't keep up)

**Recommendation:** Define a WebSocket message envelope:
```json
{
  "type": "gateway_log" | "file_changed" | "agent_status" | "error",
  "timestamp": "2026-02-25T06:00:00Z",
  "payload": { ... }
}
```
Document this in the plan so both Backend and Frontend agents implement the same protocol.

### 6.3 CLI Output Parsing is Fragile

**Section 5.3:** Gateway status comes from `openclaw gateway status`.

The plan assumes a specific output format from the CLI, but:
- OpenClaw CLI output format isn't versioned or documented as a stable API
- Any OpenClaw update could change the output
- Stderr vs stdout handling isn't specified
- What if the CLI hangs? No timeout specified.

**Recommendation:** 
1. Set a 10-second timeout on all subprocess calls
2. Parse CLI output defensively — if parsing fails, return a degraded status: `{"running": "unknown", "error": "Could not parse CLI output"}`
3. Consider reading OpenClaw's internal files directly (PID files, config) instead of shelling out to the CLI for status

### 6.4 File Path Encoding Between Backend and Frontend

**Section 5.1, 5.8:** Paths are passed between frontend and backend in multiple ways (URL paths, query params, JSON bodies).

File paths with spaces, unicode characters, or URL-special characters (`#`, `?`, `%`, `+`) will break unless both sides agree on encoding. A file named `2026-02-25 notes.md` sent as a URL path becomes `2026-02-25%20notes.md` — does the backend decode this correctly?

**Recommendation:** Standardize: all file paths in JSON bodies and query parameters are UTF-8 strings, URL-encoded when in query params. Never put file paths in URL path segments (see §2.1). Add test cases for filenames with spaces, unicode, and special characters.

### 6.5 Dev vs. Prod Serving Differences

**Section 2 (Architecture):** In dev, Vite proxies `/api` to `:8400`. In production, FastAPI serves static files.

This means:
- Different CORS behavior (proxy = same-origin in dev, static = same-origin in prod — actually fine)
- Different WebSocket routing (Vite proxy handles WS differently than direct)
- Different error pages (Vite shows overlay, FastAPI serves raw JSON)

**Recommendation:** Document the proxy config in `vite.config.ts` explicitly. Test WebSocket connections through the Vite proxy. Add a `make prod-test` command that builds and serves the production bundle for testing.

---

## 7. Missing Requirements

### 7.1 No Error Handling Strategy

The plan has no section on error handling. Questions that need answers:

- **Backend:** Are all exceptions caught by a global handler? What format? What HTTP status codes map to what errors?
- **Frontend:** What happens when a fetch call fails? Retry? Show toast? Show error page?
- **File operations:** What if a file is locked by another process? Permission denied? Disk full?
- **CLI calls:** What if `openclaw` CLI exits with non-zero? What if it writes to stderr?

**Recommendation:** Add a "§13. Error Handling" section:
- Backend: Global exception handler returns the standard error envelope (§2.3 recommendation). Log all 500s. Map known errors (FileNotFoundError → 404, PermissionError → 403, JSONDecodeError → 422).
- Frontend: `client.ts` fetch wrapper catches errors, parses the error envelope, and dispatches to toast notifications. Network errors show a "Backend unreachable" banner.

### 7.2 No Logging Strategy

- No structured logging format
- No log level configuration
- No mention of logging file operations (audit trail for writes)
- No frontend error logging

**Recommendation:** Use Python's `structlog` or `logging` with JSON format. Log every file write (who, what path, when, bytes). Log every gateway command. Log level configurable via environment variable. Frontend: `console.error` for caught errors, consider Sentry later.

### 7.3 No Graceful Degradation

What happens when:
- Backend starts but `~/.openclaw/` has no agents? (Empty dashboard — but does it crash?)
- A specific agent's workspace is missing/deleted while the dashboard is running?
- `openclaw.json` is being written by OpenClaw at the exact moment the dashboard reads it? (Partial read)
- The gateway is not installed? (Some users might not use the gateway)

**Recommendation:** Design every service function to return a degraded response rather than throwing. `agent_service.list_agents()` returns an empty list if the directory is missing, not a 500. Gateway status returns `{"installed": false}` if the CLI isn't found. Add a "system status" indicator on the dashboard that shows which subsystems are available.

### 7.4 No Testing Strategy Beyond Directory Structure

**Section 4:** Test directories exist. **Section 9:** `make test` commands exist. But:
- How do you test file operations without touching the real `~/.openclaw/`? (Need a temp directory fixture)
- How do you test gateway commands without a running gateway? (Need to mock subprocess)
- How do you test WebSocket connections? (Need async test client)
- What's the coverage target?

**Recommendation:** Add a `conftest.py` section to the plan:
```python
@pytest.fixture
def mock_openclaw_home(tmp_path):
    """Creates a realistic ~/.openclaw/ structure in a temp dir."""
    (tmp_path / "workspace").mkdir()
    (tmp_path / "agents" / "coder").mkdir(parents=True)
    (tmp_path / "openclaw.json").write_text('{"agents": {}}')
    return tmp_path
```
All tests use this fixture. No test touches the real filesystem. Coverage target: 80%+ for services.

### 7.5 No Deployment / Process Supervision

**Section 9:** `make serve` for production. But:
- No `launchctl` plist for auto-start on macOS
- No process supervisor (supervisord, pm2)
- No crash recovery
- No log rotation

For MVP, this is acceptable — Miller starts it manually. But document it as a Phase 2 item.

### 7.6 No OpenAPI Documentation Plan

FastAPI auto-generates Swagger docs at `/docs` and ReDoc at `/redoc`. The plan doesn't mention this. These are free and invaluable for the Frontend agent to understand the API contract.

**Recommendation:** Mention in the plan that `/docs` is available and should be used by the Frontend agent as the authoritative API reference. Ensure all Pydantic models have `json_schema_extra` with examples.

### 7.7 No Rate Limiting on Write Operations

A misbehaving frontend (or a developer testing with a tight loop) could:
- Save config 100 times per second → 100 backup files
- Create/delete files rapidly → filesystem churn
- Restart the gateway repeatedly → process instability

**Recommendation:** Add a simple rate limiter: max 1 config write per second, max 1 gateway command per 5 seconds. Use `slowapi` or a manual token bucket. This prevents accidental damage, not malicious attacks (those are out of scope for localhost).

---

## 8. Specific Recommendations

These are concrete, directly implementable changes — not vague advice.

### R1: Change file path parameters from URL path to query params

**Change:** `GET /api/agents/{agent_id}/files/{path}` → `GET /api/agents/{agent_id}/files?path=memory/2026-02-25.md`

**Why:** Path parameters with slashes break URL routing. Query params handle special characters naturally. Same for PUT and DELETE.

### R2: Delete the generic file endpoints

**Change:** Remove `/api/files/*` (§5.8) entirely. Route all file access through agent-scoped or skill-scoped endpoints.

**Why:** Two overlapping file access patterns = two sandboxing implementations to maintain and test. One path, one implementation.

### R3: Replace single AppContext with Zustand or split contexts

**Change:** Replace `context/AppContext.tsx` with either Zustand (preferred) or 4-5 split React contexts.

**Why:** Single context + WebSocket updates = re-render storm across all components. Zustand selectors give surgical re-renders with less code than split contexts.

### R4: Lazy-load Monaco editor

**Change:** Wrap the editor page in `React.lazy(() => import('./pages/EditorPage'))` with a `Suspense` fallback.

**Why:** Monaco is 2.5MB gzipped. Loading it on dashboard page load violates the 500ms target and wastes bandwidth when the user just wants to see the fleet overview.

### R5: Add Host header validation middleware

**Change:** Add middleware that rejects requests where `Host` is not `localhost` or `127.0.0.1`.

**Why:** Prevents DNS rebinding attacks. 10 lines of code, closes a real attack vector.

### R6: Use `create_subprocess_exec`, never `create_subprocess_shell`

**Change:** All `gateway_service.py` subprocess calls must use `exec` with argument lists, not `shell` with string interpolation.

**Why:** Prevents command injection. Non-negotiable.

### R7: Add ETags / optimistic concurrency on file writes

**Change:** Return `ETag` (mtime + size hash) on file reads. Require `If-Match` on file writes. Return 409 on conflict.

**Why:** Without this, the dashboard will silently overwrite changes made by running agents. This is the #1 data loss risk.

### R8: Cut multi-tab and file tree from MVP

**Change:** MVP file editing = click a file in agent detail → single Monaco editor → save. No tabs, no file tree sidebar.

**Why:** Multi-tab editor is the hardest frontend feature. Cutting it saves ~40% of frontend effort and still delivers the core value: editing agent files in a browser.

### R9: Cut visual config editor from MVP

**Change:** MVP config editing = Monaco editor for `openclaw.json` with JSON validation on save.

**Why:** Visual forms for heterogeneous JSON config is a massive frontend effort with diminishing returns. Monaco already handles JSON with syntax highlighting, validation, and formatting. The visual form is a Phase 2 polish item.

### R10: Generate TypeScript types from OpenAPI spec

**Change:** Add a `make types` target that runs `openapi-typescript` against `http://localhost:8400/openapi.json` and outputs `frontend/src/types/generated.ts`.

**Why:** Manual type synchronization between Pydantic and TypeScript will drift within days. Auto-generation makes this impossible.

### R11: Define WebSocket message protocol before implementation

**Change:** Add a `§5.9 WebSocket Protocol` section with message envelope format, event types, and reconnection behavior.

**Why:** Backend and Frontend agents will implement WebSocket independently. Without a shared protocol spec, they'll build incompatible implementations.

### R12: Add a startup validation step in FastAPI lifespan

**Change:** In `main.py`'s lifespan handler, validate that OPENCLAW_HOME exists, `openclaw.json` parses, and at least one workspace is present. Set a global `system_status` dict.

**Why:** Prevents cryptic 500 errors when the environment is misconfigured. Gives the frontend a clean signal for what's working.

---

## Summary: Priority Matrix

| Issue | Severity | Effort to Fix | Fix Before Build? |
|-------|----------|---------------|-------------------|
| R7: File write concurrency (ETags) | 🔴 Critical | Medium | ✅ Yes |
| R5: DNS rebinding (Host validation) | 🔴 Critical | Low | ✅ Yes |
| R6: Command injection (exec not shell) | 🔴 Critical | Low | ✅ Yes |
| R1: File path in query params | 🔴 Critical | Low | ✅ Yes |
| R3: Split state management | 🔴 Critical | Medium | ✅ Yes |
| R10: TypeScript type generation | 🟡 High | Low | ✅ Yes |
| R11: WebSocket protocol spec | 🟡 High | Low | ✅ Yes |
| R8: Cut multi-tab from MVP | 🟡 High | Saves time | ✅ Yes |
| R9: Cut visual config from MVP | 🟡 High | Saves time | ✅ Yes |
| R4: Lazy-load Monaco | 🟡 High | Low | ✅ Yes |
| R12: Startup validation | 🟡 Medium | Low | ✅ Yes |
| R2: Delete generic file endpoints | 🟡 Medium | Low | ✅ Yes |
| §1.2: File watching scope | 🟡 Medium | Medium | ⚠️ Specify now |
| §1.3: Caching strategy | 🟢 Low | Medium | 📋 Backlog |
| §3.5: Backup cleanup | 🟢 Low | Low | 📋 Backlog |
| §4.4: Accessibility | 🟢 Low | High | 📋 Phase 2 |
| §7.5: Process supervision | 🟢 Low | Medium | 📋 Phase 2 |

**Bottom line:** The plan is a good starting point but needs 12 specific revisions before 6 agents start building. The biggest risks are (1) silent data loss from concurrent writes, (2) scope overestimation on the editor and config UI, and (3) no shared type contract between backend and frontend. Fix these and the build will go smoothly.
