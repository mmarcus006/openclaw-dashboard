# MASTER-TODO.md — OpenClaw Dashboard Build-Out
_Created: 2026-02-25 | Source: WAVES.md v5.0 (4 critique rounds)_
_Baseline: MVP complete — 7,863 LOC, 72 files, 152 tests, 75% coverage_

**Milestones:** ALPHA (after Wave 2) = daily usable | OMEGA (after Wave 6) = feature-complete
**Estimate:** ~25-31 dev hours | 5-7 days with 2 parallel agents

---

## Wave 0: Foundation (2-3 hrs)
_Bug fixes + designer quick-wins + shared components. Must complete before any other wave._

### W0.1 — Verify blocker fixes (B1/M1/M2)
- [x] B1: ETag conflict handler extracts from `error.detail.current_etag` ✅ (verified in code)
- [x] M1: Config ETag uses SHA-1[:16] content hash, not mtime:size ✅ (verified in code)
- [x] M2: `discardChanges()` reverts content to `originalContent` ✅ (verified in code)
- [ ] Manual test: edit a file → save → edit same file in another way → force conflict → "Keep my changes" → save again → confirm it works

### W0.2 — Designer quick-wins (CSS + JSX)
- [ ] `globals.css`: `--text-secondary: #8b95a8` → `#a1abbe` (Fix A — WCAG AA on cards)
- [ ] `globals.css`: Accent badge text → `text-[#a5b4fc]` on `bg-accent/25` (Fix B)
- [ ] `globals.css`: Warning badge text → `text-[#fbbf24]` on `bg-warning/20` (Fix C)
- [ ] `Sidebar.tsx`: Active state → `bg-accent/20 text-accent border-l-2 border-accent pl-[10px]` + inactive gets `border-l-2 border-transparent pl-[10px]` (E5)
- [ ] `DashboardPage.tsx` (`DashboardStats`): Active count `0` renders in `text-text-secondary`, not `text-success` (D1)
- [ ] `AgentCard.tsx`: Status dot `w-2.5 h-2.5` → `w-3 h-3`; add `animate-pulse` when `status === 'active'`
- [ ] `Header.tsx`: `<h1>` class from `text-sm` to `text-base` (T1)

### W0.3 — Shared component library
- [ ] `SearchInput.tsx` (~30 LOC) — input with clear button + result count display
- [ ] `Skeleton.tsx` (~20 LOC) — `bg-bg-hover animate-pulse rounded` placeholder
- [ ] `EmptyState.tsx` (~25 LOC) — icon + title + description + optional action button
- [ ] `ConfirmDialog.tsx` (~40 LOC) — wraps existing Modal, confirm/cancel buttons + message

### W0.4 — Reviewer minor fixes (m1-m8)
- [ ] m1: `DashboardStats` receives `agents` as prop, no duplicate `useAgents()` call
- [ ] m2: `_list_workspace_files` filters against `WORKSPACE_FILES` set (not `iterdir()`)
- [ ] m3: Fix WsInitializer comment accuracy in `App.tsx`
- [ ] m4: Config `GET /api/config` returns ETag in response **headers** (not just body)
- [ ] m5: `beforeunload` handler adds `e.returnValue = ''` for Safari/compat
- [ ] m6: Wire `@limiter.limit()` decorators on config write + gateway action endpoints
- [ ] m7: Add `__all__` exports to all `__init__.py` files
- [ ] m8: Extract `_now_iso()` to `backend/app/utils.py`, update all imports
- [ ] 3 new backend tests: rate limiting, workspace file filtering, config ETag header
- [ ] All 155+ tests pass, `ruff check` clean, zero TS errors

---

## Wave 1: Dashboard & Agents Split (4-5 hrs)
_Depends on: Wave 0_

### W1.1 — Create AgentsPage with search/filter/sort
- [ ] New `AgentsPage.tsx` — uses `SearchInput` from W0.3
- [ ] Client-side filter on `name`, `id`, `model`
- [ ] Status filter: All / Active / Idle / Stopped (native `<select>`)
- [ ] Sort by: Name / Status / Last Activity (native `<select>`)
- [ ] Move `AgentGrid` usage from Dashboard to AgentsPage
- [ ] 2 frontend tests: search filters correctly, status filter works

### W1.2 — Redesign DashboardPage as fleet summary
- [ ] Add Lucide icons to stat cards (Bot, Activity, Radio, Minus) (D3)
- [ ] Add "Recent Activity" section — 5 most recently active agents + timestamps
- [ ] Gateway status summary card (running/stopped/error)
- [ ] Quick nav cards: "View All Agents →", "Open Config →"
- [ ] Section heading "Fleet ({count})" above recent activity (D10)
- [ ] Stat numbers get `tabular-nums` class (T3)
- [ ] Remove AgentGrid — Dashboard is no longer a grid page
- [ ] 1 frontend test: Dashboard renders stats + recent activity, not grid

### W1.3 — Agent store search/filter/sort state
- [ ] Add `searchTerm`, `statusFilter`, `sortBy`, `sortDir` to `agentStore.ts`
- [ ] Selector: `filteredAgents()` returns agents matching criteria
- [ ] 2 frontend tests: filter + sort correctness

### W1.4 — Router and sidebar update
- [ ] `router.tsx`: `/agents` → `AgentsPage` (not `DashboardPage`)
- [ ] `Sidebar.tsx`: "Dashboard" and "Agents" as distinct nav items
- [ ] Active state highlights correct route

---

## Wave 2: Agent Cards & Status (3-4 hrs) — ✅ CHECKPOINT ALPHA
_Depends on: Wave 0. Can run parallel with Wave 1._

### W2.1 — Fix model display bug
- [ ] Investigate: backend returns `gpt-5.3-codex` (config default) for all agents
- [ ] Fix: `agent_service.py` reads agent's most recent session `model` from `sessions.json`
- [ ] Fallback to config default only when no session exists
- [ ] 1 backend test: agent with session returns session model

### W2.2 — Rich status indicators + card polish
- [ ] Colored left-border stripe: green (active), amber (idle), gray (stopped)
- [ ] `last_activity`: parse `updatedAt` from sessions.json (Unix timestamp ms)
- [ ] Replace "Never" with "No sessions yet" in muted text when null (D8)
- [ ] Card hover: `hover:translate-y-[-1px] hover:shadow-lg` lift (D9)
- [ ] Status dot: `transition-colors duration-300` (CC8)
- [ ] 1 frontend test: card renders correct border color per status

### W2.3 — File type icons + detail polish
- [ ] New `fileIcons.ts` utility: `.md`→FileText, `.json`→Braces, `.png/.jpg`→Image, `.py/.ts/.js`→FileCode, `.sh`→Terminal (AD2)
- [ ] Focus-visible ring on file table rows `<tr>` (CC5)
- [ ] Truncate workspace path with `title` attr for hover
- [ ] 1 test: icon resolver returns correct icon per extension

### ALPHA Verification
- [ ] `make test && make build`
- [ ] Manual: dashboard shows real agent data with correct per-agent models
- [ ] Manual: agents page search/filter works
- [ ] Manual: agent cards show real timestamps and distinct status indicators

---

## Wave 3: Gateway & Cron (3-4 hrs)
_Depends on: Wave 0. Can run parallel with Waves 1-2._

### W3.1 — Fix Gateway loading state
- [ ] If API response >5s → show error state, not infinite spinner (G1)
- [ ] If gateway CLI missing → "Gateway not installed" + doc link
- [ ] If gateway stopped → prominent "Gateway Stopped" card with Start button (E4)
- [ ] Disabled button tooltips (G5)
- [ ] 2 frontend tests: timeout → error, stopped → start button

### W3.2 — Channels table + command history
- [ ] Replace `JSON.stringify(channels)` with table: Channel | Status | Provider (G4)
- [ ] Expand panel to `max-w-4xl` (G2)
- [ ] Command history: last 5 commands with timestamp + exit code
- [ ] Backend: in-memory last 10 commands, new `GET /api/gateway/history`
- [ ] 1 backend test: history returns commands

### W3.3 — Cron job viewer (section on Gateway page)
- [ ] New `CronJobList.tsx` below gateway controls
- [ ] Backend: `GET /api/cron` reads cron config from openclaw.json
- [ ] Table: Name | Schedule (human-readable via `cronstrue`) | Next Run (via `croniter`) | Enabled
- [ ] Empty state via `EmptyState` component from W0.3
- [ ] Add `croniter` to Python deps, `cronstrue` to npm deps
- [ ] 1 backend test: cron list parses config correctly

---

## Wave 4: Session Viewer (5-6 hrs)
_Depends on: Wave 1 (agent detail page exists). The killer feature._

### W4.1 — Backend: session list
- [ ] Parse `sessions.json` dict → extract per-session metadata
- [ ] Fields: `sessionId`, `updatedAt`, `model`, `label`, `spawnedBy`, `totalTokens`, `inputTokens`, `outputTokens`
- [ ] Filter by agent: session key starts with `agent:{agent_id}:`
- [ ] Sort by `updatedAt` descending
- [ ] `GET /api/agents/{agent_id}/sessions?limit=20&offset=0`
- [ ] Handle missing/corrupt sessions.json
- [ ] New files: `session_service.py`, `sessions.py` (router), `session.py` (model)
- [ ] 3 backend tests: returns sessions, filter by agent, handles missing file

### W4.2 — Backend: session messages (JSONL)
- [ ] Read `sessionFile` path from session data
- [ ] Parse JSONL: each line → JSON with role, content, timestamp
- [ ] Pagination: offset-based (line number), limit 50
- [ ] Truncate content to 2000 chars in list response
- [ ] `GET /api/sessions/{session_id}/messages?limit=50&offset=0`
- [ ] Security: validate sessionFile path under OPENCLAW_HOME
- [ ] Handle missing JSONL, malformed lines
- [ ] 3 backend tests: parse JSONL, pagination, path validation

### W4.3 — Frontend: session list tab
- [ ] Tabs on AgentPage: "Files" | "Sessions"
- [ ] Session list: date, message count, model, tokens, duration
- [ ] Click session → expand inline to show messages
- [ ] Skeleton loading from W0.3
- [ ] "Load more" button for pagination
- [ ] New files: `SessionList.tsx`, `sessions.ts` (API), `sessionStore.ts`
- [ ] 1 frontend test: renders with mock data

### W4.4 — Frontend: conversation viewer
- [ ] Messages in conversation layout (user right, assistant left)
- [ ] Code blocks with syntax highlighting
- [ ] Long messages: "Show more" toggle at 500 chars
- [ ] Copy button on messages
- [ ] New file: `SessionViewer.tsx`
- [ ] 1 frontend test: renders roles correctly

---

## Wave 5: Editor Upgrade (3-4 hrs)
_Depends on: Wave 0. Can run parallel with Waves 1-4._

### W5.1 — Backend: recursive file listing
- [ ] `GET /api/agents/{agent_id}/files?recursive=true&depth=2`
- [ ] Flat list with relative paths (frontend groups by directory)
- [ ] Exclude: `.git`, `node_modules`, `.venv`, `__pycache__`
- [ ] Max depth 3 enforced server-side
- [ ] Include: size, mtime, `is_binary` (detect by extension)
- [ ] 2 backend tests: recursive listing, depth limit

### W5.2 — Frontend: file browser sidebar
- [ ] Left sidebar (240px) with agent selector `<select>` dropdown
- [ ] Flat file list grouped by directory (collapsible groups)
- [ ] File type icons from W2.3 `fileIcons.ts`
- [ ] Binary files: `cursor-not-allowed`, no click, tooltip "Binary files cannot be edited" (AD1, AD3)
- [ ] Current file highlighted
- [ ] Click file → load in editor; if dirty → `ConfirmDialog` from W0.3
- [ ] Sidebar collapsible via toggle button
- [ ] URL updates: `/editor?agent=main&path=SOUL.md`
- [ ] New files: `EditorSidebar.tsx`, `FileList.tsx`

### W5.3 — Editor layout integration
- [ ] EditorPage layout: `[Sidebar 240px][Monaco flex-1]`
- [ ] No file selected → `EmptyState` ("Select a file to edit")
- [ ] `Layout` component: add `noPadding` prop (replace `-m-6` hack)
- [ ] Breadcrumb: `Agents / COS / SOUL.md`

---

## Wave 6: Toast, Polish & Hardening (4-5 hrs) — ✅ CHECKPOINT OMEGA
_Depends on: Waves 1-5 complete._

### W6.1 — Toast notification system
- [ ] Toast: auto-dismiss (5s), stacking (max 3), slide-in animation
- [ ] Wire into: file save, config save, gateway action, validation error, agent fetch error
- [ ] `ConnectionBanner.tsx`: amber bar on WebSocket disconnect, disappears on reconnect
- [ ] 2 tests: auto-dismiss, connection banner

### W6.2 — Config editor improvements
- [ ] Save button tooltip: "No unsaved changes" when disabled (C1)
- [ ] Config path: `FileJson` icon prefix (C2)
- [ ] Auto-validate JSON on change, not manual button (C4)
- [ ] Document title per page: `${title} — OpenClaw` (CC7)

### W6.3 — Confirm dialogs + error pages
- [ ] Reload config when dirty → `ConfirmDialog` (C3)
- [ ] `NotFoundPage.tsx`: 404 with "Go home" button, uses Layout
- [ ] `ErrorBoundary` upgrade: "Something went wrong" + "Reload" button
- [ ] Add catch-all route in `router.tsx`

### W6.4 — Test coverage push to 85%
- [ ] Backend integration tests: full file read/write cycle
- [ ] WebSocket coverage: 25% → 60% (connect, ping/pong, events, disconnect)
- [ ] Frontend component tests for SessionList, FileList, CronJobList
- [ ] E2E smoke script: `make e2e` (start backend, curl endpoints, verify status codes)
- [ ] New files: `test_integration.py`, `smoke.sh`

### OMEGA Verification
- [ ] `make test && make e2e` both green
- [ ] Backend coverage ≥ 85%
- [ ] Zero TS errors, `ruff check` clean
- [ ] Manual: full click-through all 7 pages + features

---

## Backlog (deferred)

| Feature | Revisit When |
|---------|-------------|
| WebSocket real-time updates | Multiple users or performance issues |
| Agent sub-agent tree | Miller explicitly asks for it |
| Light theme | Miller asks for it |
| Mobile responsive | Never (probably) |
| Command palette (Cmd+K) | 20+ routes |
| Keyboard shortcut legend | After Cmd+K |
| Sortable DataTable | 200+ items in a list |
| Custom Select/Dropdown | Design system formalization |

---

## Reference

- **Source plan:** `WAVES.md` v5.0 (4 critique rounds, merged designer + planner + reviewer)
- **Design review:** `DESIGN-REVIEW.md` (39 issues, all P0/P1 mapped to waves above)
- **Code review:** `FINAL-REVIEW.md` (B1/M1/M2 blockers verified fixed, m1-m8 in W0.4)
- **Architecture:** `PLAN-v2.md` (R1-R12 recommendations, all implemented in MVP)

### Stats
| Metric | v1 Plan | v5 Final |
|--------|---------|----------|
| Waves | 13 | 7 |
| Tasks | 47 | 36 |
| LOC estimate | 5,840 | 2,720 |
| Dev hours | 55-70 | 25-31 |
| Calendar (2 agents) | 3 weeks | 5-7 days |
| Features cut | 0 | 8 (all low-value) |
