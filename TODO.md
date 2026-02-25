# OpenClaw Dashboard — Build TODO
_Created: 2026-02-25T06:13:00-05:00 | Coordinator: COS_

## Execution Pipeline

```
Phase 0: Planner (MiniMax) ──────────────────────────┐
         Creates skeleton, deps, stubs, types         │
         COS verifies output                          │
                                                      ▼
Phase 1: Backend (Sonnet) ◄──────── parallel ────────► Frontend (Sonnet)
         FastAPI app, all routers,                     React app, all components,
         services, middleware                          pages, stores, styling
         COS monitors both (10-min check-ins)          │
                                                      ▼
Phase 2: Overseer (Opus) ────────────────────────────┐
         Verifies integration, runs make types,       │
         checks API contract alignment                │
                                                      ▼
Phase 3: Tester (MiniMax) ──────────────────────────┐
         Backend tests, frontend tests,               │
         security tests, coverage report              │
                                                      ▼
Phase 4: Reviewer (Opus) ───────────────────────────┐
         Final code review, security audit,           │
         verify all 12 review recommendations         │
                                                      ▼
Phase 5: COS Integration ──────────────────────────┐
         make setup → make dev → manual test →       │
         make build → git init → ship                │
```

---

## Phase 0: Planner (MiniMax-M2.5) — SKELETON + STUBS

| # | Task | Files | Done |
|---|------|-------|------|
| P-01 | Create full directory structure | All dirs per PLAN-v2.md §4 | ☐ |
| P-02 | Create top-level Makefile | `Makefile` | ☐ |
| P-03 | Create pyproject.toml with all deps | `backend/pyproject.toml` | ☐ |
| P-04 | Create package.json with all deps | `frontend/package.json` | ☐ |
| P-05 | Create vite.config.ts with /api proxy | `frontend/vite.config.ts` | ☐ |
| P-06 | Create tailwind.config.ts with dark theme colors | `frontend/tailwind.config.ts` | ☐ |
| P-07 | Create tsconfig.json | `frontend/tsconfig.json` | ☐ |
| P-08 | Create .gitignore (Python + Node + macOS) | `.gitignore` | ☐ |
| P-09 | Create backend Settings class | `backend/app/config.py` | ☐ |
| P-10 | Create ALL Pydantic models with examples | `backend/app/models/*.py` | ☐ |
| P-11 | Create TypeScript type stubs matching Pydantic models | `frontend/src/types/index.ts` | ☐ |
| P-12 | Create conftest.py with mock_openclaw_home fixture | `backend/tests/conftest.py` | ☐ |
| P-13 | Create globals.css with Tailwind + CSS variables | `frontend/src/styles/globals.css` | ☐ |
| P-14 | Create index.html with JetBrains Mono + Inter fonts | `frontend/index.html` | ☐ |
| P-15 | Create README.md | `README.md` | ☐ |
| P-16 | Create all `__init__.py` files | All Python packages | ☐ |

**Acceptance:** All files exist, directory structure matches PLAN-v2.md §4. `pyproject.toml` and `package.json` have correct dep lists.

---

## Phase 1A: Backend (Sonnet) — FASTAPI APP

| # | Task | Files | Depends On | Done |
|---|------|-------|------------|------|
| B-01 | FastAPI app with lifespan + startup validation | `app/main.py` | P-* | ☐ |
| B-02 | Host header validation middleware | `app/middleware/host_validation.py` | P-* | ☐ |
| B-03 | Global error handler → error envelope | `app/middleware/error_handler.py` | P-10 (models) | ☐ |
| B-04 | Common dependencies | `app/dependencies.py` | P-09 (config) | ☐ |
| B-05 | File service — sandboxed R/W, ETags, symlink check | `app/services/file_service.py` | P-10 | ☐ |
| B-06 | Agent service — discovery, resolve_agent_workspace() | `app/services/agent_service.py` | B-05 | ☐ |
| B-07 | Config service — R/W, backup rotation (max 10), redaction | `app/services/config_service.py` | B-05 | ☐ |
| B-08 | Gateway service — exec only, enum actions, 10s timeout | `app/services/gateway_service.py` | P-10 | ☐ |
| B-09 | Health router | `app/routers/health.py` | B-01 | ☐ |
| B-10 | Agents router — list, detail, file read/write w/ ETags | `app/routers/agents.py` | B-05, B-06 | ☐ |
| B-11 | Config router — read, write, validate | `app/routers/config.py` | B-07 | ☐ |
| B-12 | Gateway router — status + start/stop/restart | `app/routers/gateway.py` | B-08 | ☐ |
| B-13 | WebSocket handler — protocol, ping/pong, file watcher | `app/websocket/live.py` | B-05 | ☐ |
| B-14 | Verify: `uvicorn app.main:app` starts, all endpoints respond | — | B-01 thru B-13 | ☐ |

**Acceptance:** `make backend` starts without errors. `curl localhost:8400/api/health` returns 200. All CRUD endpoints respond with correct shapes.

---

## Phase 1B: Frontend (Sonnet) — REACT APP

| # | Task | Files | Depends On | Done |
|---|------|-------|------------|------|
| F-01 | App shell — main.tsx, App.tsx, router.tsx | `src/main.tsx`, `src/App.tsx`, `src/router.tsx` | P-* | ☐ |
| F-02 | Fetch wrapper — error parsing, ETag handling | `src/api/client.ts` | P-11 (types) | ☐ |
| F-03 | API modules — agents, config, gateway | `src/api/agents.ts`, `config.ts`, `gateway.ts` | F-02 | ☐ |
| F-04 | Zustand stores (5) — agent, editor, gateway, config, toast | `src/stores/*.ts` | P-11 | ☐ |
| F-05 | Common components — Badge, Button, Card, Modal, Toast, ErrorBoundary, Spinner | `src/components/common/*.tsx` | F-01 | ☐ |
| F-06 | Layout — Sidebar, Header, Layout wrapper | `src/components/layout/*.tsx` | F-05 | ☐ |
| F-07 | Dashboard — AgentCard, AgentGrid, DashboardPage | `src/pages/DashboardPage.tsx`, `src/components/agents/*` | F-03, F-04, F-06 | ☐ |
| F-08 | Agent Detail — AgentDetail, AgentPage | `src/pages/AgentPage.tsx`, `src/components/agents/AgentDetail.tsx` | F-07 | ☐ |
| F-09 | Editor — FileEditor (lazy Monaco), EditorPage | `src/pages/EditorPage.tsx`, `src/components/editor/FileEditor.tsx` | F-02, F-04 | ☐ |
| F-10 | Config — ConfigEditor (Monaco JSON), ConfigPage | `src/pages/ConfigPage.tsx`, `src/components/config/ConfigEditor.tsx` | F-02, F-04 | ☐ |
| F-11 | Gateway — GatewayPanel, GatewayPage | `src/pages/GatewayPage.tsx`, `src/components/gateway/GatewayPanel.tsx` | F-03, F-04 | ☐ |
| F-12 | Hooks — useAgents, useGateway, useWebSocket (reconnection) | `src/hooks/*.ts` | F-03, F-04 | ☐ |
| F-13 | Dark theme globals + Tailwind setup | `src/styles/globals.css` | P-06, P-13 | ☐ |
| F-14 | Verify: `npm run dev` starts, all pages render | — | F-01 thru F-13 | ☐ |

**Acceptance:** `make frontend` starts. All 5 pages render. Navigation works. Agent cards show. Editor opens Monaco.

---

## Phase 2: Overseer (Opus) — INTEGRATION VERIFICATION

| # | Task | Done |
|---|------|------|
| O-01 | Install deps: `cd backend && pip install -e .` + `cd frontend && npm install` | ☐ |
| O-02 | Run `make types` — generate TS types from backend OpenAPI spec | ☐ |
| O-03 | Diff generated types vs manual stubs — fix any mismatches | ☐ |
| O-04 | Verify Backend API responses match Frontend fetch expectations | ☐ |
| O-05 | Verify ETag flow: GET returns ETag, PUT requires If-Match, 409 on conflict | ☐ |
| O-06 | Verify WebSocket protocol: message envelope matches both sides | ☐ |
| O-07 | Verify CORS config: frontend can reach backend through Vite proxy | ☐ |
| O-08 | Fix any integration issues found, write INTEGRATION-REPORT.md | ☐ |

**Acceptance:** `make dev` starts both servers. Frontend pages load data from backend. No console errors.

---

## Phase 3: Tester (MiniMax-M2.5) — TESTS + VALIDATION

| # | Task | Files | Done |
|---|------|-------|------|
| T-01 | Agent tests — list, detail, main agent path, file list | `backend/tests/test_agents.py` | ☐ |
| T-02 | File tests — read/write, ETags, 409 conflict, path traversal, symlinks | `backend/tests/test_files.py` | ☐ |
| T-03 | Config tests — read, write, validate, backup rotation, redaction | `backend/tests/test_config.py` | ☐ |
| T-04 | Gateway tests — status, actions, enum rejection, timeout | `backend/tests/test_gateway.py` | ☐ |
| T-05 | Security tests — Host header, symlink escape, path traversal patterns | `backend/tests/test_security.py` | ☐ |
| T-06 | Frontend component tests — AgentCard, GatewayPanel renders | `frontend/src/**/*.test.ts` | ☐ |
| T-07 | Run full suite: `make test` — report coverage, all must pass | — | ☐ |

**Acceptance:** `make test` passes. Backend coverage ≥80%. Zero test failures. Write TEST-REPORT.md.

---

## Phase 4: Reviewer (Opus) — FINAL CODE REVIEW

| # | Task | Done |
|---|------|------|
| R-01 | Review all backend files — correctness, error handling, style | ☐ |
| R-02 | Review all frontend files — performance, accessibility, error boundaries | ☐ |
| R-03 | Verify ALL 12 review recommendations (R1-R12) are implemented | ☐ |
| R-04 | Security audit — path traversal vectors, command injection, DNS rebinding | ☐ |
| R-05 | Check for hardcoded paths, secrets, or Miller-specific assumptions | ☐ |
| R-06 | Write FINAL-REVIEW.md with pass/fail per item + any remaining issues | ☐ |

**Acceptance:** FINAL-REVIEW.md says "PASS" on all critical items. Any "FAIL" items fixed before ship.

---

## Phase 5: COS Integration — SHIP IT

| # | Task | Done |
|---|------|------|
| I-01 | Run `make setup` from clean state | ☐ |
| I-02 | Run `make dev` — verify both servers start | ☐ |
| I-03 | Manual test: dashboard loads, shows agents | ☐ |
| I-04 | Manual test: click agent → detail → click file → editor opens | ☐ |
| I-05 | Manual test: edit file → save → verify file on disk changed | ☐ |
| I-06 | Manual test: config page → edit JSON → save → backup created | ☐ |
| I-07 | Manual test: gateway page → status shows → restart works | ☐ |
| I-08 | Run `make build` — production build succeeds | ☐ |
| I-09 | Run `make serve` — production mode works | ☐ |
| I-10 | `git init && git add -A && git commit -m "v1.0.0 — OpenClaw Dashboard MVP"` | ☐ |
| I-11 | Update ACTIVE.md with completion | ☐ |

---

## Concurrency Plan

```
Time ──────────────────────────────────────────────────────────►

Planner ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
COS          verify░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
Backend      ░░░░░░░████████████████████░░░░░░░░░░░░░░░░░░░░░░
Frontend     ░░░░░░░████████████████████░░░░░░░░░░░░░░░░░░░░░░
Overseer     ░░░░░░░░░░░░░░░░░░░░░░░░░░████████░░░░░░░░░░░░░░
Tester       ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████████░░░░░░
Reviewer     ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████░░
COS          ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██

Max concurrent sub-agents: 2 (Backend + Frontend)
```

## Risk Mitigations

| Risk | Mitigation |
|------|-----------|
| MiniMax Planner creates wrong stubs | COS verifies before Phase 1 |
| Backend/Frontend type drift | Overseer runs `make types` in Phase 2 |
| Agent gets stuck in loop | COS 10-min check-in protocol |
| Monaco lazy load breaks | ErrorBoundary catches, shows reload message |
| File write race condition | ETags implemented from day 1 |
| Sub-agent exceeds timeout | 30-min timeout per agent, COS kills + restarts |
