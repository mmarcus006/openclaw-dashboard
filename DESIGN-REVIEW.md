# OpenClaw Dashboard — Design Review
**Reviewer:** Design Reviewer Sub-Agent  
**Date:** 2026-02-25  
**Build:** v1.0.0 (Vite + React + TypeScript + Tailwind CSS v4)  
**Viewport tested:** 1512×982 (MacBook Pro default)  
**Pages reviewed:** Dashboard `/`, Agents `/agents`, Agent Detail `/agents/:id`, Config `/config`, Gateway `/gateway`, Editor `/editor`

---

## 1. Executive Summary

Five recommendations that will deliver the highest user experience ROI:

### E1 — Resolve the Dual Dashboard Problem *(Critical)*
`/` and `/agents` both render `DashboardPage`. The sidebar has two links pointing to identical content. Either eliminate the `/agents` link (merge into Dashboard) or differentiate the pages so `/agents` becomes a searchable, sortable, full-screen agent listing while `/` is a true fleet overview with charts and live activity. As-is, users clicking "Agents" in the sidebar feel cheated — nothing changes.

### E2 — Replace the Hollow Status Dot with a Rich Status Indicator *(Critical)*
Every one of the 40 agent cards uses a 10px dot (either `bg-warning` for idle or `bg-success` for active). On a dark card background, the dot is the only status signal. At 40+ agents in a grid, users cannot scan for anomalies. Replace with a compound indicator: colored left-border stripe + text badge + animated pulse for "active" state. This is a single CSS + JSX change with outsized scanability impact.

### E3 — Add Search/Filter Bar to the Agent Grid *(High)*
40 agents with no search, no filter, no sort. The grid requires scrolling to find a specific agent. A simple `<input type="search">` with client-side filter on `agent.name` + `agent.id` + `agent.model` — all already in memory — would solve the most frequent user action in a fleet management UI. 3-line state change, no backend needed.

### E4 — Complete the Gateway Page *(High)*
The Gateway page shows a spinner indefinitely when the gateway daemon isn't running. The `GatewayPanel` has the correct conditional render for the stopped state (with Start/Stop/Restart buttons), but the spinner placeholder dominates until the API call resolves. The page needs an explicit "Gateway Stopped" state design with a prominent Start CTA — not a spinner that looks like a broken page.

### E5 — Fix the Sidebar Active State Contrast *(Medium)*
The active nav link uses `bg-accent/15` (15% opacity indigo on `#1a1f2e`). At that opacity, the computed background is approximately `#1e2036` — only 2% lighter than the sidebar base. A user cannot glance at the sidebar and know where they are. Change to `bg-accent/25` minimum or add a `border-l-2 border-accent` left indicator (VS Code / Linear pattern) alongside the current background treatment.

---

## 2. Color System Review

### 2.1 Current Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg-primary` | `#0f1219` | Page background, pre/code blocks |
| `--bg-secondary` | `#1a1f2e` | Sidebar, header, toolbar |
| `--bg-card` | `#232936` | Agent cards, stat cards, panels |
| `--bg-hover` | `#2d3548` | Hover backgrounds, ghost button fills |
| `--border` | `#333d52` | All borders, dividers |
| `--text-primary` | `#e8eaf0` | Body text, headings |
| `--text-secondary` | `#8b95a8` | Labels, metadata, secondary text |
| `--accent` | `#6366f1` | Primary action color (Indigo 500) |
| `--accent-hover` | `#818cf8` | Accent on hover (Indigo 400) |
| `--success` | `#22c55e` | Active state, positive badges |
| `--warning` | `#f59e0b` | Idle state, dirty indicator, warnings |
| `--danger` | `#ef4444` | Error states, Stop button, alerts |
| `--info` | `#3b82f6` | **Declared but unused** |

### 2.2 Contrast Analysis (WCAG 2.1)

| Foreground | Background | Ratio | WCAG AA (4.5:1) | Issue |
|------------|------------|-------|-----------------|-------|
| `#e8eaf0` on `#0f1219` | bg-primary | ~15.2:1 | ✅ AAA | — |
| `#e8eaf0` on `#1a1f2e` | bg-secondary | ~11.8:1 | ✅ AAA | — |
| `#e8eaf0` on `#232936` | bg-card | ~9.9:1 | ✅ AAA | — |
| `#8b95a8` on `#0f1219` | bg-primary | ~5.2:1 | ✅ AA | Marginally passes |
| `#8b95a8` on `#232936` | bg-card | ~4.3:1 | ❌ **FAILS** | Secondary text on cards fails AA |
| `#8b95a8` on `#1a1f2e` | bg-secondary | ~4.8:1 | ✅ AA | Passes — barely |
| `#6366f1` on `#232936` | Badge bg | ~3.1:1 | ❌ **FAILS** | Accent text on accent/20 badge fails AA |
| `#22c55e` on `#232936` | Status dot | N/A | — | Decorative — not text |
| `#f59e0b` on `#232936` | Warning badge | ~3.8:1 | ❌ **FAILS** | Warning text in badge fails AA |

### 2.3 Critical Contrast Fixes

**Fix A — Secondary text on cards:**
Change `--text-secondary` from `#8b95a8` to `#a1abbe`.  
New ratio on `#232936`: ~5.9:1 ✅ AA.  
New ratio on `#1a1f2e`: ~7.1:1 ✅ AA.  
New ratio on `#0f1219`: ~8.8:1 ✅ AAA.

**Fix B — Accent badge text:**
Change `--accent` badge text on `bg-accent/20` by increasing badge background opacity.  
Replace `bg-accent/20` with `bg-accent/25` and use `text-[#a5b4fc]` (Indigo 300) instead of `text-accent`.  
New ratio of `#a5b4fc` on `#282c4a` (~25% indigo on card): ~5.4:1 ✅ AA.

**Fix C — Warning badge text:**
Replace `text-warning` (`#f59e0b`) on `bg-warning/20` with `text-[#fbbf24]` (Amber 400).  
New ratio on computed `#2e2a14` (20% warning overlay on card): ~5.1:1 ✅ AA.

### 2.4 Palette Coherence

The palette is excellent for a developer tool dark theme. The progression from `bg-primary` → `bg-secondary` → `bg-card` → `bg-hover` creates a clear layering system. The 4-step depth works well.

**Missing:** There's no `--bg-elevated` token for modals/dropdowns. The Modal component currently uses `#1a1f2e` (bg-secondary), which creates the correct visual hierarchy — but naming it would make the design system explicit.

**`--info: #3b82f6` is orphaned.** It appears in globals.css but zero component uses it. Either wire it into the Badge component as an `info` variant or remove it. Orphaned tokens create maintenance confusion.

---

## 3. Typography Review

### 3.1 Current System

| Family | Use | Source |
|--------|-----|--------|
| Inter | UI, body, nav, labels | Google Fonts CDN |
| JetBrains Mono | Code, agent IDs, file paths, Monaco editor | Google Fonts CDN |
| System fallback | body fallback | `system-ui, -apple-system, sans-serif` |

### 3.2 Scale in Use

| Class | Size | Weight | Line Height | Used For |
|-------|------|--------|-------------|----------|
| `text-xs` | 12px | 400–600 | ~16px | Labels, metadata, badge text |
| `text-sm` | 14px | 400–600 | ~20px | Body, nav items, buttons |
| `text-base` | 16px | — | 24px | Not explicitly used |
| `text-lg` | 18px | 600 | 28px | Agent name in detail view |
| `text-2xl` | 24px | 600 | 32px | Stat card numbers |

### 3.3 Issues

**Issue T1 — Missing heading hierarchy.**  
The page `<h1>` (set in Header via `title` prop) is rendered at `text-sm font-semibold` (14px/600). This is the same size as a button. A page title should be at minimum `text-base font-semibold` (16px) and ideally `text-lg` (18px) to anchor the page. Current: "Fleet Overview" at 14px competes visually with the status dots next to it.

**Fix:** In Header.tsx, change `text-sm font-semibold` to `text-base font-semibold` for the `<h1>`.

**Issue T2 — Agent card names are only 14px.**  
Agent names (`text-sm font-semibold`) are the primary label on 40 cards. At 14px in a 4-column grid (~220px card width), names like "Creative-Director" get cramped. Consider `text-sm` is fine but ensure `font-semibold` provides sufficient weight. Currently solid — this is a minor note.

**Issue T3 — Stat numbers could use tabular figures.**  
The stat card numbers ("40", "0", "On/Off") use default Inter proportional figures. For numbers that update live (active agent count), tabular figures prevent layout shift. Add `font-variant-numeric: tabular-nums` to stat number elements.

**Fix:** Add to globals.css:
```css
.stat-value {
  font-variant-numeric: tabular-nums;
}
```
Or use Tailwind class `tabular-nums` on the `<p>` elements in DashboardStats.

**Issue T4 — JetBrains Mono loaded over Google Fonts CDN.**  
Both Inter and JetBrains Mono are loaded from `fonts.googleapis.com`. This adds 2 network round-trips on cold load. For a developer tool that may run locally (localhost:5173), this works — but consider bundling Inter locally if latency on restricted networks is a concern. JetBrains Mono is excellent for this use case; no change needed to the font choice.

**Issue T5 — No tracking (letter-spacing) on uppercase labels.**  
Section headers like "Name", "Size", "Modified" in the agent detail table use `uppercase tracking-wide` (0.025em). Good. But the same pattern should be applied consistently to any other uppercase label (e.g., "Last Command Output", "Channels" in GatewayPanel already uses `uppercase tracking-wide` — this is consistent). ✅ Consistent.

---

## 4. Per-Page Analysis

### 4.1 Dashboard Page `/` — Fleet Overview

**Screenshot analysis:** The page renders a 2×4 stat card row above a 4-column agent grid. 40 agent cards are visible with vertical scrolling.

#### Stat Cards
- 4 cards in a `grid-cols-2 sm:grid-cols-4` layout. Clean, minimal.
- Cards: Total Agents (40), Active (0 in success green), Gateway ("loading…" in gray), Idle (40 in amber).
- **Issue D1:** The "Active" stat shows `0` in `text-success` (#22c55e) even when zero agents are active. Green "0" looks like a success state, not a zero state. A zero active count should show in `text-text-secondary`, not green. Add logic: `{activeCount > 0 ? 'text-success' : 'text-text-secondary'}`.
- **Issue D2:** "Gateway" stat shows "loading…" indefinitely because the gateway API is returning null. The stat card should have a loading shimmer or a timeout fallback ("Unknown") rather than a static ellipsis. The ellipsis reads as a bug.
- **Issue D3:** Stat cards have no icons. Every other card/section uses Lucide icons. Adding a tiny icon to each stat card (e.g., `Bot` for Total, `Activity` for Active, `Radio` for Gateway, `Minus` for Idle) would improve scanability with minimal effort.
- **Issue D4:** The `bg-bg-card border border-border rounded-lg p-4` card style is correct but lacks any hover or interactive affordance since stat cards aren't clickable. This is fine — but consider making "Active" and "Idle" stats clickable to filter the agent grid (future enhancement).

#### Agent Grid
- `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4`. At 1512px viewport, this renders 4 columns.
- **Issue D5:** All 40 agents show `gpt-5.3-codex` as model. This appears to be a display bug — the backend is likely returning a placeholder or the model field is getting mangled. The badge consistently shows `gpt-5.3-codex` for all agents when in reality agents use `claude-opus-4-6`, `claude-sonnet-4-6`, etc. Investigate the `/api/agents` endpoint model field.
- **Issue D6:** Status dots are `w-2.5 h-2.5` (10px) circles. On a `bg-bg-card` (#232936) background with `bg-warning` (#f59e0b) fill, the dot is visible but small. The `aria-label` and `title` attributes are correct for accessibility. The visual size is insufficient for rapid fleet scanning. Recommendation: Increase to `w-3 h-3` (12px) or add an animated `animate-pulse` on the `bg-success` variant to make active agents visually pop.
- **Issue D7:** No search, filter, or sort capability. See E3 in Executive Summary.
- **Issue D8:** The last line of each card shows "Never" for `last_activity` on all 40 agents. When all agents show "Never", the timestamp row has no value and creates visual clutter. Consider hiding the clock row when value is "Never" or replacing it with a status-relevant message like "No sessions yet".
- **Issue D9:** Agent card hover state: `hover:bg-bg-hover` changes card from `#232936` to `#2d3548`. The delta is ~6% luminance — subtle but perceptible. No box-shadow elevation on hover. For interactive cards, a subtle `hover:shadow-lg` or `hover:border-accent/40` would better communicate interactivity.
- **Issue D10:** The "Fleet Overview" section heading is absent. After the stat cards, the agent grid appears with no label. Add a section divider with "Agents" heading, or at minimum the agent count: `<h2 class="text-text-secondary text-xs font-medium uppercase tracking-wide mb-3">Fleet ({agents.length})</h2>`.

#### Layout
- 224px sidebar + 12px header + 24px content padding on each side is appropriate.
- The main content area at 1512px wide with 4 columns of ~320px cards with 16px gaps looks correct.
- Vertical scroll works — agents below the fold (below ~row 2) are not visible on first paint. This is expected.

### 4.2 Agents Page `/agents` — DUPLICATE

**Critical Finding:** `/agents` routes to `DashboardPage` (confirmed in router.tsx: `{ path: '/agents', element: <DashboardPage /> }`). The sidebar shows "Dashboard" and "Agents" as separate links; both render identical content.

**Resolution Options:**

**Option A (Recommended): Keep Dashboard as overview, differentiate /agents as list view.**
- `/` (Dashboard): Stat cards + compact agent grid (6-col at large viewports) + activity feed column
- `/agents`: Full-width searchable/sortable/filterable agent listing with more columns visible

**Option B: Merge the navigation items.**
- Remove "Agents" from sidebar navigation
- Route `/agents` → `/` (redirect)
- Agent grid on Dashboard is the "agents" view
- Sidebar collapses to 4 items: Dashboard, Editor, Config, Gateway

Option A is better for scalability (50+ agents). Option B is simpler and eliminates the confusion immediately.

**Until resolved:** The sidebar is misleading. "Agents" navigation item creates a false expectation of different content.

### 4.3 Agent Detail Page `/agents/:agentId`

Navigation: Clicking any agent card navigates to `/agents/main` (or agent ID). This is a clean, well-implemented page.

**Positive:**
- Back button with ArrowLeft icon ← clear navigation.
- Agent header card shows name, status badge, monospace ID, workspace path, model badge.
- File table has correct column headers (Name, Size, Modified) with accessible `role="grid"`.
- File rows have hover highlight (`hover:bg-bg-hover/40`) and keyboard support (`Enter`/`Space` to open).

**Issue AD1 — File list showing ALL files including binaries.**  
The main agent workspace contains 78 files, including many `.png` screenshots (448KB–534KB each). The file browser shows these alongside `.md` files with no categorization or filtering. Users looking for SOUL.md or MEMORY.md have to scan through dozens of binary images. 

**Recommended fix:** Add file type grouping or at minimum a filter. Quick win: sort by extension (`.md` first, then code files, then images last). Or add filter chips: `All | Markdown | Code | Images`.

**Issue AD2 — File type icons are uniform.**  
Every file uses the same `<File>` Lucide icon regardless of extension. Differentiate file types visually:
- `.md` → `FileText` icon
- `.json` → `FileJson` or `Braces` icon  
- `.png`/`.jpg` → `Image` icon
- `.py`/`.ts`/`.js` → `FileCode` icon
- `.sh` → `Terminal` icon

This makes the file list scannable at a glance.

**Issue AD3 — "Open" action not differentiated for binary files.**  
Clicking a `.png` file navigates to the editor, which will show raw binary content in Monaco. The editor should detect binary files and show a "cannot edit binary" message, or the file list should mark binary files with a `cursor-not-allowed` style and no click action.

**Issue AD4 — No "Create file" or "Upload" action.**  
The workspace file panel has no way to create a new file or upload a file to an agent's workspace. Add a `+` button in the file list header. Even if the backend doesn't support it yet, a disabled button with tooltip signals the planned functionality.

**Issue AD5 — Model badge placement.**  
In the agent header card, the model badge (`gpt-5.3-codex`) is positioned top-right with `Badge variant="neutral"`. The status badge is placed inline next to the agent name. The visual hierarchy is: Name (primary) → status badge (inline) → model badge (top right). This creates an asymmetric layout. Consider moving model below the name alongside other metadata, or creating a 2-column metadata grid.

**Issue AD6 — Workspace path is very long and truncates poorly.**  
`/Users/miller/.openclaw/workspace` is 33 characters. At card widths below ~600px it may truncate. Add `truncate` class with `title` attribute for full path on hover.

### 4.4 Config Page `/config`

The Config page renders a Monaco JSON editor with a toolbar for Save/Validate/Reload actions.

**Positive:**
- Toolbar is well designed: path breadcrumb left-aligned, actions right-aligned
- Unsaved changes indicator (yellow dot) is clear
- Validation indicator (CheckCircle/XCircle) with inline "Valid JSON" / error message
- `formatOnPaste: true` and `formatOnType: true` are excellent UX for JSON
- Keyboard shortcut Cmd+S works for save
- Conflict dialog is thoughtfully designed

**Issue C1 — Save button is disabled until dirty, showing no affordance.**  
When the page loads with the config, the Save button appears grayed out (`disabled opacity-50`). A user landing on this page for the first time sees a grayed-out button and no instruction that they need to make changes first. Add a tooltip on the disabled Save button: "No unsaved changes".

**Issue C2 — The toolbar path is bare text with no icon.**  
`/Users/miller/.openclaw/openclaw.json` appears as plain text. Add a `FileJson` icon before the path. This differentiates it from the editor toolbar and makes the config nature immediately clear.

**Issue C3 — Reload button uses RefreshCw icon but no confirmation.**  
Clicking Reload while dirty will silently discard all changes. Either add a confirmation dialog when dirty (similar to the conflict modal), or disable the Reload button when dirty (with tooltip "Save or discard changes first").

**Issue C4 — Validation is triggered manually.**  
The Validate button requires manual click. JSON editors should validate on change. The Monaco editor does its own inline JSON validation (red squiggles), but the `validateConfig()` action in the toolbar is separate backend validation. The auto-validation-on-type with the `CheckCircle` indicator is already in the store — just wire it to fire on `onChange` instead of requiring the button click.

**Issue C5 — Editor fills remaining height correctly** (`flex-1 overflow-hidden`). The Monaco editor takes all available space. This is correct. ✅

**Issue C6 — "Config — openclaw.json" is verbose as a page title.**  
The header reads "Config — openclaw.json". The path `/Users/miller/.openclaw/openclaw.json` already shows in the toolbar. The page title could simplify to "Config" to reduce redundancy.

### 4.5 Gateway Page `/gateway`

**Current state:** Shows a loading spinner indefinitely in the test environment. The `GatewayPanel` component has correct conditional logic for when `status` is loaded (showing Start/Stop/Restart buttons, PID, uptime, command output, channels). The issue is the gateway daemon is not running, so the API returns null, and the component never exits the `loading && !status` spinner state.

**Wait — re-reading the source code:**  
```tsx
if (loading && !status) {
  return <Spinner ... />;
}
```
This means: show spinner ONLY while loading AND status hasn't been fetched yet. Once the API responds (even with `{running: false}`), `loading` becomes false and the panel renders. The perpetual spinner observed in the browser indicates the API call to `/api/gateway/status` is hanging or failing without setting `loading = false`. This is a **bug in the API integration**, not a design issue — but it results in a broken UI state.

**Design recommendations for Gateway page:**

**Issue G1 — No explicit "loading failed" state.**  
If the API hangs (e.g., backend not running), the spinner persists forever. Add a timeout: if `loading` is still true after 5 seconds, show an error state: "Cannot connect to gateway API. Is the backend running on :8400?"

**Issue G2 — Gateway panel width is constrained to `max-w-2xl` (672px).**  
On a 1512px viewport, the gateway controls sit in the top-left 44% of the content area with a lot of empty space. This is intentional (form follows function for a simple control panel), but the empty right side feels unbalanced. Consider either:
- Expanding the card to `max-w-3xl` and adding more info
- Adding a "Recent Logs" panel on the right (2-column layout) showing gateway log output

**Issue G3 — "Last Command Output" card only shows after an action.**  
On page load, the gateway shows only the status card and action buttons. After clicking Start/Stop/Restart, the command output appears below. This is correct progressive disclosure — but the empty state below the buttons (when no command has been run) feels sparse. Add a subtle "No recent commands" placeholder text.

**Issue G4 — Channels panel renders raw JSON.**  
```tsx
<pre>{JSON.stringify(status.channels, null, 2)}</pre>
```
Raw JSON for channel status is developer-friendly but not polished. Consider rendering channels as a simple table: Channel Name | Status | Connected | Messages. Even a basic table beats raw JSON.

**Issue G5 — Action button disabled states.**  
Start is disabled when running, Stop is disabled when stopped. The disabled opacity (`opacity-50`) is applied correctly. But there's no tooltip explaining WHY a button is disabled. Add `title="Gateway is already running"` to the disabled Start button and `title="Gateway is not running"` to the disabled Stop button.

### 4.6 Editor Page `/editor`

**Current state:** Shows the empty state — "No file loaded" with an AlertCircle icon and text "Open a file from an agent's workspace to edit it".

**Design analysis of empty state:**
- AlertCircle icon at 40px — slightly alarming for an informational empty state. Switch to `FileCode` icon.
- "No file loaded" is accurate but passive. Change to "Select a file to edit".
- The instruction text is good: "Open a file from an agent's workspace to edit it". ✅

**Issue E1 — No navigation path to reach the editor.**  
The editor is only accessible via: (1) clicking a file in the agent detail view, which navigates to `/editor?agent=X&path=Y`, or (2) direct URL. There is no way to browse agent workspaces from within the Editor page itself. A user who navigates to `/editor` from the sidebar gets the empty state with no way to select a file without going back to the agent list.

**Required addition:** A file picker sidebar or drawer within the Editor page. Minimum viable: a two-column layout with an agent list on the left (collapsible), and the editor on the right. When an agent is selected, the file list loads. Clicking a file opens it.

**Proposed Editor layout:**
```
[Sidebar 56px][File Browser 240px][Editor (flex-1)]
```
The file browser panel would show:
- Agent selector dropdown at top
- File tree/list below
- Current file highlighted

**Issue E2 — Editor toolbar is excellent when a file is loaded.**  
The toolbar design (breadcrumb left + dirty dot + Save button right) is clean and professional. The conflict modal is also well-designed. These only appear when a file IS loaded — so they're untested from the empty state.

**Issue E3 — Monaco theme is vs-dark, not matching the dashboard theme.**  
Monaco's `vs-dark` theme uses `#1e1e1e` as the editor background, which conflicts with the dashboard's `#0f1219` page background. The seam between the editor and the surrounding UI is jarring. Consider:
- Custom Monaco theme that uses `#0f1219` as editor background
- Or keep `vs-dark` but ensure the editor fills its container edge-to-edge (current `-m-6` margin compensation does this)

The `-m-6` negative margin on the editor page container is a workaround to eliminate the `p-6` content padding. This works but creates a brittle dependency on the parent layout's padding. A cleaner approach: add a Layout prop `noPadding={true}` that applies `p-0` to the main element.

---

## 5. Cross-Cutting Recommendations

### CC1 — WebSocket Live Updates (UI feedback gap)
The Header shows a "Live" status dot (WebSocket connected). The dashboard polling appears to work. But there's no visual feedback when the agent list updates in real-time. When an agent transitions from idle → active, the card should have a brief highlight animation:
```css
@keyframes pulse-card {
  0% { border-color: #22c55e; }
  100% { border-color: #333d52; }
}
```
Add a 1-second border animation when status changes from idle to active.

### CC2 — Loading Skeleton States
Currently, loading states use a centered `<Spinner>` with a label. This is acceptable but the perceived wait time feels longer when the entire content area is blank. Replace spinner with skeleton placeholders that match the actual content layout:
- Agent grid: 8 skeleton cards (gray animated shimmer rectangles in the same grid positions)
- Agent detail file list: 5 skeleton rows
- Config editor: dark rectangle in editor area

### CC3 — Toast Notifications
The Toast system exists (useToastStore) but there's no visible Toast in the DOM from the pages analyzed. Verify the ToastContainer is mounted in the component tree. Based on the source: Toast messages are added on save/error actions but the render location needs verification.

### CC4 — Empty State Consistency
Different empty states use different icons:
- Agent grid error: `Bot` (40px) + danger text
- Agent grid empty: `Bot` (40px) + neutral text  
- Editor empty: `AlertCircle` (40px) + neutral text
- Agent detail empty: centered danger text (no icon)

**Standardize:** Use `Bot` for agent-related empty states, `FileCode` for editor empty states, `AlertCircle` only for error states (not neutral empty states).

### CC5 — Focus Visible Rings
Keyboard navigation uses `focus-visible:ring-2 focus-visible:ring-accent` consistently across Button, Card (clickable), and NavLink. The ring offset uses `ring-offset-bg-primary` on buttons. This is correct and WCAG 2.4.11 compliant. ✅ However, the file table rows (`<tr role="row">`) use `tabIndex={0}` without an explicit focus-visible ring style. Add `focus-visible:outline-2 focus-visible:outline-accent focus-visible:outline-offset-[-2px]` to the `<tr>` in FileRow.

### CC6 — Responsive Behavior Below 768px
The sidebar is `w-56` (224px) fixed width. On a 768px tablet viewport, the sidebar takes 29% of screen width, leaving 71% (544px) for content. The 4-column agent grid collapses to 2 columns at `sm:` breakpoint. This is reasonable.

**Gap:** On viewports below 640px (mobile), the sidebar is still 224px, taking 35%+ of a 640px screen. There's no mobile menu/hamburger pattern. This is a developer tool likely only used on desktop, so this is low priority — but worth noting.

**Recommendation:** Add `hidden md:flex` to the sidebar and a hamburger toggle for mobile. Not critical for v1.0.

### CC7 — Page Titles and Browser Tab
All pages set the browser tab to "OpenClaw Dashboard" (from `index.html`). Individual page navigation doesn't update the document title. Add `document.title` updates per page:
```tsx
useEffect(() => {
  document.title = `${title} — OpenClaw`;
}, [title]);
```
This improves tab management when users have multiple dashboard tabs open.

### CC8 — Animation Consistency
Transition durations:
- Card hover: `transition-colors` (Tailwind default: 150ms ease-in-out) ✅
- Nav links: `transition-colors` ✅  
- Button hover: `transition-colors` ✅
- Status dot: no transition (appears/disappears instantly on status change)

**Add transition to status dot:**
```tsx
<span className={`w-2.5 h-2.5 rounded-full transition-colors duration-300 ...`} />
```

---

## 6. Component Library Gaps

### Gap 1 — Search/Filter Input Component
No search input component exists. Needed for: agent grid search, file list filter, future log search.

**Spec:**
```tsx
interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}
```
Styling: `bg-bg-card border border-border rounded-md px-3 py-1.5 text-sm text-text-primary placeholder:text-text-secondary focus:border-accent focus:outline-none`

### Gap 2 — Select/Dropdown Component
No `<select>` component exists. Needed for: model filter in agent grid, agent selector in editor, sort order.

### Gap 3 — Data Table with Sorting
The AgentDetail file table is hardcoded without sort capability. A reusable `<DataTable>` component with `sortable` columns would serve the file list, agent list, and future log viewer.

### Gap 4 — Stat Card Component
DashboardStats inline-defines stat cards with no shared component. Extract to `<StatCard label icon value color />` for reuse in Gateway page (connection count, messages/sec, etc.).

### Gap 5 — Skeleton Loader Component
No `<Skeleton>` component. Needed to replace spinners with more informative loading states.

**Spec:**
```tsx
<Skeleton className="h-16 rounded-lg" />
<Skeleton className="h-4 w-3/4" />
```
Base styles: `bg-bg-hover animate-pulse rounded`

### Gap 6 — Empty State Component
Three different inline empty states exist. Extract to:
```tsx
<EmptyState 
  icon={Bot} 
  title="No agents configured" 
  description="Add agents to openclaw.json to see them here"
  action={<Button>Open Config</Button>}
/>
```

### Gap 7 — File Type Icon Resolver
No utility function maps file extensions to Lucide icons. Needed for AgentDetail file list.

### Gap 8 — Confirmation Dialog
No "Are you sure?" pattern exists. Needed for: Reload config when dirty, delete file (future), Stop gateway.

### Gap 9 — Collapsible Panel / Accordion
The Gateway page "Channels" section and the Editor file browser would benefit from a collapsible panel pattern. Currently not implemented.

### Gap 10 — Keyboard Shortcut Legend
Developer tools commonly include a `?` keyboard shortcut to show all shortcuts. The editor has Cmd+S but no way to discover it. A `<KeyboardShortcutModal>` triggered by `?` key would improve discoverability.

---

## 7. Recommended Design System

### 7.1 Complete CSS Variable Set

```css
:root {
  /* === Backgrounds (4-level depth system) === */
  --bg-base:      #0a0d13;   /* Page, deepest level — slightly darker than current #0f1219 */
  --bg-primary:   #0f1219;   /* Page background (current — keep) */
  --bg-secondary: #1a1f2e;   /* Sidebar, header, toolbar */
  --bg-card:      #232936;   /* Cards, panels */
  --bg-hover:     #2d3548;   /* Hover states, selections */
  --bg-elevated:  #1a1f2e;   /* Modals, dropdowns (= bg-secondary, but named) */

  /* === Borders === */
  --border:         #333d52; /* Default border */
  --border-strong:  #4a5568; /* Focused, emphasized borders */
  --border-subtle:  #252b3b; /* Very subtle dividers */

  /* === Text === */
  --text-primary:   #e8eaf0; /* Body, headings — keep */
  --text-secondary: #a1abbe; /* Labels, metadata — CHANGED from #8b95a8 for AA contrast */
  --text-tertiary:  #6b7896; /* Placeholders, disabled text */
  --text-inverse:   #0f1219; /* Text on accent/colored backgrounds */

  /* === Brand/Accent === */
  --accent:         #6366f1; /* Indigo 500 — keep */
  --accent-hover:   #818cf8; /* Indigo 400 — keep */
  --accent-light:   rgba(99, 102, 241, 0.15); /* Background tint */
  --accent-border:  rgba(99, 102, 241, 0.30); /* Border tint */

  /* === Semantic Colors === */
  --success:        #22c55e; /* Green 500 */
  --success-light:  rgba(34, 197, 94, 0.15);
  --success-border: rgba(34, 197, 94, 0.30);

  --warning:        #f59e0b; /* Amber 500 */
  --warning-text:   #fbbf24; /* Amber 400 — higher contrast for text on dark bg */
  --warning-light:  rgba(245, 158, 11, 0.15);
  --warning-border: rgba(245, 158, 11, 0.30);

  --danger:         #ef4444; /* Red 500 */
  --danger-light:   rgba(239, 68, 68, 0.15);
  --danger-border:  rgba(239, 68, 68, 0.30);

  --info:           #3b82f6; /* Blue 500 — wire up or remove */
  --info-light:     rgba(59, 130, 246, 0.15);
  --info-border:    rgba(59, 130, 246, 0.30);

  /* === Typography === */
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, monospace;

  /* === Spacing Scale === */
  /* Uses Tailwind's default 4px base — no custom tokens needed */

  /* === Radii === */
  --radius-sm:  4px;   /* Badges, small chips */
  --radius-md:  6px;   /* Buttons, inputs */
  --radius-lg:  8px;   /* Cards, panels */
  --radius-xl:  12px;  /* Modals */

  /* === Shadows === */
  --shadow-card:    0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.3);
  --shadow-modal:   0 20px 60px rgba(0,0,0,0.5);
  --shadow-tooltip: 0 4px 12px rgba(0,0,0,0.4);

  /* === Z-index Scale === */
  --z-sidebar:  100;
  --z-header:   200;
  --z-modal:    500;
  --z-toast:    600;
  --z-tooltip:  700;

  /* === Transitions === */
  --transition-fast:   100ms ease-in-out;
  --transition-base:   150ms ease-in-out;
  --transition-slow:   300ms ease-in-out;
}
```

### 7.2 Spacing Scale (Tailwind-aligned)

| Token | Value | Use |
|-------|-------|-----|
| 0.5 | 2px | Tight inline spacing |
| 1 | 4px | Icon gap, badge padding |
| 1.5 | 6px | Small button padding-y |
| 2 | 8px | Badge padding-x, compact spacing |
| 2.5 | 10px | Status dot to text gap |
| 3 | 12px | Card internal gaps |
| 4 | 16px | Card padding, grid gap |
| 5 | 20px | Section spacing |
| 6 | 24px | Page padding |
| 8 | 32px | Major section gaps |
| 16 | 64px | Empty state padding |

### 7.3 Component Patterns

**Sidebar active state:**
```tsx
// Current: bg-accent/15 text-accent (too subtle)
// Recommended:
isActive
  ? 'bg-accent/20 text-accent border-l-2 border-accent pl-[10px]'
  : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover border-l-2 border-transparent pl-[10px]'
```
The `border-l-2` adds a 2px left stroke on the active item — the VS Code / Linear pattern that's unmistakably clear.

**Status dot sizes:**
```tsx
// Current: w-2.5 h-2.5 (10px)
// Recommended: w-3 h-3 (12px) for agent cards
// Add animate-pulse for active status:
agent.status === 'active' ? 'w-3 h-3 rounded-full bg-success animate-pulse' : ...
```

**Agent card model badge:**
```tsx
// Current: all agents show "gpt-5.3-codex" (likely API bug)
// Badge should truncate long model names with title attr:
<Badge ... title={agent.model} className="max-w-[140px] truncate">
  {shortenModel(agent.model)}
</Badge>
```

---

## 8. Priority Matrix

| # | Recommendation | Impact | Effort | Priority |
|---|----------------|--------|--------|----------|
| E1 | Resolve dual Dashboard/Agents pages | 🔴 Critical | Medium | P0 |
| E5 | Fix sidebar active state (border-l-2) | 🔴 Critical | Tiny | P0 |
| E3 | Add search/filter to agent grid | 🔴 Critical | Small | P0 |
| Fix A | text-secondary #8b95a8 → #a1abbe (WCAG AA) | 🟠 High | Tiny | P1 |
| D1 | Active count 0 should not show green | 🟠 High | Tiny | P1 |
| D5 | Fix model display bug (gpt-5.3-codex) | 🟠 High | Small | P1 |
| AD1 | File list: filter/group binary files | 🟠 High | Small | P1 |
| AD2 | File type icons by extension | 🟡 Medium | Small | P1 |
| G1 | Gateway: API timeout → error state | 🟠 High | Small | P1 |
| E4 | Gateway: "stopped" explicit design | 🟠 High | Small | P1 |
| E1-A | Editor: file browser sidebar | 🔴 Critical | Large | P1 |
| CC1 | WS live update card animation | 🟡 Medium | Small | P2 |
| CC2 | Skeleton loading states | 🟡 Medium | Medium | P2 |
| D3 | Stat card icons | 🟢 Low | Tiny | P2 |
| D9 | Card hover: shadow or accent border | 🟡 Medium | Tiny | P2 |
| D10 | "Fleet (40)" section heading | 🟢 Low | Tiny | P2 |
| D8 | Hide "Never" last_activity when all never | 🟡 Medium | Tiny | P2 |
| T1 | Page title h1 text-base not text-sm | 🟡 Medium | Tiny | P2 |
| T3 | Tabular figures for stat numbers | 🟢 Low | Tiny | P2 |
| C1 | Save button tooltip when disabled | 🟡 Medium | Tiny | P2 |
| C2 | Config path: add FileJson icon | 🟢 Low | Tiny | P2 |
| C3 | Reload confirmation when dirty | 🟡 Medium | Small | P2 |
| C4 | Auto-validate on change | 🟡 Medium | Small | P2 |
| G4 | Channels: table instead of raw JSON | 🟡 Medium | Medium | P2 |
| G5 | Button disabled tooltips | 🟢 Low | Tiny | P2 |
| AD3 | Block editor open for binary files | 🟠 High | Small | P2 |
| AD5 | Agent detail: model badge placement | 🟢 Low | Tiny | P3 |
| CC5 | Focus ring on file table rows | 🟡 Medium | Tiny | P2 |
| CC7 | Document title updates per page | 🟢 Low | Tiny | P3 |
| CC8 | Status dot transition-colors | 🟢 Low | Tiny | P3 |
| Gap 1 | SearchInput component | 🔴 Critical | Small | P1 |
| Gap 2 | Select/Dropdown component | 🟡 Medium | Medium | P2 |
| Gap 3 | Sortable DataTable | 🟡 Medium | Large | P2 |
| Gap 4 | StatCard component | 🟢 Low | Small | P3 |
| Gap 5 | Skeleton loader | 🟡 Medium | Small | P2 |
| Gap 6 | EmptyState component | 🟢 Low | Small | P2 |
| Gap 10 | Keyboard shortcut legend | 🟢 Low | Medium | P3 |
| Fix B | Accent badge text contrast | 🟠 High | Tiny | P1 |
| Fix C | Warning badge text contrast | 🟠 High | Tiny | P1 |
| Info | Wire --info color or remove it | 🟢 Low | Tiny | P3 |

---

## Appendix A — Quick-Win Bundle (1-hour changes)

These changes can be made in under 1 hour combined and have outsized UX impact:

1. **`globals.css`**: Change `--text-secondary: #8b95a8` → `#a1abbe`
2. **`Sidebar.tsx`**: Add `border-l-2 border-accent pl-[10px]` to active state, `border-l-2 border-transparent pl-[10px]` to inactive
3. **`DashboardStats` in `DashboardPage.tsx`**: Change active count text logic — `text-success` only when `activeCount > 0`
4. **`AgentCard.tsx`**: Increase status dot `w-2.5 h-2.5` → `w-3 h-3`, add `animate-pulse` when active
5. **`AgentGrid.tsx`**: Add a search input above the grid with `useState` filter on `agent.name.toLowerCase().includes(query)`
6. **`AgentDetail.tsx`**: Change AlertCircle → FileText icon for `.md` files, Image for `.png/.jpg`
7. **`Header.tsx`**: Change `<h1>` from `text-sm` to `text-base`
8. **`router.tsx`**: Remove `{ path: '/agents', element: <DashboardPage /> }` and add redirect to `/`

---

## Appendix B — Search Input Implementation

Paste this into `AgentGrid.tsx` above the grid return:

```tsx
// Add at top of component:
const [query, setQuery] = React.useState('');

// Filter agents:
const filteredAgents = query.trim()
  ? agents.filter(a => 
      a.name.toLowerCase().includes(query.toLowerCase()) ||
      a.id.toLowerCase().includes(query.toLowerCase()) ||
      a.model.toLowerCase().includes(query.toLowerCase())
    )
  : agents;

// Add before the grid div:
<div className="mb-4 flex items-center gap-3">
  <input
    type="search"
    value={query}
    onChange={e => setQuery(e.target.value)}
    placeholder={`Search ${agents.length} agents…`}
    className="flex-1 bg-bg-card border border-border rounded-md px-3 py-1.5 text-sm text-text-primary placeholder:text-text-secondary focus:border-accent focus:outline-none transition-colors"
  />
  {query && (
    <span className="text-text-secondary text-xs">
      {filteredAgents.length} of {agents.length}
    </span>
  )}
</div>

// Replace agents.map → filteredAgents.map
```

---

*End of Design Review — OpenClaw Dashboard v1.0.0*  
*Screenshots archived at: `/Users/miller/Projects/openclaw-dashboard/design-review-screenshots/`*
