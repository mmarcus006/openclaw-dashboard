# WAVES-v4.md — OpenClaw Dashboard Development Plan
_Version: 4.0 | Revised: 2026-02-25 | Round: 4/5_

## Changelog from v3

### Critical Fixes (Round 4 — Adversarial Code Review)

- **C-R4.1 (JSONL format mismatch):** Rewrote `SessionMessage` Pydantic model. Real JSONL content is `list[ContentBlock]` (types: `text`, `thinking`, `toolCall`, `toolResult`), not a flat string. Added `ContentBlock` model, `JournalEntry` discriminated union for all JSONL entry types (`session`, `message`, `model_change`, `thinking_level_change`, `custom`, `compaction`). Updated W4.0 exit criteria with verified format. Updated W4.2 parsing to filter `type == "message"` entries only, concatenate text blocks before truncation. Updated W4.4 to render content blocks with type-specific styling. Verified against live JSONL: 463 messages, 53 custom entries, content blocks include text (377), thinking (72), toolCall (194).
- **C-R4.2 (`_last_activity()` broken):** Added W0.5 task — rewrite `_last_activity()` to iterate session keys matching `agent:{agent_id}:*` prefix instead of `sessions.get(agent_id)`. Parse `updatedAt` as int/ms Unix timestamp (not ISO string — `fromisoformat()` would also fail). Also fixes `_extract_agent_meta()` to read per-session model. This is a **prerequisite for W2.2** (status indicators). Added test `test_last_activity_real_key_format`.
- **C-R4.3 (sessions.json 71KB/session performance):** Added caching + selective parsing to W4.1. Skip `skillsSnapshot` field during parsing (62KB per entry). Cache parsed result with file-mtime invalidation. Use `asyncio.to_thread(json.loads, ...)` if >1MB. At 11 sessions = 784KB today; at 200 sessions = 14MB without mitigation. Updated Risk Assessment with scaling math.

### Important Fixes (Round 4)

- **I-R4.1 (Stale-fetch race):** W4.3 `fetchSessions()` now uses `AbortController` to cancel in-flight requests when `selectedAgentId` changes. Added test case: `test_stale_fetch_discarded`.
- **I-R4.2 (`file_changed` WS events):** Added mini-task to W6.1 — wire `file_changed` WebSocket events into a stale-file warning toast when the currently-edited file is modified externally. ~15 LOC addition.
- **I-R4.3 (W5.1 LOC underestimate):** Revised from 60→110 impl LOC. Current `_list_workspace_files()` is flat `iterdir()` — W5.1 needs recursion, depth limit, excludes, binary detection, max_files. Clarified this is a NEW function separate from the W0.4 m2 fix.
- **I-R4.4 (`_discover_agent_ids()` scans `~`):** Added fix to W0.5. Code does `home.parent.iterdir()` which scans entire home directory. Should be `home.iterdir()` — verified workspace-* dirs are IN `~/.openclaw/`, not `~/`.
- **I-R4.5 (Breadcrumb navigation guard):** W5.3 now specifies `beforeNavigate` guard on breadcrumb links when editor is dirty.
- **I-R4.6 (Deleted session files):** W4.2 now handles missing JSONL files gracefully — returns empty message list with `warning: "Session file not found (may have been archived)"`. 82% of sessionFile paths point to `.deleted.*` renamed files.
- **I-R4.7 (CSS `--warning-text` naming):** Renamed to `--warning-contrast` to avoid confusion with `--warning` in Tailwind utility generation.
- **I-R4.8 (W0.1 already fixed):** Noted that B1/M2 are likely already fixed in codebase. W0.1 time estimate adjusted — mostly verification, not implementation.

### LOC & Time Adjustments
- W0: +25 LOC (new W0.5 task for `_last_activity()` + `_discover_agent_ids()` fixes)
- W4.1: +30 LOC (caching layer + selective parsing)
- W4.2: +15 LOC (content block handling + deleted file handling)
- W4.3: +10 LOC (AbortController)
- W4.4: +20 LOC (content block rendering)
- W5.1: +50 LOC (revised estimate: 60→110)
- W6.1: +15 LOC (file_changed handler)
- **Project total: ~2,988→~3,153 (+165 LOC)**

---

## Decisions (Reviewer Questions Q1–Q5, from Round 1)

| # | Question | Decision | Rationale | Confidence |
|---|----------|----------|-----------|------------|
| Q1 | Is light theme needed? | **CUT.** Deferred to backlog. | This is a localhost dev tool. Miller uses dark mode. The entire codebase is dark-first. Adding light theme requires duplicating 15+ CSS variables, FOUC prevention, and testing all pages in both modes. ROI is negative. Revisit only if Miller explicitly requests it. | High |
| Q2 | Should D5 (model display bug) be in Wave 0? | **No. Stays in W2.1.** | D5 is a real bug (all agents show `gpt-5.3-codex`), but the fix requires reading per-session model data from `sessions.json`. This overlaps with W2's agent card work. Moving it to W0 would add session parsing to the foundation wave, increasing scope. The bug is cosmetic (doesn't block functionality), so W2 is appropriate. **UPDATE (v4):** W0.5 fixes the `_last_activity()` key lookup which unblocks W2.1's model fix — W2.1 can now read per-session model via the corrected session key iteration. | High |
| Q3 | What's the session JSONL format? | **VERIFIED in v4.** | Session index is `sessions.json` (flat dict keyed by session key like `agent:main:main`). Individual session files are JSONL with multiple entry types: `session`, `message`, `model_change`, `thinking_level_change`, `custom`, `compaction`. Message content is `list[ContentBlock]`, not a string. W4.0 research task kept for implementer verification but Pydantic models are now based on verified data. | High |
| Q4 | Is `croniter` the right dependency? | **Yes. Keep `croniter`.** | Standard library (10M+ monthly downloads, maintained). Pure Python, no native extensions. | High |
| Q5 | Should E2E be shell or Playwright? | **Shell (curl-based) for v1. Playwright deferred.** | Playwright adds ~200MB of browser binaries. Shell smoke tests cover backend API correctness. Frontend covered by component tests. | High |

---

## FINAL PLAN: 7 Waves

### Wave Overview

| Wave | Name | Scope | Est. Time | Dependencies | Milestone |
|------|------|-------|-----------|--------------|-----------|
| 0 | Foundation | Bug fixes (B1/M1/M2) + `_last_activity()` fix + designer quick-wins + CSS tokens + shared components | 2.5-3.5 hrs | None | — |
| 1 | Dashboard & Agents Split | Route fix, agents page with search/filter, dashboard as summary | 4-5 hrs | Wave 0 | — |
| 2 | Agent Cards & Status | Real status data, card polish, file type icons, contrast fixes | 3-4 hrs | Wave 0 | ✅ **ALPHA** |
| 3 | Gateway & Cron | Gateway loading fix, channels table, cron job list (same page) | 3-4 hrs | Wave 0 | — |
| 4 | Session Viewer | Research + session list + message viewer on agent detail page | 7-9 hrs | Wave 1 | — |
| 5 | Editor Upgrade | File browser sidebar (flat list), binary detection, agent selector, Monaco theme | 4-5.5 hrs | Wave 0 | — |
| 6 | Toast, Polish & Hardening | Toast system + file_changed handler, 404 page, confirm dialogs, coverage push to 85% | 4-5.5 hrs | Waves 1-5 | ✅ **OMEGA** |

**Total: ~28-36 dev hours across 40 tasks. That's 40-55% less than the original 13-wave plan.**

### Dependency Graph

```
Wave 0 (Foundation — includes _last_activity() fix)
  │
  ├──► Wave 1 (Dashboard/Agents Split) ──► Wave 4 (Session Viewer)
  │
  ├──► Wave 2 (Agent Cards & Status) ← requires W0.5 _last_activity() fix
  │
  ├──► Wave 3 (Gateway & Cron)
  │
  └──► Wave 5 (Editor Upgrade)
  
  Waves 1-5 all complete ──► Wave 6 (Polish & Hardening)
```

**Parallel execution (2 agents):**
```
Sprint 1 (~8-9 hrs):
  Agent A (Frontend): Wave 0 (solo, 1.5-2.5h) → commit baseline → Wave 1 (4-5h)
  Agent B (Backend):  Waits for W0 baseline commit (~2h) → Wave 3 backend (2-3h) → Wave 4 backend (4-5h)

Sprint 2 (~7-8 hrs):
  Agent A (Frontend): Wave 2 (3-4h) → Wave 4 frontend (3-4h)
  Agent B (Backend):  Wave 5 backend (1.5-2.5h) → Wave 5 frontend (2-3h) → start Wave 6 tests

Sprint 3 (~4-6 hrs):
  Agent A (Frontend): Wave 6 frontend (2-3h) → integration checkpoint
  Agent B (Backend):  Wave 6 backend + E2E smoke script (2-3h)
```

**Why Agent A does W0 solo:** Wave 0 is 2.5-3.5 hours of CSS fixes, component scaffolding, bug fixes, and the critical `_last_activity()` fix. Having two agents touch `globals.css`, `editorStore.ts`, `agent_service.py`, and component files simultaneously creates merge conflicts. Agent A does W0, commits a clean baseline, then both agents diverge on non-overlapping files.

**Why Agent B starts W3 not W1:** W1 (Dashboard/Agents split) is almost entirely frontend. W3 has a backend-heavy component (gateway service, cron service, new API endpoints) that Agent B can start while Agent A works W1 frontend.

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
| D5 — Model display bug | P1 High | W2 | W2.1 | Planned (unblocked by W0.5) |
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
# backend/app/models/session.py (NEW — REVISED in v4 based on verified JSONL format)

# --- Content block models (verified against live JSONL data) ---

class ContentBlock(BaseModel):
    """A single content block within a message.
    
    Verified types from live data:
      - "text": has `text` field
      - "thinking": has `text` field (may be empty string for redacted thinking)
      - "toolCall": has `id`, `name`, `input` fields (NO `text`)
      - "toolResult": has `toolCallId`, `content` fields
    """
    type: str                            # "text", "thinking", "toolCall", "toolResult"
    text: str | None = None              # present on text/thinking blocks
    # toolCall fields
    id: str | None = None                # tool call ID
    name: str | None = None              # tool name
    input: dict | None = None            # tool input args
    # toolResult fields
    tool_call_id: str | None = None      # references a toolCall.id
    content: str | list | None = None    # tool result content

    def extract_text(self) -> str:
        """Extract displayable text from this block."""
        if self.type in ("text", "thinking") and self.text:
            return self.text
        if self.type == "toolCall" and self.name:
            return f"[Tool: {self.name}]"
        if self.type == "toolResult":
            return "[Tool Result]"
        return ""


class SessionMessage(BaseModel):
    """A single message extracted from a JSONL session file.
    
    JSONL format (verified):
      {"type": "message", "id": "...", "parentId": "...", "timestamp": "...",
       "message": {"role": "user"|"assistant", "content": [ContentBlock, ...]}}
    
    Content is ALWAYS a list of ContentBlock objects, never a plain string.
    """
    id: str                              # message ID from JSONL
    role: str                            # "user", "assistant"
    content: list[ContentBlock]          # typed content blocks (NEVER a string)
    content_text: str | None = None      # concatenated text for display (computed)
    timestamp: str | None = None         # ISO 8601 from JSONL entry
    parent_id: str | None = None         # parent message ID (for threading)


class SessionSummary(BaseModel):
    session_id: str                         # session key (e.g., "agent:main:main")
    updated_at: int                         # Unix timestamp (ms) — verified int type
    model: str | None = None                # e.g., "claude-opus-4-6" (from session, NOT config default)
    model_provider: str | None = None       # e.g., "anthropic" (from sessions.json)
    label: str | None = None                # human-readable label
    spawned_by: str | None = None           # parent session key
    total_tokens: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_read: int | None = None           # cache read tokens (present in sessions.json)
    message_count: int | None = None        # total JSONL lines if known
    session_file: str | None = None         # path to JSONL file


class SessionListResponse(BaseModel):
    sessions: list[SessionSummary]
    total: int
    warning: str | None = None              # e.g., "Unknown session format version X"


class SessionMessageListResponse(BaseModel):
    messages: list[SessionMessage]
    total: int
    has_more: bool
    skipped_lines: int = 0                   # non-message JSONL lines skipped
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
Fix all known bugs (B1, M1, M2, m1-m8), fix the critical `_last_activity()` and `_discover_agent_ids()` bugs, AND the designer's quick-wins AND extend the design system tokens AND build the 4 shared components that unblock later waves.

### Time: 2.5-3.5 hours

### Tasks

**W0.0: Supersede DESIGN-TRACKING.md**
- Prepend a notice to the top of `DESIGN-TRACKING.md`:
  ```markdown
  > ⚠️ **Superseded.** The authoritative designer issue tracking table is in WAVES-v4.md (§ Designer Issue Tracking). This file reflects the Round 1 snapshot and is preserved for historical reference only.
  ```
- Files: `DESIGN-TRACKING.md`
- LOC: ~3 modified
- Exit: DESIGN-TRACKING.md opens with superseded notice. No ambiguity about which tracking table is authoritative.

**W0.1: Fix blockers B1 + M1 + M2 from FINAL-REVIEW**
- B1: `editorStore.ts` — extract ETag from `error.detail.current_etag`, not `error.message`. After "Keep my changes", set file's ETag to `conflictEtag` so next save uses correct baseline.
- M1: `file_service.py` — switch config ETag from `mtime:size` to `SHA-1[:16]` content hash.
- M2: `editorStore.ts` — `discardChanges()` must revert `content` to `originalContent`, not just reset dirty flag.
- **NOTE (v4):** Daily log + R4 code review both suggest B1 and M2 are already fixed in the codebase. **VERIFY FIRST** — if already fixed, mark done (~5 min). If not fixed, implement (~30 min). This task is mostly verification.
- Test: `frontend/src/stores/__tests__/editorStore.test.ts::test_conflict_extracts_current_etag` — verify that on 409 response, the store extracts `detail.current_etag` (not `error.message`) and that a subsequent save after "Keep my changes" uses the new ETag.
- Test: existing 152 tests must still pass after changes.
- Files: `frontend/src/stores/editorStore.ts`, `backend/app/services/file_service.py`
- LOC: ~20 modified + ~15 test (less if already fixed)
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
  --warning-contrast: #fbbf24;       /* Amber 400 — higher contrast for text on dark (RENAMED from --warning-text in v4) */
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
  **Token naming rationale (v4):** `--warning-contrast` instead of `--warning-text` to avoid Tailwind CSS v4 generating `text-warning-text` (awkward alongside `text-warning`). `--warning-contrast` → `text-warning-contrast` is unambiguous.
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
- m2: `_list_workspace_files` filters against `WORKSPACE_FILES` set (**NOTE (v4):** This is the existing flat-list function for `list_agents()`/`get_agent()`. W5.1 creates a SEPARATE recursive listing function for `/api/agents/{id}/files?recursive=true`. They serve different use cases.)
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

**W0.5: Fix `_last_activity()` key lookup + `_discover_agent_ids()` scan path (NEW in v4)**

This task fixes two verified bugs in `agent_service.py` that make all downstream status/activity features show incorrect data.

**Bug 1 — `_last_activity()` (line 207-226):** Three compounding issues:
  1. **Key format:** `sessions.get(agent_id, [])` where `agent_id = "main"` → returns `[]` ALWAYS. Actual keys are `"agent:main:main"`, `"agent:main:subagent:uuid"`, etc.
  2. **Value shape:** Even if the key matched, the value is a dict (single session), not a list of sessions. Code iterates it expecting dicts with `updated_at`.
  3. **Timestamp format:** Code uses `datetime.fromisoformat(ts_str)` but `updatedAt` is an int (ms Unix epoch, e.g., `1772031239308`), not an ISO string. Also looks for `updated_at` / `created_at` / `timestamp` — none of which exist. Real field is `updatedAt`.

**Fix:**
```python
def _last_activity(self, agent_id: str, sessions: dict) -> datetime | None:
    """Find most recent updatedAt across all sessions for this agent.
    
    sessions.json keys are session keys like "agent:main:main",
    "agent:main:subagent:uuid", "agent:main:whatsapp:...".
    Values are dicts with updatedAt as int (ms Unix timestamp).
    """
    prefix = f"agent:{agent_id}:"
    latest: datetime | None = None
    
    for key, session_data in sessions.items():
        if not key.startswith(prefix):
            continue
        if not isinstance(session_data, dict):
            continue
        updated_at = session_data.get("updatedAt")
        if not isinstance(updated_at, (int, float)):
            continue
        try:
            ts = datetime.fromtimestamp(updated_at / 1000, tz=timezone.utc)
            if latest is None or ts > latest:
                latest = ts
        except (ValueError, OSError, OverflowError):
            pass
    
    return latest
```

**Bug 2 — `_discover_agent_ids()` (line 146-155):** Code does `home.parent.iterdir()` where `home = ~/.openclaw`. `home.parent` = `~` → iterates the ENTIRE home directory. Workspace-* dirs are in `~/.openclaw/`, not `~/`. Currently works by accident (no `workspace-*` dirs in `~/`), but:
  - Scans 100+ home directory entries unnecessarily
  - Would pick up false positives if user creates `~/workspace-test/`

**Fix:** Change `home.parent.iterdir()` → `home.iterdir()` and remove the `entry.name != "workspace"` guard (it's already the main workspace).

**Also fix `_extract_agent_meta()` model source:** Currently reads model only from `openclaw.json` config. Add fallback: read the agent's most recent session model from sessions.json (same key iteration as `_last_activity()`). This unblocks W2.1.

- Tests: `backend/tests/test_agent_service.py`:
  - `test_last_activity_real_key_format` — sessions with keys like `agent:main:main` return correct timestamp
  - `test_last_activity_ms_timestamp` — updatedAt as int (ms) is parsed correctly
  - `test_last_activity_no_matching_sessions` — agent with no sessions returns None
  - `test_discover_agents_scans_openclaw_home` — verify workspace-* dirs discovered from `~/.openclaw/` not `~/`
- Files: `agent_service.py`
- LOC: ~50 impl + ~40 test
- Exit: `_last_activity("main", sessions_data)` returns correct UTC datetime from `agent:main:main` session's `updatedAt` (ms timestamp). `_discover_agent_ids()` scans `~/.openclaw/` not `~/`. All 4 new tests pass.

### Exit Criteria (Wave 0)
1. All 159+ tests pass (original 152 + new B1 conflict test + 4 new agent_service tests + 3 m-fix tests)
2. WCAG AA compliance on all text/background combinations
3. Conflict resolution flow works end-to-end (manual verification)
4. 4 shared components ready for consumption
5. All design system tokens declared in `globals.css`
6. Single polling interval on Dashboard (m1 fixed)
7. `_last_activity()` returns correct timestamps from real sessions.json key format
8. `_discover_agent_ids()` scans `~/.openclaw/` not `~/`
9. `ruff check` clean, zero TS errors
10. DESIGN-TRACKING.md has superseded notice (W0.0)

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
- **Root cause (verified in v4):** `_extract_agent_meta()` reads model from `openclaw.json` → `agents.defaults.model.primary` = `openai-codex/gpt-5.3-codex`. It never checks per-session model data.
- **Fix:** W0.5 already fixes the session key iteration. W2.1 extends `_extract_agent_meta()` to read the agent's most recent session model from sessions.json as primary source, falling back to config default only when no session exists.
- **Verified:** sessions.json has per-session `model` field (e.g., `"model": "claude-opus-4-6"`).
- Test: `backend/tests/test_agent_service.py::test_agent_model_from_session` — agent with session returns session model, agent without returns default
- Files: `agent_service.py`
- LOC: ~20 test + ~30 impl
- Exit: `curl /api/agents | jq '.[0].model'` returns the agent's session model (e.g., `claude-opus-4-6`), not the config default. Agent with no sessions returns config default.

**W2.2: Rich status indicators + card polish**
- Status: colored left-border stripe on cards (green=active, amber=idle, gray=stopped)
- Active agents: `animate-pulse` on status dot (already added in W0.2, verify)
- `last_activity`: **W0.5 already fixed** `_last_activity()` to parse `updatedAt` from sessions.json correctly (ms Unix timestamp, key prefix matching). W2.2 consumes this data.
- Hide "Never" when value is null — show "No sessions yet" in muted text (D8)
- Card hover: add `hover:translate-y-[-1px] hover:shadow-lg` lift effect (D9)
- Status dot: add `transition-colors duration-300` (CC8)
- Test: `frontend/src/components/agents/__tests__/AgentCard.test.tsx` — 1 test (card renders correct status class)
- Files: `AgentCard.tsx`, `Card.tsx`
- LOC: ~15 test + ~40 impl
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
1. Agent cards show correct per-agent models (from sessions.json, not config default)
2. Status indicators are visually distinct (border stripe + dot + color)
3. Last activity shows real timestamps from sessions (not "Never" for all)
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
curl -s localhost:8400/api/agents | jq '.[0].last_activity' # Should NOT be null for active agents

# Manual (5 min)
1. Open localhost:5173 → Dashboard shows stat cards + recent activity (NOT agent grid)
2. Click "Agents" in sidebar → Full agent grid with search bar
3. Type "main" in search → Filters to matching agents
4. Click an agent → Agent detail shows correct model, real last_activity timestamp, file type icons
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
  - **In-memory only:** History resets on backend restart. Acceptable for a dev tool — no persistence needed.
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
- **Error handling:** If `croniter` raises `ValueError` or `KeyError` on a malformed cron expression, catch the exception and return the job with `next_run: null` and `error: "Invalid schedule"` in the `CronJobEntry`. Frontend renders "Invalid schedule" in the Next Run column with `text-danger` styling. Don't fail the entire list for one bad expression.
- "No cron jobs" empty state using W0.3 EmptyState component
- Test: `backend/tests/test_cron_service.py` — 2 tests: `test_cron_list` (parses config correctly), `test_malformed_cron_expression` (bad expression returns error field, doesn't crash)
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
THE killer feature. Show what agents have been doing. Session list on agent detail page + conversation message viewer. The JSONL format has been verified — Pydantic models are based on real data.

### Time: 7-9 hours _(revised from 6.5-8.5h: +30min caching, +15min content blocks, +15min deleted files)_

### Tasks

**W4.0: Research — verify and document session file format**
- Read `~/.openclaw/sessions/sessions.json` and 2-3 JSONL session files
- **v4 NOTE:** Format has been pre-verified during planning. This task confirms and documents for implementers:
  - sessions.json: dict keyed by session key (`agent:{agent_id}:{type}`), values are session dicts
  - Session dict fields: `sessionId`, `updatedAt` (int ms), `model`, `modelProvider`, `skillsSnapshot` (LARGE ~62KB), `sessionFile` (path), `inputTokens`, `outputTokens`, `totalTokens`, `cacheRead`, `cacheWrite`, `deliveryContext`, `lastChannel`, `lastTo`, `contextTokens`, `abortedLastRun`, `totalTokensFresh`, `systemSent`
  - JSONL entry types: `session`, `message`, `model_change`, `thinking_level_change`, `custom`, `compaction`
  - Message content: `list[ContentBlock]` with types `text`, `thinking`, `toolCall` (NOT `tool_use`), `toolResult`
  - **82% of sessionFile paths point to `.deleted.*` files** — must handle gracefully
- Output: `docs/session-format.md` in the project
- Time: 20 minutes (mostly documenting what's verified)
- Exit: Schema documented with field types, optionality, and content block types. Real examples included. `.deleted.*` pattern documented.

**W4.1: Backend — session list from sessions.json**
- Parse `sessions.json` (dict keyed by session key)
- **CRITICAL (v4): Selective field extraction.** Do NOT parse the entire JSON into Python objects naively. The `skillsSnapshot` field is ~62KB per entry (62% of total size). Strategy:
  1. **Primary approach — field-level extraction:** After `json.loads()`, iterate entries and extract only needed fields (`sessionId`, `updatedAt`, `model`, `modelProvider`, `label`, `spawnedBy`, `totalTokens`, `inputTokens`, `outputTokens`, `cacheRead`, `sessionFile`). Do NOT copy `skillsSnapshot` into Pydantic models. Let GC reclaim the raw dict.
  2. **Caching:** Cache the parsed `SessionListResponse` with file-mtime invalidation. sessions.json changes every few minutes, not every 5 seconds. The file watcher already watches it → clear cache on `file_changed`.
  3. **Thread offload:** If sessions.json exceeds 1MB, parse in a thread via `await asyncio.to_thread(json.loads, content)` to avoid blocking the event loop.
  4. **50MB hard cap:** If file exceeds 50MB, return `413 Payload Too Large`.
- **Response model:** `SessionListResponse` containing `list[SessionSummary]` (see Pydantic Models section)
- Filter by agent: session key starts with `agent:{agent_id}:` prefix
- Sort by `updatedAt` descending
- Endpoint: `GET /api/agents/{agent_id}/sessions?limit=20&offset=0`
- Handle missing/corrupt sessions.json gracefully
- **Explicit constraints:**
  - Schema validation: unknown fields are ignored (forward-compatible). Missing expected fields default to `null`.
  - Format-version detection: if top-level `version` key exists, validate it. Unknown version → return data with `warning` field.
  - Empty `sessions.json` (valid JSON `{}`): return `{sessions: [], total: 0}` — not an error.
- Test: `backend/tests/test_session_service.py` — 8 tests:
  - `test_list_sessions` — returns sessions sorted by updatedAt desc
  - `test_filter_by_agent_key_prefix` — only `agent:{id}:*` sessions returned (uses REAL key format)
  - `test_missing_sessions_json` — returns empty list, no error
  - `test_sessions_json_too_large` — returns 413 when >50MB
  - `test_empty_sessions_json` — returns `{sessions: [], total: 0}`
  - `test_unknown_format_version` — returns data with warning field
  - `test_sessions_cache_invalidation` — mtime change clears cache
  - `test_skills_snapshot_not_in_response` — verify `skillsSnapshot` is NOT included in response data
- Files: `session_service.py` (new), `sessions.py` (new router), `models/session.py` (new)
- LOC: ~100 test + ~190 impl _(revised from 80+160: +10 test for cache/snapshot, +30 impl for caching layer)_
- Exit: `GET /api/agents/{id}/sessions` returns paginated sessions sorted by updatedAt desc. Filter by agent key prefix works. `skillsSnapshot` excluded from response. Cached with mtime invalidation. 50MB cap returns 413. Empty file returns empty list. Unknown version returns warning.

**W4.2: Backend — session messages from JSONL file**
- Read `sessionFile` path from session data
- **CRITICAL (v4): Handle real JSONL format.**
  1. Each JSONL line is a JSON object with `type` field discriminator
  2. Only parse lines where `type == "message"` — skip `session`, `model_change`, `thinking_level_change`, `custom`, `compaction` entries
  3. For message entries: extract from `obj["message"]` which has `{role, content: list[ContentBlock]}`
  4. Build `SessionMessage` with content blocks, computing `content_text` by concatenating text blocks:
     ```python
     def _extract_content_text(blocks: list[dict]) -> str:
         """Concatenate text from all text/thinking blocks."""
         parts = []
         for block in blocks:
             if block.get("type") in ("text", "thinking") and block.get("text"):
                 parts.append(block["text"])
         return "\n\n".join(parts)
     ```
  5. Truncation: truncate `content_text` to 2000 chars in list response (not the raw `content` blocks). Pass `full=true` for untruncated. When `full=true`, include full content blocks; when `full=false`, include truncated `content_text` only.
  6. `skipped_lines` counter increments for ALL non-message lines (they're valid, just not messages — rename field semantics or add `non_message_lines` to response).
- **Handle deleted/missing JSONL files (v4):** 82% of sessionFile paths point to `.deleted.*` renamed files. When JSONL file is missing at the stated path:
  - Do NOT scan for `.deleted.*` variants (they're archived for a reason)
  - Return `{messages: [], total: 0, has_more: false, skipped_lines: 0, warning: "Session file not found (session may have been archived)"}`
  - This is NOT an error — return 200 with warning, not 404
- **Response model:** `SessionMessageListResponse` containing `list[SessionMessage]`
- Pagination: offset-based on message entries only (skip non-message lines, offset counts messages)
- Endpoint: `GET /api/sessions/{session_id}/messages?limit=50&offset=0&full=false`
- Security: validate sessionFile path is under OPENCLAW_HOME (path traversal prevention)
- **Explicit constraints:**
  - JSONL file size cap: 50MB → return warning response
  - Malformed JSON lines: skip, increment `skipped_lines`
  - Encoding: UTF-8, replace invalid bytes with U+FFFD
- Test: `backend/tests/test_session_service.py` — 7 tests:
  - `test_parse_jsonl_messages_content_blocks` — parses real format with content block list
  - `test_non_message_entries_skipped` — session/model_change/custom entries not in messages list
  - `test_content_text_concatenation` — text blocks concatenated correctly
  - `test_message_pagination` — offset/limit work on message entries only
  - `test_path_traversal_blocked` — `../` in path returns 403
  - `test_missing_jsonl_returns_warning` — missing file returns 200 with warning (NOT 404)
  - `test_jsonl_file_too_large` — returns warning when >50MB
- Files: `session_service.py`, `sessions.py`
- LOC: ~90 test + ~95 impl _(revised from 70+80: +20 test for content blocks + deleted files, +15 impl for block handling)_
- Exit: `GET /api/sessions/{id}/messages` returns paginated messages with content blocks. Non-message JSONL entries skipped. Missing JSONL files return 200 with warning. `content_text` computed from text blocks. Path traversal returns 403.

**W4.3: Frontend — session list tab on agent detail**
- Add tabs to AgentPage: "Files" | "Sessions"
- Session list: date, message count, model, token count, duration
- Click session → expand inline to show messages (not a separate page)
- Use Skeleton component from W0.3 for loading
- Infinite scroll for session list (load more button, not auto-scroll)
- **New store:** `sessionStore.ts` (Zustand) with:
  - `sessions: SessionSummary[]`, `loading: boolean`, `selectedAgentId: string | null`
  - `fetchSessions(agentId, offset)` — async action
  - **Agent-change behavior:** When `selectedAgentId` changes, immediately clear `sessions` array and set `loading: true`.
  - **Stale-fetch prevention (v4):** Use `AbortController` to cancel in-flight fetch when agent changes:
    ```typescript
    let abortController: AbortController | null = null;
    
    fetchSessions: async (agentId: string, offset = 0) => {
      // Cancel any in-flight request for a different agent
      if (abortController) abortController.abort();
      abortController = new AbortController();
      
      set({ loading: true, selectedAgentId: agentId });
      try {
        const res = await fetch(`/api/agents/${agentId}/sessions?offset=${offset}`, {
          signal: abortController.signal,
        });
        // ... handle response
      } catch (e) {
        if (e instanceof DOMException && e.name === 'AbortError') return; // Expected
        // ... handle real errors
      }
    }
    ```
  - `clearAndLoad(agentId)` — sets `selectedAgentId`, clears sessions, calls `fetchSessions`
- Test: `frontend/src/components/sessions/__tests__/SessionList.test.tsx` — 2 tests:
  - `test_session_list_renders` — session list renders with mock data
  - `test_stale_fetch_discarded` — navigating to new agent aborts previous fetch
- Files: `SessionList.tsx` (new), `AgentPage.tsx`, `sessions.ts` (new API module), `sessionStore.ts` (new)
- LOC: ~35 test + ~210 impl _(revised from 25+200: +10 test for stale fetch, +10 impl for AbortController)_
- Exit: Agent detail page has Files/Sessions tabs. Sessions tab loads session list from API. Switching agents cancels in-flight request and clears stale data. "Load more" button loads next page. Empty state for agents with no sessions.

**W4.4: Frontend — conversation message viewer**
- **Content block rendering (v4):** Messages contain `list[ContentBlock]`, not plain strings. Render each block type differently:
  - `text` blocks: render as markdown (or plain text with code highlighting)
  - `thinking` blocks: render in a collapsible `<details>` with muted styling and "Thinking..." label
  - `toolCall` blocks: render as a compact card with tool name and collapsed input
  - `toolResult` blocks: render inline below the tool call, collapsible
- Messages in conversation layout: user messages right-aligned, assistant left-aligned
- Code blocks with syntax highlighting (lightweight lib like `highlight.js`, NOT Monaco tokenizer — too heavy for inline)
- Long messages: "Show more" toggle (collapsed at 500 chars of `content_text`)
- Token count per message if available
- Copy button on messages (copies `content_text`, uses `navigator.clipboard`)
- Test: `frontend/src/components/sessions/__tests__/SessionViewer.test.tsx` — 2 tests:
  - `test_message_viewer_renders_roles` — user right, assistant left
  - `test_content_blocks_rendered` — text block renders text, thinking block renders with details tag
- Files: `SessionViewer.tsx` (new), `ContentBlockRenderer.tsx` (new)
- LOC: ~25 test + ~140 impl _(revised from 15+120: +10 test for content blocks, +20 impl for ContentBlockRenderer)_
- Exit: Messages render in conversation layout (user right, assistant left). Content blocks render with type-specific styling. Thinking blocks collapsible. Tool calls shown as cards. Code blocks highlighted. Long messages collapsed at 500 chars. Copy button works.

### Exit Criteria (Wave 4)
1. Agent detail shows session list with real data
2. Clicking a session shows conversation messages with content blocks
3. Pagination works for both session list and messages
4. Large sessions (1000+ messages) don't crash the UI
5. Session files >50MB show a graceful warning (not a crash)
6. Missing/deleted session files show warning (not error)
7. Schema format documented in `docs/session-format.md`
8. Agent navigation cancels in-flight fetches (no stale data flash)
9. `skillsSnapshot` excluded from session list response (performance)
10. Sessions.json cached with mtime invalidation
11. All tests pass: 15 new backend tests + 4 frontend tests

---

## Wave 5: Editor Upgrade

### Goal
Add a file browser to the editor so users don't have to navigate back to agent detail to open another file. Keep it simple — flat list with agent dropdown, not a full tree. Fix Monaco theme mismatch.

### Time: 4-5.5 hours _(revised from 3.5-5h: +30-45min for W5.1 LOC increase)_

### Tasks

**W5.1: Backend — recursive file listing endpoint**
- `GET /api/agents/{agent_id}/files?recursive=true&depth=2&max_files=200`
- **Response model:** `FileListResponse` containing `list[FileEntry]` (see Pydantic Models section)
- **NOTE (v4): This is a NEW function**, separate from the W0.4 m2 fix. W0.4 filters the existing flat `_list_workspace_files()` for `list_agents()`/`get_agent()`. W5.1 creates `_list_workspace_files_recursive()` for the `/api/agents/{id}/files?recursive=true` endpoint. Different use cases, different functions.
- **Implementation scope (v4 — revised):** Current `_list_workspace_files()` is a flat `workspace.iterdir()` with no recursion, no depth limit, no binary detection, no excludes, no max_files. W5.1 needs ALL of these. This is essentially a new function, not a 60-LOC extension. Comparable to `file_service.py` at 179 LOC.
  - Recursive directory scanning with `os.walk()` or `pathlib.rglob()`
  - Depth limit (max 3 enforced server-side)
  - Exclude patterns: `.git`, `node_modules`, `.venv`, `__pycache__`, `*.pyc`
  - Binary detection by extension: `.png`, `.jpg`, `.gif`, `.webp`, `.ico`, `.woff`, `.woff2`, `.ttf`, `.pdf`, `.zip`, `.tar`, `.gz`
  - Max files limit: default 200, `truncated: true` when exceeded
  - Returns flat list with relative paths (frontend can group by directory)
- Test: `backend/tests/test_agent_service.py` — 4 tests:
  - `test_recursive_listing` — returns files from subdirectories
  - `test_depth_limit` — max depth 3 enforced
  - `test_excludes` — `.git`/`node_modules` not in results
  - `test_max_files_truncation` — >200 files returns `truncated: true`
- Files: `agents.py` (router), `agent_service.py`, `models/file.py` (extend)
- LOC: ~50 test + ~110 impl _(revised from 40+60: +10 test for excludes, +50 impl for full implementation)_
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
- **Breadcrumb navigation guard (v4):** Breadcrumb links (e.g., clicking "Agents") must check for unsaved changes. Use `react-router-dom`'s `useBlocker` or a `beforeNavigate` wrapper to show ConfirmDialog when editor is dirty. This covers the case where W5.2's ConfirmDialog handles file-to-file navigation, but NOT navigation away from the editor entirely.
- **Custom Monaco theme (E3-A from DESIGN-REVIEW §4.6):** Create `openclaw-dark` Monaco theme that uses `--bg-primary` (#0f1219) as editor background instead of `vs-dark`'s #1e1e1e. This eliminates the jarring seam between editor and dashboard. Other colors (syntax highlighting) inherit from `vs-dark`.
- **Test:** `frontend/src/pages/__tests__/EditorPage.test.tsx` — 3 tests:
  - (a) Opening a file from sidebar loads it in the Monaco editor
  - (b) Switching files with unsaved changes shows ConfirmDialog warning
  - (c) Breadcrumb navigation with dirty state shows ConfirmDialog
- Files: `EditorPage.tsx`, `Layout.tsx`, `monacoTheme.ts` (new)
- LOC: ~30 test + ~70 impl _(revised from 30+60: +10 impl for breadcrumb guard)_
- Exit: Editor background matches dashboard (#0f1219). No color seam. Layout uses `noPadding` prop. Breadcrumb shows `Agents / {name} / {file}`. Breadcrumb navigation blocked when dirty.

### Exit Criteria (Wave 5)
1. Editor has file browser sidebar
2. Agent selector dropdown works
3. Binary files blocked from opening (visual indicator + no click)
4. Dirty state warning when switching files OR navigating away via breadcrumb
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
6. Click "Agents" in breadcrumb with dirty state → ConfirmDialog appears
7. Click a .png file → Blocked with tooltip
8. Navigate to /agents/main → Sessions tab shows real session data
9. Click a session → Messages render in conversation layout with content blocks
```

---

## Wave 6: Toast, Polish & Hardening — ✅ CHECKPOINT OMEGA

### Goal
Final wave. Wire toast notifications into all operations, add file_changed WebSocket handler, add 404 page, add confirm dialogs where missing, push coverage to 85% backend, and clean up any remaining issues.

### Time: 4-5.5 hours _(revised from 4-5h: +15min for file_changed handler)_

### Tasks

**W6.1: Toast notification system + file_changed WebSocket handler**
- Upgrade existing Toast: auto-dismiss (5s), stacking (max 3), slide-in animation
- Use `--z-toast: 600` from design system tokens
- Wire into all operations:
  - File save → success toast
  - Config save → success toast
  - Gateway action → success/error toast
  - Validation error → error toast with message
  - Agent fetch error → error toast
- Connection banner: amber bar when WebSocket disconnects
- **Wire `file_changed` WS events (v4):** Currently, `useWebSocket.ts` only handles `ping` and `gateway_status`. Add handler for `file_changed`:
  ```typescript
  if (msg.type === 'file_changed') {
    const { path, name, agent_id } = msg.payload;
    // If the currently-edited file was modified externally, show warning
    const currentFile = useEditorStore.getState().currentFile;
    if (currentFile && currentFile.path === path) {
      addToast({ type: 'warning', message: `${name} was modified externally. Reload to see changes.` });
    }
  }
  ```
  This prevents the scenario: user edits SOUL.md → external process modifies SOUL.md → user saves → 409 conflict with no prior warning. The warning toast gives the user a heads-up before they hit save.
- Test: `frontend/src/components/common/__tests__/Toast.test.tsx` — 2 tests (toast auto-dismiss timing, connection banner show/hide)
- Test: `frontend/src/hooks/__tests__/useWebSocket.test.ts` — 1 test (file_changed event triggers warning toast for current file)
- Files: `Toast.tsx`, `toastStore.ts`, `ConnectionBanner.tsx` (new), `Layout.tsx`, `useWebSocket.ts`
- LOC: ~35 test + ~95 impl _(revised from 25+80: +10 test, +15 impl for file_changed handler)_
- Exit: Toasts auto-dismiss at 5s, stack max 3, slide-in animation. All save/error/gateway operations trigger toasts. Amber banner on WS disconnect. `file_changed` events show warning toast for currently-edited file.

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
- WebSocket test coverage: 25% → 60% (connect, ping/pong, events, disconnect, file_changed handler)
- Frontend component tests for new components (SessionList, FileList, CronJobList, ContentBlockRenderer)
- E2E smoke script: `make e2e` — starts backend, curls all endpoints, verifies status codes
- Test: ~160 new test LOC
- Files: `test_integration.py` (new), `test_websocket.py` (expand), `smoke.sh` (new)
- LOC: ~160 test + ~30 impl (test utils + smoke script)
- Exit: `make test` green. `make e2e` (smoke.sh) green. **Backend coverage ≥85%.** **Frontend coverage ≥70% (component tests).** Combined ≥80%. WebSocket coverage ≥60%.

### Exit Criteria (Wave 6) — **CHECKPOINT OMEGA: Dashboard is complete**
1. All operations have toast feedback
2. `file_changed` WebSocket events trigger stale-file warning on editor
3. 404 page works for invalid routes
4. Config reload warns when dirty
5. Backend coverage ≥ 85%
6. Frontend coverage ≥ 70%
7. WebSocket coverage ≥ 60%
8. `make test && make e2e` both green
9. Zero TS errors, `ruff check` clean
10. Document titles update per page
11. `--info` token either wired or removed (no orphans)

### What "Omega" means
After Wave 6, the dashboard is feature-complete for daily use:
- Fleet overview with real KPIs
- Agent search, filter, sort
- Agent detail with files + sessions + conversation viewer
- Session messages with content block rendering (text, thinking, tool calls)
- File editor with browser sidebar + custom theme
- Config editor with validation + conflict resolution
- Gateway management with cron job viewer
- Toast notifications for all operations (including external file changes)
- 85%+ backend test coverage, 70%+ frontend coverage

---

## Backlog (deferred — not worth the complexity now)

| Feature | Why Deferred | Revisit When |
|---------|-------------|--------------|
| WebSocket real-time updates (auto-refresh) | Polling + file_changed warning is sufficient for single-user localhost | Multiple users OR performance issues |
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
| Streaming JSON parser (ijson) | sessions.json caching handles current scale | sessions.json consistently >5MB |

---

## Testing Strategy

### Per-Wave Requirements

| Wave | New Backend Tests | New Frontend Tests | Cumulative Coverage |
|------|------------------|--------------------|---------------------|
| 0 | 3 (rate limit, file filter, ETag header) + 1 (B1 conflict) + **4 (agent_service: activity, timestamp, no-match, discover)** | 0 | 76% |
| 1 | 0 | 5 (AgentsPage ×2, DashboardPage ×1, agentStore ×2) | 77% |
| 2 | 2 (model resolution, status endpoint) | 2 (AgentCard, fileIcons) | 78% |
| 3 | 4 (gateway loading, history, cron list, cron malformed) | 2 (GatewayPanel timeout, stopped state) | 80% |
| 4 | **19** (session list ×8, messages ×7, cache, snapshot, content blocks, deleted files) | **4** (SessionList ×2, SessionViewer ×2) | 84% |
| 5 | **4** (recursive listing, depth limit, excludes, max files truncation) | **7** (EditorSidebar ×3, EditorPage ×3, existing) | 86% |
| 6 | 20+ (integration, WS coverage, E2E) | **6** (Toast ×2, ConnectionBanner, file_changed, new components) | 88%+ |
| **Total** | **~57** | **~26** | **BE ≥85%, FE ≥70%** |

**Changes from v3:**
- Wave 0: +4 backend tests (W0.5 agent_service fixes)
- Wave 4 backend: 11→19 (+8: cache invalidation, snapshot exclusion, content blocks, deleted files, key prefix with real format)
- Wave 4 frontend: 2→4 (+2: stale fetch, content block rendering)
- Wave 5 backend: 3→4 (+1: excludes test)
- Wave 6 frontend: 5→6 (+1: file_changed WebSocket handler)
- **Total backend: ~44→~57, Total frontend: ~23→~26**

### Integration Checkpoints

**After Wave 2 — ALPHA checkpoint:**
```bash
# Automated
make test && make build && curl -s localhost:8400/api/health | jq .status
curl -s localhost:8400/api/agents | jq '.[0].model'  # Verify NOT "gpt-5.3-codex"
curl -s localhost:8400/api/agents | jq '.[0].last_activity'  # Verify NOT null for active agents

# Manual (5 min)
1. Dashboard: stat cards + recent activity (NOT agent grid)
2. /agents: search bar works, status filter works
3. Agent detail: correct model (from session), real timestamps, file icons
4. Editor: save + conflict resolution flow end-to-end
```

**After Wave 5 — Pre-Omega checkpoint:**
```bash
# Automated
make test && make build

# Manual (5 min)
1. /editor: sidebar file browser loads, agent selector works
2. Binary file (.png) click blocked
3. Dirty-state warning on file switch AND breadcrumb navigation
4. Monaco background matches dashboard (no color seam)
5. /agents/{id}: Sessions tab shows data, messages render with content blocks
6. Thinking blocks collapsible, tool calls shown as cards
7. Session pagination: "Load more" button works
8. Gateway: no infinite spinner, channels as table, cron list visible
```

**After Wave 6 — OMEGA checkpoint:**
```bash
# Automated
make test && make e2e  # smoke.sh hits all API endpoints

# Manual (5 min)
1. Full click-through: Dashboard → Agents → Agent Detail → Sessions → Editor → Config → Gateway
2. Toast appears on save/error/gateway action
3. Edit a file → have external process modify it → warning toast appears
4. Navigate to /nonexistent → 404 page
5. Edit config, click Reload → ConfirmDialog appears
6. All page tabs show correct title
```

---

## LOC Summary

| Wave | New | Modified | Tests | Total |
|------|-----|----------|-------|-------|
| 0 | 115 | 243 | 95 | **453** |
| 1 | 260 | 55 | 85 | 400 |
| 2 | 30 | 100 | 45 | 175 |
| 3 | 200 | 100 | 70 | 370 |
| 4 | 540 | 30 | 250 | **820** |
| 5 | 350 | 100 | 115 | **565** |
| 6 | 185 | 130 | 195 | **510** |
| **Total** | **~1,680** | **~758** | **~855** | **~3,293** |

**Changes from v3:**
- Wave 0: new 115→115, modified 193→243 (+50 W0.5), tests 55→95 (+40 W0.5), total 363→**453**
- Wave 4: new 480→540, tests 190→250, total 720→**820** (caching +30, content blocks +15, deleted files +10, stale fetch +10, extra tests +60)
- Wave 5: new 310→350 (+40 W5.1 increase + breadcrumb guard), tests 105→115 (+10 excludes + breadcrumb), total 505→**565**
- Wave 6: new 170→185 (+15 file_changed), tests 175→195 (+20 WS file_changed tests), total 465→**510**
- **Project total: ~2,988→~3,293 (+305 LOC, split between impl, tests, and caching/content-block infrastructure)**

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
--warning-contrast: #fbbf24;        /* Amber 400 — higher contrast (v4: renamed from --warning-text) */
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

**Token naming convention (v4):** `--warning-contrast` generates `text-warning-contrast` in Tailwind CSS v4 auto-utility generation. This is unambiguous alongside `text-warning` (the base warning color). Previous name `--warning-text` would have generated the awkward `text-warning-text`.

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
| **sessions.json scaling (71KB/session)** | High | High | W4 | **NEW (v4):** Skip `skillsSnapshot` during extraction (62KB/entry). Cache parsed result with file-mtime invalidation. Thread-offload `json.loads` if >1MB. At 200 sessions (projected), raw file = ~14MB. After skillsSnapshot skip, Python memory for response = ~1.8MB. Without mitigation: 14MB parsed every 5s = 150-300ms event loop block. With caching: parsed once, cache hit on subsequent polls. |
| **Session JSONL format varies across OpenClaw versions** | Medium | Medium | W4 | **REDUCED (v4):** Format verified against live data. Pydantic models match real content block types. W4.0 confirms for implementers. Unknown `type` values in JSONL gracefully skipped. |
| **82% of sessionFile paths point to deleted files** | High | Medium | W4 | **NEW (v4):** Return 200 with `warning` field, not 404. Users see "Session may have been archived" instead of an error. |
| **Wave 4 slip cascades to W6** | Medium | High | W4-W6 | W4 is the largest wave (**7-9h**). If it slips, W6 can start backend tests while W4 frontend completes. Agent B handles W4 backend in Sprint 1 to front-load risk. |
| **Stale fetch race on agent navigation** | Medium | Medium | W4 | **NEW (v4):** `AbortController` cancels in-flight requests. Response discarded if agent changed. Test case verifies behavior. |
| **External file changes cause silent 409 conflicts** | Medium | Medium | W6 | **NEW (v4):** `file_changed` WS events trigger warning toast on editor. User sees "SOUL.md was modified externally" before attempting save. |
| **Large workspace (500+ files) slows file listing** | Low | Medium | W5 | `max_files=200` server-side limit with `truncated` flag. Depth 3 cap. `.git`/`node_modules` excluded. |
| **`_discover_agent_ids()` false positives** | Low | Low | W0 | **NEW (v4):** Fixed — scans `~/.openclaw/` not `~/`. No false positives from `~/workspace-*` dirs. |
| **Config ETag same-second race (M1)** | Low | Medium | W0 | Content-hash ETag for config writes. |
| **`croniter` dependency** | Low | Low | W3 | Pure Python, pinned version. 10M+ monthly downloads. |
| **Monaco custom theme breaks syntax highlighting** | Low | Medium | W5 | Only overrides background color; syntax colors inherit from `vs-dark`. |
| **Agent B idle time in Sprint 1** | Low | Low | Sprint | Agent B starts W3 backend after W0 baseline commit (~2h wait). |

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

### Verified Runtime Data (NEW in v4)
| Data Point | Value | Source |
|-----------|-------|--------|
| sessions.json size | 784KB (11 sessions) | `ls -la ~/.openclaw/sessions/sessions.json` |
| sessions.json per-session | ~71KB | 784KB / 11 |
| `skillsSnapshot` per entry | ~62KB (87% of entry) | `len(json.dumps(entry['skillsSnapshot']))` |
| Session keys format | `agent:{agent_id}:{type}` | `json.load(sessions.json).keys()` |
| `updatedAt` type | int (ms Unix timestamp) | `type(entry['updatedAt'])` → int |
| JSONL entry types | session, message, model_change, thinking_level_change, custom, compaction | First 10 lines of live JSONL |
| Content block types | text, thinking, toolCall | Counter across 463 messages |
| Active vs deleted JSONL files | 12 active / 66 deleted (82% deleted) | `ls ~/.openclaw/agents/main/sessions/` |
| workspace-* dirs location | `~/.openclaw/workspace-*` (33 dirs) | `ls -d ~/.openclaw/workspace-*` |
| `_last_activity()` current behavior | Returns `None` for ALL agents | `sessions.get("main")` → `[]` always |

### Rules of Thumb
- Simple page (stat cards + grid): ~50 LOC
- Complex component (editor, gateway panel): ~100-150 LOC
- Content block renderer (v4): ~60-80 LOC (discriminated by block type)
- Zustand store with async actions + AbortController: ~100-140 LOC
- Backend service with file I/O + caching: ~180-220 LOC
- Backend router with 3-4 endpoints: ~80-120 LOC
- Test file (3-5 test cases): ~40-60 LOC
- Test file (8+ edge cases): ~80-120 LOC
- CSS token additions: ~3 LOC per token

### Estimate Confidence
| Wave | Confidence | Notes |
|------|-----------|-------|
| 0 | **High** | Bug fixes + CSS + now-verified `_last_activity()` fix — well-scoped |
| 1 | High | Mostly moving existing code + adding search (proven pattern) |
| 2 | **High** | Incremental card improvements, data format verified, W0.5 unblocks model/status |
| 3 | Medium-High | Gateway timeout is straightforward; cron parsing depends on config format |
| 4 | **Medium-High** _(up from Medium)_ | Session format VERIFIED. Pydantic models match real data. Content block types known. Caching strategy defined. Main unknowns: frontend rendering edge cases. |
| 5 | **Medium-High** | Revised LOC estimate based on actual `_list_workspace_files()` code inspection. Monaco theme is small but untested. |
| 6 | Medium | Coverage push is variable — depends on which lines are uncovered |

---

_WAVES-v4.md complete. Ready for Round 5 review._
