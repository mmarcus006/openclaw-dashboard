# QA Fixes Log

## 2026-02-26 — QA Agent during Wave 1 + Wave 3

### Fix 1: Unused imports in `tests/test_gateway_service.py`
- **Pass #4** — Wave 3 agent added new test file with unused `pytest` and `GatewayService` imports
- **Fix**: Removed both unused imports
- Tests: 168 passed after fix

### Fix 2: Unused imports in `tests/test_cron_service.py`
- **Pass #4** — Wave 3 agent added new test file with unused `pytest` and `CronService` imports (same pattern)
- **Fix**: Removed both unused imports
- Tests: 168 passed after fix

## 2026-02-26 — QA Agent during Waves 2+4+5 (Sprint 2)

### Fix 3: Undefined name `FileListResponse` in `agent_service.py` (F821)
- **Round 4** — Wave 5 agent added `list_workspace_files_recursive()` with return type annotation `"FileListResponse"` but the import was only inside the function body
- **Fix**: Added `from __future__ import annotations` and `TYPE_CHECKING` guard import for `FileListResponse`
- Ruff: Clean after fix

### Fix 4: Unused imports in `session_service.py` (F401)
- **Round 4** — Wave 4 agent added `from datetime import datetime, timezone` but neither is used
- **Fix**: Removed the entire unused `from datetime` import line

### Fix 5: Unused variable `message_count` in `session_service.py` (F841)
- **Round 4** — Wave 4 agent assigned `message_count = 0` but never read it
- **Fix**: Removed the unused assignment

### Fix 6: Broken `test_path_traversal_blocked` in `test_session_service.py`
- **Round 5** — Wave 4 agent wrote test using `../../etc/passwd` in URL, but httpx normalizes `..` path segments before sending → route returns 404 not 403
- **Fix**: Used percent-encoded dots (`%2e%2e%2fetc%2fpasswd`) so `..` reaches FastAPI literally
- Backend: 187 passed after fix

### Fix 7: Unused `pytest_asyncio` import in `test_session_service.py` (F401)
- **Round 5** — Wave 4 agent imported `pytest_asyncio` but never used it
- **Fix**: Removed unused import

### Fix 8: Unused imports in session frontend components (TS6133)
- **Round 5** — Wave 4 agent left unused `Copy`, `Check` in ContentBlockRenderer.tsx and unused `Cpu`, `Card` in SessionList.tsx
- **Fix**: Removed all 4 unused imports
- TSC: Clean after fix

### Fix 9: Unused `userEvent` import in `SessionList.test.tsx` (TS6133)
- **Round 6** — Wave 4 agent imported `userEvent` but never used it
- **Fix**: Removed unused import

### Fix 10: Unused `selectedSessionId` in `AgentDetail.tsx` (TS6133)
- **Round 6** — Wave 4 agent declared `selectedSessionId` from sessionStore but never referenced it
- **Fix**: Removed unused variable declaration

---

## 2026-02-26 — QA Agent during Wave 6

### Fix 11: Unused imports and variable in Wave 6 test files (F401, F841)
- **Loop 9** — Wave 6 agent added new tests in `test_integration.py` and `test_websocket.py` with unused imports (`os`, `timezone`, `MagicMock`) and an unused variable (`svc`)
- **Fix**: Removed `import os` from test_integration.py, removed `timezone` and `MagicMock` imports from test_websocket.py, removed unused `svc` assignment (along with its setup lines `s` and `fs`) from test_websocket.py
- Ruff: Clean after fix, Backend: 293 passed

---

## 2026-02-26 — QA Agent during Wave 7

### Fix 12: EditorSidebar test expects 'COS (main)' but dropdown changed to custom listbox
- **Cycle 3** — Wave 7 agent replaced the native `<select>` dropdown with a custom listbox. The button now shows only the agent name (`COS`), with `COS (main)` visible only when the dropdown is opened.
- **Fix**: Updated test to check for `COS` in the button, then open the dropdown and verify `COS (main)` in the listbox options.

### Fix 13: Unused `useState` import in AgentDetail.tsx (TS6133)
- **Cycle 3** — Wave 7 agent replaced `useState<TabId>('files')` with URL-based state via `useSearchParams`, but left the `useState` import.
- **Fix**: Removed unused `useState` import.

### Fix 14: `TABS[index]` returns `TabId | undefined` in AgentDetail.tsx (TS2345)
- **Cycle 3** — Array indexing with modular arithmetic returns `TabId | undefined` due to strict TypeScript array types, but `setActiveTab` expects `TabId`.
- **Fix**: Added `as TabId` assertion since the modular arithmetic guarantees a valid index.

### Fix 15: Card component doesn't accept `id`, `role`, `aria-labelledby` props (TS2322)
- **Cycle 3** — Wave 7 agent added ARIA attributes to `<Card>` in AgentDetail.tsx, but `CardProps` didn't extend `HTMLDivElement` attributes.
- **Fix**: Extended `CardProps` to `React.HTMLAttributes<HTMLDivElement>` and spread `...rest` onto the underlying `<div>`.

---

**WAVE 7 FINAL PASS (Cycle 5): ALL GREEN**

| Check | Result |
|-------|--------|
| Backend tests | 293 passed |
| Frontend tests | 37 passed (13 files) |
| Ruff lint | All checks passed |
| TSC types | Clean |

**Wave 7 committed**: `0786705` feat: Wave 7 — design polish, P1/P2 fixes from design review V2

**Summary**: 5 QA cycles, 4 fixes applied (Fixes 12-15). Wave 7 committed and verified green.
