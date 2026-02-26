> **Superseded.** The authoritative designer issue tracking table is in WAVES-v4.md (§ Designer Issue Tracking). This file reflects the Round 1 snapshot and is preserved for historical reference only.

# DESIGN-TRACKING.md — Design Review Recommendation Mapping
_Maps every DESIGN-REVIEW.md recommendation to a WAVES task. Updated each planning round._
_Last Updated: 2026-02-25T09:22:00-05:00_

## Status Legend
✅ = Assigned to wave task | ⬜ = Unassigned (needs wave) | 🔄 = Deferred to backlog | ❌ = Won't fix

---

## Executive Summary (E1-E5)
| ID | Recommendation | Priority | Wave | Status |
|----|---------------|----------|------|--------|
| E1 | Resolve dual Dashboard/Agents problem | Critical | W1 | ✅ |
| E2 | Rich status indicators (left-border + badge + pulse) | Critical | W2 | ✅ |
| E3 | Search/filter bar for agent grid | High | W1 | ✅ |
| E4 | Complete Gateway page (no infinite spinner) | High | W4 | ✅ |
| E5 | Fix sidebar active state contrast | Medium | W1 | ✅ |

## WCAG Contrast Fixes (Fix A-C)
| ID | Recommendation | Wave | Status |
|----|---------------|------|--------|
| Fix A | --text-secondary #8b95a8 → #a1abbe (4.3:1 → 5.9:1 on cards) | ⬜ | ⬜ NEEDS WAVE |
| Fix B | Accent badge text → #a5b4fc on bg-accent/25 | ⬜ | ⬜ NEEDS WAVE |
| Fix C | Warning badge text → #fbbf24 (Amber 400) | ⬜ | ⬜ NEEDS WAVE |

## Dashboard Page Issues (D1-D10)
| ID | Recommendation | Wave | Status |
|----|---------------|------|--------|
| D1 | Active count "0" should not be green | W1 | ✅ (DashboardPage redesign) |
| D2 | Gateway stat "loading..." needs timeout/fallback | W1 | ✅ (DashboardPage redesign) |
| D3 | Stat cards missing icons | W1 | ✅ (DashboardPage redesign) |
| D4 | Stat cards not clickable to filter grid | ⬜ | ⬜ Future enhancement |
| D5 | All agents show gpt-5.3-codex (model display bug) | ⬜ | ⬜ NEEDS WAVE — backend bug |
| D6 | Status dots too small (10px → 12px + pulse) | W2 | ✅ |
| D7 | No search/filter (see E3) | W1 | ✅ |
| D8 | "Never" timestamp clutter — hide or replace | W2 | ✅ |
| D9 | Card hover needs shadow/border accent | W2 | ✅ |
| D10 | Missing section heading / agent count | W1 | ✅ |

## Agent Detail Issues (AD1-AD6)
| ID | Recommendation | Wave | Status |
|----|---------------|------|--------|
| AD1 | File list showing ALL files including binaries | W5 | ✅ (file tree filters) |
| AD2 | File type icons are uniform (need per-type icons) | W3 | ✅ |
| AD3 | "Open" action not differentiated for binary files | ⬜ | ⬜ NEEDS WAVE |
| AD4 | No "Create file" or "Upload" action | ⬜ | 🔄 Deferred — post-v2 |
| AD5 | Model badge placement | W2 | ✅ |
| AD6 | Workspace path truncates poorly | ⬜ | ⬜ NEEDS WAVE |

## Cross-Cutting (CC1-CC8)
| ID | Recommendation | Wave | Status |
|----|---------------|------|--------|
| CC1 | WebSocket live updates (UI feedback) | W7 | ✅ |
| CC2 | Loading skeleton states | ⬜ | ⬜ NEEDS WAVE |
| CC3 | Toast notifications | W6 | ✅ |
| CC4 | Empty state consistency | ⬜ | ⬜ NEEDS WAVE |
| CC5 | Focus visible rings | ⬜ | ⬜ NEEDS WAVE |
| CC6 | Responsive below 768px | W10 | ✅ |
| CC7 | Page titles and browser tab | ⬜ | ⬜ NEEDS WAVE |
| CC8 | Animation consistency | ⬜ | ⬜ NEEDS WAVE |

## Component Library Gaps (Gap 1-10)
| ID | Recommendation | Wave | Status |
|----|---------------|------|--------|
| Gap 1 | Search/Filter Input component | W1 | ✅ |
| Gap 2 | Select/Dropdown component | W1 | ✅ (status filter) |
| Gap 3 | Data Table with sorting | ⬜ | ⬜ NEEDS WAVE |
| Gap 4 | Stat Card component (refactored) | W1 | ✅ |
| Gap 5 | Skeleton Loader component | ⬜ | ⬜ NEEDS WAVE |
| Gap 6 | Empty State component (reusable) | ⬜ | ⬜ NEEDS WAVE |
| Gap 7 | File Type Icon Resolver | W3 | ✅ |
| Gap 8 | Confirmation Dialog | ⬜ | ⬜ NEEDS WAVE |
| Gap 9 | Collapsible Panel / Accordion | W5 | ✅ (file tree) |
| Gap 10 | Keyboard Shortcut Legend | W10 | ✅ |

## Design System (§7)
| ID | Recommendation | Wave | Status |
|----|---------------|------|--------|
| §7.1 | Complete CSS variable set (full token list) | ⬜ | ⬜ NEEDS WAVE |
| §7.2 | Spacing scale (4/8/12/16/24/32/48/64) | ⬜ | ⬜ NEEDS WAVE |
| §7.3 | Component patterns (card, badge, button standards) | ⬜ | ⬜ NEEDS WAVE |

## Priority Matrix Items (§8)
| ID | Recommendation | Effort | Impact | Wave | Status |
|----|---------------|--------|--------|------|--------|
| Quick-Win Bundle (Appendix A) | 6 one-hour changes | Low | High | ⬜ | ⬜ NEEDS WAVE |
| Appendix B | Drop-in search implementation | Low | High | W1 | ✅ |

---

## Summary
- **Assigned**: 23 recommendations mapped to waves
- **Unassigned**: 19 recommendations need wave assignment
- **Deferred**: 1 (AD4 — create file/upload)

**The planner must address the 19 unassigned items in WAVES-v2.**
