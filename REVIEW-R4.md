# Plan Review — Round 4 (Adversarial)
_Reviewer: Adversarial Review Agent (Opus) | Date: 2026-02-25_
_Reviewing: WAVES-v3.md against actual source code and runtime data_

---

## Verdict: REVISE

Round 3 approved this plan based on internal consistency, naming conventions, and coverage metrics. This round tested the plan against **the actual codebase and real runtime data**. I found 2 critical code-plan misalignments that will cause implementation failure in Wave 4 (the largest wave), plus 1 already-broken function the plan doesn't identify.

Estimated revision effort: **60-90 minutes** to address the critical items. The plan's structure and wave ordering are sound — the problems are in the assumptions about data formats.

---

## Implementation Traps Found

### 1. 🔴 CRITICAL — `_last_activity()` Is Completely Broken Against Real sessions.json

**The plan says (W2.2):** "parse `updatedAt` from sessions.json"

**What the code actually does (`agent_service.py:207-226`):**
```python
def _last_activity(self, agent_id: str, sessions: dict) -> datetime | None:
    if isinstance(sessions, dict):
        agent_sessions = sessions.get(agent_id, [])  # ← BUG
```

**What sessions.json actually looks like (verified on disk):**
```json
{
  "agent:main:main": { "updatedAt": 1772030860949, ... },
  "agent:main:subagent:7198fc8c-...": { "updatedAt": 1772028755794, ... },
  "agent:main:whatsapp:default:direct:+19492917570": { "updatedAt": 1772029243999, ... }
}
```

`sessions.get("main", [])` returns `[]` — **ALWAYS**. Keys are session keys like `agent:main:main`, not agent IDs like `main`. This means:
- Every agent's `last_activity` is `None`
- Every agent's `status` evaluates to `"idle"` (see `_compute_status`)
- The DESIGN-REVIEW's observation that all 40 agents show "Never" is **caused by this bug**
- The plan's W4.1 correctly identifies the key format (`session key starts with agent:{agent_id}:`) for NEW session listing code — but **never backports this fix to the existing `_last_activity()` method**

**→ Fix:** W0 or W2 must add a task: rewrite `_last_activity()` to iterate sessions.json keys matching `agent:{agent_id}:*` prefix, extracting `updatedAt` (which is an int/ms Unix timestamp, NOT an ISO string — the current code parses with `datetime.fromisoformat()` which will also fail even if the lookup worked).

**Impact if unfixed:** Waves 0-3 ship with broken agent status. W2.2's "Rich status indicators" will show beautiful colored borders on cards that all say "idle" forever.

### 2. W0.1 Blockers B1/M2 Appear Already Fixed — Time Estimate Inflated

**The plan says (W0.1):** "B1: `editorStore.ts` — extract ETag from `error.detail.current_etag`, not `error.message`" and "M2: `discardChanges()` must revert `content` to `originalContent`"

**What the code actually shows (`editorStore.ts`):**
```typescript
// B1 — already extracts from error.detail:
const serverEtag = error.detail?.current_etag ?? null;
set({ saving: false, conflictEtag: serverEtag, error: 'CONFLICT' });

// keepMyChanges() already updates ETag:
set({ currentFile: { ...currentFile, etag: conflictEtag }, ... });

// M2 — discardChanges() already reverts content:
set({ currentFile: { ...currentFile, content: currentFile.originalContent, dirty: false }, ... });
```

The plan correctly notes "daily log suggests this may already be fixed. VERIFY first" — so this isn't a plan error, just a note that W0.1's time estimate (20 modified LOC + 15 test LOC) is probably 5 minutes of verification, not implementation. Net effect: W0 may finish ~30min faster than estimated.

**→ Action:** Not a revision — just a note for implementers. W0.1 verify steps will likely confirm these are done.

### 3. W5.1 "Extend Existing" File Listing Is Actually a Full Rewrite

**The plan says (W5.1):** "Extend existing `models/file.py`" and estimates 60 LOC impl.

**What `_list_workspace_files()` actually does (`agent_service.py:174-195`):** A flat `workspace.iterdir()` over top-level files. No recursion, no depth limit, no binary detection, no max_files, no exclude list.

W5.1 needs: recursive scanning, depth limit, exclude list (`.git`, `node_modules`, etc.), binary detection, max_files cap, `truncated` flag. This is essentially a new function, not a 60-LOC extension. Comparable to `file_service.py` at 179 LOC.

**→ Fix:** Revise W5.1 LOC estimate from 60 to ~100-120 impl. Time impact: +30-45 min.

---

## State Management Risks

### 1. 🟡 Session Fetch Race on Agent Navigation (W4.3)

**Scenario:**
1. User navigates to Agent A → `fetchSessions("A")` fires
2. User quickly navigates to Agent B → `clearAndLoad("B")` fires, `fetchSessions("B")` fires
3. Agent A's response arrives → state updates with A's sessions
4. Agent B's response arrives → overwrites with B's sessions

Between steps 3 and 4, the user sees **Agent A's sessions on Agent B's page**. Classic stale-fetch race.

The plan's `clearAndLoad()` clears sessions and sets `selectedAgentId`, but doesn't cancel the in-flight fetch for Agent A. When A's response arrives, the Zustand store blindly applies it.

**→ Fix:** W4.3 must specify: `fetchSessions()` checks that `selectedAgentId` still matches the requested `agentId` before applying the response. Or use `AbortController` to cancel the previous request. Add this to the task description and add a test case: "stale fetch for previous agent is discarded."

### 2. 🟡 WebSocket `file_changed` Events Silently Ignored

**What the code does (`useWebSocket.ts:71-77`):**
```typescript
if (msg.type === 'gateway_status') {
    void getFetchStatus()();
}
// That's it. No handler for 'file_changed'.
```

The WebSocket server sends `file_changed` events when workspace files are modified externally. The frontend discards them. This means:
- User opens SOUL.md in editor
- External process (or another agent) modifies SOUL.md
- WebSocket fires `file_changed`
- Frontend ignores it
- User saves → 409 conflict with no prior warning

The plan defers "WebSocket real-time updates" to the backlog, which is fine for auto-refreshing the agent grid. But it should at least wire `file_changed` into a **stale-file warning** on the editor page. This is a 10-line addition:
```typescript
if (msg.type === 'file_changed' && msg.payload.path === currentEditorFile) {
  showToast({ type: 'warning', message: 'File modified externally' });
}
```

**→ Fix:** Add a mini-task to W6.1 (Toast system) or W5.3 (Editor layout): "Wire `file_changed` WS event into a warning toast when the currently-edited file is modified externally." ~15 LOC, ~15 min.

### 3. Unsaved Editor Content on Breadcrumb/Navigation

W5.3 adds a breadcrumb `Agents / COS / SOUL.md` to the editor page. If the user clicks "Agents" in the breadcrumb while the editor has unsaved changes, there's no guard. W5.2 specifies a ConfirmDialog when clicking a different *file*, but not when navigating *away* from the editor entirely.

**→ Fix:** W5.3 should specify: "Breadcrumb links use `beforeNavigate` guard (or `react-router-dom` blocker) to show ConfirmDialog when editor is dirty." Add to W5.3 exit criteria.

---

## Race Conditions

### 1. 🟡 `json.loads()` Blocks Event Loop for Large sessions.json

**The math:** sessions.json is 714KB for only 10 sessions. The `skillsSnapshot` field in each session entry contains the **entire skills prompt** (thousands of characters). With 40 agents × 5+ sessions each, sessions.json could easily reach 5-15MB.

`_load_sessions_index()` does `json.loads(content)` synchronously on the event loop. At 10MB, `json.loads` takes ~100-500ms on ARM64, blocking ALL concurrent requests including WebSocket pings.

`list_agents()` calls `_load_sessions_index()` and is polled every 5 seconds from the frontend. That's a 100-500ms event loop block every 5 seconds.

**→ Fix:** Add to W4.1: "If `sessions.json` exceeds 1MB, parse in a thread via `await asyncio.to_thread(json.loads, content)`. Or cache the parsed result with a file-mtime invalidation (sessions.json changes infrequently — every few minutes, not every 5 seconds)."

The caching approach is better: parse once, cache, invalidate on file change. The file watcher already watches `sessions.json`, so it can clear the cache on `file_changed`.

### 2. Two Polling Intervals After Unmount

`useAgents()` creates a `setInterval` in `useEffect`. React 18 Strict Mode in development double-mounts, creating two intervals. The cleanup function clears one, but the second might persist briefly. With two components calling `useAgents()` simultaneously (m1 bug pre-fix), this means up to 4 intervals during development. Not a production issue (strict mode is dev-only), but worth noting for devs debugging "why am I seeing double requests."

**→ Action:** Note-only, not a plan revision. Dev artifacts, not user-facing.

---

## Missing Error States

### 1. 🟡 JSONL Files Renamed to `.deleted.*` Pattern

**What the filesystem shows:**
```
b8c7b187-7802-4334-96bc-d3606834969c.jsonl          (active)
032cdf86-e97c-4dc4-b16a-3b1caff58688.jsonl.deleted.2026-02-25T04-05-46.952Z  (deleted)
```

sessions.json's `sessionFile` field points to `/path/to/uuid.jsonl`. OpenClaw renames session files to `.jsonl.deleted.*` when they expire. When the dashboard tries to open a `sessionFile` that's been renamed:
- `Path(sessionFile).exists()` → `False`
- The plan says "Handle missing JSONL files" but doesn't account for this pattern

56 deleted files vs 12 active files means **82% of session file paths in sessions.json point to files that no longer exist at the stated path**.

**→ Fix:** W4.2 must account for this: when the JSONL file is missing, also scan for `.jsonl.deleted.*` files matching the UUID prefix. Or more pragmatically: just return an empty message list with `warning: "Session file not found (session may have been archived)"`. Don't throw an error.

### 2. 🟡 sessions.json 714KB for 10 Sessions — Scaling Projection

714KB ÷ 10 sessions = ~71KB per session entry. This is dominated by `skillsSnapshot` (the entire skills prompt embedded in every session). With 40 agents running actively, generating 5+ sessions each, that's 200 sessions × 71KB = **14MB** of sessions.json.

The plan's 50MB cap catches the extreme case, but doesn't account for the performance cliff between "fine" and "50MB cap hit." At 14MB:
- `json.loads()` takes 150-300ms (event loop block)
- Memory: 14MB file → ~60-100MB Python objects (JSON expansion ratio)
- Polled every 5 seconds

**→ Fix:** Add to plan Risk Assessment: "sessions.json size is dominated by `skillsSnapshot` field (~7KB per session). For session listing, only extract `sessionId`, `updatedAt`, `model`, `label`, `spawnedBy`, and token fields. Consider a streaming parser (ijson) or caching strategy if sessions.json exceeds 2MB."

### 3. 🟢 Monaco CDN Failure (Minor)

If Monaco fails to load (CDN blocked, corporate network), the ErrorBoundary catches it and shows "Editor failed to load." There's no fallback textarea. This is acceptable for a localhost dev tool — but worth noting that the error message should suggest checking network connectivity.

**→ Action:** Note-only. The ErrorBoundary handles this adequately for v1.

---

## Performance Concerns

### 1. sessions.json Parsed on Every `/api/agents` Poll

**The math:**
- Frontend polls `/api/agents` every 5 seconds
- `list_agents()` calls `_load_sessions_index()` which reads + parses the entire sessions.json
- sessions.json is 714KB NOW, projected to 5-15MB with active usage
- `_load_openclaw_config()` is ALSO called on every poll — double file I/O

**The fix is simple:** Add a `functools.lru_cache` or `TTLCache` on `_load_sessions_index()` and `_load_openclaw_config()` with mtime-based invalidation. These files change every few minutes, not every 5 seconds.

**→ Fix:** Add to W0.4 or W4.1: "Cache parsed sessions.json and openclaw.json with file-mtime invalidation. Cache TTL: 5 seconds (matches frontend poll interval). Invalidate on file watcher notification."

### 2. `_list_workspace_files` Returns ALL Files (78+ for main workspace)

The current function iterates everything in the workspace. The FINAL-REVIEW's m2 flagged this, and W0.4 plans to fix it. But the plan says "filter against `WORKSPACE_FILES` set" — which limits to 9 known files. This breaks W5.1's recursive listing, which needs to return ALL files (minus excludes).

**→ Fix:** Clarify in W0.4: the m2 fix filters against `WORKSPACE_FILES` for the *existing* `list_agents()`/`get_agent()` endpoints. W5.1 creates a *separate* recursive listing function for the `/api/agents/{id}/files?recursive=true` endpoint. These should not share the same underlying function — different use cases.

---

## Code-Plan Misalignments

### 1. 🔴 CRITICAL — JSONL Format Doesn't Match Plan's SessionMessage Model

**What the plan's Pydantic model assumes (`SessionMessage`):**
```python
class SessionMessage(BaseModel):
    role: str                    # "user", "assistant", "system", "tool"
    content: str                 # message text
    timestamp: str | None        # ISO 8601
    tool_calls: list[dict] | None
    tokens: int | None
```

**What the actual JSONL entries look like (verified from `b8c7b187...jsonl`):**
```json
{"type": "session", "version": "...", "id": "...", "timestamp": "...", "cwd": "..."}
{"type": "model_change", "id": "...", "modelId": "...", "provider": "..."}
{"type": "thinking_level_change", "id": "...", "thinkingLevel": "..."}
{"type": "custom", "customType": "...", "data": {...}}
{"type": "message", "id": "...", "parentId": "...", "timestamp": "...", "message": {"role": "user", "content": [{"type": "text", "text": "..."}], "timestamp": "..."}}
{"type": "message", "id": "...", "message": {"role": "assistant", "content": [{"type": "thinking", ...}, {"type": "text", "text": "..."}]}}
```

**Five mismatches:**

1. **Top-level structure:** Each JSONL line has `{type, id, parentId, timestamp, ...}` — NOT `{role, content, timestamp}`. Messages are nested in a `message` field only when `type == "message"`.

2. **Content is NOT a string:** Content is a `list[{type, text?, ...}]`, not a `str`. Types include `"text"`, `"thinking"`, `"tool_use"`, `"tool_result"`. The plan's `content: str` and "truncate to 2000 chars" logic won't work on a list of content blocks.

3. **Multiple entry types:** The JSONL contains `session`, `model_change`, `thinking_level_change`, `custom`, and `message` entries. The plan only models `message` entries. The parser must filter for `type == "message"` and skip others (or include metadata events as system info).

4. **No `tokens` field per message:** Token counts are in the session-level entry in sessions.json, not per-JSONL-line.

5. **`timestamp` format:** In JSONL entries, timestamps are ISO strings. But in sessions.json, `updatedAt` is an int (ms Unix timestamp). The plan's `SessionSummary.updated_at: int` is correct for sessions.json, but the `SessionMessage.timestamp: str` assumption needs verification per-entry.

**Impact:** This invalidates W4.2's entire parsing logic and the `SessionMessage` Pydantic model. The W4.0 research task is supposed to catch this — but the plan pre-specifies exact Pydantic models and code that will need to be redesigned after W4.0 discovers the real format.

**→ Fix:** 
1. Mark the `SessionMessage` Pydantic model as **provisional pending W4.0 research**. 
2. Add to W4.0 exit criteria: "Document content block format. If content is a list (not string), revise `SessionMessage` model before W4.2 begins."
3. Revise `SessionMessage`:
   ```python
   class ContentBlock(BaseModel):
       type: str  # "text", "thinking", "tool_use", "tool_result"
       text: str | None = None
       # ... other fields per type
   
   class SessionMessage(BaseModel):
       id: str
       role: str
       content: list[ContentBlock] | str  # Handle both formats
       timestamp: str | None = None
       parent_id: str | None = None
   ```
4. The "truncate content to 2000 chars" logic must concatenate text blocks first, then truncate.
5. W4.4's conversation viewer must render content blocks (text, thinking, tool_use) differently — not just dump a string.

### 2. 🔴 CRITICAL — `_last_activity()` and `_extract_agent_meta()` Assume Wrong sessions.json Shape

Already detailed in Implementation Trap #1. To summarize the misalignment:

| Aspect | Plan/Code Assumes | Reality |
|--------|------------------|---------|
| sessions.json key format | `sessions.get(agent_id)` → list of sessions | `sessions.get("agent:{agent_id}:...")` → single session dict |
| `updatedAt` type | ISO string (code uses `fromisoformat()`) | Integer (ms Unix timestamp, e.g., `1772030860949`) |
| Model source for agents | `openclaw.json` agents section | Config defaults only; per-session model is in sessions.json |
| Session filtering by agent | `sessions.get(agent_id, [])` | Must iterate all keys matching `agent:{agent_id}:*` prefix |

**→ Fix:** Add a task to W0 or W2 (before W2.2's status indicators): "Fix `_last_activity()` to iterate session keys matching `agent:{agent_id}:*` prefix and parse `updatedAt` as int/ms Unix timestamp." This is a prerequisite for W2.2 to show meaningful status.

### 3. 🟡 CSS Token `--warning-text` Naming Inconsistency

The plan adds `--warning-text: #fbbf24` but uses it via direct hex: `text-[#fbbf24]` (Fix C) rather than the Tailwind utility `text-warning-text`. Meanwhile, `--warning` maps to `text-warning` in existing code. Having both `--warning` and `--warning-text` creates confusion: when do you use which?

Tailwind CSS v4 auto-generates utilities from CSS variables. `--warning-text` becomes `text-warning-text`, which is awkward alongside `text-warning`. 

**→ Fix:** Minor — rename to `--warning-contrast: #fbbf24` or just use `--warning-400: #fbbf24` to follow the Tailwind color scale pattern. Or document the convention explicitly.

### 4. 🟡 `_discover_agent_ids()` Scans Parent of OPENCLAW_HOME

```python
home = self._settings.OPENCLAW_HOME  # ~/.openclaw
if home.parent.exists():  # This is ~ (HOME)
    for entry in sorted(home.parent.iterdir()):  # Iterates entire HOME directory!
```

The code iterates the USER'S ENTIRE HOME DIRECTORY to find `workspace-*` siblings. But `OPENCLAW_HOME` is `~/.openclaw`, and `home.parent` is `~`. This iterates `~` which may have hundreds of entries (Desktop, Documents, Downloads, Applications, etc.).

The correct logic should scan `~/.openclaw/` for `workspace-*` subdirectories, not `~/` for `workspace-*` entries. The `workspace-*` directories ARE in `~/.openclaw/`, not in `~`.

Wait — checking the filesystem: `ls -d ~/.openclaw/workspace-*` confirms they're IN `~/.openclaw/`. But the code does `home.parent.iterdir()` = `~/.iterdir()` which searches `~`. The only reason this works is that there are NO `workspace-*` dirs in `~`. But if someone creates `~/workspace-test/`, it'd be picked up as an agent. The code should be `home.iterdir()` not `home.parent.iterdir()`.

**→ Fix:** This is an existing bug in `agent_service.py:146`. The plan doesn't create this bug, but it also doesn't fix it. Add to W0.4 or document it as a known issue.

---

## Verdict Justification

### Why REVISE, not APPROVED_WITH_NOTES

Round 3 approved based on internal consistency. But testing against the actual runtime data reveals:

1. **The #1 feature of this plan (Wave 4: Session Viewer) is built on incorrect format assumptions.** The JSONL format is fundamentally different from what the `SessionMessage` Pydantic model describes. Content is a list of typed blocks, not a string. Non-message entries dominate the file. The plan pre-specifies exact models that will need redesign. This isn't a minor note — it's the kind of thing that causes a Wave 4 mid-implementation rewrite.

2. **The existing `_last_activity()` function is broken and the plan doesn't fix it.** This makes Waves 2-3 (status indicators, card polish) ship with fake data. The plan correctly identifies the key format in W4.1 but doesn't retroactively fix the function that W2.2 depends on.

3. **sessions.json is 71KB per session entry due to embedded skills prompts.** The scaling math wasn't done: 200 sessions × 71KB = 14MB, parsed synchronously on every 5-second poll. This is a performance time bomb, not a "low probability" risk.

These three items are all fixable within 60-90 minutes of plan revision. The wave structure, sprint plan, design coverage, and testing strategy are solid. The corrections are surgical:

- Add `_last_activity()` fix to W0.4 or W2 (15 min)
- Mark `SessionMessage` as provisional, add JSONL format notes (20 min)
- Add content-block handling to W4.2/W4.4 descriptions (15 min)
- Add sessions.json caching to W4.1 or W0.4 (10 min)
- Add stale-fetch abort to W4.3 (5 min)
- Revise W5.1 LOC estimate (5 min)

**After these fixes, the plan is execution-ready.** The architecture is right. The wave ordering is right. The testing strategy is right. It just needs to match the real data formats.

---

## Summary Table

| # | Category | Severity | Item | Plan Section | Fix Required |
|---|----------|----------|------|-------------|--------------|
| 1 | Code-Plan | 🔴 CRITICAL | JSONL format doesn't match SessionMessage model | W4.0-W4.4 | Revise Pydantic model + parsing logic |
| 2 | Code-Plan | 🔴 CRITICAL | `_last_activity()` broken against real sessions.json keys | W2.2 prereq | Add fix task to W0 or W2 |
| 3 | Performance | 🟡 MAJOR | sessions.json 71KB/session, parsed every 5s poll | W4.1, Risk Assessment | Add caching + thread-based parse |
| 4 | State Mgmt | 🟡 MAJOR | Session fetch race on agent navigation | W4.3 | Add AbortController / stale check |
| 5 | State Mgmt | 🟡 MAJOR | `file_changed` WS events silently discarded | W6.1 or W5.3 | Wire into stale-file warning |
| 6 | Error State | 🟡 MODERATE | 82% of sessionFile paths point to `.deleted.*` files | W4.2 | Handle gracefully in error messaging |
| 7 | Impl Trap | 🟡 MODERATE | W5.1 is a rewrite, not extension (LOC underestimate) | W5.1 | Revise to 100-120 LOC |
| 8 | Code-Plan | 🟡 MODERATE | `_discover_agent_ids()` scans `~` not `~/.openclaw` | Existing bug | Document or fix in W0.4 |
| 9 | State Mgmt | 🟢 MINOR | Navigation away from dirty editor via breadcrumb | W5.3 | Add beforeNavigate guard |
| 10 | CSS | 🟢 MINOR | `--warning-text` naming inconsistency | W0.2 | Rename or document |
| 11 | Impl Trap | 🟢 INFO | B1/M2 already fixed — W0.1 faster than estimated | W0.1 | Note for implementers |

---

_Round 4 complete. Verdict: REVISE. Two critical misalignments with real data formats need plan updates before execution._
