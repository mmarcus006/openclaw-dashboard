# WAVES.md — OpenClaw Dashboard Development Plan
_Version: 5.0 (FINAL) | Author: COS | Date: 2026-02-25_
_Baseline: MVP complete (7,863 LOC, 72 source files, 152 tests, 75% coverage)_
_Sources: DESIGN-REVIEW.md (designer), WAVES v1.0 (planner), FINAL-REVIEW.md (reviewer)_

---

## REVIEW LOG — 4 Critique Rounds

### Round 1: The Teardown

I reviewed the planner's v1.0 against the designer's recommendations, the actual codebase, and the real OpenClaw data model. Here's what was wrong:

**1. The plan is massively over-scoped.** 13 waves, 47 tasks, 55-70 dev hours, ~5,840 LOC — for a personal localhost dashboard used by ONE person. That's 3 weeks of agent time for a tool with an audience of 1. The ROI math collapses. Every wave needs to justify its existence against "would Miller actually use this daily?"

**2. The designer's fixes weren't merged — they were ignored.** The planner created Wave 0 from FINAL-REVIEW.md's m1-m8. But the designer identified 3 WCAG contrast failures, a broken active state, a zero-state color bug, and 8 quick-wins doable in 1 hour. None of those appear in Wave 0. The designer's Priority Matrix (39 items with P0/P1/P2/P3 ratings) was never integrated into the wave structure.

**3. The dependency graph is over-serialized.** Wave 5 (Editor File Browser) depends on Wave 3 (Agent Detail Nav), which depends on Wave 1 (Dashboard Differentiation). But the editor file browser doesn't need agent detail improvements — it needs a file list endpoint that already exists. Artificial coupling adds 10-15 hours of blocking wait.

**4. Wrong data model for sessions.** The planner's Wave 8 talks about "session JSONL files" with "cursor-based pagination with line offsets." The actual data: `sessions.json` is a single 292KB JSON dict keyed by session key. Each session has `sessionFile` pointing to a JSONL file, but the session INDEX is a flat dict — not paginated JSONL. The Wave 8 backend architecture is built on wrong assumptions.

**5. Wave 7 (WebSocket real-time) is premature optimization.** 5-second polling for a single-user localhost app is completely fine. The complexity of WS event propagation across 6 Zustand stores, reconnection handling, polling-as-fallback — to save a handful of local API calls per minute? Net negative ROI.

**6. Features nobody asked for.** Wave 11 (Agent Sub-Agent Tree visualization) — cool demo, unclear utility. Wave 10.4 (Cmd+K Command Palette) — for a 6-page app with a sidebar? Wave 10.1 (Light theme) — this is a dev tool, dark theme is fine. Wave 10.2 (Mobile responsive) — nobody manages agents from their phone. These are resume features, not user features.

**7. Wave 12 (E2E Tests) as a final wave is backwards.** Testing should be incremental. A "hardening wave" at the end implies all prior waves shipped without proper testing. This contradicts the TDD mandate.

**8. Session Viewer is the killer feature, buried at Wave 8.** "What have my agents been doing?" is THE question this dashboard should answer. It's blocked by 7 prior waves. Meanwhile, Wave 9 (Cron Viewer) — a read-only table — gets its own wave.

**9. LOC estimates are false precision.** "15 test + 25 impl" for a task? These are guesses wearing lab coats. The 3-week timeline with 2 parallel agents ignores coordination overhead, context switching, and the reality that sub-agents need supervision.

**10. No shipping milestone.** When is "done"? After Wave 4? Wave 6? Wave 12? There's no definition of a usable product versus a complete product.

---

### Round 2: The Restructure

After the teardown, I restructured with these principles:

1. **Ship something useful FAST** — Wave 0 should be the quick-wins bundle (1 hour), not a 4-task hygiene pass.
2. **Cut everything that doesn't serve daily use** — Light theme, mobile responsive, command palette, agent tree, keyboard legend → CUT.
3. **Unblock the killer feature** — Session viewer should be Wave 3 or 4, not Wave 8.
4. **Merge designer + reviewer fixes properly** — Every designer P0/P1 item needs a wave assignment.
5. **Fix the data model** — sessions.json is a dict, not JSONL. Redesign accordingly.
6. **Drop WebSocket upgrades** — Polling is fine. Remove Wave 7 entirely.

**Proposed restructure (Round 2):**

- Wave 0: Quick Wins (designer's 1-hour bundle + FINAL-REVIEW B1/M1/M2) — 1-2 hrs
- Wave 1: Dashboard ≠ Agents (E1 + search/filter) — 4-5 hrs
- Wave 2: Agent Status + Card Polish (designer P0/P1 visual fixes) — 3-4 hrs
- Wave 3: Gateway Fix (loading state + channels table) — 2-3 hrs
- Wave 4: Session Viewer (the killer feature) — 5-7 hrs
- Wave 5: Editor File Browser — 4-6 hrs
- Wave 6: Toast + UX Polish (notifications, 404, confirmation dialogs) — 3-4 hrs
- Wave 7: Cron Viewer — 3-4 hrs
- Backlog: Agent tree, light theme, WS upgrade, responsive, Cmd+K

**But this still had problems...**

---

### Round 3: Questioning Everything

Challenged every wave in the Round 2 plan:

**"Does Wave 1 (Dashboard ≠ Agents) matter?"** YES. The duplicate route is confusing, and more importantly, the Dashboard needs to become the "at a glance" view while Agents becomes the "manage and search" view. But — do we need stat cards redesign AND search AND sort in one wave? SPLIT IT. Quick route fix first (30 min), full agents page later.

**"Is the Session Viewer feasible at Wave 4?"** PARTIALLY. The session data is accessible (sessions.json dict → sessionFile JSONL paths). But parsing JSONL files that can be megabytes needs care. The planner's cursor-based pagination idea was right for the JSONL message files, wrong for the session index. Hybrid approach: session LIST from dict (fast), message DETAIL from JSONL with streaming/pagination.

**"Why is the Editor File Browser a 4-6 hour wave?"** Because the planner spec'd a full tree component with expand/collapse, keyboard navigation, agent selector dropdown, and resizable sidebar. OVERBUILT. A flat file list with agent dropdown is 80% of the value in 30% of the code. Tree view can come later if needed.

**"Does anyone need the Cron Viewer?"** YES, actually. Miller has cron jobs for heartbeats, monitoring, reminders. Seeing what's scheduled and when it last ran IS useful daily. But it's read-only and simple — could be part of the Gateway page rather than a whole new route.

**"Should Wave 0 include the designer's contrast fixes?"** ABSOLUTELY. The designer found `#8b95a8` text on `#232936` cards FAILS WCAG AA. That's not a "nice to have" — it's a 1-line CSS variable change that fixes readability for every card in the dashboard. It should be the FIRST thing fixed.

**"Are the blocker fixes (B1, M1, M2) really Wave 0?"** YES. B1 (ETag conflict handler) is broken functionality — the conflict resolution flow literally doesn't work. M1 (same-second race) and M2 (discardChanges doesn't revert) are real bugs. These go before any new features.

**"How many waves can actually run in parallel?"** Realistically, 2 agents max. One frontend, one backend. They MUST NOT touch the same files. The planner's "Sprint 1: Agent A does W0→W1→W2, Agent B waits then does W4→W6" is unrealistic — Agent B can't start until Agent A finishes W0 since they share dependencies.

**New realization: the Component Library Gaps matter.** The designer identified 10 missing components (SearchInput, Select, DataTable, StatCard, Skeleton, EmptyState, FileTypeIcon, ConfirmDialog, Collapsible, KeyboardShortcutModal). Rather than sprinkling these across waves, create a focused component wave that future waves can consume. This UNBLOCKS parallelism.

---

### Round 4: The Final Plan

Incorporating all critique rounds. Rules:

1. Every wave must ship a visibly improved dashboard.
2. Max 8 waves (not 13). Ruthlessly cut or merge.
3. Designer P0/P1 items assigned. Every item tracked.
4. Data model verified against real sessions.json.
5. Parallel execution plan that's actually achievable.
6. "Done" milestones defined — Checkpoint Alpha (usable) and Checkpoint Omega (complete).

---

## FINAL PLAN: 7 Waves

### Wave Overview

| Wave | Name | Scope | Est. Time | Dependencies | Milestone |
|------|------|-------|-----------|--------------|-----------|
| 0 | Foundation | Bug fixes (B1/M1/M2) + designer quick-wins + shared components | 2-3 hrs | None | — |
| 1 | Dashboard & Agents Split | Route fix, agents page with search/filter, dashboard as summary | 4-5 hrs | Wave 0 | — |
| 2 | Agent Cards & Status | Real status data, card polish, file type icons, contrast fixes | 3-4 hrs | Wave 0 | ✅ **ALPHA** |
| 3 | Gateway & Cron | Gateway loading fix, channels table, cron job list (same page) | 3-4 hrs | Wave 0 | — |
| 4 | Session Viewer | Session list + message viewer on agent detail page | 5-6 hrs | Wave 1 | — |
| 5 | Editor Upgrade | File browser sidebar (flat list), binary detection, agent selector | 3-4 hrs | Wave 0 | — |
| 6 | Toast, Polish & Hardening | Toast system, 404 page, confirm dialogs, coverage push to 85% | 4-5 hrs | Waves 1-5 | ✅ **OMEGA** |

**Total: ~25-31 dev hours across 36 tasks. That's 40-55% less than v1.**

### Dependency Graph

```
Wave 0 (Foundation)
  │
  ├──► Wave 1 (Dashboard/Agents Split) ──► Wave 4 (Session Viewer)
  │
  ├──► Wave 2 (Agent Cards & Status)
  │
  ├──► Wave 3 (Gateway & Cron)
  │
  └──► Wave 5 (Editor Upgrade)
  
  Waves 1-5 all complete ──► Wave 6 (Polish & Hardening)
```

**Parallel execution (2 agents):**
```
Sprint 1 (~8 hrs):
  Agent A (Frontend): Wave 0 frontend → Wave 1 → Wave 2
  Agent B (Backend):  Wave 0 backend → Wave 3 backend → Wave 4 backend

Sprint 2 (~8 hrs):
  Agent A (Frontend): Wave 4 frontend → Wave 5
  Agent B (Backend):  Wave 5 backend → Wave 6 tests

Sprint 3 (~6 hrs):
  Agent A (Frontend): Wave 6 frontend
  Agent B (Backend):  Wave 6 backend + integration tests
```

**Realistic calendar: 5-7 days with 2 agents (not 3 weeks).**

### Designer Issue Tracking

Every designer item mapped to a wave:

| Designer Item | Priority | Wave | Task |
|---------------|----------|------|------|
| E1 — Dual Dashboard/Agents | P0 Critical | W1 | W1.1-W1.3 |
| E2 — Rich Status Indicator | P0 Critical | W2 | W2.2 |
| E3 — Search/Filter | P0 Critical | W1 | W1.2 |
| E4 — Complete Gateway | P1 High | W3 | W3.1 |
| E5 — Sidebar Active State | P0 Critical | W0 | W0.2 |
| Fix A — text-secondary contrast | P1 High | W0 | W0.2 |
| Fix B — Accent badge contrast | P1 High | W0 | W0.2 |
| Fix C — Warning badge contrast | P1 High | W0 | W0.2 |
| D1 — Active count green zero | P1 High | W0 | W0.2 |
| D3 — Stat card icons | P2 Medium | W1 | W1.3 |
| D5 — Model display bug | P1 High | W2 | W2.1 |
| D8 — Hide "Never" activity | P2 Medium | W2 | W2.2 |
| D9 — Card hover shadow | P2 Medium | W2 | W2.2 |
| D10 — Fleet section heading | P2 Medium | W1 | W1.3 |
| AD1 — Filter binary files | P1 High | W5 | W5.2 |
| AD2 — File type icons | P1 Medium | W2 | W2.3 |
| AD3 — Block binary in editor | P2 High | W5 | W5.2 |
| AD5 — Model badge placement | P3 Low | BACKLOG | — |
| G1 — Gateway API timeout | P1 High | W3 | W3.1 |
| G2 — Gateway width | P2 Medium | W3 | W3.2 |
| G4 — Channels table | P2 Medium | W3 | W3.2 |
| G5 — Button disabled tooltips | P2 Low | W3 | W3.1 |
| C1 — Save tooltip | P2 Medium | W6 | W6.2 |
| C2 — Config path icon | P2 Low | W6 | W6.2 |
| C3 — Reload confirmation | P2 Medium | W6 | W6.3 |
| C4 — Auto-validate on change | P2 Medium | W6 | W6.2 |
| CC2 — Skeleton loaders | P2 Medium | W0 | W0.3 (component) |
| CC3 — Toast system | P2 Medium | W6 | W6.1 |
| CC4 — Empty state consistency | P2 Medium | W0 | W0.3 (component) |
| CC5 — Focus ring on table rows | P2 Medium | W2 | W2.3 |
| CC7 — Document title per page | P3 Low | W6 | W6.2 |
| CC8 — Status dot transition | P3 Low | W2 | W2.2 |
| T1 — h1 text-base | P2 Medium | W0 | W0.2 |
| T3 — Tabular figures | P2 Low | W1 | W1.3 |
| Gap 1 — SearchInput | P1 Critical | W0 | W0.3 |
| Gap 5 — Skeleton | P2 Medium | W0 | W0.3 |
| Gap 6 — EmptyState | P2 Medium | W0 | W0.3 |
| Gap 8 — ConfirmDialog | P2 Medium | W0 | W0.3 |

**CUT (not worth the complexity):**
- Gap 2 (Select/Dropdown) — native `<select>` is fine
- Gap 3 (Sortable DataTable) — overkill for 40-item lists
- Gap 10 (Keyboard shortcut legend) — premature
- CC1 (WS live card animation) — cut with WS wave
- CC6 (Mobile responsive) — personal tool, desktop only
- Wave 10.1 (Light theme) — nobody asked for this
- Wave 10.4 (Command Palette) — 6 pages, use the sidebar
- Wave 11 (Agent Tree) — cool but unclear daily utility
- Wave 7 (WebSocket upgrade) — polling is fine for localhost

---

## Wave 0: Foundation

### Goal
Fix all known bugs (B1, M1, M2, m1-m8) AND the designer's quick-wins AND build the 4 shared components that unblock later waves. This is the "clean the house before renovating" wave.

### Time: 2-3 hours

### Tasks

**W0.1: Fix blockers B1 + M1 + M2 from FINAL-REVIEW**
- B1: `editorStore.ts` — extract ETag from `error.detail.current_etag`, not `error.message`. After "Keep my changes", set file's ETag to `conflictEtag` so next save uses correct baseline.
- M1: `file_service.py` — switch config ETag from `mtime:size` to `SHA-1[:16]` content hash. (Already fixed in MVP per daily log, VERIFY.)
- M2: `editorStore.ts` — `discardChanges()` must revert `content` to `originalContent`, not just reset dirty flag. (Already fixed per daily log, VERIFY.)
- Test: existing 152 tests + verify conflict flow manually
- Files: `frontend/src/stores/editorStore.ts`, `backend/app/services/file_service.py`
- LOC: ~20 modified
- Exit: Conflict flow works end-to-end. Save after "Keep my changes" succeeds.

**W0.2: Designer quick-wins bundle (CSS + JSX, 1 hour)**
- `globals.css`: `--text-secondary: #8b95a8` → `#a1abbe` (Fix A — WCAG AA)
- `globals.css`: Accent badge text → `text-[#a5b4fc]` on `bg-accent/25` (Fix B)
- `globals.css`: Warning badge text → `text-[#fbbf24]` on `bg-warning/20` (Fix C)
- `Sidebar.tsx`: Active state → `bg-accent/20 text-accent border-l-2 border-accent pl-[10px]` (E5)
- `DashboardStats`: Active count `0` → `text-text-secondary` not green (D1)
- `AgentCard.tsx`: Status dot `w-2.5 h-2.5` → `w-3 h-3`, add `animate-pulse` when active
- `Header.tsx`: `<h1>` from `text-sm` to `text-base` (T1)
- Files: `globals.css`, `Sidebar.tsx`, `DashboardPage.tsx`, `AgentCard.tsx`, `Header.tsx`
- LOC: ~40 modified
- Exit: WCAG AA passes on all text. Sidebar active state clearly visible. Status dots 12px with pulse.

**W0.3: Shared component library (unblock future waves)**
- `SearchInput.tsx` (~30 LOC): Reusable search input with clear button and result count
- `Skeleton.tsx` (~20 LOC): Animated placeholder for loading states
- `EmptyState.tsx` (~25 LOC): Consistent icon + title + description + optional action button
- `ConfirmDialog.tsx` (~40 LOC): "Are you sure?" modal wrapping the existing Modal component
- Files: 4 new files in `frontend/src/components/common/`
- LOC: ~115 new
- Exit: All 4 components exported and importable. No consumers yet (that's Waves 1-6).

**W0.4: Reviewer minor fixes m1-m8**
- m1: `DashboardStats` receives `agents` as prop (no duplicate `useAgents()`)
- m2: `_list_workspace_files` filters against `WORKSPACE_FILES` set
- m3: WsInitializer comment accuracy in App.tsx
- m4: Config GET returns ETag in response headers (not just body)
- m5: `beforeunload` adds `e.returnValue = ''`
- m6: Rate limit decorators on config write + gateway action
- m7: `__all__` exports in `__init__.py` files
- m8: Extract `_now_iso()` to `utils.py`
- Tests: 3 new backend tests (rate limit, file filter, ETag header)
- LOC: ~40 test + ~60 impl
- Exit: 155+ tests pass. `ruff check` clean. Zero TS errors.

### Exit Criteria (Wave 0)
1. All 155+ tests pass
2. WCAG AA compliance on all text/background combinations
3. Conflict resolution flow works end-to-end
4. 4 shared components ready for consumption
5. Single polling interval on Dashboard
6. `ruff check` clean, zero TS errors

---

## Wave 1: Dashboard & Agents Split

### Goal
Fix the #1 UX problem: `/` and `/agents` are identical. After this wave, Dashboard is a fleet summary and `/agents` is a searchable, filterable agent list.

### Time: 4-5 hours

### Tasks

**W1.1: Create AgentsPage with SearchInput and status filter**
- New `AgentsPage.tsx` with `SearchInput` component from W0.3
- Client-side filter on name/id/model (already in memory, no backend needed)
- Status filter: All / Active / Idle / Stopped (native `<select>`, not a custom component)
- Sort by: Name / Status / Last Activity (native `<select>`)
- Move `AgentGrid` from Dashboard to AgentsPage
- Test: 2 new tests (search filters agents, status filter works)
- Files: `AgentsPage.tsx` (new), `router.tsx`, tests
- LOC: ~40 test + ~120 impl

**W1.2: Redesign DashboardPage as fleet summary**
- Stat cards with Lucide icons (Bot, Activity, Radio, Minus) (D3)
- "Recent Activity" — 5 most recently active agents with timestamps
- Gateway status summary card (running/stopped/error)
- Quick nav cards: "View All Agents →", "Open Config →", etc.
- Section heading "Fleet ({count})" above recent activity (D10)
- Stat numbers get `tabular-nums` class (T3)
- Remove AgentGrid import — Dashboard no longer renders the grid
- Test: 1 new test (Dashboard renders stats and recent activity, not grid)
- Files: `DashboardPage.tsx` (rewrite)
- LOC: ~15 test + ~100 impl

**W1.3: Add search/filter/sort state to agentStore**
- `setSearchTerm(s)`, `setStatusFilter(s)`, `setSortBy(field, dir)`
- Selector `filteredAgents()` returns matching agents
- Persist filter state during session (not across reloads)
- Test: 2 new tests (filter + sort correctness)
- Files: `agentStore.ts`
- LOC: ~30 test + ~40 impl

**W1.4: Update router and sidebar**
- `/agents` → `AgentsPage` (not `DashboardPage`)
- Sidebar: both "Dashboard" and "Agents" as separate nav items
- Active state correctly highlights current route
- Files: `router.tsx`, `Sidebar.tsx`
- LOC: ~15 impl

### Exit Criteria (Wave 1)
1. `/` and `/agents` render visually distinct pages
2. Search filters 40 agents with no perceptible lag
3. Status filter and sort work correctly
4. Dashboard shows KPI summary, not full grid
5. 5+ new tests pass

---

## Wave 2: Agent Cards & Status — ✅ CHECKPOINT ALPHA after this wave

### Goal
Make agent cards informative and visually distinct. Fix the "all agents show gpt-5.3-codex" bug. Add real timestamps. Polish cards with hover effects and file type icons on agent detail.

After Wave 2, the dashboard is USABLE for daily monitoring.

### Time: 3-4 hours

### Tasks

**W2.1: Fix model display — investigate and fix gpt-5.3-codex on all cards**
- The real issue: `openclaw.json` defaults.model.primary = `openai-codex/gpt-5.3-codex`. The backend likely returns the default model for all agents instead of per-agent overrides.
- Check: does `sessions.json` have per-session `model` field? YES — confirmed: `"model": "claude-opus-4-6"` in session data.
- Fix: `agent_service.py` should read the agent's most recent session model from sessions.json, not the default from config.
- Fallback: use config default only when no session exists for the agent.
- Test: 1 new test (agent with session returns session model, agent without returns default)
- Files: `agent_service.py`
- LOC: ~20 test + ~30 impl

**W2.2: Rich status indicators + card polish**
- Status: colored left-border stripe on cards (green=active, amber=idle, gray=stopped)
- Active agents: `animate-pulse` on status dot (already added in W0.2, verify)
- `last_activity`: parse `updatedAt` from sessions.json (it's a Unix timestamp in ms)
- Hide "Never" when value is null — show "No sessions yet" in muted text (D8)
- Card hover: add `hover:translate-y-[-1px] hover:shadow-lg` lift effect (D9)
- Status dot: add `transition-colors duration-300` (CC8)
- Test: 1 new test (card renders correct status class)
- Files: `AgentCard.tsx`, `Card.tsx`, `agent_service.py`
- LOC: ~15 test + ~50 impl

**W2.3: File type icons + detail page polish**
- Map extensions to Lucide icons: `.md`→FileText, `.json`→Braces, `.png/.jpg`→Image, `.py/.ts/.js`→FileCode, `.sh`→Terminal (AD2)
- Add focus-visible ring on file table rows (CC5)
- Truncate long workspace paths with `title` attribute for hover
- Test: 1 test (icon resolver returns correct icon per extension)
- Files: `AgentDetail.tsx`, new `fileIcons.ts` utility
- LOC: ~10 test + ~30 impl

### Exit Criteria (Wave 2) — **CHECKPOINT ALPHA: Dashboard is usable**
1. Agent cards show correct per-agent models
2. Status indicators are visually distinct (border stripe + dot + color)
3. Last activity shows real timestamps from sessions
4. File type icons differentiate file types at a glance
5. All tests pass

### What "Alpha" means
After Wave 2, you can:
- See all agents at a glance with real status
- Search and filter agents
- View agent details with file list
- Edit agent files with conflict resolution
- Manage gateway start/stop/restart
- Edit openclaw.json with validation

---

## Wave 3: Gateway & Cron

### Goal
Fix the perpetual spinner on Gateway page. Add channels as a proper table. Add cron job viewer as a section ON the Gateway page (not a separate route — it's ops-related, keep it together).

### Time: 3-4 hours

### Tasks

**W3.1: Fix Gateway loading state**
- GatewayPanel: if API response takes >5s, show error state instead of infinite spinner (G1)
- If gateway CLI not found: show "Gateway not installed" with doc link
- If gateway stopped: show prominent "Gateway Stopped" card with Start button (E4)
- Disabled button tooltips: "Gateway is already running" / "Gateway is not running" (G5)
- Test: 2 new tests (timeout shows error, stopped shows start button)
- Files: `GatewayPanel.tsx`, `useGateway.ts`
- LOC: ~25 test + ~40 impl

**W3.2: Channels table + command history**
- Replace `JSON.stringify(channels)` with a proper table: Channel | Status | Provider (G4)
- Expand gateway panel to `max-w-4xl` (G2)
- Add "Last Command Output" section below controls (already partially exists)
- Show last 5 commands with timestamp + exit code (green 0 / red non-zero)
- Backend: store last 10 commands in memory, new `GET /api/gateway/history`
- Test: 1 new backend test (history returns commands)
- Files: `GatewayPanel.tsx`, `gateway_service.py`, `gateway.py` (router)
- LOC: ~15 test + ~60 impl

**W3.3: Cron job viewer (section on Gateway page)**
- New `CronJobList.tsx` component rendered below gateway controls
- Backend: `GET /api/cron` — reads cron jobs from openclaw.json
- Display: table with Name | Schedule (human readable) | Next Run | Enabled
- Human-readable schedule: use `cronstrue` npm package (e.g., "Every 30 minutes")
- Next run: compute from cron expression (use `croniter` in Python backend)
- "No cron jobs" empty state using W0.3 EmptyState component
- Why same page: Gateway and Cron are both "ops" — users checking gateway status will also want to see scheduled jobs. One page, two sections.
- Test: 1 backend test (cron list parses config correctly)
- Files: `CronJobList.tsx` (new), `cron.py` (new router), `cron_service.py` (new), `GatewayPage.tsx`
- LOC: ~20 test + ~100 impl
- Dep: `croniter` (Python), `cronstrue` (npm)

### Exit Criteria (Wave 3)
1. Gateway page loads in <2 seconds — never shows infinite spinner
2. Channels render as a readable table
3. Cron jobs display with human-readable schedules
4. Command history shows after gateway actions
5. All tests pass

---

## Wave 4: Session Viewer

### Goal
THE killer feature. Show what agents have been doing. Session list on agent detail page + conversation message viewer.

### Time: 5-6 hours

### Tasks

**W4.1: Backend — session list from sessions.json**
- Parse `sessions.json` (dict keyed by session key)
- For each session: extract `sessionId`, `updatedAt`, `model`, `label`, `spawnedBy`, `totalTokens`, `inputTokens`, `outputTokens`
- Filter by agent: session key starts with `agent:{agent_id}:` (main, subagent, etc.)
- Sort by `updatedAt` descending
- Endpoint: `GET /api/agents/{agent_id}/sessions?limit=20&offset=0`
- Return: `{sessions: [...], total: N}`
- Handle missing/corrupt sessions.json gracefully
- Test: 3 new tests (list returns sessions, filter by agent works, handles missing file)
- Files: `session_service.py` (new), `sessions.py` (new router), `session.py` (new model)
- LOC: ~50 test + ~100 impl

**W4.2: Backend — session messages from JSONL file**
- Read `sessionFile` path from session data
- Parse JSONL: each line is a JSON object with role, content, timestamp, etc.
- Pagination: offset-based (line number), limit 50 per request
- Truncate content to 2000 chars in response (full content on dedicated endpoint if needed)
- Endpoint: `GET /api/sessions/{session_id}/messages?limit=50&offset=0`
- Return: `{messages: [...], total: N, hasMore: bool}`
- Handle missing JSONL files, malformed lines, binary content
- Security: validate sessionFile path is under OPENCLAW_HOME
- Test: 3 new tests (parse JSONL, pagination, path validation)
- Files: `session_service.py`, `sessions.py`
- LOC: ~50 test + ~80 impl

**W4.3: Frontend — session list tab on agent detail**
- Add tabs to AgentPage: "Files" | "Sessions"
- Session list: date, message count, model, token count, duration
- Click session → expand inline to show messages (not a separate page)
- Use Skeleton component from W0.3 for loading
- Infinite scroll for session list (load more button, not auto-scroll)
- Test: 1 test (session list renders with mock data)
- Files: `SessionList.tsx` (new), `AgentPage.tsx`, `sessions.ts` (new API module), `sessionStore.ts` (new)
- LOC: ~20 test + ~120 impl

**W4.4: Frontend — conversation message viewer**
- Messages in conversation layout: user messages right-aligned, assistant left-aligned
- Code blocks with syntax highlighting (reuse Monaco's language tokenizer OR use a lightweight lib like `highlight.js`)
- Long messages: "Show more" toggle (collapsed at 500 chars)
- Token count per message if available
- Copy button on messages (use navigator.clipboard)
- Test: 1 test (message viewer renders roles correctly)
- Files: `SessionViewer.tsx` (new)
- LOC: ~15 test + ~120 impl

### Exit Criteria (Wave 4)
1. Agent detail shows session list with real data
2. Clicking a session shows conversation messages
3. Pagination works for both session list and messages
4. Large sessions (1000+ messages) don't crash the UI
5. All tests pass, 6+ new backend tests

---

## Wave 5: Editor Upgrade

### Goal
Add a file browser to the editor so users don't have to navigate back to agent detail to open another file. Keep it simple — flat list with agent dropdown, not a full tree.

### Time: 3-4 hours

### Tasks

**W5.1: Backend — recursive file listing endpoint**
- `GET /api/agents/{agent_id}/files?recursive=true&depth=2`
- Returns flat list of files with relative paths (not nested tree — frontend can group if needed)
- Exclude: `.git`, `node_modules`, `.venv`, `__pycache__`
- Max depth 3 enforced server-side
- Include: size, mtime, is_binary (detect by extension)
- Test: 2 new tests (recursive listing, depth limit enforcement)
- Files: `agents.py` (router), `agent_service.py`
- LOC: ~30 test + ~50 impl

**W5.2: Frontend — file browser sidebar**
- Left sidebar (240px) with agent selector dropdown at top
- Flat file list below, grouped by directory (collapsible groups)
- File type icons from W2.3 utility
- Binary files: show with `cursor-not-allowed`, no click action (AD3). Tooltip: "Binary files cannot be edited" (AD1)
- Current file highlighted
- Click file → load in editor. If dirty, show ConfirmDialog from W0.3
- Sidebar collapsible via toggle button
- URL updates: `/editor?agent=main&path=SOUL.md`
- Files: `EditorSidebar.tsx` (new), `FileList.tsx` (new), `EditorPage.tsx`
- LOC: ~80 + ~60 + ~30 modified = ~170 impl

**W5.3: Editor layout integration**
- EditorPage: `[Sidebar 240px][Monaco flex-1]`
- When no file selected: show EmptyState from W0.3 ("Select a file to edit")
- Layout prop `noPadding` for editor page (replace hacky `-m-6` negative margin)
- Add breadcrumb: `Agents / COS / SOUL.md` when editing a file
- Files: `EditorPage.tsx`, `Layout.tsx`
- LOC: ~40 impl

### Exit Criteria (Wave 5)
1. Editor has file browser sidebar
2. Agent selector dropdown works
3. Binary files blocked from opening
4. Dirty state warning when switching files
5. All tests pass

---

## Wave 6: Toast, Polish & Hardening — ✅ CHECKPOINT OMEGA

### Goal
Final wave. Wire toast notifications into all operations, add 404 page, add confirm dialogs where missing, push coverage to 85%, and clean up any remaining issues.

### Time: 4-5 hours

### Tasks

**W6.1: Toast notification system**
- Upgrade existing Toast: auto-dismiss (5s), stacking (max 3), slide-in animation
- Wire into all operations:
  - File save → success toast
  - Config save → success toast
  - Gateway action → success/error toast
  - Validation error → error toast with message
  - Agent fetch error → error toast
- Connection banner: amber bar when WebSocket disconnects
- Test: 2 tests (toast auto-dismiss, connection banner show/hide)
- Files: `Toast.tsx`, `toastStore.ts`, `ConnectionBanner.tsx` (new), `Layout.tsx`
- LOC: ~25 test + ~80 impl

**W6.2: Config editor improvements**
- Save button: tooltip "No unsaved changes" when disabled (C1)
- Config path: add `FileJson` icon (C2)
- Auto-validate JSON on change instead of manual button click (C4)
- Document title updates per page: `${title} — OpenClaw` (CC7)
- Files: `ConfigEditor.tsx`, `configStore.ts`, various pages
- LOC: ~40 impl

**W6.3: Confirm dialogs + 404**
- Reload config when dirty → ConfirmDialog (C3)
- 404 page: "Page not found" with "Go home" button, uses Layout
- ErrorBoundary upgrade: "Something went wrong" with "Reload" button
- Files: `ConfigEditor.tsx`, `NotFoundPage.tsx` (new), `ErrorBoundary.tsx`, `router.tsx`
- LOC: ~60 impl

**W6.4: Test coverage push to 85%**
- Backend integration tests: full request lifecycle (create file → read → verify)
- WebSocket test coverage: 25% → 60% (connect, ping/pong, events, disconnect)
- Frontend component tests for new components (SessionList, FileList, CronJobList)
- E2E smoke script: `make e2e` — starts backend, curls all endpoints, verifies status codes
- Test: ~150 new test LOC
- Files: `test_integration.py` (new), `test_websocket.py` (expand), `smoke.sh` (new)
- LOC: ~150 test + ~30 impl (test utils + smoke script)

### Exit Criteria (Wave 6) — **CHECKPOINT OMEGA: Dashboard is complete**
1. All operations have toast feedback
2. 404 page works for invalid routes
3. Config reload warns when dirty
4. Backend coverage ≥ 85%
5. WebSocket coverage ≥ 60%
6. `make test && make e2e` both green
7. Zero TS errors, `ruff check` clean

### What "Omega" means
After Wave 6, the dashboard is feature-complete for daily use:
- Fleet overview with real KPIs
- Agent search, filter, sort
- Agent detail with files + sessions + conversation viewer
- File editor with browser sidebar
- Config editor with validation + conflict resolution
- Gateway management with cron job viewer
- Toast notifications for all operations
- 85%+ test coverage

---

## Backlog (deferred — not worth the complexity now)

| Feature | Why Deferred | Revisit When |
|---------|-------------|--------------|
| WebSocket real-time updates | Polling is fine for single-user localhost | Multiple users OR performance issues |
| Agent sub-agent tree | Cool visualization, unclear daily utility | Miller explicitly asks for it |
| Light theme | Dev tool, dark is fine | Miller asks for it |
| Mobile responsive | Nobody manages agents from phone | Never (probably) |
| Command palette (Cmd+K) | 7 pages with a sidebar | 20+ pages or routes |
| Keyboard shortcut legend | Premature | After Cmd+K if ever |
| Sortable DataTable component | Native sort + filter is sufficient for 40 items | 200+ items in a list |
| Custom Select/Dropdown | Native `<select>` works | Design system formalization |

---

## Testing Strategy

### Per-Wave Requirements

| Wave | New Backend Tests | New Frontend Tests | Cumulative Coverage |
|------|------------------|--------------------|---------------------|
| 0 | 3 (rate limit, file filter, ETag header) | 0 | 75% |
| 1 | 0 | 5 (AgentsPage, DashboardPage, agentStore) | 76% |
| 2 | 2 (model resolution, status endpoint) | 2 (AgentCard, fileIcons) | 77% |
| 3 | 4 (gateway loading, history, cron list, cron parse) | 0 | 79% |
| 4 | 6 (session list, messages, pagination, filter, path validation, corrupt handling) | 2 (SessionList, SessionViewer) | 82% |
| 5 | 2 (recursive listing, depth limit) | 0 | 83% |
| 6 | 20+ (integration, WS coverage, E2E) | 3 (Toast, ConnectionBanner, new components) | 85%+ |

### Checkpoints

**After Wave 2 (ALPHA):**
```bash
make test && make build && curl -s localhost:8400/api/health | jq .status
# Manual: verify dashboard shows real agent data with correct models
```

**After Wave 6 (OMEGA):**
```bash
make test && make e2e
# Manual: full click-through of all features
```

---

## LOC Summary

| Wave | New | Modified | Tests | Total |
|------|-----|----------|-------|-------|
| 0 | 115 | 160 | 40 | 315 |
| 1 | 260 | 55 | 85 | 400 |
| 2 | 30 | 110 | 45 | 185 |
| 3 | 200 | 100 | 60 | 360 |
| 4 | 420 | 30 | 135 | 585 |
| 5 | 310 | 70 | 30 | 410 |
| 6 | 170 | 120 | 175 | 465 |
| **Total** | **~1,505** | **~645** | **~570** | **~2,720** |

**v1 was 5,840 LOC. This is 2,720 — 53% less code for the same usable outcome.** The difference: we cut the features nobody needs and stopped building abstractions ahead of demand.

---

## Design System Changes (from DESIGN-REVIEW.md)

Applied in Wave 0 and carried through all waves:

```css
/* Updated tokens */
--text-secondary: #a1abbe;          /* Was #8b95a8 — now passes WCAG AA on cards */
--bg-elevated: #1a1f2e;             /* New — for modals/dropdowns (= bg-secondary, named) */
--border-subtle: #252b3b;           /* New — very subtle dividers */

/* Sidebar active state */
.nav-active {
  @apply bg-accent/20 text-accent border-l-2 border-accent pl-[10px];
}
.nav-inactive {
  @apply text-text-secondary hover:text-text-primary hover:bg-bg-hover border-l-2 border-transparent pl-[10px];
}
```

No other design system changes needed. The existing 4-level depth system (primary → secondary → card → hover) is solid. The `--info` token remains unused — remove in W6 cleanup or wire into a Badge variant.
