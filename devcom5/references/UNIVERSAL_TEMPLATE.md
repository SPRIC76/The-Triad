# Universal Document Template
<!-- DevCom5 v1.0 | 2026-02-10 | Architect mode reference -->

Templates for the five-document system. Adapt to classification.
Never template-stamp — use only sections appropriate to project maturity.

---

## INDEX.md

```markdown
# [Project Name]
> [One-line purpose]

## Quick Start
[Minimum steps to run/use. Code blocks for commands.]

## What This Is
[2-3 sentences. What problem it solves, who it's for.]

## Structure
[Key directories/files and what they contain.]

## Documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) — Technical decisions and structure
- [USER_EXPERIENCE.md](USER_EXPERIENCE.md) — Guides and workflows
- [PLANNING.md](PLANNING.md) — Roadmap and ideas
- [HISTORY.md](HISTORY.md) — Session log and changelog

## Status
[Current state: working/in-progress/blocked. Last updated date.]
```

---

## ARCHITECTURE.md

```markdown
# Architecture — [Project Name]
> Technical map for builders and maintainers.

## Overview
[System diagram in words or mermaid. 1-2 paragraphs max.]

## Stack
| Layer | Technology | Notes |
|-------|-----------|-------|
| Runtime | | |
| Framework | | |
| Build | | |
| Data | | |

## Key Decisions
### [Decision Title]
**Chose:** [what] | **Over:** [alternatives] | **Because:** [why]

## Element Notes
[Per-component documentation. This is where scattered knowledge centralizes.]

### [Component/Module Name]
**Purpose:** [one line]
**Key files:** [paths]
**Depends on:** [other components]
**Notes:** [implementation details, gotchas, edge cases]

## Conventions
[Naming, patterns, file organization rules specific to this project.]
```

---

## USER_EXPERIENCE.md

```markdown
# User Experience — [Project Name]
> How it works from the user's perspective.

## Core Workflow
[Step-by-step primary use case.]

## Features
### [Feature Name]
**What:** [description]
**How:** [usage instructions]
**Example:** [concrete example]

## Configuration
[User-facing settings and their effects.]

## Troubleshooting
| Symptom | Cause | Fix |
|---------|-------|-----|
| | | |
```

---

## PLANNING.md

```markdown
# Planning — [Project Name]
> Roadmap, backlog, and ideas.

## Current Priority
[What's being worked on right now and why.]

## Backlog
| Priority | Item | Effort | Notes |
|----------|------|--------|-------|
| 🔴 High | | | |
| 🟡 Med | | | |
| 🟢 Low | | | |

## Ideas Addendum
[Unvalidated ideas, POTIMPs, future possibilities. Separate from backlog.]

- [Idea]: [brief rationale]

## Constraints
[Known limitations, dependencies, blockers.]
```

---

## HISTORY.md

```markdown
# History — [Project Name]
> Session log and changelog. Append-only. Newest first.

## [Date] — [Session Title]
**Mode:** [Cartographer/Architect/Scribe]
**Depth:** [level] | **Duration:** [approx]

### What happened
[Brief narrative of session work.]

### Changes
- [file]: [what changed]

### Decisions
- [Decision and rationale]

### Next
- [Carry-forward items]

---
[Previous sessions below, newest first]
```

---

## Maturity-Based Selection

| Maturity | Required Docs | Optional |
|----------|--------------|----------|
| Seed | INDEX, PLANNING | — |
| MVP | INDEX, ARCHITECTURE, PLANNING, HISTORY | USER_EXPERIENCE |
| Production | All five | — |
| Legacy | All five (aggressive capture priority) | — |
