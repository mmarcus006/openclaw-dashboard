# Design Review V2 — Interactive Audit (Post-Wave 6)
_Date: 2026-02-26 | All pages hands-on tested_

## 1. Dashboard (`/`)
**Score: 6.5/10**
**Status:** ⚠️ Issues

### What Works
- Four stat cards load with real data (Total Agents: 40, Active: 0, Gateway: On, Idle: 40)
- Gateway Status card present and functional — shows "Running", clicks through to `/gateway`
- Recent Activity section shows "No recent agent activity" (correct — no sessions yet)
- Two quick nav cards: "View All Agents" → `/agents`, "Open Config" → `/config` — both navigate correctly
- Clean 4-column grid layout, logical information hierarchy, good sidebar/header/content split
- Typography: Inter font, clear size/weight hierarchy, `tabular-nums` on stat values
- Good ARIA attributes: `role="button"`, `tabIndex={0}`, keyboard handlers, `aria-label` on status dots and nav

### Issues Found
- **[P0 Bug] Tailwind v4 color utility classes broken** — Project uses Tailwind CSS v4 (`@import "tailwindcss"`) but defines custom colors in Tailwind v3-style `tailwind.config.ts`. Classes like `bg-success`, `text-success`, `text-text-secondary`, `bg-bg-card` do NOT generate correct styles. CSS custom properties (`--success: #22c55e`, etc.) ARE defined in `:root`, but Tailwind utility classes resolve to `rgba(0,0,0,0)` (transparent). Header status dots are **invisible**. Status-colored text broken throughout.
- **[P2 Medium] Hover effect barely perceptible** — Card hover transitions from `#232936` → `#2d3548` (~10% brightness). Nearly invisible. Needs more pronounced hover.
- **[P2 Medium] Large empty space** — Significant empty space between activity text and quick nav cards, and below cards to viewport bottom.
- **[P3 Low] Loading state polish** — Gateway stat shows "..." and status card shows "Loading..." during fetch. Skeleton animations would be more polished.

### Design Token Reference (CSS Custom Properties)
| Token | Value | Usage |
|-------|-------|-------|
| `--bg-primary` | `#0f1219` | Page background |
| `--bg-secondary` | `#1a1f2e` | Header background |
| `--bg-card` | `#232936` | Card backgrounds |
| `--bg-hover` | `#2d3548` | Hover state |
| `--border` | `#333d52` | Card borders |
| `--text-primary` | `#e8eaf0` | Primary text |
| `--text-secondary` | `#a1abbe` | Muted text |
| `--accent` | `#6366f1` | Indigo accent |
| `--success` | `#22c55e` | Green |
| `--warning` | `#f59e0b` | Amber |
| `--danger` | `#ef4444` | Red |

### Recommendations
- Fix Tailwind v4 theme registration: add `@theme` block in `globals.css` to register custom colors with Tailwind v4's engine
- Increase hover contrast (e.g., `#3a4560` or add `box-shadow`)
- Add dashboard content for empty states (system health, model usage sparklines)
- Add skeleton loading animations for stat cards and gateway status

---

## 2. Agents (`/agents`)
**Score: 6.5/10**
**Status:** ⚠️ Issues

### What Works
- 4-column responsive grid (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`) with 39 agent cards
- **Search is excellent**: typing "main" instantly filters to 1 result, shows result count badge, has clear (X) button, searches name/id/model fields
- Status filter works: All Status / Active / Idle / Stopped options
- Sort dropdown works: Name / Status / Last Activity options
- Agent cards show: name (bold), ID (monospace), model badge ("MiniMax-M2.5"), status dot, session info
- Card clicks navigate correctly to `/agents/{id}` with clean URL routing
- Zustand store pattern with `filteredAgents` selector is clean and performant

### Issues Found
- **[P0 Bug] Status-colored left border invisible** — AgentCard applies `border-l-4 border-l-warning` for idle agents (should be 4px amber left border), but the computed border color is `#e8eaf0` (white) instead of `#f59e0b` (amber). Root cause: Tailwind config uses `border` as both a color token name AND it conflicts with the `border` utility class shorthand. The `border-border` class overrides `border-l-warning`. This removes a critical visual status differentiator from all cards.
- **[P1 High] Misleading empty state on filter** — When status filter produces zero results (e.g., "Active" when no agents are active), message says "No agents configured / Add agents to openclaw.json to see them here." Should say "No agents match the selected status."
- **[P1 High] No focus ring on cards** — Card component has `tabIndex={0}` and keyboard handlers but no `focus:ring-*` or `focus:outline-*` styles. Keyboard users cannot see which card is focused.
- **[P2 Medium] Undefined `text-tertiary` color** — Search icon uses `text-text-tertiary` which is not defined in the Tailwind config. May resolve to no color at all.
- **[P2 Medium] Hover effect too subtle** — Same issue as dashboard: dark-on-dark color change barely perceptible.
- **[P3 Low] Model badge monotony** — All 39 cards show "MiniMax-M2.5" (reflects real config data, not a frontend bug). Creates visual monotony.

### Recommendations
- **P0 Fix:** Rename `border` color token in `tailwind.config.ts` to `border-default` or `border-line` to avoid collision with the `border` utility class
- **P1 Fix:** Add filter-aware empty state: check if search/filter is active, show "No agents match" instead of "No agents configured"
- **P1 Fix:** Add `focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-bg-primary` to Card component
- **P2 Fix:** Define `--text-tertiary` in CSS custom properties or replace with `text-text-secondary`

---

## 3. Agent Detail (`/agents/main`)
**Score: 7.5/10**
**Status:** ⚠️ Issues

### What Works
- Agent metadata display is excellent: name ("Main"), status badge ("idle" in amber pill), agent ID (monospace), workspace path with FolderOpen icon, model badge ("MiniMax-M2.5")
- Visual hierarchy is clear: name > status > id > workspace/model
- **Files tab (78 files)**: table with NAME/SIZE/MODIFIED columns, file-type icons (FileText for `.md`, Image for `.png`, generic File for dotfiles), monospace filenames, click-to-open-in-editor integration navigates to `/editor?agent=main&path=FILENAME`
- File rows are keyboard accessible: `tabIndex={0}`, `onKeyDown`, `role="row"`, `aria-label="Open {filename}"`, `focus-visible:outline-2`
- **Sessions tab**: well-architected two-panel master-detail layout (`grid-cols-[minmax(300px,380px)_1fr]`), left panel session list, right panel message viewer
- Session viewer features: role-based message styling (user right-aligned accent tint, assistant left-aligned card bg), collapsible thinking blocks, tool call cards with Wrench icon, copy button on hover, long message truncation (>500 chars), load-more pagination
- Tab design: active tab has indigo underline + text, inactive has transparent border + secondary text, each tab has icon
- `max-w-5xl` constraint prevents overly wide layouts
- Consistent dark theme with proper typography (Inter for UI, JetBrains Mono for code)

### Issues Found
- **[P1 High] "Back to fleet" navigates to `/` not `/agents`** — Code in `AgentDetail.tsx` line 119: `navigate('/')`. Should explicitly navigate to `/agents` (the fleet list page).
- **[P1 High] Sessions tab shows raw error** — "ApiError: Not Found" displayed as plain red text when sessions endpoint returns 404. No friendly message, icon, or retry button. Right panel shows stale "Select a session" state even when list failed to load.
- **[P1 High] Missing ARIA tab pattern** — Tabs are plain `<button>` elements without `role="tablist"` / `role="tab"` / `role="tabpanel"`, `aria-selected`, or `aria-controls`. No keyboard arrow-key navigation between tabs.
- **[P2 Medium] Tab state not in URL** — Refreshing page always returns to Files tab. Browser back button doesn't track tab changes.
- **[P2 Medium] No file sorting/filtering** — 78 files rendered without search, column sort, or pagination. Column headers aren't clickable.
- **[P2 Medium] `.DS_Store` in file list** — OS artifact should be filtered out.
- **[P3 Low] No session count in tab label** — Files tab shows "Files (78)" but Sessions tab just says "Sessions" with no count.
- **[P3 Low] No virtualization for large file lists** — All 78 rows rendered in DOM; could cause jank with very large workspaces.

### Recommendations
- Fix "Back to fleet" navigation target from `/` to `/agents`
- Add friendly error state for sessions: icon + "Could not load sessions" + retry button + `role="alert"`
- Implement ARIA tab pattern: `role="tablist"`, `role="tab"` with `aria-selected`, `role="tabpanel"` with `aria-labelledby`, arrow key navigation
- Add `?tab=sessions` URL param to persist tab state
- Filter `.DS_Store` and other OS artifacts from file list
- Consider adding column sorting to file table for large workspaces

---

## 4. Editor (`/editor`)
**Score: 6.5/10**
**Status:** ⚠️ Issues (critical backend bug blocks core functionality)

### What Works
- **Monaco theme integration is excellent**: custom theme sets `editor.background` to `#0f1219`, exactly matching `--bg-primary`. No color seam at editor edges. Gutter bg also matches. Line highlight uses `#1a1f2e` (`--bg-secondary`). Outstanding attention to detail.
- **Triple-signal dirty indicator**: (1) toolbar amber dot with `aria-label="Unsaved changes"`, (2) breadcrumb orange bullet after filename, (3) Save button enabled/disabled state. Plus `beforeunload` guard and Cmd+S/Ctrl+S shortcut.
- **Breadcrumb**: "Agents > analyst > IDENTITY.md" with clickable segments. Dirty guard on navigation (ConfirmDialog). Current file segment is bold white, navigation links are secondary with hover accent.
- **File browser sidebar** (code-verified): 240px width, files grouped by directory with collapsible folders, file-type icons via `getFileIcon()`, active file highlighted in accent tint, binary files disabled with tooltip, 200-file truncation warning, dirty-file-switch guard dialog.
- **Sidebar collapse**: collapses to 40px strip, editor expands to fill space, `automaticLayout: true` handles Monaco resize correctly.
- **Empty states**: appropriate messaging for no agent selected, no file selected, loading spinner.
- **Font**: JetBrains Mono at 13px with ligatures. Professional monospace choice.
- **Monaco options**: minimap disabled, word wrap on, tab size 2, whitespace rendered on selection only.

### Issues Found
- **[P0 Bug] `/files/browse` endpoint returns 404** — The file listing API returns 404 for all agents. File browser sidebar always shows "No files found." The route exists in backend code (`agents.py` line 96) but the running server doesn't serve it — likely needs server restart after route was added. This blocks the core file browsing workflow.
- **[P1 High] Native `<select>` for agent selector** — Uses browser-default dropdown chrome, clashing with the polished dark UI. Should be a custom styled dropdown (Headless UI Listbox or Radix Select).
- **[P2 Medium] Breadcrumb `<nav>` lacks `aria-label`** — Two unlabeled `<nav>` elements on the page (sidebar nav + breadcrumb nav). Screen readers can't distinguish them. Add `aria-label="Breadcrumb"`.
- **[P2 Medium] Collapse button missing `aria-label`** — Uses `title` attribute but not `aria-label`. Screen readers won't announce button purpose reliably.
- **[P2 Medium] Redundant toolbar + breadcrumb info** — "analyst / IDENTITY.md" in toolbar AND "Agents > analyst > IDENTITY.md" in breadcrumb show nearly identical info.
- **[P3 Low] No sidebar collapse animation** — Instant toggle; `transition-all duration-200` would feel smoother.
- **[P3 Low] Line number contrast** — `#4a5568` on `#0f1219` ≈ 3.3:1 ratio, fails WCAG AA for normal text (needs 4.5:1).
- **[P3 Low] No file tabs** — Single-file editing only. Users can't compare files or quick-switch.

### Recommendations
- Fix backend: restart server or verify `/files/browse` route is registered. This alone would raise the score to 7.5–8/10.
- Replace native `<select>` with custom dark-themed dropdown component
- Add `aria-label="Breadcrumb"` to breadcrumb `<nav>`, `aria-label="Collapse sidebar"` to collapse button
- Consolidate toolbar path display and breadcrumb (keep breadcrumb, remove toolbar path)
- Add `transition-all duration-200` to sidebar collapse/expand
- Lighten line number color to `#6b7280` for better contrast

---

## 5. Config (`/config`)
**Score: 6.5/10**
**Status:** ⚠️ Issues

### What Works
- Loads `/Users/miller/.openclaw/openclaw.json` with full JSON content in Monaco editor
- File path displayed in toolbar with `FileJson` icon (monospace, truncated if narrow)
- **Validation indicator**: shows "Valid JSON" (checkmark icon) or "Invalid JSON syntax" (X icon) — updates correctly after 500ms debounce
- **Reload button**: always enabled, shows ConfirmDialog when dirty ("You have unsaved changes. Reloading will discard them.") — excellent UX, prevents data loss
- **Cmd+S / Ctrl+S** keyboard shortcut for save
- **beforeunload guard** prevents navigation with unsaved changes
- **External change detection**: modal handles "Config changed externally" for multi-tool editing scenarios
- Sensitive values redacted as `"__REDACTED__"` — good security practice
- Responsive toolbar: wraps gracefully at 768px via `flex-wrap gap-2`

### Issues Found
- **[P0 Bug] `text-success`/`text-danger` classes generate NO CSS** — The `text` color group in `tailwind.config.ts` conflicts with Tailwind's `text-*` utility prefix. Validation indicator text is white/light gray in BOTH valid and invalid states. Users lose the critical green/red color signal. This affects the entire app (validation indicators, error messages, status badges, toasts).
- **[P1 High] Save button enabled when JSON is invalid** — `disabled={!dirty}` only checks dirty state, not `validation.valid`. Users can attempt to save broken JSON, which fails with vague "Save failed: Unknown error" toast.
- **[P1 High] "Save failed" error message is vague** — Race condition between async save and toast display causes stale `error` state. Should show the actual validation or server error message.
- **[P2 Medium] Monaco `vs-dark` theme mismatch** — Editor bg is `#1e1e1e` (standard `vs-dark`), app bg is `#0f1219`. Creates visible color seam. Note: the Editor page's custom Monaco theme solves this — the Config page should use the same custom theme.
- **[P3 Low] 48px dead space below editor** — `p-6` padding on main content creates gap between editor bottom and viewport bottom. Should be reduced for full-screen editor feel.

### Recommendations
- **P0 Fix**: Same Tailwind v4 `@theme` fix as Dashboard — register color utilities properly
- **P1 Fix**: Change Save button to `disabled={!dirty || !validation?.valid}`, add tooltip "Fix JSON errors before saving"
- **P1 Fix**: Pass actual error message to toast: `toast.error(error.message || 'Save failed')`
- **P2 Fix**: Apply the same custom Monaco theme from `monacoTheme.ts` to the Config editor (it already exists — just import and use it)
- **P3 Fix**: Remove bottom padding on Config page or use `p-6 pb-0` to eliminate dead space

---

## 6. Gateway (`/gateway`)
**Score: 7/10**
**Status:** Mostly functional

### What Works
- **No infinite spinner**: 5-second timeout with "Gateway Status Unavailable" fallback + "Try Again" button. Well-designed failsafe.
- **Clear status display**: green Radio icon + "Running" badge when active; grey icon + "Gateway Stopped" card when inactive; "Not Installed" variant with warning triangle if CLI missing. All three states are visually distinct.
- **Control buttons**: Start / Stop / Restart with correct enable/disable logic. Start disabled with `title="Gateway is already running"` when running; Stop disabled when stopped. Loading spinners during actions. Toast notifications on success/failure.
- **PID display**: "PID: 67665" in monospace with Hash icon.
- **Channels table** (code-verified): proper HTML `<table>` with Channel / Status / Provider columns. Status uses green "Connected" badge. No raw JSON.
- **Cron Jobs section**: separate card with proper empty state ("No cron jobs configured in openclaw.json"). If jobs existed, shows Name / Schedule (human-readable via `cronstrue`) / Next Run / Enabled columns.
- **ErrorBoundary** wrappers around both GatewayPanel and CronJobList.
- **Rate limiting**: 5 actions/minute on gateway controls.

### Issues Found
- **[P1 High] `/api/gateway/history` and `/api/cron` return 404** — Backend endpoints not registered in running server. "Last Command Output" always shows "No recent commands"; cron section always shows empty state. Features exist in code but are non-functional without server restart.
- **[P2 Medium] Channels section silently hidden when empty** — `channels: {}` causes the entire Channels section to not render. No empty state like "No channels configured." Users can't discover the feature exists.
- **[P2 Medium] Native `title` tooltips on disabled buttons** — Uses browser `title` attribute with ~500ms delay, unstyled, nearly invisible on dark backgrounds. Should use custom tooltip component consistent with design system.
- **[P2 Medium] Stopped-state button layout inconsistency** — When stopped, Stop and Restart buttons render outside the card wrapper, looking orphaned. Running state has all buttons inside the status card.
- **[P2 Medium] Uptime always null** — API returns `uptime: null`, leaving the metadata grid half-empty (PID only in a 2-column grid).
- **[P3 Low] Cron Jobs empty state oversized** — ~230px tall with centered icon + text + generous padding. Disproportionate to compact cards above.
- **[P3 Low] No "last refreshed" indicator** — Page polls every 10s but gives no visual indication of data freshness.

### Recommendations
- Restart backend to register `/api/gateway/history` and `/api/cron` routes
- Add empty state for channels: "No channels configured" with link to docs
- Replace native `title` tooltips with custom styled tooltip component
- Unify button layout between running/stopped states (always inside card)
- Add "Last updated: {time}" text near status or in footer
- Parse uptime from gateway status output in backend

---

## 7. Cross-Cutting Concerns
**Score: 6/10**

### 404 Page
- Navigating to `/nonexistent` shows a proper 404 page with "Page Not Found" heading, description text, and "Go to Dashboard" link. Clean, on-brand. No broken layout or console errors.

### Sidebar Navigation
- Five nav items: Dashboard, Agents, Editor, Config, Gateway — each with Lucide icon
- **Active state**: accent text color + `bg-accent/10` background highlight. Correctly tracks current route.
- **Hover**: `hover:bg-bg-hover` on inactive items
- Sidebar is fixed-width, doesn't collapse on desktop (no hamburger menu)
- **Issue**: No `aria-current="page"` attribute on active nav item. Screen readers can't identify current page from nav alone.

### Page Titles
- Each page sets `document.title` via a custom hook: "Dashboard — OpenClaw", "Agents — OpenClaw", "Edit: {filename} — OpenClaw", "Config — OpenClaw", "Gateway — OpenClaw"
- Titles update correctly on navigation
- **Issue**: No dirty indicator in title (e.g., "Config * — OpenClaw") when editor/config has unsaved changes

### Focus Management
- **Mixed results**: File table rows in Agent Detail have excellent `focus-visible:outline-2 focus-visible:outline-accent` rings. Agent cards on `/agents` page lack focus rings entirely despite having `tabIndex={0}`. Sidebar nav items have browser-default focus outlines (blue ring), not themed.
- **Tab order**: Generally logical (sidebar → header → content), but focus doesn't move to main content on route change. Users must Tab through sidebar on every page navigation.

### Keyboard Navigation
- **Cards**: Enter/Space handlers on agent cards and dashboard stat cards — good
- **Tabs**: Agent detail tabs respond to click but lack arrow-key navigation (not ARIA tab pattern)
- **Editor**: Monaco handles all keyboard interactions internally — excellent
- **Escape**: No global Escape key handling (e.g., to close modals, clear search)

### Responsive Design
- **Not tested for mobile** — the dashboard appears designed for desktop/laptop use (admin panel pattern). Sidebar does not collapse to hamburger. Grid columns reduce via responsive breakpoints (`sm:`, `lg:`, `xl:`).
- Agent card grid responsive breakpoints are correct: 1 col mobile → 2 col sm → 3 col lg → 4 col xl

### Performance
- Monaco lazy-loaded via `React.lazy()` — non-editor pages load fast
- Agent list renders all 39 cards without virtualization (acceptable at this count)
- File table renders all 78 rows without virtualization (acceptable but watch for growth)
- Zustand stores with selective subscriptions prevent unnecessary re-renders
- No observable jank or slow transitions during testing

### Accessibility Summary
| Feature | Status |
|---------|--------|
| Focus rings | Partial — file table yes, cards no, sidebar browser-default |
| ARIA labels | Partial — some buttons/links have them, breadcrumb nav and tabs missing |
| Keyboard navigation | Partial — cards yes, tabs no arrow keys, modals no trap |
| Screen reader landmarks | Missing — no `<main>`, no `role="navigation"` on sidebar, no `aria-current` |
| Color contrast | Issues — line numbers fail WCAG AA, status colors invisible due to Tailwind bug |
| Focus management on route change | Missing — focus stays on clicked nav link |

---

## Executive Summary

**Overall Score: 6.5 / 10**

The OpenClaw Dashboard has strong architectural foundations — Zustand state management, Monaco editor integration, proper component decomposition, and a cohesive dark theme with well-chosen design tokens. The codebase demonstrates solid engineering practices (ETag concurrency control, debounced validation, error boundaries, lazy loading).

However, **two systemic issues severely undercut the experience**:

1. **Tailwind v4 migration incomplete** — Custom colors defined in v3-style `tailwind.config.ts` are not registered with Tailwind v4's `@theme` system. This makes all status-colored elements (dots, borders, badges, validation text) invisible or wrong-colored across every page. This is the single highest-impact fix.

2. **Backend routes not registered in running server** — `/files/browse`, `/sessions`, `/gateway/history`, and `/cron` endpoints exist in code but return 404 from the live server. This breaks the Editor file browser (unusable), Sessions tab (error), Gateway history (empty), and Cron jobs (empty). A server restart would likely fix all four.

### What's IMPROVED Since V1

The original V1 review identified these issues. Here's what changed:

| V1 Finding | Status |
|-----------|--------|
| Duplicate Dashboard/Agents pages | **FIXED** — Dashboard and Agents are distinct pages with different content |
| No search on Agents page | **FIXED** — Excellent real-time search with result count badge and clear button |
| Infinite spinner on Gateway page | **FIXED** — 5-second timeout with fallback card and "Try Again" button |
| No file browser in Editor | **PARTIALLY FIXED** — File browser UI exists with icons, collapse, and agent selector, but backend endpoint returns 404 |
| Broken status indicators | **NOT FIXED** — Still broken due to Tailwind v4 color registration issue |
| No filter/sort on Agents | **FIXED** — Status filter (All/Active/Idle/Stopped) and Sort (Name/Status/Activity) dropdowns work correctly |
| Raw JSON in Gateway channels | **FIXED** — Proper table with Channel/Status/Provider columns (when data exists) |

### Page Scores

| Page | Score | Key Blocker |
|------|-------|-------------|
| Dashboard `/` | 6.5/10 | Invisible status dots, empty space |
| Agents `/agents` | 6.5/10 | Invisible status borders, misleading empty state |
| Agent Detail `/agents/:id` | 7.5/10 | Sessions 404, wrong "Back" target |
| Editor `/editor` | 4/10 | File browser 404 — page unusable via UI |
| Config `/config` | 6.5/10 | Status colors invisible, save allows invalid JSON |
| Gateway `/gateway` | 7/10 | History/cron 404, channels hidden when empty |
| Cross-cutting | 6/10 | Inconsistent focus rings, missing ARIA patterns |

---

## Prioritized Action Items

| # | Priority | Issue | Page(s) | Type | Recommendation | Est. LOC |
|---|----------|-------|---------|------|----------------|----------|
| 1 | **P0** | Tailwind v4 colors not registered | ALL | Bug | Add `@theme` block in `globals.css` to register `--bg-*`, `--text-*`, `--success`, `--warning`, `--danger`, `--accent`, `--border` with Tailwind v4. Or rename conflicting tokens (e.g., `border` → `border-line`, `text` → `txt`) | ~30 |
| 2 | **P0** | Backend routes not serving (files/browse, sessions, history, cron) | Editor, Agent Detail, Gateway | Bug | Restart backend server. If still 404, verify router includes in `main.py` are executing. | 0 (ops) |
| 3 | **P1** | "Back to fleet" navigates to `/` instead of `/agents` | Agent Detail | Bug | Change `navigate('/')` to `navigate('/agents')` in `AgentDetail.tsx` | 1 |
| 4 | **P1** | Sessions tab shows raw "ApiError: Not Found" | Agent Detail | UX | Replace error string with friendly component: icon + "Could not load sessions" + retry button | ~20 |
| 5 | **P1** | Save button enabled when JSON invalid | Config | Bug | Change to `disabled={!dirty \|\| !validation?.valid}`, add tooltip | 3 |
| 6 | **P1** | Misleading empty state when filter active | Agents | UX | Check if search/filter is active; show "No agents match" vs "No agents configured" | ~10 |
| 7 | **P1** | No focus ring on agent cards | Agents | A11y | Add `focus-visible:ring-2 focus-visible:ring-accent` to Card component | 2 |
| 8 | **P1** | Native `<select>` for agent selector in Editor | Editor | UX | Replace with custom styled dropdown matching dark theme | ~40 |
| 9 | **P2** | Monaco theme mismatch on Config page | Config | Visual | Import and apply the custom `openclaw-dark` theme from `monacoTheme.ts` | 5 |
| 10 | **P2** | Missing ARIA tab pattern on Agent Detail | Agent Detail | A11y | Add `role="tablist"`, `role="tab"`, `aria-selected`, arrow key nav | ~25 |
| 11 | **P2** | Hover effects too subtle across app | All cards | Visual | Increase hover bg to `#3a4560` or add `box-shadow: 0 2px 8px rgba(0,0,0,0.3)` | ~5 |
| 12 | **P2** | Tab state not in URL (Agent Detail) | Agent Detail | UX | Add `?tab=sessions` URL param, read on mount | ~15 |
| 13 | **P2** | Channels section hidden when empty | Gateway | UX | Add "No channels configured" empty state | ~10 |
| 14 | **P2** | Native `title` tooltips on Gateway buttons | Gateway | UX | Replace with custom tooltip component | ~20 |
| 15 | **P2** | `.DS_Store` shown in file list | Agent Detail | UX | Filter OS artifacts from file list display | 3 |
| 16 | **P2** | Undefined `text-tertiary` color | Agents | Bug | Define `--text-tertiary` in CSS or replace with `text-text-secondary` | 2 |
| 17 | **P2** | No `aria-current="page"` on active nav | Sidebar | A11y | Add `aria-current="page"` to active NavLink | 2 |
| 18 | **P3** | Dirty indicator too small (8x8px dot) | Editor, Config | UX | Increase to 10px dot or add "Modified" text label | 3 |
| 19 | **P3** | No dirty indicator in browser tab title | Editor, Config | UX | Prepend asterisk to title when dirty | 5 |
| 20 | **P3** | Large empty space on Dashboard | Dashboard | Layout | Add system health section or compact layout | ~30 |
| 21 | **P3** | Loading states use text instead of skeletons | Dashboard | Polish | Add skeleton pulse animations for stat cards | ~20 |
| 22 | **P3** | Line number contrast fails WCAG AA | Editor | A11y | Change from `#4a5568` to `#6b7280` | 1 |
| 23 | **P3** | No sidebar collapse animation | Editor | Polish | Add `transition-all duration-200` | 2 |
| 24 | **P3** | Redundant toolbar path + breadcrumb | Editor | UX | Remove toolbar path display, keep breadcrumb only | ~5 |

---

_End of Design Review V2. Total issues found: 24. Critical blockers: 2 (Tailwind v4 theme + backend routes)._
