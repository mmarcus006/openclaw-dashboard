# WAVES-v3.md — OpenClaw Dashboard Development Plan
_Version: 3.0 | Revised: 2026-02-25 | Round: 3/5_

## Changelog from v2

### Improvements Addressed (Round 2)
- **I-R2.1 (Wave 4 LOC underestimates):** Revised W4.1 from 100→160 impl, W4.3 from 120→200 impl. Wave 4 total moves from 585→720 LOC, time estimate from 5.5-7h→6.5-8.5h. Project total LOC updated from ~2,850→~2,985.
- **I-R2.2 (Per-task exit criteria):** Added one-line "Exit:" to every task in Waves 1-6. Format matches Wave 0's existing style. Each exit criterion is specific, testable, and scoped to that task only.
- **I-R2.3 (Pydantic response models):** Defined model names, field types, and file locations for all 5 new API endpoints: `GatewayCommandEntry`/`GatewayHistoryResponse`, `CronJobEntry`/`CronJobListResponse`, `SessionSummary`/`SessionListResponse`, `SessionMessage`/`SessionMessageListResponse`, `FileEntry`/`FileListResponse`. All in `backend/app/models/`.
- **I-R2.4 (sessionStore agent-change):** Added to W4.3: sessionStore clears `sessions` array and resets to loading state when `selectedAgentId` changes. No stale data flash on agent navigation.
- **I-R2.5 (Wave 4 backend tests sparse):** Added 5 edge-case tests: `test_sessions_json_too_large`, `test_empty_sessions_json`, `test_unknown_format_version`, `test_malformed_jsonl_lines_skipped`, `test_jsonl_file_too_large`. Wave 4 backend tests: 6→11. Testing strategy table updated.
- **I-R2.6 (DESIGN-TRACKING.md outdated):** Added note to WAVES-v3 instructing implementers to prepend a superseded notice to DESIGN-TRACKING.md during W0. See W0.0 task.
- **I-R2.7 (W3.3 cron error handling):** Added malformed cron expression handling: show job with "Invalid schedule" in Next Run column, `text-danger` styling. Don't fail the entire list.

### Reviewer Questions Answered (Round 2)
- **RQ2.1 (sessionStore on agent change):** Addressed via I-R2.4 — store clears and reloads.
- **RQ2.2 (gateway history in-memory):** Yes, in-memory only. Documented explicitly in W3.2 — history resets on backend restart, which is acceptable for a dev tool.
- **RQ2.3 (message truncation scope):** Clarified in W4.2 — truncation is list-level only. The same endpoint with `full=true` query param returns untruncated content. No separate endpoint needed.
- **RQ2.4 (500+ workspace files):** Added `max_files=200` server-side limit to W5.1 with a `truncated: true` flag when exceeded.
- **RQ2.5 (coverage 85% scope):** Clarified in W6.4 exit criteria — 85% is backend coverage. Frontend target is 70%+ (component tests). Combined ≥80%.

### Other Changes
- Added W0.0 meta-task: prepend superseded notice to DESIGN-TRACKING.md.
- Updated LOC Summary table with revised Wave 4 estimates.
- Updated Testing Strategy table with new Wave 4 edge-case tests.
- Updated Risk Assessment: Wave 4 slip risk revised with new time estimate.
- Sprint parallelism adjusted for Wave 4's increased scope.

---

## Decisions (Reviewer Questions Q1–Q5, from Round 1)

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
| 4 | Session Viewer | Research + session list + message viewer on agent detail page | 6.5-8.5 hrs | Wave 1 | — |
| 5 | Editor Upgrade | File browser sidebar (flat list), binary detection, agent selector, Monaco theme | 3.5-5 hrs | Wave 0 | — |
| 6 | Toast, Polish & Hardening | Toast system, 404 page, confirm dialogs, coverage push to 85% | 4-5 hrs | Waves 1-5 | ✅ **OMEGA** |

**Total: ~27-34 dev hours across 39 tasks. That's 40-55% less than the original 13-wave plan.**

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
Sprint 1 (~8-9 hrs):
  Agent A (Frontend): Wave 0 (solo, 1-2h) → commit baseline → Wave 1 (4-5h)
  Agent B (Backend):  Waits for W0 baseline commit (~1.5h) → Wave 3 backend (2-3h) → Wave 4 backend (4-5h)

Sprint 2 (~7-8 hrs):
  Agent A (Frontend): Wave 2 (3-4h) → Wave 4 frontend (3-4h)
  Agent B (Backend):  Wave 5 backend (1-2h) → Wave 5 frontend (2-3h) → start Wave 6 tests

Sprint 3 (~4-6 hrs):
  Agent A (Frontend): Wave 6 frontend (2-3h) → integration checkpoint
  Agent B (Backend):  Wave 6 backend + E2E smoke script (2-3h)
```

**Why Agent A does W0 solo:** Wave 0 is 2-3 hours of CSS fixes, component scaffolding, and bug fixes. Having two agents touch `globals.css`, `editorStore.ts`, and component files simultaneously creates merge conflicts. Agent A does W0, commits a clean baseline, then both agents diverge on non-overlapping files.

**Why Agent B starts W3 not W1:** W1 (Dashboard/Agents split) is almost entirely frontend (new AgentsPage, rewrite DashboardPage, update router). W3 has a backend-heavy component (gateway service, cron service, new API endpoints) that Agent B can start while Agent A works W1 frontend. This eliminates the 1-2h idle wait identified in I3.

**Note on Wave 4 time increase:** Wave 4 is now estimated at 6.5-8.5h (up from 5.5-7h) due to revised LOC estimates (I-R2.1) and additional edge-case tests (I-R2.5). Agent B handles W4 backend in Sprint 1, Agent A handles W4 frontend in Sprint 2. If W4 backend slips, Agent A can start W2 frontend in parallel.

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
| E3-A — Monaco theme mismatch | P2 Medium | W5 | W5.3 | Custom Monaco theme |
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
| Info — Wire or remove --info | P3 Low | W6 | W6.2 | Wire into Badge info variant |

**Coverage: 56 items tracked. 38 planned in waves, 8 already passing, 7 cut with rationale, 3 in backlog.**

---

## Pydantic Response Models — New API Endpoints

All new endpoints must define Pydantic response models so `make types` (openapi-typescript) generates correct frontend types.

### Model Definitions

```python
# backend/app/models/gateway.py (NEW)

class GatewayCommandEntry(BaseModel):
    command: str                   # e.g., "start", "stop", "restart"
    timestamp: str                 # ISO 8601
    exit_code: int                 # 0 = success
    output: str | None = None     # stdout/stderr snippet (max 500 chars)

class GatewayHistoryResponse(BaseModel):
    commands: list[GatewayCommandEntry]
    total: int
```

```python
# backend/app/models/cron.py (NEW)

class CronJobEntry(BaseModel):
    name: str                          # job name from config
    schedule: str                      # raw cron expression
    schedule_human: str                # cronstrue output, e.g., "Every 30 minutes"
    next_run: str | None = None        # ISO 8601 or None if invalid
    enabled: bool
    error: str | None = None           # "Invalid schedule" if croniter fails

class CronJobListResponse(BaseModel):
    jobs: list[CronJobEntry]
    total: int
```

```python
# backend/app/models/session.py (NEW)

class SessionSummary(BaseModel):
    session_id: str                         # unique session key
    updated_at: int                         # Unix timestamp (ms)
    model: str | None = None                # e.g., "claude-opus-4-6"
    label: str | None = None                # human-readable label
    spawned_by: str | None = None           # parent session key
    total_tokens: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    message_count: int | None = None        # total JSONL lines if known

class SessionListResponse(BaseModel):
    sessions: list[SessionSummary]
    total: int
    warning: str | None = None              # e.g., "Unknown session format version X"

class SessionMessage(BaseModel):
    role: str                                # "user", "assistant", "system", "tool"
    content: str                             # message text (may be truncated)
    timestamp: str | None = None             # ISO 8601 if available
    tool_calls: list[dict] | None = None     # raw tool call objects
    tokens: int | None = None                # token count if available

class SessionMessageListResponse(BaseModel):
    messages: list[SessionMessage]
    total: int
    has_more: bool
    skipped_lines: int = 0                   # malformed JSONL lines skipped
    warning: str | None = None               # e.g., "Session file too large (>50MB)"
```

```python
# backend/app/models/file.py (EXTEND existing)

class FileEntry(BaseModel):
    name: str                                # filename
    path: str                                # relative path from workspace root
    size: int                                # bytes
    mtime: float                             # Unix timestamp
    is_binary: bool                          # detected by extension
    is_directory: bool = False

class FileListResponse(BaseModel):
    files: list[FileEntry]
    total: int
    truncated: bool = False                  # True if max_files limit hit
```

### Endpoint → Model Mapping

| Endpoint | Wave | Request Model | Response Model | File |
|----------|------|---------------|----------------|------|
| `GET /api/gateway/history` | W3.2 | — | `GatewayHistoryResponse` | `models/gateway.py` |
| `GET /api/cron` | W3.3 | — | `CronJobListResponse` | `models/cron.py` |
| `GET /api/agents/{id}/sessions` | W4.1 | `limit: int=20, offset: int=0` (query) | `SessionListResponse` | `models/session.py` |
| `GET /api/sessions/{id}/messages` | W4.2 | `limit: int=50, offset: int=0, full: bool=false` (query) | `SessionMessageListResponse` | `models/session.py` |
| `GET /api/agents/{id}/files` | W5.1 | `recursive: bool=false, depth: int=2, max_files: int=200` (query) | `FileListResponse` | `models/file.py` |

---

## Wave 0: Foundation

### Goal
Fix all known bugs (B1, M1, M2, m1-m8) AND the designer's quick-wins AND extend the design system tokens AND build the 4 shared components that unblock later waves. This is the "clean the house before renovating" wave.

### Time: 2-3 hours

### Tasks

**W0.0: Supersede DESIGN-TRACKING.md (NEW — addressing I-R2.6)**
- Prepend a notice to the top of `DESIGN-TRACKING.md`:
  ```markdown
  > ⚠️ **Superseded.** The authoritative designer issue tracking table is in WAVES-v3.md (§ Designer Issue Tracking). This file reflects the Round 1 snapshot and is preserved for historical reference only.
  ```
- Files: `DESIGN-TRACKING.md`
- LOC: ~3 modified
- Exit: DESIGN-TRACKING.md opens with superseded notice. No ambiguity about which tracking table is authoritative.

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
- **Design System token expansion** (from DESIGN-REVIEW §7.1):
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
8. DESIGN-TRACKING.md has superseded notice (W0.0)

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
- Exit: `/agents` renders SearchInput + status dropdown. Typing "main" shows only matching agents. Selecting "Active" shows 0 agents when none active.

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
- Exit: `/` shows 4 stat cards with icons, recent activity list (5 agents), gateway summary, and quick nav cards. No AgentGrid import.

**W1.3: Add search/filter/sort state to agentStore**
- `setSearchTerm(s)`, `setStatusFilter(s)`, `setSortBy(field, dir)`
- Selector `filteredAgents()` returns matching agents
- Persist filter state during session (not across reloads)
- Test: `frontend/src/stores/__tests__/agentStore.test.ts` — 2 tests (filter + sort correctness)
- Files: `agentStore.ts`
- LOC: ~30 test + ~40 impl
- Exit: `filteredAgents()` selector returns correct subset for search term + status filter + sort. Filter state persists within session.

**W1.4: Update router and sidebar**
- `/agents` → `AgentsPage` (not `DashboardPage`)
- Sidebar: both "Dashboard" and "Agents" as separate nav items
- Active state correctly highlights current route
- Files: `router.tsx`, `Sidebar.tsx`
- LOC: ~15 impl
- Exit: Clicking "Dashboard" in sidebar navigates to `/` (fleet summary). Clicking "Agents" navigates to `/agents` (agent grid with search). Sidebar active state highlights current route.

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
- Exit: `curl /api/agents | jq '.[0].model'` returns the agent's session model (e.g., `claude-opus-4-6`), not the config default. Agent with no sessions returns config default.

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
- Exit: Cards have colored left-border stripe (green/amber/gray). Active dots pulse. "Never" timestamps show "No sessions yet" in muted text. Hover lifts card with shadow.

**W2.3: File type icons + detail page polish**
- Map extensions to Lucide icons: `.md`→FileText, `.json`→Braces, `.png/.jpg`→Image, `.py/.ts/.js`→FileCode, `.sh`→Terminal (AD2)
- Add focus-visible ring on file table rows (CC5): `focus-visible:outline-2 focus-visible:outline-accent focus-visible:outline-offset-[-2px]`
- Truncate long workspace paths with `truncate` class + `title` attribute for hover (AD6)
- Test: `frontend/src/utils/__tests__/fileIcons.test.ts` — 1 test (icon resolver returns correct icon per extension)
- Files: `AgentDetail.tsx`, new `fileIcons.ts` utility
- LOC: ~10 test + ~30 impl
- Exit: File list shows differentiated icons per extension (.md=FileText, .json=Braces, .png=Image, etc.). File rows have focus-visible ring. Workspace paths truncate with hover showing full path.

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
- Exit: Gateway page loads in <2s. API timeout after 5s shows error state. Stopped gateway shows prominent Start button. Disabled buttons have tooltips.

**W3.2: Channels table + command history**
- Replace `JSON.stringify(channels)` with a proper table: Channel | Status | Provider (G4)
- Expand gateway panel to `max-w-4xl` (G2)
- Add "Last Command Output" section below controls (already partially exists)
- Show last 5 commands with timestamp + exit code (green 0 / red non-zero)
- When no commands have been run: show "No recent commands" placeholder text (G3)
- Backend: store last 10 commands in memory, new `GET /api/gateway/history`
  - **Response model:** `GatewayHistoryResponse` (see Pydantic Models section)
  - **In-memory only:** History resets on backend restart. This is acceptable for a dev tool — no persistence needed. Document this in a code comment so implementers don't try to add disk storage.
- Test: `backend/tests/test_gateway_service.py::test_history` — 1 test (history returns commands)
- Files: `GatewayPanel.tsx`, `gateway_service.py`, `gateway.py` (router), `models/gateway.py` (new)
- LOC: ~15 test + ~60 impl
- Exit: Channels render as table (not JSON). Last 5 commands shown with timestamp + exit code. "No recent commands" placeholder when history empty.

**W3.3: Cron job viewer (section on Gateway page)**
- New `CronJobList.tsx` component rendered below gateway controls
- Backend: `GET /api/cron` — reads cron jobs from openclaw.json
  - **Response model:** `CronJobListResponse` (see Pydantic Models section)
- Display: table with Name | Schedule (human readable) | Next Run | Enabled
- Human-readable schedule: use `cronstrue` npm package (e.g., "Every 30 minutes")
- Next run: compute from cron expression using `croniter` in Python backend
  - _Rationale for `croniter` (Q4):_ Standard library (10M+ monthly PyPI downloads), handles edge cases (DoW+DoM conflicts, ranges with steps) that a regex parser would miss. Pure Python, no native extensions. Pinned in `pyproject.toml`.
  - **Error handling (I-R2.7):** If `croniter` raises `ValueError` or `KeyError` on a malformed cron expression, catch the exception and return the job with `next_run: null` and `error: "Invalid schedule"` in the `CronJobEntry`. Frontend renders "Invalid schedule" in the Next Run column with `text-danger` styling. Don't fail the entire list for one bad expression.
- "No cron jobs" empty state using W0.3 EmptyState component
- Why same page: Gateway and Cron are both "ops" — users checking gateway status will also want to see scheduled jobs. One page, two sections.
- Test: `backend/tests/test_cron_service.py` — 2 tests: `test_cron_list` (cron list parses config correctly), `test_malformed_cron_expression` (bad expression returns error field, doesn't crash)
- Files: `CronJobList.tsx` (new), `cron.py` (new router), `cron_service.py` (new), `models/cron.py` (new), `GatewayPage.tsx`
- LOC: ~30 test + ~100 impl
- Dep: `croniter` (Python), `cronstrue` (npm)
- Exit: Cron section shows jobs from config with human-readable schedule (cronstrue) and computed next run (croniter). Malformed expressions show "Invalid schedule" in red. Empty state for no jobs.

### Exit Criteria (Wave 3)
1. Gateway page loads in <2 seconds — never shows infinite spinner
2. Channels render as a readable table
3. Cron jobs display with human-readable schedules
4. Malformed cron expressions show "Invalid schedule" without breaking the list
5. Command history shows after gateway actions
6. "No recent commands" placeholder when no commands run
7. All tests pass

---

## Wave 4: Session Viewer

### Goal
THE killer feature. Show what agents have been doing. Session list on agent detail page + conversation message viewer. Starts with a research subtask to document the actual session file format.

### Time: 6.5-8.5 hours _(revised from 5.5-7h per I-R2.1)_

### Tasks

**W4.0: Research — document session file format**
- Read `~/.openclaw/sessions/sessions.json` and 2-3 JSONL session files
- Document: (a) session index schema (keys, fields, types), (b) JSONL message schema (role, content, timestamp, tool calls, etc.), (c) file size distribution (min/max/median), (d) any format-version indicators
- Output: `docs/session-format.md` in the project — referenced by W4.1 and W4.2
- Identify: which fields are guaranteed vs optional, max observed file size, encoding
- Time: 30 minutes
- Exit: Schema documented with field types and optionality. Implementers can code against documented schema without guessing.

**W4.1: Backend — session list from sessions.json**
- Parse `sessions.json` (dict keyed by session key)
- For each session: extract `sessionId`, `updatedAt`, `model`, `label`, `spawnedBy`, `totalTokens`, `inputTokens`, `outputTokens`
- **Response model:** `SessionListResponse` containing `list[SessionSummary]` (see Pydantic Models section)
- Filter by agent: session key starts with `agent:{agent_id}:` (main, subagent, etc.)
- Sort by `updatedAt` descending
- Endpoint: `GET /api/agents/{agent_id}/sessions?limit=20&offset=0`
- Handle missing/corrupt sessions.json gracefully
- **Explicit constraints (from I6):**
  - `sessions.json` file size cap: 50MB. If larger, return `413 Payload Too Large` with message "Session index too large to process".
  - Schema validation: unknown fields are ignored (forward-compatible). Missing expected fields default to `null`.
  - Format-version detection: if `sessions.json` contains a top-level `version` key, validate it. If unknown version, return data with a `warning: "Unknown session format version X"` field in `SessionListResponse`.
  - Empty `sessions.json` (valid JSON `{}`): return `{sessions: [], total: 0}` — not an error.
- Test: `backend/tests/test_session_service.py` — 6 tests:
  - `test_list_sessions` — returns sessions sorted by updatedAt desc
  - `test_filter_by_agent` — only agent-prefixed sessions returned
  - `test_missing_sessions_json` — returns empty list, no error
  - `test_sessions_json_too_large` — returns 413 when >50MB _(NEW — I-R2.5)_
  - `test_empty_sessions_json` — returns `{sessions: [], total: 0}` _(NEW — I-R2.5)_
  - `test_unknown_format_version` — returns data with warning field _(NEW — I-R2.5)_
- Files: `session_service.py` (new), `sessions.py` (new router), `models/session.py` (new)
- LOC: ~80 test + ~160 impl _(revised from 50 test + 100 impl per I-R2.1)_
- Exit: `GET /api/agents/{id}/sessions` returns paginated sessions sorted by updatedAt desc. Filter by agent key prefix works. 50MB cap returns 413. Empty file returns empty list. Unknown version returns warning field.

**W4.2: Backend — session messages from JSONL file**
- Read `sessionFile` path from session data
- Parse JSONL: each line is a JSON object with role, content, timestamp, etc.
- **Response model:** `SessionMessageListResponse` containing `list[SessionMessage]` (see Pydantic Models section)
- Pagination: offset-based (line number), limit 50 per request
- Truncate content to 2000 chars in list response. Pass `full=true` query param for untruncated content (same endpoint, no separate endpoint needed).
- Endpoint: `GET /api/sessions/{session_id}/messages?limit=50&offset=0&full=false`
- Handle missing JSONL files, malformed lines (skip with warning), binary content
- **Explicit constraints (from I6):**
  - JSONL file size cap: 50MB. If larger, return `{messages: [], total: 0, has_more: false, skipped_lines: 0, warning: "Session file too large (>50MB)"}`.
  - Malformed lines: skip silently, increment `skipped_lines` counter in the `SessionMessageListResponse`.
  - Encoding: assume UTF-8. On decode errors, replace invalid bytes with U+FFFD.
- Security: validate sessionFile path is under OPENCLAW_HOME (path traversal prevention)
- Test: `backend/tests/test_session_service.py` — 5 tests:
  - `test_parse_jsonl_messages` — parses valid JSONL and returns messages
  - `test_message_pagination` — offset/limit work correctly
  - `test_path_traversal_blocked` — `../` in path returns 403
  - `test_malformed_jsonl_lines_skipped` — bad lines skipped, counter incremented _(NEW — I-R2.5)_
  - `test_jsonl_file_too_large` — returns warning when >50MB _(NEW — I-R2.5)_
- Files: `session_service.py`, `sessions.py`
- LOC: ~70 test + ~80 impl
- Exit: `GET /api/sessions/{id}/messages` returns paginated JSONL messages. Malformed lines skipped with counter in response. Path traversal returns 403. `full=true` returns untruncated content.

**W4.3: Frontend — session list tab on agent detail**
- Add tabs to AgentPage: "Files" | "Sessions"
- Session list: date, message count, model, token count, duration
- Click session → expand inline to show messages (not a separate page)
- Use Skeleton component from W0.3 for loading
- Infinite scroll for session list (load more button, not auto-scroll)
- **New store:** `sessionStore.ts` (Zustand) with:
  - `sessions: SessionSummary[]`, `loading: boolean`, `selectedAgentId: string | null`
  - `fetchSessions(agentId, offset)` — async action
  - **Agent-change behavior (I-R2.4):** When `selectedAgentId` changes, immediately clear `sessions` array and set `loading: true`. The `sessions()` selector returns empty array during loading. This prevents stale data flash when navigating between agents (e.g., `/agents/main` → `/agents/coder`).
  - `clearAndLoad(agentId)` — convenience method: sets `selectedAgentId`, clears sessions, fetches new data
- Test: `frontend/src/components/sessions/__tests__/SessionList.test.tsx` — 1 test (session list renders with mock data)
- Files: `SessionList.tsx` (new), `AgentPage.tsx`, `sessions.ts` (new API module), `sessionStore.ts` (new)
- LOC: ~25 test + ~200 impl _(revised from 20 test + 120 impl per I-R2.1: store 100 + component 60 + API 20 + page mods 20)_
- Exit: Agent detail page has Files/Sessions tabs. Sessions tab loads session list from API. Switching agents clears stale data immediately. "Load more" button loads next page. Empty state for agents with no sessions.

**W4.4: Frontend — conversation message viewer**
- Messages in conversation layout: user messages right-aligned, assistant left-aligned
- Code blocks with syntax highlighting (reuse Monaco's language tokenizer OR use a lightweight lib like `highlight.js`)
- Long messages: "Show more" toggle (collapsed at 500 chars)
- Token count per message if available
- Copy button on messages (use navigator.clipboard)
- Test: `frontend/src/components/sessions/__tests__/SessionViewer.test.tsx` — 1 test (message viewer renders roles correctly)
- Files: `SessionViewer.tsx` (new)
- LOC: ~15 test + ~120 impl
- Exit: Messages render in conversation layout (user right, assistant left). Code blocks highlighted. Long messages collapsed at 500 chars with "Show more". Copy button works.

### Exit Criteria (Wave 4)
1. Agent detail shows session list with real data
2. Clicking a session shows conversation messages
3. Pagination works for both session list and messages
4. Large sessions (1000+ messages) don't crash the UI
5. Session files >50MB show a graceful warning (not a crash)
6. Schema format documented in `docs/session-format.md`
7. Agent navigation clears session data (no stale flash)
8. All tests pass, 11 new backend tests + 2 frontend tests

---

## Wave 5: Editor Upgrade

### Goal
Add a file browser to the editor so users don't have to navigate back to agent detail to open another file. Keep it simple — flat list with agent dropdown, not a full tree. Fix Monaco theme mismatch.

### Time: 3.5-5 hours

### Tasks

**W5.1: Backend — recursive file listing endpoint**
- `GET /api/agents/{agent_id}/files?recursive=true&depth=2&max_files=200`
- **Response model:** `FileListResponse` containing `list[FileEntry]` (see Pydantic Models section)
- Returns flat list of files with relative paths (not nested tree — frontend can group if needed)
- Exclude: `.git`, `node_modules`, `.venv`, `__pycache__`
- Max depth 3 enforced server-side
- **Max files limit (RQ2.4):** Default `max_files=200`. If directory has more files, return first 200 sorted by path with `truncated: true` in response. Prevents runaway responses for agents with 500+ workspace files.
- Include: size, mtime, is_binary (detect by extension: `.png`, `.jpg`, `.gif`, `.webp`, `.ico`, `.woff`, `.woff2`, `.ttf`, `.pdf`, `.zip`, `.tar`, `.gz`)
- Test: `backend/tests/test_agent_service.py` — 3 tests: `test_recursive_listing`, `test_depth_limit`, `test_max_files_truncation` (new — verifies truncated flag)
- Files: `agents.py` (router), `agent_service.py`, `models/file.py` (extend)
- LOC: ~40 test + ~60 impl
- Exit: `GET /api/agents/{id}/files?recursive=true` returns flat list with size, mtime, is_binary. Max depth 3 enforced. `.git`/`node_modules` excluded. >200 files returns `truncated: true`.

**W5.2: Frontend — file browser sidebar**
- Left sidebar (240px) with agent selector dropdown at top
- Flat file list below, grouped by directory (collapsible groups)
- File type icons from W2.3 utility
- Binary files: show with `cursor-not-allowed opacity-60`, no click action (AD3). Tooltip: "Binary files cannot be edited" (AD1)
- Current file highlighted with `bg-accent/15`
- Click file → load in editor. If dirty, show ConfirmDialog from W0.3
- Sidebar collapsible via toggle button
- URL updates: `/editor?agent=main&path=SOUL.md`
- **Test:** `frontend/src/components/editor/__tests__/EditorSidebar.test.tsx` — 3 tests:
  - (a) Agent dropdown renders and changing agent loads new file list
  - (b) Binary file click is blocked (no navigation, shows tooltip)
  - (c) File click with dirty state shows ConfirmDialog
- Files: `EditorSidebar.tsx` (new), `FileList.tsx` (new), `EditorPage.tsx`
- LOC: ~35 test + ~170 impl (80 sidebar + 60 file list + 30 modified)
- Exit: 240px sidebar with agent dropdown. Binary files show `cursor-not-allowed`. File click with dirty state shows ConfirmDialog. URL updates on file selection.

**W5.3: Editor layout integration + Monaco theme**
- EditorPage: `[Sidebar 240px][Monaco flex-1]`
- When no file selected: show EmptyState from W0.3 ("Select a file to edit")
- Layout prop `noPadding` for editor page (replace hacky `-m-6` negative margin)
- Add breadcrumb: `Agents / COS / SOUL.md` when editing a file
- **Custom Monaco theme (E3-A from DESIGN-REVIEW §4.6):** Create `openclaw-dark` Monaco theme that uses `--bg-primary` (#0f1219) as editor background instead of `vs-dark`'s #1e1e1e. This eliminates the jarring seam between editor and dashboard. Other colors (syntax highlighting) inherit from `vs-dark`.
- **Test:** `frontend/src/pages/__tests__/EditorPage.test.tsx` — 3 tests:
  - (a) Opening a file from sidebar loads it in the Monaco editor
  - (b) Switching files with unsaved changes shows ConfirmDialog warning
  - (c) URL updates reflect current agent and file path
- Files: `EditorPage.tsx`, `Layout.tsx`, `monacoTheme.ts` (new)
- LOC: ~30 test + ~60 impl
- Exit: Editor background matches dashboard (#0f1219). No color seam. Layout uses `noPadding` prop. Breadcrumb shows `Agents / {name} / {file}`.

### Exit Criteria (Wave 5)
1. Editor has file browser sidebar
2. Agent selector dropdown works
3. Binary files blocked from opening (visual indicator + no click)
4. Dirty state warning when switching files
5. Monaco editor background matches dashboard theme (no seam)
6. Layout uses `noPadding` prop (no negative margin hack)
7. >200 files handled gracefully (truncation notice)
8. **7 new frontend tests pass** (3 sidebar + 3 integration + 1 existing)

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
Final wave. Wire toast notifications into all operations, add 404 page, add confirm dialogs where missing, push coverage to 85% backend, and clean up any remaining issues.

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
- Exit: Toasts auto-dismiss at 5s, stack max 3, slide-in animation. All save/error/gateway operations trigger toasts. Amber banner on WS disconnect.

**W6.2: Config editor improvements + misc polish**
- Save button: tooltip "No unsaved changes" when disabled (C1)
- Config path: add `FileJson` icon (C2)
- Auto-validate JSON on change instead of manual button click (C4)
- Document title updates per page: `${title} — OpenClaw` using `useEffect` hook (CC7)
- Simplify config page title from "Config — openclaw.json" to "Config" (C6)
- **`--info` token resolution:** Wire into Badge component as `variant="info"` using `bg-info/15 text-[#60a5fa]` (blue-400 for contrast). If no component needs it by this point, remove the token from globals.css to avoid orphan.
- Files: `ConfigEditor.tsx`, `configStore.ts`, various pages (title hook), `Badge.tsx`
- LOC: ~50 impl
- Exit: Save tooltip says "No unsaved changes" when disabled. FileJson icon on config path. JSON validates on every keystroke. `document.title` updates per page.

**W6.3: Confirm dialogs + 404**
- Reload config when dirty → ConfirmDialog (C3)
- 404 page: "Page not found" with "Go home" button, uses Layout
- ErrorBoundary upgrade: "Something went wrong" with "Reload" button
- Files: `ConfigEditor.tsx`, `NotFoundPage.tsx` (new), `ErrorBoundary.tsx`, `router.tsx`
- LOC: ~60 impl
- Exit: Reload config when dirty shows ConfirmDialog. `/nonexistent` shows 404 page with "Go home" button.

**W6.4: Test coverage push to 85% backend**
- Backend integration tests: full request lifecycle (create file → read → verify)
- WebSocket test coverage: 25% → 60% (connect, ping/pong, events, disconnect)
- Frontend component tests for new components (SessionList, FileList, CronJobList)
- E2E smoke script: `make e2e` — starts backend, curls all endpoints, verifies status codes
  - _Rationale for shell over Playwright (Q5):_ Playwright adds ~200MB of browser binaries. Frontend behavior is covered by component tests (Vitest + Testing Library). Shell smoke tests cover backend API correctness, which is where bugs actually happen. If complex multi-step UI flows are added later, Playwright becomes worthwhile._
- Test: ~150 new test LOC
- Files: `test_integration.py` (new), `test_websocket.py` (expand), `smoke.sh` (new)
- LOC: ~150 test + ~30 impl (test utils + smoke script)
- Exit: `make test` green. `make e2e` (smoke.sh) green. **Backend coverage ≥85%.** **Frontend coverage ≥70% (component tests).** Combined ≥80%. WebSocket coverage ≥60%.

### Exit Criteria (Wave 6) — **CHECKPOINT OMEGA: Dashboard is complete**
1. All operations have toast feedback
2. 404 page works for invalid routes
3. Config reload warns when dirty
4. Backend coverage ≥ 85%
5. Frontend coverage ≥ 70%
6. WebSocket coverage ≥ 60%
7. `make test && make e2e` both green
8. Zero TS errors, `ruff check` clean
9. Document titles update per page
10. `--info` token either wired or removed (no orphans)

### What "Omega" means
After Wave 6, the dashboard is feature-complete for daily use:
- Fleet overview with real KPIs
- Agent search, filter, sort
- Agent detail with files + sessions + conversation viewer
- File editor with browser sidebar + custom theme
- Config editor with validation + conflict resolution
- Gateway management with cron job viewer
- Toast notifications for all operations
- 85%+ backend test coverage, 70%+ frontend coverage

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
| 3 | 4 (gateway loading, history, cron list, **cron malformed**) | 2 (GatewayPanel timeout, stopped state) | 79% |
| 4 | **11** (session list, filter, missing file, **50MB cap**, **empty file**, **unknown version**, messages, pagination, path validation, **malformed JSONL**, **JSONL too large**) | 2 (SessionList, SessionViewer) | 83% |
| 5 | **3** (recursive listing, depth limit, **max files truncation**) | **7 (EditorSidebar ×3, EditorPage ×3, existing)** | 85% |
| 6 | 20+ (integration, WS coverage, E2E) | 5 (Toast ×2, ConnectionBanner, new components) | 87%+ |
| **Total** | **~44** | **~23** | **BE ≥85%, FE ≥70%** |

**Changes from v2:**
- Wave 3 backend tests: 3→4 (added `test_malformed_cron_expression`)
- Wave 4 backend tests: 6→11 (added 5 edge-case tests per I-R2.5)
- Wave 5 backend tests: 2→3 (added `test_max_files_truncation`)
- Total backend tests: ~38→~44

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

**After Wave 5 — Pre-Omega checkpoint:**
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
| 0 | 115 | 193 | 55 | 363 |
| 1 | 260 | 55 | 85 | 400 |
| 2 | 30 | 110 | 45 | 185 |
| 3 | 200 | 100 | 70 | 370 |
| 4 | 480 | 30 | 190 | **720** |
| 5 | 310 | 90 | 105 | 505 |
| 6 | 170 | 120 | 175 | 465 |
| **Total** | **~1,565** | **~698** | **~725** | **~2,988** |

**Changes from v2:**
- Wave 3: tests 60→70 (+10, malformed cron test), total 360→370
- Wave 4: new 420→480, tests 135→190, total 585→**720** (revised per I-R2.1 + I-R2.5)
  - W4.1 impl: 100→160, tests: 50→80
  - W4.3 impl: 120→200, tests: 20→25
- Wave 5: tests 95→105 (+10, max files truncation test), total 495→505
- **Project total: ~2,850→~2,988 (+138 LOC, mostly tests and revised service estimates)**

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
| **Wave 4 slip cascades to W6** | Medium | High | W4-W6 | W4 is the largest wave (**6.5-8.5h**, revised up from 5.5-7h). If it slips, W6 can start backend tests while W4 frontend completes. W6 frontend doesn't depend on W4 directly. Agent B handles W4 backend in Sprint 1 to front-load risk. |
| **Large workspace (500+ files) slows file listing** | Low | Medium | W5 | `max_files=200` server-side limit with `truncated` flag in response. Depth 3 cap prevents deep traversal. |
| **Config ETag same-second race (M1)** | Low | Medium | W0 | Content-hash ETag for config writes. mtime:size acceptable for workspace files (narrow race window). |
| **`croniter` dependency** | Low | Low | W3 | Pure Python, pinned version. 10M+ monthly downloads, actively maintained. No native extensions. |
| **Monaco custom theme breaks syntax highlighting** | Low | Medium | W5 | Custom theme only overrides background color; all syntax colors inherit from `vs-dark`. If issues arise, fall back to `vs-dark` (cosmetic regression, not functional). |
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
| 3 | Medium-High | Gateway timeout is straightforward; cron parsing depends on config format. Malformed cron handling adds minor complexity. |
| 4 | Medium | Session parsing depends on actual file format (W4.0 mitigates). Revised LOC estimates (I-R2.1) are calibrated against rules-of-thumb. Edge-case tests (I-R2.5) add ~55 test LOC but are well-scoped. |
| 5 | Medium-High | File list is straightforward. Max-files limit (RQ2.4) is simple server-side check. Monaco theme customization is small but untested. |
| 6 | Medium | Coverage push is variable — depends on which lines are uncovered. Integration tests depend on all prior waves being stable. |

---

_WAVES-v3.md complete. Ready for Round 3 review._
