# Plan Review — Round 1

_Reviewer: Review Agent (Opus) | Date: 2026-02-25_

---

## Verdict: NEEDS_WORK

The plan is structurally sound — wave decomposition, dependency graph, TDD-first approach, and calibration appendix are all well-done. But it has **3 critical gaps** that must be fixed: (1) the FINAL-REVIEW blocker B1 is not in any wave, (2) ~20 DESIGN-REVIEW recommendations have no assigned wave task, and (3) several tasks lack test coverage for non-trivial components. The estimates are tight but defensible. Sequencing is good with minor improvements possible.

---

## Critical Issues (must fix before next version)

### C1. **FINAL-REVIEW Blocker B1 Missing from Wave 0**
**Problem:** FINAL-REVIEW.md identifies B1 (editor conflict handler extracts `error.message` instead of `error.detail.current_etag`) as the **only blocker** for ship. It's a ~10-line fix. But WAVES.md Wave 0 doesn't include it — W0.3 covers the *Config* ETag header (m4), not the *editor* conflict ETag extraction (B1).
→ **Fix:** Add a new task W0.5 (or fold into W0.3) that explicitly fixes `editorStore.ts:87` conflict handler to extract `detail.current_etag` from the ApiError. Test file: `frontend/src/stores/__tests__/editorStore.test.ts::test_conflict_extracts_current_etag`. This is the single most important fix in the entire plan.

### C2. **FINAL-REVIEW Majors M1 and M2 Not Assigned**
**Problem:** M1 (config ETag same-second race — content-hash fix, ~5 lines) and M2 (`discardChanges` doesn't revert content, ~3 lines) are flagged as "should fix before regular use" in FINAL-REVIEW. Neither appears in any wave. M1 is particularly dangerous because config saves are the most likely scenario for same-second collisions.
→ **Fix:** Add M1 and M2 to Wave 0. M1 → fold into W0.3 (already touches config ETags). M2 → fold into W0.1 or new W0.5. Both are <10 lines. Total additional time: ~15 minutes.

### C3. **~20 DESIGN-REVIEW Recommendations Unassigned**
**Problem:** The plan addresses the 5 Executive Summary items (E1-E5) and some per-page issues, but many P1 and P2 recommendations from DESIGN-REVIEW have no corresponding wave task. Specifically unassigned:

**P1 (should fix):**
- Fix A: `--text-secondary` contrast (#8b95a8 → #a1abbe) — WCAG AA failure
- Fix B: Accent badge text contrast
- Fix C: Warning badge text contrast
- D1: Active count 0 showing green
- D5: Model display bug (all agents showing "gpt-5.3-codex") — this is a **real bug**, not polish
- AD1: Filter/group binary files in file list
- AD3: Block editor open for binary files (Monaco will show garbage)

**P2 (should fix when nearby):**
- CC2: Skeleton loading states (replace spinners)
- CC5: Focus ring on file table rows (WCAG 2.4.11)
- C3: Reload confirmation when dirty
- C4: Auto-validate config on change
- T1: Page title h1 text-sm → text-base
- T3: Tabular figures for stat numbers
- CC7: Document title updates per page

→ **Fix:** Create a new **Wave 0.5: Design System & Contrast Fixes** (or fold into Wave 0) covering all 3 WCAG contrast fixes (Fix A/B/C), the sidebar `border-l-2` active state, the `--bg-elevated` token, and the D1 green-zero fix. These are all CSS-only or single-line JSX changes — total ~30 minutes. Assign D5 (model display bug) to Wave 2 since it's agent-data related. Assign AD3 (binary file blocking) to Wave 3 or Wave 5. Assign the remaining P2 items to the wave that touches the relevant component.

---

## Improvements (should fix)

### I1. **W5.3 EditorSidebar (100 LOC) Has No Tests**
**Problem:** W5.3 creates a resizable sidebar with agent selector dropdown and collapse button. It says "N/A (integration test via E2E)" for the test file. But the E2E smoke test (W12.4) is a `curl`-based shell script that can't test frontend component behavior. This is a non-trivial interactive component with resize drag handle, min/max constraints, and collapse toggle.
→ **Fix:** Add a test file: `frontend/src/components/editor/__tests__/EditorSidebar.test.tsx` testing: (a) agent dropdown renders and changes agent, (b) collapse button hides sidebar, (c) resize respects min 180px and max 400px bounds.

### I2. **W5.4 EditorPage Integration Has No Tests**
**Problem:** W5.4 integrates the sidebar into EditorPage with dirty-state warnings on file switch and URL updates. This is business logic, not just visual wiring. "N/A (visual verification)" is insufficient.
→ **Fix:** Add test: `frontend/src/pages/__tests__/EditorPage.test.tsx` testing: (a) opening a file from tree loads it in editor, (b) switching files with unsaved changes shows warning, (c) URL updates with agent and path params.

### I3. **Sprint Schedule Has Agent B Waiting for Wave 0**
**Problem:** The "Optimal Execution Order" in the appendix shows Agent B waiting for Wave 0, then doing W4→W6. Wave 0 is 1-2 hours. Having Agent B idle for 1-2 hours at the start wastes time.
→ **Fix:** Wave 0 is small enough for one agent. Restructure Sprint 1:
- Agent A: Wave 0 (1-2h) → Wave 1 (4-6h)
- Agent B: Starts Wave 4 immediately after W0 completes (Agent A shares the clean baseline), then Wave 6
- Or better: Agent A does W0 solo, then both agents split W1 (backend-heavy tasks) and W4/W6 (frontend-heavy tasks) in parallel.

### I4. **W10.1 Dark/Light Theme Underestimated**
**Problem:** W10.1 estimates 100 LOC for implementation. But the current codebase uses hardcoded CSS variable values throughout `globals.css`. A proper light theme requires: (a) all 12+ CSS variables duplicated under `.light` class, (b) a mechanism to avoid FOUC (flash of unstyled content), (c) testing both themes across all pages. The 100 LOC estimate doesn't account for all the CSS variable duplication.
→ **Fix:** Bump estimate to 150-180 LOC impl. Consider whether light theme is actually needed for a localhost developer tool. If not, move to a future wave and save 5-7 hours.

### I5. **No Explicit Task for Design System Token Additions**
**Problem:** DESIGN-REVIEW §7.1 proposes a complete CSS variable set with new tokens: `--bg-elevated`, `--bg-base`, `--border-strong`, `--border-subtle`, `--text-tertiary`, `--text-inverse`, `--success-light`, `--warning-text`, `--danger-light`, `--shadow-card`, `--shadow-modal`, `--z-sidebar`, `--z-header`, `--z-modal`, `--z-toast`, `--z-tooltip`, `--transition-fast/base/slow`, and `--radius-sm/md/lg/xl`. None of these additions are assigned to a wave.
→ **Fix:** Add a task to Wave 0 or create Wave 0.5: "Extend CSS variables per DESIGN-REVIEW §7.1". These tokens will be consumed by later waves. Doing it upfront prevents ad-hoc `#hex` values creeping into components.

### I6. **Wave 8 Session JSONL Parsing Is the Highest-Risk Task with No Fallback Strategy**
**Problem:** W8.1 says "Reads from `~/.openclaw/sessions/` directory" and W8.2 says "Returns paginated messages from a session JSONL file." But the plan doesn't specify: (a) the exact JSONL schema, (b) what happens if the format changes between OpenClaw versions, (c) a size limit for session files (some could be 50MB+). The risk assessment says "Medium-high" but the only mitigation is "cursor-based pagination."
→ **Fix:** Add explicit constraints: (a) max file size to scan = 50MB, return "session too large" for bigger files, (b) schema validation with graceful degradation (unknown fields ignored, missing fields = null), (c) add a `--format-version` check in the session file header if one exists. Also consider: W8.1 should include a research subtask to document the actual session file format before implementing.

### I7. **W10.4 CommandPalette Estimate Too Low**
**Problem:** W10.4 estimates 120 LOC for a command palette that searches agents by name, files by name, and navigates to pages. Real command palettes (VS Code, Linear, GitHub) need: fuzzy search algorithm, keyboard navigation (up/down/Enter/Escape), result grouping by category, recent items, and focus management. 120 LOC is a basic modal, not a command palette.
→ **Fix:** Either (a) bump to 200-250 LOC and 4-5 hours, or (b) scope down to "agent search only" (no file search, no page navigation) and keep the estimate. I'd recommend (b) — ship simple, iterate.

### I8. **No Integration Test Between WebSocket (W7) and Editor (W5)**
**Problem:** W7.2 says "When `file_changed` event for file open in editor, show a toast: 'File modified externally' with 'Reload' action. If the user has unsaved changes, show conflict dialog." This is a critical cross-wave interaction (WS event → editorStore update → UI dialog). But there's no integration test planned for this flow until W12, which is far away.
→ **Fix:** Add an integration checkpoint after Wave 7 that explicitly tests: (a) modify a file on disk while it's open in the editor, (b) verify toast appears, (c) with dirty state, verify conflict dialog appears. This can be manual but should be documented in the Wave 7 exit criteria.

---

## Strengths (don't change these)

### S1. **TDD-First Per Task**
Every task specifies the test file before the implementation file. The "test first, then impl" ordering within each wave enforces discipline. This is exactly right for a 47-task plan.

### S2. **Dependency Graph with Parallelization Opportunities**
The ASCII dependency graph and matrix are clear. Identifying that W1+W4+W6 can run in parallel after W0, and that W2+W3 can run in parallel after W1, is valuable for the 2-agent execution strategy.

### S3. **Calibration Appendix**
Providing actual LOC measurements from the existing codebase as a reference for estimates is excellent. The "rule of thumb" section (page=50 LOC, complex component=150 LOC, etc.) gives the executing agents a concrete baseline.

### S4. **Integration Checkpoints Every 3 Waves**
The 4 checkpoint structure (after W0-2, W3-5, W6-8, W9-11) with specific verification commands catches cross-wave regressions early.

### S5. **Coverage Target Ratchet**
The per-wave coverage targets (75% → 76% → ... → 85%) create a monotonically increasing quality bar. No wave is allowed to decrease coverage.

### S6. **Risk Assessments Per Wave**
Every wave has a risk assessment with probability and mitigation. The honesty about W8 being "Medium-high" risk is good.

### S7. **Exit Criteria Are Specific and Measurable**
Exit criteria like "40 agents filtered in <5ms" (W1.3), "response time <50ms per agent" (W2.2), and "Build time under 2 seconds" (W10) are concrete and testable.

---

## Questions for Planner

1. **Is light theme actually needed?** W10.1 adds dark/light toggle for a localhost developer tool. Miller uses dark mode (the entire codebase is dark-first). If light theme is cut, Wave 10 shrinks by ~5 hours and the theme-related risks disappear. Should it be deferred to a future wave?

2. **Should the model display bug (D5) be prioritized higher?** DESIGN-REVIEW reports all 40 agents show "gpt-5.3-codex" as the model. If this is a backend parsing bug, it should be in Wave 0 (bug fix). If it's a test environment artifact, document it and move on.

3. **What's the session JSONL format?** W8 depends entirely on correctly parsing session files. Has anyone documented the actual schema? Should there be a W8.0 research task?

4. **Is `croniter` the right dependency for W9?** Adding a new Python dependency for a read-only cron viewer seems heavy. Python's `cron_descriptor` is lighter for human-readable descriptions, and next-run can be computed with a simple regex parser for common cron expressions. Or just display the raw expression with no computation.

5. **Should Wave 12 E2E be a shell script or Playwright?** W12.4 specifies a `curl`-based `smoke.sh`. This can't test any frontend behavior (navigation, search, file opening). A Playwright smoke test would cover the full stack. Is shell-only intentional to avoid adding Playwright as a dependency?

---

## Missing Features / Gaps

- **B1 blocker from FINAL-REVIEW** (editor conflict ETag) — not in any wave
- **M1 major from FINAL-REVIEW** (config content-hash ETag) — not in any wave
- **M2 major from FINAL-REVIEW** (`discardChanges` content revert) — not in any wave
- **3 WCAG contrast fixes** (Fix A, B, C from DESIGN-REVIEW §2.3) — not assigned to any wave
- **Sidebar active state `border-l-2`** (E5 from DESIGN-REVIEW) — not explicitly in W1.4
- **`--bg-elevated` and extended CSS tokens** (DESIGN-REVIEW §7.1) — not assigned
- **D5: Model display bug** ("gpt-5.3-codex" on all agents) — not assigned
- **AD3: Binary file blocking in editor** — user can open .png in Monaco with no guard
- **CC2: Skeleton loading states** — spinners are the only loading pattern
- **CC7: Document title per page** — all tabs show "OpenClaw Dashboard"
- **C3: Reload confirmation when editor is dirty** — silent data loss risk
- **C4: Config auto-validate on change** — requires manual button click
- **Memory explorer / search** (PLAN-v2 Phase 2) — not included, acceptable but worth noting
- **Diff view in editor** (PLAN-v2 Phase 2) — not included, acceptable
- **`--info` token orphaned** — declared but unused, should wire or remove

---

## Suggested Resequencing

1. **Move B1/M1/M2 into Wave 0.** These are the FINAL-REVIEW's highest-priority fixes (combined: <30 minutes). Not having them in Wave 0 means the codebase starts feature work with a known blocker. This is the most important resequencing change.

2. **Create Wave 0.5 (or expand Wave 0) for Design System tokens + WCAG fixes.** The 3 contrast fixes, sidebar active state, and CSS token additions from DESIGN-REVIEW §7.1 are all CSS-only changes. Doing them before any feature wave means new components automatically use the correct tokens. Total: ~45 minutes.

3. **Move W10.1 (dark/light theme) to Wave 13 (optional).** If Miller doesn't need light theme, this saves 5-7 hours and removes a risk. Keep W10.2 (responsive), W10.3 (error pages), and W10.4 (keyboard shortcuts) in Wave 10.

4. **Split W8 into W8a (backend: sessions parsing) and W8b (frontend: session viewer).** W8 is the highest-risk wave. By splitting, W8a can be validated independently (correct data from API) before W8b builds UI on top. W8a.0 should be a 30-minute research task documenting the session JSONL format.

5. **Move W9 (Cron Viewer) earlier — it can run in parallel with W5.** W9 depends only on W4. W5 depends on W3. They're completely independent. In the current Sprint 2 schedule, Agent B does W7→W9, but W7 has heavy dependencies (W2+W6). If Agent B did W9 while waiting for W2/W6 to complete, it would reduce idle time.

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Session JSONL format varies across OpenClaw versions** — W8 parses files with unknown schema stability | High | High | Add W8.0 research task. Parse defensively with schema validation. Set 50MB file size limit. Fallback to "format unsupported" message. |
| **WebSocket event ordering / race conditions** — W7 has multiple stores reacting to WS events, possible stale state | Medium | High | Keep 30s polling as fallback. Add sequence numbers to WS events. Test with simulated rapid-fire events. |
| **FileTree keyboard navigation complexity** — W5.2 is a non-trivial accessible component | Medium | Medium | Scope down: if keyboard nav exceeds estimate, ship with click-only first, add keyboard in a follow-up. Use a flat indented list instead of recursive tree. |
| **Light theme CSS propagation** — W10.1 requires all components to use CSS variables, not hardcoded hex values | Medium | Medium | Audit all components for hardcoded colors before starting W10.1. Consider deferring entirely. |
| **Command palette scope creep** — W10.4 fuzzy search across agents + files + pages is complex | Medium | Low | Scope to agent search only for v1. Add file search and page navigation in a follow-up wave. |
| **Wave 8 slip cascades to W11 and W12** — W11 (agent tree) depends on W8, W12 depends on all | High | High | If W8 slips, W11 can proceed with mock session data. W12 can start backend-only tests while W8 frontend completes. |
| **`croniter` dependency introduces supply chain risk** — W9 adds a new PyPI dependency | Low | Low | Pin version in pyproject.toml. Alternatively, use stdlib `datetime` + simple cron parser for the 5-6 common patterns. |

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Waves | 13 (W0–W12) |
| Tasks | 47 |
| Tasks with no test file | 8 (17%) — 2 are non-trivial (W5.3, W5.4) |
| FINAL-REVIEW items covered | 8/11 (missing B1, M1, M2) |
| DESIGN-REVIEW P0 items covered | 5/5 |
| DESIGN-REVIEW P1 items covered | 3/10 (30%) |
| DESIGN-REVIEW P2 items covered | ~5/15 (33%) |
| Est. total hours | 55-70 (realistic if light theme deferred) |
| Highest-risk wave | Wave 8 (Session & Log Viewer) |
| Most likely to slip | Wave 8 (unknown JSONL format + complex UI) |

---

_Round 1 complete. Awaiting planner revisions for Round 2._
