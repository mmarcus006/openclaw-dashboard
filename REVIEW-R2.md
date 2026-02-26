# Plan Review — Round 2
_Reviewer: Review Agent (Opus) | Date: 2026-02-25_
_Reviewing: WAVES-v2.md_

---

## Verdict: IMPROVING

Significant progress from v1. All 3 critical issues and 8 improvements from Round 1 are substantively addressed — not just acknowledged, but implemented with specifics. The plan is now structurally complete: every DESIGN-REVIEW item is mapped, FINAL-REVIEW blockers are in Wave 0, integration checkpoints exist, and test coverage for Wave 5 jumped from 0 to 7 frontend tests. The design system token expansion in W0.2 is thorough with good rationale for included vs deferred tokens.

However, Round 2 finds **Wave 4 LOC estimates are systematically low** (30-40% under calibration benchmarks), **tasks in Waves 1-6 lack per-task exit criteria** (Wave 0 has them, later waves don't), and **new API endpoints don't specify Pydantic response models** (breaking the `make types` pipeline). These are not structural gaps — they're specification gaps that would slow down the implementing agents. One more round of tightening should get this to APPROVED.

---

## R1 Fix Verification

| R1 Issue | Status | Notes |
|----------|--------|-------|
| C1: B1 blocker missing from Wave 0 | ✅ Fixed | W0.1 now explicitly includes B1 with the correct field (`error.detail.current_etag`), a named test case (`test_conflict_extracts_current_etag`), and a clear exit criterion ("Save after 'Keep my changes' succeeds"). Substantive fix. |
| C2: M1/M2 missing | ✅ Fixed | Both in W0.1 with VERIFY-first instructions (smart — avoids re-fixing if MVP already patched). M1 specifies SHA-1[:16] content hash. M2 specifies reverting `content` to `originalContent`. |
| C3: ~20 DESIGN-REVIEW items unassigned | ✅ Fixed | Tracking table now covers 56 items: 38 in waves, 8 passing, 7 cut with rationale, 3 in backlog. I verified all 19 previously-unassigned items from DESIGN-TRACKING.md — every one has a wave, cut decision, or backlog entry. The 6 newly-added items (AD4, AD6, Monaco theme, C6, Gap 4, G3) are correctly assigned. |
| I1: W5 EditorSidebar no tests | ✅ Fixed | W5.2 now has `EditorSidebar.test.tsx` with 3 specific tests (agent dropdown, binary blocking, dirty state ConfirmDialog). These test real behavior, not just rendering. |
| I2: W5 EditorPage integration no tests | ✅ Fixed | W5.3 now has `EditorPage.test.tsx` with 3 specific tests (file open from sidebar, dirty-state warning, URL param sync). |
| I3: Sprint schedule idle time | ✅ Fixed | Agent B now starts W3 backend after W0 baseline commit (~1.5h wait, not full W0). Clear rationale for why Agent B does W3 (backend-heavy) not W1 (frontend-heavy). |
| I4: Dark/Light Theme | ✅ Fixed | CUT with strong rationale in Q1 decision table. "Revisit only if Miller explicitly requests it." Correct call. |
| I5: Design System token additions | ✅ Fixed | W0.2 has 20+ new tokens with exact hex values, rationale for each, and explicit list of deferred tokens with "why not yet" explanations. This is well done. |
| I6: Session JSONL highest-risk | ✅ Fixed | W4.0 research subtask added (30 min). W4.1 and W4.2 both have explicit constraints: 50MB cap, schema validation, graceful degradation, format-version detection, encoding handling. |
| I7: CommandPalette | ✅ Fixed | CUT, in backlog with "Revisit when 20+ pages or routes." |
| I8: No cross-wave integration test | ✅ Fixed | Two integration checkpoints added: Alpha (after W2) and Pre-Omega (after W5). Both have automated (`make test && make build`) and manual (5-step) verification procedures. |

**R1 Fix Summary: 11/11 addressed. All substantive — no "claim to fix without substance" detected.**

---

## New Critical Issues (Round 2)

None. The plan has no structural gaps remaining. The issues below are all Improvements.

---

## New Improvements (Round 2)

### I-R2.1: Wave 4 LOC Estimates Are Systematically Low (~30-40%)

**Problem:** Wave 4 is the highest-risk wave AND the largest (5.5-7 hrs, 585 LOC). But cross-referencing against the calibration appendix, several task estimates are low:

| Task | Estimate | Calibration-Based Expected | Delta |
|------|----------|---------------------------|-------|
| W4.1 (session service + router + model) | 100 impl | ~160 (service 80-100 + router 40 + model 20) | -37% |
| W4.3 (SessionList + AgentPage tabs + API module + sessionStore) | 120 impl | ~200 (store 80-120 + component 60 + API 20 + mods 20) | -40% |
| W4 total | 585 | ~720-750 | -20% |

The calibration appendix says "Zustand store with async actions: ~80-120 LOC" and "Backend service with file I/O: ~150-200 LOC." W4.1 creates a new service with complex file I/O (JSON parsing, 50MB cap, schema validation, format-version detection, agent filtering) — that's at least 80-100 LOC for the service alone before the router and model. W4.3 creates a new Zustand store (80-120 LOC per calibration) PLUS a new component, API module, and page modifications.

**Impact:** If Wave 4 is 20% larger than estimated, the 5.5-7 hour estimate becomes 6.5-8.5 hours. Since Wave 4 slip is already identified as a risk (and cascades to W6), the underestimate compounds the risk.

→ **Fix:** Revise W4.1 to ~160 impl, W4.3 to ~200 impl. Update Wave 4 total to ~720 LOC and time estimate to 6.5-8.5 hours. Update the LOC Summary table accordingly. Total project LOC moves from ~2,850 to ~2,985.

### I-R2.2: Tasks in Waves 1-6 Lack Per-Task Exit Criteria

**Problem:** Wave 0 has excellent per-task "Exit:" lines (W0.1: "Conflict flow works end-to-end. Save after 'Keep my changes' succeeds. discardChanges() reverts content to originalContent."). But Waves 1-6 only have wave-level exit criteria. A developer working on W2.1 alone must infer completion from the wave-level exit criteria, which mix concerns from all tasks in the wave.

This matters because the plan is designed for 2 parallel agents — Agent A might be doing W2.1 while Agent B does W3.2. Each agent needs to know exactly when THEIR task is done, not just when the whole wave is done.

→ **Fix:** Add a one-line "Exit:" to each task in Waves 1-6. Examples:
- W1.1: "Exit: `/agents` renders search bar + status filter. Typing 'main' shows only matching agents. Status filter 'Active' shows 0 agents."
- W2.1: "Exit: `curl /api/agents | jq '.[0].model'` returns the agent's session model (e.g., `claude-opus-4-6`), not the config default."
- W4.3: "Exit: Agent detail page has Files/Sessions tabs. Sessions tab loads session list from API. Empty state renders for agents with no sessions."

### I-R2.3: New API Endpoints Don't Specify Pydantic Response Models

**Problem:** The project uses `make types` (openapi-typescript) to auto-generate frontend types from the backend's OpenAPI schema. This requires every endpoint to have a Pydantic response model. Five new endpoints in WAVES-v2 describe their behavior but don't name or define their Pydantic models:

| Endpoint | Wave | Response Schema Status |
|----------|------|----------------------|
| `GET /api/gateway/history` | W3.2 | ❌ No model name. Says "commands with timestamp + exit code" |
| `GET /api/cron` | W3.3 | ❌ No model name. Says "table with Name, Schedule, Next Run, Enabled" |
| `GET /api/agents/{id}/sessions` | W4.1 | ⚠️ Fields listed but no `SessionSummary` model defined |
| `GET /api/sessions/{id}/messages` | W4.2 | ⚠️ Fields listed but no `SessionMessage` model defined |
| `GET /api/agents/{id}/files?recursive=true` | W5.1 | ⚠️ Fields mentioned (size, mtime, is_binary) but no model |

Without explicit model definitions, the implementing agent will improvise names and field types, and the `make types` output may not match what the frontend expects.

→ **Fix:** For each new endpoint, specify: (a) the Pydantic response model name, (b) field names with types, (c) which file the model goes in (e.g., `models/session.py`). Example for W4.1:
```
Model: SessionSummary(sessionId: str, updatedAt: int, model: str | None, label: str | None, spawnedBy: str | None, totalTokens: int | None, inputTokens: int | None, outputTokens: int | None)
Response: SessionListResponse(sessions: list[SessionSummary], total: int)
File: backend/app/models/session.py
```

### I-R2.4: sessionStore Needs Clear-on-Agent-Change Behavior

**Problem:** W4.3 introduces a new `sessionStore.ts` for session data. The session list is per-agent (filtered by agent ID). When a user navigates from `/agents/main` to `/agents/coder`, the sessionStore must clear/replace its data. If it doesn't, the user briefly sees main's sessions on coder's page.

The plan doesn't specify this. The `agentStore` already handles this correctly (it stores all agents, not per-agent), but `sessionStore` is inherently per-agent.

→ **Fix:** Add to W4.3 task description: "sessionStore clears `sessions` array and sets `loading: true` when `selectedAgentId` changes. Selector `sessions()` returns empty array during loading. No stale data flash on agent navigation."

### I-R2.5: Wave 4 Backend Test Coverage Is Sparse for Complexity

**Problem:** W4.1 has 3 backend tests and W4.2 has 3 backend tests (6 total). These cover the happy paths (list, filter, parse, pagination, path validation, missing file). But the plan specifies 6 explicit error-handling behaviors that have no corresponding tests:

| Behavior | Specified In | Test? |
|----------|-------------|-------|
| 50MB file size cap → 413 response | W4.1 | ❌ No test |
| Unknown format-version → warning field | W4.1 | ❌ No test |
| Malformed JSONL lines → skippedLines counter | W4.2 | ❌ No test |
| UTF-8 decode errors → U+FFFD replacement | W4.2 | ❌ No test |
| Empty sessions.json | W4.1 | ❌ No test (only "missing file") |
| 50MB JSONL cap → graceful warning | W4.2 | ❌ No test |

These are exactly the edge cases that will bite in production (OpenClaw sessions can get large). If you specify defensive behavior, you should test it.

→ **Fix:** Add 4-5 more backend tests to W4: `test_sessions_json_too_large`, `test_unknown_format_version`, `test_malformed_jsonl_lines_skipped`, `test_jsonl_file_too_large`. This brings W4 backend tests from 6 to ~10, which is appropriate for the highest-risk wave. Update the testing strategy table accordingly.

### I-R2.6: DESIGN-TRACKING.md Still Shows R1 Snapshot

**Problem:** DESIGN-TRACKING.md still has 19 items marked "⬜ NEEDS WAVE" from the R1 snapshot. WAVES-v2.md has its own comprehensive tracking table that supersedes it. But two tracking documents that disagree is confusing for implementing agents.

→ **Fix:** Either (a) update DESIGN-TRACKING.md to match WAVES-v2's tracking table, or (b) add a note at the top of DESIGN-TRACKING.md: "⚠️ Superseded by the Designer Issue Tracking table in WAVES-v2.md. This file reflects the R1 snapshot."

### I-R2.7: W3.3 Cron Job Viewer Has No Error State for Malformed Cron Expressions

**Problem:** W3.3 uses `croniter` to compute "Next Run" from cron expressions. If a user has a malformed cron expression in `openclaw.json`, `croniter` will raise an exception. The task doesn't specify error handling for this case. Should the entire cron list fail? Should the one bad job show "Invalid expression"?

→ **Fix:** Add to W3.3: "If `croniter` fails to parse a cron expression, show the job with 'Invalid schedule' in the Next Run column and `text-danger` styling. Don't fail the entire list."

---

## Acceptance Criteria Audit

| Task | Issue | Suggested Fix |
|------|-------|---------------|
| W1.1 | No per-task "Exit:" line | "Exit: `/agents` renders SearchInput + status dropdown. Typing 'main' filters to matching agents. Selecting 'Active' shows 0 agents when none active." |
| W1.2 | No per-task "Exit:" line | "Exit: `/` shows 4 stat cards with icons, recent activity list (5 agents), gateway summary, and quick nav cards. No AgentGrid import." |
| W1.3 | No per-task "Exit:" line | "Exit: `filteredAgents()` selector returns correct subset for search term + status filter + sort. Filter state persists within session." |
| W2.1 | No per-task "Exit:" line | "Exit: `GET /api/agents` returns per-agent model from most recent session. Agent with no sessions returns config default. No agent shows hardcoded `gpt-5.3-codex`." |
| W2.2 | No per-task "Exit:" line | "Exit: Cards have colored left-border stripe (green/amber/gray). Active dots pulse. 'Never' timestamps show 'No sessions yet' in muted text. Hover lifts card." |
| W3.1 | No per-task "Exit:" line | "Exit: Gateway page loads in <2s. API timeout after 5s shows error state. Stopped gateway shows prominent Start button. Disabled buttons have tooltips." |
| W3.2 | No per-task "Exit:" line | "Exit: Channels render as table (not JSON). Last 5 commands shown. 'No recent commands' placeholder when history empty." |
| W3.3 | No per-task "Exit:" line | "Exit: Cron section shows jobs from config with human-readable schedule (cronstrue) and computed next run (croniter). Empty state for no jobs." |
| W4.1 | No per-task "Exit:" line | "Exit: `GET /api/agents/{id}/sessions` returns paginated sessions sorted by updatedAt desc. Filter by agent key prefix works. 50MB cap returns 413." |
| W4.2 | No per-task "Exit:" line | "Exit: `GET /api/sessions/{id}/messages` returns paginated JSONL messages. Malformed lines skipped with counter. Path traversal returns 403." |
| W4.3 | No per-task "Exit:" line | "Exit: Agent detail page has Files/Sessions tabs. Sessions tab shows list with date, model, tokens. 'Load more' button works. Empty state for agents with no sessions." |
| W4.4 | No per-task "Exit:" line | "Exit: Messages render in conversation layout (user right, assistant left). Code blocks highlighted. Long messages collapsed at 500 chars with 'Show more'. Copy button works." |
| W5.1 | No per-task "Exit:" line | "Exit: `GET /api/agents/{id}/files?recursive=true` returns flat list with size, mtime, is_binary. Max depth 3 enforced. `.git`/`node_modules` excluded." |
| W5.2 | No per-task "Exit:" line | "Exit: 240px sidebar with agent dropdown. Binary files show `cursor-not-allowed`. File click with dirty state shows ConfirmDialog. URL updates on file selection." |
| W5.3 | No per-task "Exit:" line | "Exit: Editor background matches dashboard (#0f1219). No color seam. Layout uses `noPadding` prop. Breadcrumb shows `Agents / {name} / {file}`." |
| W6.1 | No per-task "Exit:" line | "Exit: Toasts auto-dismiss at 5s, stack max 3, slide-in animation. All save/error/gateway operations trigger toasts. Amber banner on WS disconnect." |
| W6.2 | No per-task "Exit:" line | "Exit: Save tooltip says 'No unsaved changes' when disabled. FileJson icon on config path. JSON validates on every keystroke. `document.title` updates per page." |
| W6.3 | No per-task "Exit:" line | "Exit: Reload config when dirty shows ConfirmDialog. `/nonexistent` shows 404 page with 'Go home' button." |
| W6.4 | No per-task "Exit:" line | "Exit: `make test` green. `make e2e` (smoke.sh) green. Backend coverage ≥85%. WebSocket coverage ≥60%." |

---

## LOC Estimate Audit

| Task | Estimate | Expected (Calibration) | Delta | Issue |
|------|----------|------------------------|-------|-------|
| W4.1 (session service + router + model) | 100 impl | ~160 | -37% | Service with JSON parse + 50MB cap + schema validation + agent filtering = 80-100 LOC alone. Plus router (~40) + model (~20). |
| W4.3 (SessionList + AgentPage + API + sessionStore) | 120 impl | ~200 | -40% | New Zustand store = 80-120 per calibration. Plus component (~60) + API module (~20) + page mods (~20). |
| W3.3 (CronJobList + cron_service + cron router) | 100 impl | ~130 | -23% | Component (~60) + service (~40-50) + router (~30). Marginal but worth noting. |
| W0.2 (CSS tokens + JSX fixes) | 70 modified | ~70-80 | OK | Close enough. Token declarations are one-liners. |
| W4.4 (SessionViewer) | 120 impl | ~120-150 | OK | Complex component, calibration says 100-150. Estimate is at the low end but defensible. |
| W5.2 (EditorSidebar + FileList) | 170 impl | ~190-210 | -12% | Marginal. Within acceptable range. |

**Summary:** W4.1 and W4.3 are meaningfully under-estimated. The rest are within ±25% which is acceptable. Revising Wave 4 adds ~140 LOC to the project total, pushing it from ~2,850 to ~2,990.

---

## Strengths (keep these — improvements from v1)

1. **Decisions table (Q1-Q5) is excellent.** Each question has a decision, rationale, and confidence level. The light theme cut (Q1) and shell-over-Playwright (Q5) are particularly well-argued. This is how planning decisions should be documented.

2. **Designer Issue Tracking table is comprehensive.** 56 items with wave assignments, cut rationale, and backlog notes. 100% coverage of DESIGN-REVIEW items. This alone resolves the biggest R1 gap (C3).

3. **W0.2 design token expansion with included/deferred rationale.** The planner didn't just dump all tokens in — they chose which ones are needed now (consumed by W1-W6 components) vs which to defer, with explanations. This shows architectural thinking.

4. **Integration checkpoints with both automated and manual verification.** The Alpha (W2) and Pre-Omega (W5) checkpoints have specific `curl` commands AND 5-step manual walkthroughs. This catches cross-wave regressions without requiring Playwright.

5. **Wave 5 test coverage jumped from 0 to 7 frontend tests.** The most impactful change from v1. EditorSidebar (3 tests) and EditorPage (3 tests) cover real interactive behavior, not just rendering.

6. **Sprint parallelism is well-reasoned.** The explanation for why Agent A does W0 solo (avoid merge conflicts on shared files) and why Agent B starts W3 (backend-heavy, non-overlapping files) shows practical understanding of multi-agent coordination.

7. **Risk assessment improved.** 7 risks with actionable mitigations. The W4.0 research subtask directly mitigates the highest risk (session format uncertainty). The Monaco theme fallback is pragmatic.

8. **W4.0 research subtask is the right call.** 30 minutes to document the actual session file format before writing 500+ LOC against it. This alone could save hours of rework.

---

## Questions for Planner

1. **W4.3 sessionStore — what happens on agent change?** If a user navigates from `/agents/main` to `/agents/coder`, does the store clear? Show stale data? The plan should specify the reset behavior to prevent stale session flashes.

2. **W3.2 gateway history — is this in-memory only?** "Store last 10 commands in memory" means history resets on backend restart. Is that acceptable? If yes, document it explicitly so the implementing agent doesn't try to persist to disk.

3. **W4.2 message content truncation — 2000 chars in list view, full on dedicated endpoint?** The task mentions "Truncate content to 2000 chars in response (full content on dedicated endpoint if needed)." Is the dedicated endpoint in scope for this wave, or deferred? If deferred, long messages in the viewer (W4.4) will be truncated with no way to see the full content.

4. **W5.1 recursive listing + W5.2 file browser — what about agents with 500+ workspace files?** The recursive listing has max depth 3, but a flat directory with 500 files at depth 1 would still return all of them. Should there be a count limit (e.g., first 200 files)? The plan has a risk for "sessions.json too large" but not for "workspace listing too large."

5. **W6.4 coverage push — is 85% backend or overall?** Exit criteria say "Backend coverage ≥ 85%" and "WebSocket coverage ≥ 60%." What about frontend coverage? The testing strategy table shows cumulative 85%+ but doesn't clarify if that's backend, frontend, or combined.

---

## Summary Statistics

| Metric | v1 Value | v2 Value | Change |
|--------|----------|----------|--------|
| Waves | 13 | 7 | -6 (consolidated) |
| Tasks | 47 | 38 | -9 |
| FINAL-REVIEW items covered | 8/11 (73%) | 11/11 (100%) | +3 |
| DESIGN-REVIEW P0 items covered | 5/5 | 5/5 | — |
| DESIGN-REVIEW P1 items covered | 3/10 (30%) | 10/10 (100%) | +7 |
| DESIGN-REVIEW P2+ items covered/cut | ~5/15 (33%) | 41/41 (100%) | All tracked |
| Tasks with per-task exit criteria | Wave 0 only | Wave 0 only | ⚠️ No change |
| New API endpoints with response schemas | N/A | 0/5 | ⚠️ New gap |
| Test count (planned new) | ~38 BE + ~23 FE | ~38 BE + ~23 FE | — |
| W5 frontend tests | 0 | 7 | +7 ✅ |
| Est. total hours | 55-70 | 26-33 | -50% (scope cut) |
| Total LOC | ~5,840 (13-wave) | ~2,850 (should be ~2,990) | -49% |
| R1 issues addressed | — | 11/11 (100%) | ✅ |

---

## Round 2 Action Items (ordered by priority)

1. **Add per-task "Exit:" lines to all tasks in Waves 1-6** (I-R2.2) — Biggest specification gap. Use the acceptance criteria audit table above as a starting point.
2. **Revise W4 LOC estimates** (I-R2.1) — W4.1: 100→160, W4.3: 120→200. Update totals.
3. **Specify Pydantic response models for new endpoints** (I-R2.3) — Name the models, list fields with types, specify file locations.
4. **Add W4 backend edge-case tests** (I-R2.5) — 4-5 tests for 50MB cap, malformed JSONL, format version, empty file.
5. **Specify sessionStore agent-change behavior** (I-R2.4) — One line in W4.3.
6. **Add cron expression error handling to W3.3** (I-R2.7) — One line.
7. **Update or supersede DESIGN-TRACKING.md** (I-R2.6) — Low effort.

**Estimated revision effort: 30-45 minutes.**

---

_Round 2 complete. Plan is structurally sound. Remaining gaps are specification precision, not architecture. Expecting APPROVED after Round 3 revisions._
