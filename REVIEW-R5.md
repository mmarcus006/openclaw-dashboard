# Plan Review — Round 5 (Final)
_Reviewer: Final Review Agent (Opus) | Date: 2026-02-25_
_Reviewing: WAVES-v4.md_

## Verdict: APPROVED
Score: 9/10

This plan is ready for implementation. After 4 prior rounds — structural fixes, specification tightening, coverage improvements, and adversarial code verification — WAVES-v4.md is a thorough, accurate, and executable development plan. The v4 revisions directly address all 3 critical bugs found by reading actual source code, and my independent spot-checks against the live codebase confirm every fix targets the correct code, correct line numbers, and correct data structures. No new code-plan misalignments found.

The remaining items below are minor observations — none warrant a REVISE verdict.

## Must-Pass Gate Results

| Gate | Result | Notes |
|------|--------|-------|
| G1: R4 criticals addressed | ✅ | All 3 criticals (C1 JSONL format, C2 `_last_activity` key bug, C3 sessions.json bloat) have specific, complete, testable fixes in v4. See detailed findings below. |
| G2: No code-plan misalignments | ✅ | Verified all v4 fixes against actual source code. File paths, function names, line numbers, data structures, and field names all match. See Code Spot-Check Results. |
| G3: Test coverage realistic | ✅ | ~57 backend + ~26 frontend new tests. Each test targets a distinct, testable behavior. Coverage targets (85% BE / 70% FE) are achievable from the 152-test baseline. |
| G4: Wave dependencies acyclic | ✅ | DAG confirmed: W0 → {W1, W2, W3, W5}; W1 → W4; {W1-W5} → W6. No cycles. W2.1 depends on W0.5 (within W0). |
| G5: LOC estimates realistic | ✅ | Cross-referenced against calibration appendix. All estimates within 30%. W4.1 (190 impl) is tight vs. calibration (~220-250 with models) but the Pydantic models section is defined separately, which accounts for the gap. |

## Should-Pass Gate Results

| Gate | Result | Notes |
|------|--------|-------|
| G6: Parallel plan conflict-free | ⚠️ | Minor: Sprint 2 has Agent A (W2) and Agent B (W5) both touching `agent_service.py`. W2 modifies `_extract_agent_meta()`, W5.1 adds `_list_workspace_files_recursive()`. Different functions in the same file — manageable but requires coordination. |
| G7: Designer items tracked | ✅ | 56/56 items from DESIGN-REVIEW.md tracked: 38 planned in waves, 8 already passing, 7 cut with rationale, 3 in backlog. 100% coverage. |
| G8: Backlog rationale clear | ✅ | Every backlog item has a specific "Why Deferred" and "Revisit When" column. Rationale is practical (e.g., "Nobody manages agents from phone", "7 pages with a sidebar"). |
| G9: Risk mitigations actionable | ✅ | All 12 risks have specific technical mitigations, not just "be careful." Examples: sessions.json scaling → skip skillsSnapshot + cache with mtime; stale fetch → AbortController; external file changes → WS `file_changed` toast. |

## Detailed Findings

### Finding 1: W0.5 `_extract_agent_meta()` signature change needed (minor)
**Where:** W0.5, last paragraph ("Also fix `_extract_agent_meta()` model source")
**What:** The plan says to add session model reading to `_extract_agent_meta()`. Current function signature is `_extract_agent_meta(self, agent_id: str, cfg: dict)` — it doesn't receive the sessions dict. The caller `_build_summary()` has `sessions_index` available and would need to pass it. The plan describes the behavior but doesn't note the signature change.
**Severity:** Minor — any competent implementer will see this when they modify the function.
**Fix (optional):** Add a note: "Update `_extract_agent_meta()` signature to accept `sessions: dict` parameter. `_build_summary()` already has `sessions_index` available to pass."

### Finding 2: W4.2 content field population ambiguity when `full=false` (minor)
**Where:** W4.2, truncation logic paragraph
**What:** The plan says "When `full=false`, include truncated `content_text` only." But `SessionMessage` model always has `content: list[ContentBlock]` as a required field. An implementer might wonder whether to set `content=[]` when `full=false`, or include the blocks but only populate `content_text`. The model definition makes `content` non-optional.
**Severity:** Minor — the plan's intent is clear (list endpoint returns truncated text summaries, detail endpoint returns full blocks). A reasonable implementation would either: (a) make `content` optional and omit it when `full=false`, or (b) always include blocks but add truncated `content_text` for display convenience.
**Fix (optional):** Add one sentence: "When `full=false`, set `content=[]` (empty list) and populate only `content_text`. When `full=true`, populate both `content` blocks and `content_text`."

### Finding 3: Session ID URL encoding for colon-containing keys (minor)
**Where:** W4.2, endpoint `GET /api/sessions/{session_id}/messages`
**What:** Session IDs are keys like `agent:main:main` containing colons. FastAPI path parameters handle URL encoding automatically, but the frontend must encode the session ID when constructing the URL (e.g., `encodeURIComponent("agent:main:main")`). Not mentioned in W4.3's frontend implementation.
**Severity:** Minor — standard web practice, any implementer would handle this.
**Fix (optional):** Add to W4.3: "Session IDs contain colons — use `encodeURIComponent()` when building API URLs."

### Finding 4: App.tsx m3 comment fix is accurate (note)
**Where:** W0.4 m3
**What:** Verified — `WsInitializer` renders as a sibling of `RouterProvider`, not inside it. The current comment says "Must render inside RouterProvider context so it persists across navigations" which is factually incorrect. The plan correctly flags this as m3.
**Severity:** Note — confirming the plan is right.

### Finding 5: W0.1 B1/M2 confirmed already fixed (note)
**Where:** W0.1
**What:** Verified against `editorStore.ts`: B1 (ETag extraction from `error.detail?.current_etag`) is already implemented at line 87-90. M2 (`discardChanges()` reverting to `originalContent`) is already implemented at line 99-107. `keepMyChanges()` correctly sets `etag: conflictEtag` at line 112-118.
**Severity:** Note — the plan correctly predicts "VERIFY FIRST — if already fixed, mark done (~5 min)." This will save ~25 minutes from the W0.1 estimate.
**Impact:** W0 will likely finish 30 minutes faster than estimated.

### Finding 6: M1 ETag content-hash also appears already implemented (note)
**Where:** W0.1 M1
**What:** `file_service.py` already uses SHA-1[:16] content hashing via `_hash_bytes()` for both `read_file()` and `write_file()`. The `compute_etag()` method at line 126 also uses content hashing. If M1 was about the config endpoint specifically using `mtime:size`, that would need checking in the config router — but the underlying `FileService` already provides content-hash ETags.
**Severity:** Note — further reduces W0.1 time. May be 100% verification, 0% implementation.

## Code Spot-Check Results

### `agent_service.py` — W0.5 fix targets
- **`_last_activity()` (lines 207-226):** Confirmed all 3 bugs the plan identifies:
  1. `sessions.get(agent_id, [])` where `agent_id="main"` → always returns `[]` because real keys are `agent:main:main` etc. ✅
  2. Code iterates expecting a list of dicts with `updated_at`/`created_at`/`timestamp` — but values are single session dicts with `updatedAt` (camelCase, int). ✅
  3. `datetime.fromisoformat()` would fail on int timestamps. ✅
- **`_discover_agent_ids()` (lines 146-155):** Confirmed `home.parent.iterdir()` scans `~/` not `~/.openclaw/`. Plan's fix (`home.iterdir()`) is correct — `resolve_agent_workspace()` at line 82 confirms workspace dirs live under `~/.openclaw/`. ✅
- **`_extract_agent_meta()` (lines 178-205):** Confirmed reads model only from config (`agents_cfg.get(agent_id, {})`), with fallback to defaults. No session model reading. Plan's fix to add session model fallback is correct. ✅

### `editorStore.ts` — W0.1 claims
- **B1 (ETag extraction):** Line 87-90: `error.detail?.current_etag` — already fixed. ✅
- **M2 (discardChanges):** Line 99-107: reverts `content` to `originalContent` — already fixed. ✅
- **keepMyChanges ETag update:** Line 112-118: sets `etag: conflictEtag` — already fixed. ✅
- Plan's "VERIFY FIRST" note is accurate. ✅

### `file_service.py` — M1 ETag approach
- **`_hash_bytes()`** (line 131): Uses SHA-1[:16] content hash. ✅
- **`read_file()`**: Computes ETag from `_hash_bytes(raw)` — content-based. ✅
- **`write_file()`**: ETag check uses `_hash_bytes(existing_bytes)` — content-based. ✅
- **`compute_etag()`** (line 126): Uses `_hash_bytes(path.read_bytes())`. ✅
- Content-hash ETags already implemented throughout. Plan's M1 may be already done. ✅

### `App.tsx` — m3 comment
- `WsInitializer` renders as sibling of `RouterProvider`, not inside it. Comment says "Must render inside RouterProvider context" — inaccurate. Plan correctly flags this. ✅

### `Layout.tsx` — layout structure
- Current: `<main className="flex-1 overflow-auto p-6">`. The `p-6` padding is what W5.3's `noPadding` prop would conditionally remove. Plan's approach is sound. ✅
- No existing `noPadding` prop — W5.3 would add it. ✅

### `globals.css` — current tokens
- `--text-secondary: #8b95a8` — confirmed, plan correctly targets this for WCAG fix to `#a1abbe`. ✅
- `--info: #3b82f6` — declared but plan notes it's unused. W6.2 resolution (wire or remove) is correct. ✅
- No existing `--bg-elevated`, `--border-subtle`, `--text-tertiary`, etc. — confirms all W0.2 additions are genuinely new. ✅
- No conflicts between existing tokens and proposed new tokens. ✅

## Final Assessment

WAVES-v4.md is an exceptionally thorough development plan that has been refined through 4 rounds of increasingly rigorous review. The critical turning point was Round 4's adversarial code inspection, which caught 3 bugs that would have caused implementation failures — all now addressed with specific, verified fixes.

The plan's strongest qualities are: (1) every task has specific, testable exit criteria; (2) Pydantic models are pre-defined with verified field types from real runtime data; (3) the W0.5 fix for `_last_activity()` correctly targets all three compounding bugs (key format, value shape, timestamp type); (4) the sessions.json caching strategy is well-reasoned with concrete scaling math; and (5) the 56-item designer tracking table achieves 100% coverage with defensible cut/defer decisions.

The primary execution risk is Wave 4 (Session Viewer, 7-9 hours, largest wave). The plan mitigates this well: JSONL format is pre-verified, Pydantic models match real data, caching strategy is defined, and content block types are enumerated with rendering approach. The secondary risk is the Sprint 2 `agent_service.py` contention between Agents A and B — this is flagged above and manageable with basic git coordination. My confidence level for successful implementation is **high** — this plan will survive first contact with code.
