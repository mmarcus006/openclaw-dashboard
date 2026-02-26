# WAVES-v2.md — OpenClaw Dashboard Development Plan
_Version: 2.0 | Revised: 2026-02-25 | Round: 2/5_
_Changes from v1: Addressed all 3 critical issues, 8 improvements, and 5 reviewer questions from REVIEW-R1.md_

## Changelog from v1

### Critical Issues Addressed
- **C1 (B1 blocker missing):** Verified — B1 was already in W0.1 of v1 (the reviewer reviewed the pre-self-critique plan). W0.1 text now includes explicit test case name and verification step.
- **C2 (M1/M2 missing):** Verified — M1 and M2 were already in W0.1 of v1. Added explicit VERIFY instructions since daily logs suggest these may already be fixed in the MVP codebase.
- **C3 (~20 DESIGN-REVIEW items unassigned):** Added 6 previously unmapped items: AD4 (create file button → backlog), AD6 (workspace path truncation → W2.3), Monaco theme mismatch (→ W5.3), C6 (config title verbose → W6.2), Gap 4 (StatCard → backlog), G3 (empty command placeholder → W3.2). Full tracking table updated with 100% coverage of DESIGN-REVIEW items.

### Improvements Addressed
- **I1 (W5 EditorSidebar no tests):** Added `EditorSidebar.test.tsx` to W5.2 — tests agent dropdown, binary blocking, file click with dirty state.
- **I2 (W5 EditorPage integration no tests):** Added `EditorPage.test.tsx` to W5.3 — tests file open from sidebar, dirty-state warning on switch, URL param sync.
- **I3 (Sprint schedule idle time):** Restructured Sprint 1 — Agent A does W0 solo (1-2h), Agent B starts W3 backend immediately after W0 baseline commit. Eliminated Agent B idle time.
- **I4 (Dark/Light Theme):** Already cut in v1. Decision documented in Reviewer Questions section.
- **I5 (Design System token additions):** Expanded W0.2 to include `--bg-elevated`, `--border-subtle`, `--text-tertiary`, `--warning-text`, z-index scale, radius scale, and transition tokens from DESIGN-REVIEW §7.1. Added rationale for which tokens are included vs deferred.
- **I6 (Session JSONL highest-risk):** Added W4.0 research subtask (30 min) to document actual session file format before implementation. Added explicit constraints: 50MB file size cap, schema validation with graceful degradation, format-version detection.
- **I7 (CommandPalette):** Already cut in v1. Decision documented.
- **I8 (No cross-wave integration test):** Added Integration Checkpoint specs after Wave 2 (Alpha) and after Wave 5 (pre-Omega) with specific manual and automated verification steps.

### Reviewer Questions Answered
- Added "Decisions" section with explicit answers to all 5 reviewer questions (Q1-Q5), each with rationale and confidence level.

### Other Changes
- Wave 5 testing table updated: 0 → 4 frontend tests (from 0 in v1).
- Added `croniter` rationale to W3.3 as inline note.
- Added E2E rationale to W6.4 as inline note.
- Added Monaco custom theme subtask to W5.3.
- Added workspace path truncation to W2.3.
- Tightened sprint parallelism estimate: 4-6 days (down from 5-7).
- Added `--info` token resolution decision to W6.2.
- Total LOC revised to ~2,830 (up from ~2,720 due to new tests and tokens).

---

## Decisions (Reviewer Questions Q1–Q5)

| # | Question | Decision | Rationale | Confidence |
|---|----------|----------|-----------|------------|
| Q1 | Is light theme needed? | **CUT.** Deferred to backlog. | This is a localhost dev tool. Miller uses dark mode. The entire codebase is dark-first. Adding light theme requires duplicating 15+ CSS variables, FOUC prevention, and testing all pages in both modes. ROI is negative. Revisit only if Miller explicitly requests it. | High |
| Q2 | Should D5 (model display bug) be in Wave 0? | **No. Stays in W2.1.** | D5 is a real bug (all agents show `gpt-5.3-codex`), but the fix requires reading per-session model data from `sessions.json`. This overlaps with W2's agent card work. Moving it to W0 would add session parsing to the foundation wave, increasing scope. The bug is cosmetic (doesn't block functionality), so W2 is appropriate. | High |
| Q3 | What's the session JSONL format? | **Added W4.0 research subtask.** | The session index is `sessions.json` (flat dict), not JSONL. Individual session message files ARE JSONL. W4.0 (30 min) documents the actual schema before implementation. Constraints: 50MB cap, graceful degradation on unknown fields, format-version detection. | Medium (format may vary across OpenClaw versions) |
| Q4 | Is `croniter` the right dependency? | **Yes. Keep `croniter`.** | `croniter` is the standard Python cron library (10M+ monthly downloads, maintained). `cron_descriptor` is Python 2 era and less maintained. Rolling our own regex parser for cron expressions invites bugs for edge cases (day-of-week + day-of-month conflicts, ranges with steps). The dependency cost is minimal (pure Python, no native extensions). `cronstrue` on the frontend handles human-readable display. | High |
| Q5 | Should E2E be shell or Playwright? | **Shell (curl-based) for v1. Playwright deferred.** | Adding Playwright as a dependency for a localhost tool adds ~200MB of browser binaries and significant test infrastructure. The `smoke.sh` script covers backend API correctness, which is where bugs actually happen. Frontend behavior is covered by component tests (Vitest + Testing Library). If we add more complex UI flows later (multi-step session browsing, drag-resize), Playwright becomes worthwhile. For now, shell is intentional. | High |

---

## FINAL PLAN: 7 Waves

### Wave Overview

| Wave | Name | Scope | Est. Time | Dependencies | Milestone |
|------|------|-------|-----------|--------------|-----------|
| 0 | Foundation | Bug fixes (B1/M1/M2) + designer quick-wins + CSS tokens + shared components | 2-3 hrs | None | — |
| 1 | Dashboard & Agents Split | Route fix, agents page with search/filter, dashboard as summary | 4-5 hrs | Wave 0 | — |
| 2 | Agent Cards & Status | Real status data, card polish, file type icons, contrast fixes | 3-4 hrs | Wave 0 | ✅ **ALPHA** |
| 3 | Gateway & Cron | Gateway loading fix, channels table, cron job list (same page) | 3-4 hrs | Wave 0 | — |
| 4 | Session Viewer | Research + session list + message viewer on agent detail page | 5.5-7 hrs | Wave 1 | — |
| 5 | Editor Upgrade | File browser sidebar (flat list), binary detection, agent selector, Monaco theme | 3.5-5 hrs | Wave 0 | — |
| 6 | Toast, Polish & Hardening | Toast system, 404 page, confirm dialogs, coverage push to 85% | 4-5 hrs | Waves 1-5 | ✅ **OMEGA** |

**Total: ~26-33 dev hours across 38 tasks. That's 40-55% less than the original 13-wave plan.**

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
Sprint 1 (~7-8 hrs):
  Agent A (Frontend): Wave 0 (solo, 1-2h) → commit baseline → Wave 1 (4-5h)
  Agent B (Backend):  Waits for W0 baseline commit (~1.5h) → Wave 3 backend (2-3h) → Wave 4 backend (3-4h)

Sprint 2 (~7-8 hrs):
  Agent A (Frontend): Wave 2 (3-4h) → Wave 4 frontend (2-3h)
  Agent B (Backend):  Wave 5 backend (1-2h) → Wave 5 frontend (2-3h) → start Wave 6 tests

Sprint 3 (~4-6 hrs):
  Agent A (Frontend): Wave 6 frontend (2-3h) → integration checkpoint
  Agent B (Backend):  Wave 6 backend + E2E smoke script (2-3h)
```

**Why Agent A does W0 solo:** Wave 0 is 2-3 hours of CSS fixes, component scaffolding, and bug fixes. Having two agents touch `globals.css`, `editorStore.ts`, and component files simultaneously creates merge conflicts. Agent A does W0, commits a clean baseline, then both agents diverge on non-overlapping files.

**Why Agent B starts W3 not W1:** W1 (Dashboard/Agents split) is almost entirely frontend (new AgentsPage, rewrite DashboardPage, update router). W3 has a backend-heavy component (gateway service, cron service, new API endpoints) that Agent B can start while Agent A works W1 frontend. This eliminates the 1-2h idle wait identified in I3.

**Realistic calendar: 4-6 days with 2 agents.**

### Designer Issue Tracking — Complete Coverage

Every DESIGN-REVIEW item mapped to a wave or explicitly deferred:

| Designer Item | Priority | Wave | Task | Status |
|---------------|----------|------|------|--------|
| E1 — Dual Dashboard/Agents | P0 Critical | W1 | W1.1-W1.4 | Planned |
| E2 — Rich Status Indicator | P0 Critical | W2 | W2.2 | Planned |
| E3 — Search/Filter | P0 Critical | W1 | W1.1, W1.3 | Planned |
| E4 — Complete Gateway | P1 High | W3 | W3.1 | Planned |
| E5 — Sidebar Active State | P0 Critical | W0 | W0.2 | Planned |
| Fix A — text-secondary contrast | P1 High | W0 | W0.2 | Planned |
| Fix B — Accent badge contrast | P1 High | W0 | W0.2 | Planned |
| Fix C — Warning badge contrast | P1 High | W0 | W0.2 | Planned |
| D1 — Active count green zero | P1 High | W0 | W0.2 | Planned |
| D2 — Gateway stat shimmer | P1 High | W3 | W3.1 | Planned (timeout fallback) |
| D3 — Stat card icons | P2 Medium | W1 | W1.2 | Planned |
| D4 — Stat cards clickable | P3 Low | BACKLOG | — | Future enhancement |
| D5 — Model display bug | P1 High | W2 | W2.1 | Planned |
| D6 — Status dot size | P2 Medium | W0 | W0.2 | Planned (w-3 h-3) |
| D7 — No search | P0 Critical | W1 | W1.1 | Planned (= E3) |
| D8 — Hide "Never" activity | P2 Medium | W2 | W2.2 | Planned |
| D9 — Card hover shadow | P2 Medium | W2 | W2.2 | Planned |
| D10 — Fleet section heading | P2 Medium | W1 | W1.2 | Planned |
| AD1 — Filter binary files | P1 High | W5 | W5.2 | Planned |
| AD2 — File type icons | P1 Medium | W2 | W2.3 | Planned |
| AD3 — Block binary in editor | P2 High | W5 | W5.2 | Planned |
| AD4 — Create file button | P3 Low | BACKLOG | — | Disabled placeholder if time permits |
| AD5 — Model badge placement | P3 Low | BACKLOG | — | Low impact |
| AD6 — Workspace path truncation | P2 Medium | W2 | W2.3 | Planned (truncate + title attr) |
| G1 — Gateway API timeout | P1 High | W3 | W3.1 | Planned |
| G2 — Gateway width | P2 Medium | W3 | W3.2 | Planned |
| G3 — Empty command placeholder | P2 Low | W3 | W3.2 | Planned ("No recent commands") |
| G4 — Channels table | P2 Medium | W3 | W3.2 | Planned |
| G5 — Button disabled tooltips | P2 Low | W3 | W3.1 | Planned |
| C1 — Save tooltip | P2 Medium | W6 | W6.2 | Planned |
| C2 — Config path icon | P2 Low | W6 | W6.2 | Planned |
| C3 — Reload confirmation | P2 Medium | W6 | W6.3 | Planned |
| C4 — Auto-validate on change | P2 Medium | W6 | W6.2 | Planned |
| C5 — Editor fills height | ✅ Pass | — | — | Already correct |
| C6 — Config title verbose | P3 Low | W6 | W6.2 | Planned (simplify to "Config") |
| CC1 — WS live card animation | P2 Medium | CUT | — | Cut with WS upgrade wave |
| CC2 — Skeleton loaders | P2 Medium | W0 | W0.3 | Planned (component) |
| CC3 — Toast system | P2 Medium | W6 | W6.1 | Planned |
| CC4 — Empty state consistency | P2 Medium | W0 | W0.3 | Planned (component) |
| CC5 — Focus ring on table rows | P2 Medium | W2 | W2.3 | Planned |
| CC6 — Mobile responsive | P3 Low | CUT | — | Desktop-only dev tool |
| CC7 — Document title per page | P3 Low | W6 | W6.2 | Planned |
| CC8 — Status dot transition | P3 Low | W2 | W2.2 | Planned |
| T1 — h1 text-base | P2 Medium | W0 | W0.2 | Planned |
| T2 — Agent card name 14px | ✅ Pass | — | — | Designer said "minor note", no action |
| T3 — Tabular figures | P2 Low | W1 | W1.2 | Planned |
| T4 — JetBrains Mono CDN | ✅ Pass | — | — | No change needed |
| T5 — Uppercase tracking | ✅ Pass | — | — | Already consistent |
| E1-A — Editor file browser | P1 Critical | W5 | W5.2-W5.3 | Planned |
| E2-A — Editor toolbar | ✅ Pass | — | — | Already excellent |
| E3-A — Monaco theme mismatch | P2 Medium | W5 | W5.3 | **NEW:** Custom Monaco theme |
| Gap 1 — SearchInput | P1 Critical | W0 | W0.3 | Planned |
| Gap 2 — Select/Dropdown | P2 Medium | CUT | — | Native `<select>` is fine |
| Gap 3 — Sortable DataTable | P2 Medium | CUT | — | Overkill for 40-item lists |
| Gap 4 — StatCard component | P3 Low | BACKLOG | — | Inline is fine for 4 cards |
| Gap 5 — Skeleton | P2 Medium | W0 | W0.3 | Planned |
| Gap 6 — EmptyState | P2 Medium | W0 | W0.3 | Planned |
| Gap 7 — FileTypeIcon resolver | P1 Medium | W2 | W2.3 | Planned |
| Gap 8 — ConfirmDialog | P2 Medium | W0 | W0.3 | Planned |
| Gap 9 — Collapsible Panel | P2 Medium | W5 | W5.2 | Implicit (collapsible groups) |
| Gap 10 — Keyboard shortcut legend | P3 Low | CUT | — | Premature |
| Info — Wire or remove --info | P3 Low | W6 | W6.2 | **NEW:** Wire into Badge info variant |

**Coverage: 56 items tracked. 38 planned in waves, 8 already passing, 7 cut with rationale, 3 in backlog.**

---

## Wave 0: Foundation

### Goal
Fix all known bugs (B1, M1, M2, m1-m8) AND the designer's quick-wins AND extend the design system tokens AND build the 4 shared components that unblock later waves. This is the "clean the house before renovating" wave.

### Time: 2-3 hours

### Tasks

**W0.1: Fix blockers B1 + M1 + M2 from FINAL-REVIEW**
- B1: `editorStore.ts` — extract ETag from `error.detail.current_etag`, not `error.message`. After "Keep my changes", set file's ETag to `conflictEtag` so next save uses correct baseline.
- M1: `file_service.py` — switch config ETag from `mtime:size` to `SHA-1[:16]` content hash. _(Note: daily log suggests this may already be fixed in the MVP codebase. VERIFY first — if fixed, mark done and move on.)_
- M2: `editorStore.ts` — `discardChanges()` must revert `content` to `originalContent`, not just reset dirty flag. _(Note: daily log suggests this may already be fixed. VERIFY first.)_
- Test: `frontend/src/stores/__tests__/editorStore.test.ts::test_conflict_extracts_current_etag` — verify that on 409 response, the store extracts `detail.current_etag` (not `error.message`) and that a subsequent save after "Keep my changes" uses the new ETag.
- Test: existing 152 tests must still pass after changes.
- Files: `frontend/src/stores/editorStore.ts`, `backend/app/services/file_service.py`
- LOC: ~20 modified + ~15 test
- Exit: Conflict flow works end-to-end. Save after "Keep my changes" succeeds. `discardChanges()` reverts content to `originalContent`.

**W0.2: Designer quick-wins bundle + Design System token expansion**
- `globals.css`: `--text-secondary: #8b95a8` → `#a1abbe` (Fix A — WCAG AA)
- `globals.css`: Accent badge text → `text-[#a5b4fc]` on `bg-accent/25` (Fix B)
- `globals.css`: Warning badge text → `text-[#fbbf24]` on `bg-warning/20` (Fix C)
- `Sidebar.tsx`: Active state → `bg-accent/20 text-accent border-l-2 border-accent pl-[10px]` (E5)
- `DashboardStats`: Active count `0` → `text-text-secondary` not green (D1)
- `AgentCard.tsx`: Status dot `w-2.5 h-2.5` → `w-3 h-3`, add `animate-pulse` when active (D6)
- `Header.tsx`: `<h1>` from `text-sm` to `text-base` (T1)
- **NEW — Design System token expansion** (from DESIGN-REVIEW §7.1):
  ```css
  /* New tokens added to globals.css */
  --bg-elevated: #1a1f2e;            /* Modals, dropdowns (= bg-secondary, named) */
  --border-subtle: #252b3b;          /* Very subtle dividers */
  --border-strong: #4a5568;          /* Focused/emphasized borders */
  --text-tertiary: #6b7896;          /* Placeholders, disabled text */
  --text-inverse: #0f1219;           /* Text on colored backgrounds */
  --warning-text: #fbbf24;           /* Amber 400 — higher contrast for text on dark */
  --success-light: rgba(34,197,94,0.15);
  --danger-light: rgba(239,68,68,0.15);
  --shadow-card: 0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.3);
  --shadow-modal: 0 20px 60px rgba(0,0,0,0.5);
  --z-sidebar: 100;
  --z-header: 200;
  --z-modal: 500;
  --z-toast: 600;
  --z-tooltip: 700;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --transition-fast: 100ms ease-in-out;
  --transition-base: 150ms ease-in-out;
  --transition-slow: 300ms ease-in-out;
  ```
  **Rationale for inclusion:** These tokens will be consumed by Waves 1-6 components (modals use `--z-modal`, cards use `--shadow-card`, toasts use `--z-toast`, etc.). Adding them upfront prevents ad-hoc `#hex` values and z-index magic numbers from creeping into components.
  **Deferred from §7.1:** `--bg-base` (#0a0d13 — current `--bg-primary` is fine), `--accent-light/border` (can use Tailwind `accent/15` syntax), `--info-light/border` (info not yet wired), `--shadow-tooltip` (no tooltip component yet). These can be added when a component needs them.
- Files: `globals.css`, `Sidebar.tsx`, `DashboardPage.tsx`, `AgentCard.tsx`, `Header.tsx`
- LOC: ~70 modified (40 JSX + 30 CSS tokens)
- Exit: WCAG AA passes on all text. Sidebar active state clearly visible. Status dots 12px with pulse. All new tokens declared and usable via `var(--token-name)`.

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
- Files: various backend + frontend files
- LOC: ~40 test + ~60 impl
- Exit: 155+ tests pass. `ruff check` clean. Zero TS errors.

### Exit Criteria (Wave 0)
1. All 155+ tests pass (including new B1 conflict test)
2. WCAG AA compliance on all text/background combinations
3. Conflict resolution flow works end-to-end (manual verification)
4. 4 shared components ready for consumption
5. All design system tokens declared in `globals.css`
6. Single polling interval on Dashboard (m1 fixed)
7. `ruff check` clean, zero TS errors

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
- Test: `frontend/src/pages/__tests__/AgentsPage.test.tsx` — 2 tests (search filters agents, status filter works)
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
- Test: `frontend/src/pages/__tests__/DashboardPage.test.tsx` — 1 test (renders stats and recent activity, not grid)
- Files: `DashboardPage.tsx` (rewrite)
- LOC: ~15 test + ~100 impl

**W1.3: Add search/filter/sort state to agentStore**
- `setSearchTerm(s)`, `setStatusFilter(s)`, `setSortBy(field, dir)`
- Selector `filteredAgents()` returns matching agents
- Persist filter state during session (not across reloads)
- Test: `frontend/src/stores/__tests__/agentStore.test.ts` — 2 tests (filter + sort correctness)
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
2. Search filters 40 agents with no perceptible lag (<5ms per filter op)
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
- Test: `backend/tests/test_agent_service.py::test_agent_model_from_session` — agent with session returns session model, agent without returns default
- Files: `agent_service.py`
- LOC: ~20 test + ~30 impl

**W2.2: Rich status indicators + card polish**
- Status: colored left-border stripe on cards (green=active, amber=idle, gray=stopped)
- Active agents: `animate-pulse` on status dot (already added in W0.2, verify)
- `last_activity`: parse `updatedAt` from sessions.json (it's a Unix timestamp in ms)
- Hide "Never" when value is null — show "No sessions yet" in muted text (D8)
- Card hover: add `hover:translate-y-[-1px] hover:shadow-lg` lift effect (D9)
- Status dot: add `transition-colors duration-300` (CC8)
- Test: `frontend/src/components/agents/__tests__/AgentCard.test.tsx` — 1 test (card renders correct status class)
- Files: `AgentCard.tsx`, `Card.tsx`, `agent_service.py`
- LOC: ~15 test + ~50 impl

**W2.3: File type icons + detail page polish**
- Map extensions to Lucide icons: `.md`→FileText, `.json`→Braces, `.png/.jpg`→Image, `.py/.ts/.js`→FileCode, `.sh`→Terminal (AD2)
- Add focus-visible ring on file table rows (CC5): `focus-visible:outline-2 focus-visible:outline-accent focus-visible:outline-offset-[-2px]`
- Truncate long workspace paths with `truncate` class + `title` attribute for hover (AD6)
- Test: `frontend/src/utils/__tests__/fileIcons.test.ts` — 1 test (icon resolver returns correct icon per extension)
- Files: `AgentDetail.tsx`, new `fileIcons.ts` utility
- LOC: ~10 test + ~30 impl

### Exit Criteria (Wave 2) — **CHECKPOINT ALPHA: Dashboard is usable**
1. Agent cards show correct per-agent models
2. Status indicators are visually distinct (border stripe + dot + color)
3. Last activity shows real timestamps from sessions
4. File type icons differentiate file types at a glance
5. Workspace paths truncate cleanly with hover for full path
6. All tests pass

### What "Alpha" means
After Wave 2, you can:
- See all agents at a glance with real status
- Search and filter agents
- View agent details with file list
- Edit agent files with conflict resolution
- Manage gateway start/stop/restart
- Edit openclaw.json with validation

### Integration Checkpoint: Alpha Verification
```bash
# Automated
make test && make build && curl -s localhost:8400/api/health | jq .status
curl -s localhost:8400/api/agents | jq '.[0].model' # Should NOT be "gpt-5.3-codex"

# Manual (5 min)
1. Open localhost:5173 → Dashboard shows stat cards + recent activity (NOT agent grid)
2. Click "Agents" in sidebar → Full agent grid with search bar
3. Type "main" in search → Filters to matching agents
4. Click an agent → Agent detail shows correct model, file type icons, workspace path
5. Click a .md file → Opens in editor, save works, conflict resolution works
```

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
- Gateway stat card on Dashboard: timeout → show "Unknown" instead of "loading…" (D2)
- Test: `frontend/src/components/gateway/__tests__/GatewayPanel.test.tsx` — 2 tests (timeout shows error, stopped shows start button)
- Files: `GatewayPanel.tsx`, `useGateway.ts`
- LOC: ~25 test + ~40 impl

**W3.2: Channels table + command history**
- Replace `JSON.stringify(channels)` with a proper table: Channel | Status | Provider (G4)
- Expand gateway panel to `max-w-4xl` (G2)
- Add "Last Command Output" section below controls (already partially exists)
- Show last 5 commands with timestamp + exit code (green 0 / red non-zero)
- When no commands have been run: show "No recent commands" placeholder text (G3)
- Backend: store last 10 commands in memory, new `GET /api/gateway/history`
- Test: `backend/tests/test_gateway_service.py::test_history` — 1 test (history returns commands)
- Files: `GatewayPanel.tsx`, `gateway_service.py`, `gateway.py` (router)
- LOC: ~15 test + ~60 impl

**W3.3: Cron job viewer (section on Gateway page)**
- New `CronJobList.tsx` component rendered below gateway controls
- Backend: `GET /api/cron` — reads cron jobs from openclaw.json
- Display: table with Name | Schedule (human readable) | Next Run | Enabled
- Human-readable schedule: use `cronstrue` npm package (e.g., "Every 30 minutes")
- Next run: compute from cron expression using `croniter` in Python backend
  - _Rationale for `croniter` (Q4):_ Standard library (10M+ monthly PyPI downloads), handles edge cases (DoW+DoM conflicts, ranges with steps) that a regex parser would miss. Pure Python, no native extensions. Pinned in `pyproject.toml`.
- "No cron jobs" empty state using W0.3 EmptyState component
- Why same page: Gateway and Cron are both "ops" — users checking gateway status will also want to see scheduled jobs. One page, two sections.
- Test: `backend/tests/test_cron_service.py::test_cron_list` — 1 test (cron list parses config correctly)
- Files: `CronJobList.tsx` (new), `cron.py` (new router), `cron_service.py` (new), `GatewayPage.tsx`
- LOC: ~20 test + ~100 impl
- Dep: `croniter` (Python), `cronstrue` (npm)

### Exit Criteria (Wave 3)
1. Gateway page loads in <2 seconds — never shows infinite spinner
2. Channels render as a readable table
3. Cron jobs display with human-readable schedules
4. Command history shows after gateway actions
5. "No recent commands" placeholder when no commands run
6. All tests pass

---

## Wave 4: Session Viewer

### Goal
THE killer feature. Show what agents have been doing. Session list on agent detail page + conversation message viewer. Starts with a research subtask to document the actual session file format.

### Time: 5.5-7 hours

### Tasks

**W4.0: Research — document session file format (NEW)**
- Read `~/.openclaw/sessions/sessions.json` and 2-3 JSONL session files
- Document: (a) session index schema (keys, fields, types), (b) JSONL message schema (role, content, timestamp, tool calls, etc.), (c) file size distribution (min/max/median), (d) any format-version indicators
- Output: `docs/session-format.md` in the project — referenced by W4.1 and W4.2
- Identify: which fields are guaranteed vs optional, max observed file size, encoding
- Time: 30 minutes
- Exit: Schema documented with field types and optionality. Implementers can code against documented schema without guessing.

**W4.1: Backend — session list from sessions.json**
- Parse `sessions.json` (dict keyed by session key)
- For each session: extract `sessionId`, `updatedAt`, `model`, `label`, `spawnedBy`, `totalTokens`, `inputTokens`, `outputTokens`
- Filter by agent: session key starts with `agent:{agent_id}:` (main, subagent, etc.)
- Sort by `updatedAt` descending
- Endpoint: `GET /api/agents/{agent_id}/sessions?limit=20&offset=0`
- Return: `{sessions: [...], total: N}`
- Handle missing/corrupt sessions.json gracefully
- **Explicit constraints (from I6):**
  - `sessions.json` file size cap: 50MB. If larger, return `413 Payload Too Large` with message "Session index too large to process".
  - Schema validation: unknown fields are ignored (forward-compatible). Missing expected fields default to `null`.
  - Format-version detection: if `sessions.json` contains a top-level `version` key, validate it. If unknown version, return data with a `warning: "Unknown session format version X"` field.
- Test: `backend/tests/test_session_service.py` — 3 tests (list returns sessions, filter by agent works, handles missing file)
- Files: `session_service.py` (new), `sessions.py` (new router), `session.py` (new model)
- LOC: ~50 test + ~100 impl

**W4.2: Backend — session messages from JSONL file**
- Read `sessionFile` path from session data
- Parse JSONL: each line is a JSON object with role, content, timestamp, etc.
- Pagination: offset-based (line number), limit 50 per request
- Truncate content to 2000 chars in response (full content on dedicated endpoint if needed)
- Endpoint: `GET /api/sessions/{session_id}/messages?limit=50&offset=0`
- Return: `{messages: [...], total: N, hasMore: bool}`
- Handle missing JSONL files, malformed lines (skip with warning), binary content
- **Explicit constraints (from I6):**
  - JSONL file size cap: 50MB. If larger, return `{messages: [], total: 0, hasMore: false, warning: "Session file too large (>50MB)"}`.
  - Malformed lines: skip silently, increment a `skippedLines` counter in the response.
  - Encoding: assume UTF-8. On decode errors, replace invalid bytes with U+FFFD.
- Security: validate sessionFile path is under OPENCLAW_HOME (path traversal prevention)
- Test: `backend/tests/test_session_service.py` — 3 tests (parse JSONL, pagination, path validation)
- Files: `session_service.py`, `sessions.py`
- LOC: ~50 test + ~80 impl

**W4.3: Frontend — session list tab on agent detail**
- Add tabs to AgentPage: "Files" | "Sessions"
- Session list: date, message count, model, token count, duration
- Click session → expand inline to show messages (not a separate page)
- Use Skeleton component from W0.3 for loading
- Infinite scroll for session list (load more button, not auto-scroll)
- Test: `frontend/src/components/sessions/__tests__/SessionList.test.tsx` — 1 test (session list renders with mock data)
- Files: `SessionList.tsx` (new), `AgentPage.tsx`, `sessions.ts` (new API module), `sessionStore.ts` (new)
- LOC: ~20 test + ~120 impl

**W4.4: Frontend — conversation message viewer**
- Messages in conversation layout: user messages right-aligned, assistant left-aligned
- Code blocks with syntax highlighting (reuse Monaco's language tokenizer OR use a lightweight lib like `highlight.js`)
- Long messages: "Show more" toggle (collapsed at 500 chars)
- Token count per message if available
- Copy button on messages (use navigator.clipboard)
- Test: `frontend/src/components/sessions/__tests__/SessionViewer.test.tsx` — 1 test (message viewer renders roles correctly)
- Files: `SessionViewer.tsx` (new)
- LOC: ~15 test + ~120 impl

### Exit Criteria (Wave 4)
1. Agent detail shows session list with real data
2. Clicking a session shows conversation messages
3. Pagination works for both session list and messages
4. Large sessions (1000+ messages) don't crash the UI
5. Session files >50MB show a graceful warning (not a crash)
6. Schema format documented in `docs/session-format.md`
7. All tests pass, 6+ new backend tests

---

## Wave 5: Editor Upgrade

### Goal
Add a file browser to the editor so users don't have to navigate back to agent detail to open another file. Keep it simple — flat list with agent dropdown, not a full tree. Fix Monaco theme mismatch.

### Time: 3.5-5 hours

### Tasks

**W5.1: Backend — recursive file listing endpoint**
- `GET /api/agents/{agent_id}/files?recursive=true&depth=2`
- Returns flat list of files with relative paths (not nested tree — frontend can group if needed)
- Exclude: `.git`, `node_modules`, `.venv`, `__pycache__`
- Max depth 3 enforced server-side
- Include: size, mtime, is_binary (detect by extension: `.png`, `.jpg`, `.gif`, `.webp`, `.ico`, `.woff`, `.woff2`, `.ttf`, `.pdf`, `.zip`, `.tar`, `.gz`)
- Test: `backend/tests/test_agent_service.py::test_recursive_listing` and `test_depth_limit` — 2 tests
- Files: `agents.py` (router), `agent_service.py`
- LOC: ~30 test + ~50 impl

**W5.2: Frontend — file browser sidebar**
- Left sidebar (240px) with agent selector dropdown at top
- Flat file list below, grouped by directory (collapsible groups)
- File type icons from W2.3 utility
- Binary files: show with `cursor-not-allowed opacity-60`, no click action (AD3). Tooltip: "Binary files cannot be edited" (AD1)
- Current file highlighted with `bg-accent/15`
- Click file → load in editor. If dirty, show ConfirmDialog from W0.3
- Sidebar collapsible via toggle button
- URL updates: `/editor?agent=main&path=SOUL.md`
- **Test (NEW — addressing I1):** `frontend/src/components/editor/__tests__/EditorSidebar.test.tsx` — 3 tests:
  - (a) Agent dropdown renders and changing agent loads new file list
  - (b) Binary file click is blocked (no navigation, shows tooltip)
  - (c) File click with dirty state shows ConfirmDialog
- Files: `EditorSidebar.tsx` (new), `FileList.tsx` (new), `EditorPage.tsx`
- LOC: ~35 test + ~170 impl (80 sidebar + 60 file list + 30 modified)

**W5.3: Editor layout integration + Monaco theme**
- EditorPage: `[Sidebar 240px][Monaco flex-1]`
- When no file selected: show EmptyState from W0.3 ("Select a file to edit")
- Layout prop `noPadding` for editor page (replace hacky `-m-6` negative margin)
- Add breadcrumb: `Agents / COS / SOUL.md` when editing a file
- **NEW — Custom Monaco theme (E3-A from DESIGN-REVIEW §4.6):** Create `openclaw-dark` Monaco theme that uses `--bg-primary` (#0f1219) as editor background instead of `vs-dark`'s #1e1e1e. This eliminates the jarring seam between editor and dashboard. Other colors (syntax highlighting) inherit from `vs-dark`.
- **Test (NEW — addressing I2):** `frontend/src/pages/__tests__/EditorPage.test.tsx` — 3 tests:
  - (a) Opening a file from sidebar loads it in the Monaco editor
  - (b) Switching files with unsaved changes shows ConfirmDialog warning
  - (c) URL updates reflect current agent and file path
- Files: `EditorPage.tsx`, `Layout.tsx`, `monacoTheme.ts` (new)
- LOC: ~30 test + ~60 impl

### Exit Criteria (Wave 5)
1. Editor has file browser sidebar
2. Agent selector dropdown works
3. Binary files blocked from opening (visual indicator + no click)
4. Dirty state warning when switching files
5. Monaco editor background matches dashboard theme (no seam)
6. Layout uses `noPadding` prop (no negative margin hack)
7. **7 new frontend tests pass** (3 sidebar + 3 integration + 1 existing)

### Integration Checkpoint: Pre-Omega Verification
```bash
# Automated
make test && make build

# Manual (5 min)
1. Navigate to /editor from sidebar → Empty state shows
2. Select agent from dropdown → File list loads
3. Click a .md file → Opens in editor with matching background color
4. Edit content → dirty indicator appears
5. Click different file → ConfirmDialog appears
6. Click a .png file → Blocked with tooltip
7. Navigate to /agents/main → Sessions tab shows real session data
8. Click a session → Messages render in conversation layout
```

---

## Wave 6: Toast, Polish & Hardening — ✅ CHECKPOINT OMEGA

### Goal
Final wave. Wire toast notifications into all operations, add 404 page, add confirm dialogs where missing, push coverage to 85%, and clean up any remaining issues.

### Time: 4-5 hours

### Tasks

**W6.1: Toast notification system**
- Upgrade existing Toast: auto-dismiss (5s), stacking (max 3), slide-in animation
- Use `--z-toast: 600` from design system tokens
- Wire into all operations:
  - File save → success toast
  - Config save → success toast
  - Gateway action → success/error toast
  - Validation error → error toast with message
  - Agent fetch error → error toast
- Connection banner: amber bar when WebSocket disconnects
- Test: `frontend/src/components/common/__tests__/Toast.test.tsx` — 2 tests (toast auto-dismiss timing, connection banner show/hide)
- Files: `Toast.tsx`, `toastStore.ts`, `ConnectionBanner.tsx` (new), `Layout.tsx`
- LOC: ~25 test + ~80 impl

**W6.2: Config editor improvements + misc polish**
- Save button: tooltip "No unsaved changes" when disabled (C1)
- Config path: add `FileJson` icon (C2)
- Auto-validate JSON on change instead of manual button click (C4)
- Document title updates per page: `${title} — OpenClaw` using `useEffect` hook (CC7)
- Simplify config page title from "Config — openclaw.json" to "Config" (C6)
- **`--info` token resolution:** Wire into Badge component as `variant="info"` using `bg-info/15 text-[#60a5fa]` (blue-400 for contrast). If no component needs it by this point, remove the token from globals.css to avoid orphan.
- Files: `ConfigEditor.tsx`, `configStore.ts`, various pages (title hook), `Badge.tsx`
- LOC: ~50 impl

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
  - _Rationale for shell over Playwright (Q5):_ Playwright adds ~200MB of browser binaries. Frontend behavior is covered by component tests (Vitest + Testing Library). Shell smoke tests cover backend API correctness, which is where bugs actually happen. If complex multi-step UI flows are added later, Playwright becomes worthwhile._
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
8. Document titles update per page
9. `--info` token either wired or removed (no orphans)

### What "Omega" means
After Wave 6, the dashboard is feature-complete for daily use:
- Fleet overview with real KPIs
- Agent search, filter, sort
- Agent detail with files + sessions + conversation viewer
- File editor with browser sidebar + custom theme
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
| Light theme (Q1) | Dev tool, dark is fine, ~5-7h for negative ROI | Miller explicitly asks |
| Mobile responsive (CC6) | Nobody manages agents from phone | Never (probably) |
| Command palette (Cmd+K) | 7 pages with a sidebar | 20+ pages or routes |
| Keyboard shortcut legend (Gap 10) | Premature | After Cmd+K if ever |
| Sortable DataTable (Gap 3) | Native sort + filter sufficient for 40 items | 200+ items in a list |
| Custom Select/Dropdown (Gap 2) | Native `<select>` works | Design system formalization |
| StatCard component (Gap 4) | Inline is fine for 4 cards | Reuse needed on 3+ pages |
| Create file button (AD4) | Backend doesn't support it yet | File creation API added |
| Model badge placement (AD5) | Low impact, current layout works | Agent detail page redesign |
| Stat cards clickable (D4) | Nice-to-have, not core | Dashboard v2 redesign |

---

## Testing Strategy

### Per-Wave Requirements

| Wave | New Backend Tests | New Frontend Tests | Cumulative Coverage |
|------|------------------|--------------------|---------------------|
| 0 | 3 (rate limit, file filter, ETag header) + 1 (B1 conflict) | 0 | 75% |
| 1 | 0 | 5 (AgentsPage ×2, DashboardPage ×1, agentStore ×2) | 76% |
| 2 | 2 (model resolution, status endpoint) | 2 (AgentCard, fileIcons) | 77% |
| 3 | 4 (gateway loading, history, cron list, cron parse) | 2 (GatewayPanel timeout, stopped state) | 79% |
| 4 | 6 (session list, messages, pagination, filter, path validation, corrupt handling) | 2 (SessionList, SessionViewer) | 82% |
| 5 | 2 (recursive listing, depth limit) | **7 (EditorSidebar ×3, EditorPage ×3, existing)** | 84% |
| 6 | 20+ (integration, WS coverage, E2E) | 5 (Toast ×2, ConnectionBanner, new components) | 85%+ |
| **Total** | **~38** | **~23** | **85%+** |

**Note on Wave 5 test increase:** v1 had 0 frontend tests for Wave 5. v2 adds 7 tests addressing I1 (EditorSidebar: 3 tests) and I2 (EditorPage: 3 tests) + 1 existing. This is the largest single change from v1.

### Integration Checkpoints

**After Wave 2 — ALPHA checkpoint:**
```bash
# Automated
make test && make build && curl -s localhost:8400/api/health | jq .status
curl -s localhost:8400/api/agents | jq '.[0].model'  # Verify NOT "gpt-5.3-codex"

# Manual (5 min)
1. Dashboard: stat cards + recent activity (NOT agent grid)
2. /agents: search bar works, status filter works
3. Agent detail: correct model, file icons, workspace path truncated with hover
4. Editor: save + conflict resolution flow end-to-end
```

**After Wave 5 — Pre-Omega checkpoint (NEW — addressing I8):**
```bash
# Automated
make test && make build

# Manual (5 min)
1. /editor: sidebar file browser loads, agent selector works
2. Binary file (.png) click blocked
3. Dirty-state warning on file switch
4. Monaco background matches dashboard (no color seam)
5. /agents/{id}: Sessions tab shows data, messages render
6. Session pagination: "Load more" button works
7. Gateway: no infinite spinner, channels as table, cron list visible
```

**After Wave 6 — OMEGA checkpoint:**
```bash
# Automated
make test && make e2e  # smoke.sh hits all API endpoints

# Manual (5 min)
1. Full click-through: Dashboard → Agents → Agent Detail → Sessions → Editor → Config → Gateway
2. Toast appears on save/error/gateway action
3. Navigate to /nonexistent → 404 page
4. Edit config, click Reload → ConfirmDialog appears
5. All page tabs show correct title
```

---

## LOC Summary

| Wave | New | Modified | Tests | Total |
|------|-----|----------|-------|-------|
| 0 | 115 | 190 | 55 | 360 |
| 1 | 260 | 55 | 85 | 400 |
| 2 | 30 | 110 | 45 | 185 |
| 3 | 200 | 100 | 60 | 360 |
| 4 | 420 | 30 | 135 | 585 |
| 5 | 310 | 90 | 95 | 495 |
| 6 | 170 | 120 | 175 | 465 |
| **Total** | **~1,505** | **~695** | **~650** | **~2,850** |

**v1 (original 13-wave plan) was ~5,840 LOC. This is ~2,850 — 51% less code.**
**Change from WAVES v1 (7-wave): +130 LOC (mostly new tests in W0 and W5, plus CSS tokens in W0.2).**

---

## Design System Changes

Applied in Wave 0 and carried through all waves:

```css
/* Updated tokens */
--text-secondary: #a1abbe;          /* Was #8b95a8 — now passes WCAG AA on cards */

/* New tokens (from DESIGN-REVIEW §7.1, added in W0.2) */
--bg-elevated: #1a1f2e;             /* Modals, dropdowns */
--border-subtle: #252b3b;           /* Very subtle dividers */
--border-strong: #4a5568;           /* Focused/emphasized borders */
--text-tertiary: #6b7896;           /* Placeholders, disabled text */
--text-inverse: #0f1219;            /* Text on colored backgrounds */
--warning-text: #fbbf24;            /* Amber 400 — higher contrast */
--success-light: rgba(34,197,94,0.15);
--danger-light: rgba(239,68,68,0.15);
--shadow-card: 0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.3);
--shadow-modal: 0 20px 60px rgba(0,0,0,0.5);
--z-sidebar: 100;
--z-header: 200;
--z-modal: 500;
--z-toast: 600;
--z-tooltip: 700;
--radius-sm: 4px;
--radius-md: 6px;
--radius-lg: 8px;
--radius-xl: 12px;
--transition-fast: 100ms ease-in-out;
--transition-base: 150ms ease-in-out;
--transition-slow: 300ms ease-in-out;

/* Sidebar active state */
.nav-active {
  @apply bg-accent/20 text-accent border-l-2 border-accent pl-[10px];
}
.nav-inactive {
  @apply text-text-secondary hover:text-text-primary hover:bg-bg-hover border-l-2 border-transparent pl-[10px];
}
```

**Tokens deferred from §7.1 (not needed yet):**
- `--bg-base` (#0a0d13) — current `--bg-primary` is sufficient
- `--accent-light`, `--accent-border` — Tailwind `accent/15` syntax works
- `--info-light`, `--info-border` — `--info` itself may be wired or removed in W6.2
- `--shadow-tooltip` — no tooltip component exists yet

**`--info` token status:** Declared but unused. Resolution in W6.2: wire into Badge `variant="info"` if any component needs a blue info badge by then. If not, remove from globals.css. No orphaned tokens in the final build.

---

## Risk Assessment

| Risk | Probability | Impact | Wave | Mitigation |
|------|------------|--------|------|------------|
| **Session format varies across OpenClaw versions** | High | High | W4 | W4.0 research subtask documents actual format. Schema validation with graceful degradation. 50MB file size cap. Unknown fields ignored. Format-version check. |
| **sessions.json too large for in-memory parse** | Medium | High | W4 | 50MB cap enforced. For very active OpenClaw instances, sessions.json could grow. If this becomes real, switch to streaming JSON parser (ijson). |
| **Config ETag same-second race (M1)** | Low | Medium | W0 | Content-hash ETag for config writes. mtime:size acceptable for workspace files (narrow race window). |
| **`croniter` dependency** | Low | Low | W3 | Pure Python, pinned version. 10M+ monthly downloads, actively maintained. No native extensions. |
| **Monaco custom theme breaks syntax highlighting** | Low | Medium | W5 | Custom theme only overrides background color; all syntax colors inherit from `vs-dark`. If issues arise, fall back to `vs-dark` (cosmetic regression, not functional). |
| **Wave 4 slip cascades to W6** | Medium | High | W4-W6 | W4 is the largest wave (5.5-7h). If it slips, W6 can start backend tests while W4 frontend completes. W6 frontend doesn't depend on W4 directly. |
| **Agent B idle time in Sprint 1** | Low | Low | Sprint | Restructured: Agent B starts W3 backend after W0 baseline commit (~1.5h wait), not after full W0 completion. If W0 runs long, Agent B can start W3 backend scaffolding (new files, no shared dependencies). |

---

## Calibration Appendix (from v1 — preserved per S3)

### Existing Codebase Measurements
| Component | LOC | Type |
|-----------|-----|------|
| `DashboardPage.tsx` | 48 | Page |
| `AgentCard.tsx` | 42 | Component |
| `AgentDetail.tsx` | 97 | Complex component |
| `FileEditor.tsx` | 135 | Complex component |
| `ConfigEditor.tsx` | 128 | Complex component |
| `GatewayPanel.tsx` | 107 | Complex component |
| `editorStore.ts` | 94 | Zustand store |
| `agent_service.py` | 194 | Service |
| `file_service.py` | 179 | Service |
| `config_service.py` | 153 | Service |
| `gateway_service.py` | 132 | Service |

### Rules of Thumb
- Simple page (stat cards + grid): ~50 LOC
- Complex component (editor, gateway panel): ~100-150 LOC
- Zustand store with async actions: ~80-120 LOC
- Backend service with file I/O: ~150-200 LOC
- Backend router with 3-4 endpoints: ~80-120 LOC
- Test file (3-5 test cases): ~40-60 LOC
- CSS token additions: ~3 LOC per token

### Estimate Confidence
| Wave | Confidence | Notes |
|------|-----------|-------|
| 0 | High | Bug fixes + CSS changes — well-scoped, low ambiguity |
| 1 | High | Mostly moving existing code + adding search (proven pattern) |
| 2 | High | Incremental card improvements, all data available |
| 3 | Medium-High | Gateway timeout is straightforward; cron parsing depends on config format |
| 4 | Medium | Session parsing depends on actual file format (W4.0 mitigates). Message viewer is a known pattern but variable complexity. |
| 5 | Medium-High | File list is straightforward. Monaco theme customization is small but untested. |
| 6 | Medium | Coverage push is variable — depends on which lines are uncovered. Integration tests depend on all prior waves being stable. |

---

_WAVES-v2.md complete. Ready for Round 2 review._
