---
name: devcom5
description: >
  Developer Communications system with adaptive 5-doc Markdown framework,
  co-authoring workflows, and internal comms generation. 
  deep-read project state/trajectory/gaps, write/maintain the 5-doc system, 
  co-author docs, proposals, specs, status reports,  3P updates, newsletters, 
  FAQs with structured workflows). Multi-tiered depth with adaptive 
  mid-scan adjustment. 
  Cross-skill integration with Synk182 and Solid8 via shared PULSE.json.
  Standalone; amplified with Synk182/Solid8.
  Supersedes: doc-coauthoring, internal-comms.
  
---

# DevCom5 — Developer Communications · 5
 Also known as **Logger**. 
> *Far from the woods and a lager, look farther. One might never glimpse a forest through the trees, never stood tall, aye, they'd bend at their knees*

**Three modes. One system. Adaptive depth that processes, and maintains overwatch.**

>**Cartographer** — Read/comprehend. Diagnose state, trajectory, gaps.
>**Architect** — Write/maintain the 5-doc system calibrated to project needs.
>**Scribe** — Co-author documents, proposals, specs, and internal comms through structured workflows with iterative refinement.

TRIGGER when/user mentions: "devcom5", "dc5", "logger",  
  documentation mentioned, onboarding to unfamiliar project,
  resuming after lapse, asked about status/trajectory, creating/updating
  docs, handover prep, writing proposals/specs/decision docs, drafting
  internal comms (status reports, 3P updates, newsletters, FAQs, incident
  reports), or user says "document this", "project status", "catch me up",
  "where were we", "write/update docs", "draft a proposal", "write a spec",
  "3P update", "status report", "write a newsletter". Trigger proactively
  on missing/stale docs. 

---

## The Digest System

The tracking system doesn't passively check a heartbeat — it actively
processes. Each interaction is a **digest cycle**: Intake → Breakdown →
Absorb → Eliminate. If nothing changed, it says so fast and moves on.
If everything changed, it escalates and digs deep.

Tracked via `docs/PULSE.json`. Read first, write last, every interaction.

```json
{
  "project": "Name",
  "pulse_version": "2.0",
  "classification": { "domain": "software", "maturity": "mvp", "complexity": "solo" },
  "heartbeat": {
    "last_seen": "ISO-8601-ET", "last_depth": "standard",
    "last_mode": "cartographer|architect|scribe",
    "last_context": "Brief summary", "session_count": 5
  },
  "health": {
    "docs_exist": [], "docs_missing": [], "docs_stale": [],
    "drift_flags": [], "last_audit": "ISO-8601-ET"
  },
  "cross_skill": {
    "synk_last_run": null, "synk_drift_detected": false,
    "solid8_last_run": null, "solid8_files_consolidated": 0,
    "pending_signals": []
  },
  "digest_history": [
    {
      "timestamp": "ISO-8601-ET", "depth_requested": "deep",
      "depth_actual": "standard", "reason": "mid-scan downshift: no changes detected",
      "summary": "Brief findings", "recommended_next": "action"
    }
  ]
}
```

### On Entry
1. Read PULSE.json (missing = first encounter → Deep)
2. Calculate depth via three-tier system (below)
3. Display status: `📡 DevCom5: [staleness] | Depth: [selected] | Docs: [n/5] | [flags]`

### On Exit
1. Update heartbeat + digest_history (max 10 entries, prune oldest)
2. Update health assessment
3. Write cross-skill signals
4. Display: `📡 Updated: [context] | Next: [recommendation]`

---

## Three-Tier Depth System

Depth is not static. It's determined, then **adjusted mid-operation**.

### Tier 1: Staleness Gauge (initial selection)

| Staleness | Default Depth |
|-----------|---------------|
| < 24h | **Pulse** — PULSE.json + tree (2 levels) + diff vs last digest |
| 1–7 days | **Standard** — + READMEs, configs, existing docs |
| 1–4 weeks | **Thorough** — + entry points, modules, tests. See `references/AUDIT_PROTOCOL.md` |
| > 1 month / new | **Deep** — + secondary source, POTIMP/archives, full drift. See `references/AUDIT_PROTOCOL.md` |

### Tier 2: Adaptive Mid-Scan (dynamic adjustment)

During any scan, the system evaluates whether its current depth is appropriate:

**Auto-Downshift** (save tokens when nothing's happening):
- Deep scan finds <5% file changes since last digest → downshift to Standard
- Thorough scan finds zero drift flags → downshift to Pulse-level report
- 3+ consecutive digests with "no significant changes" → suggest skipping to action

**Auto-Upshift** (catch problems before they compound):
- Pulse scan finds new files not in last snapshot → upshift to Standard
- Standard scan finds doc-reality drift → upshift to Thorough
- Any scan where file count changed >20% → upshift to Deep
- Missing PULSE.json fields or corruption → upshift to Deep (rebuild baseline)

**Always report shifts:**
`📡 Depth adjusted: Deep → Standard (only 2 files changed since last digest)`

### Tier 3: Cross-Skill Signal Modifiers (override upward only)

| Signal | Effect |
|--------|--------|
| `synk_drift_detected: true` | ≥ Thorough |
| `pending_signals` not empty | Process first, may raise depth |
| `drift_flags` not empty | ≥ Standard even if < 24h |
| Recent `solid8_last_run` | Check ARCHITECTURE element notes |

---

## Adaptive Engine

Classify once per project, reuse from PULSE. Reclassify on visible stage change.

| Axis | Values | Effect |
|------|--------|--------|
| **Domain** | software · creative · research · hybrid | Doc priority + vocabulary |
| **Maturity** | seed · mvp · production · legacy | Aggressiveness of documentation |
| **Complexity** | solo · small_team · distributed | Depth and audience assumptions |

Software → ARCHITECTURE heavy. Creative → USER_EXPERIENCE heavy. Research → PLANNING heavy.
Seed → PLANNING + INDEX. Production → full. Legacy → aggressive capture.
Solo → concise. Distributed → zero assumptions.

---

## Mode 1: Cartographer

Produce a **Project Audit Report** adapted to depth and classification.

### Full Audit (Standard+)
```
## Project Audit: [Name]
Classification: [D/M/C] | Depth: [level] (adjusted: [if changed]) | Sessions: [n]

### 1. Identity — one paragraph
### 2. Structure Map — interpreted directory overview
### 3. Current State — working / broken / in-progress / blocked
### 4. Doc Health — exist / missing / stale / drift
### 5. Trajectory — evidence + inference (marked which is which)
### 6. Actions — prioritized: (impact × urgency) / effort
```

### Pulse Check (< 24h, no changes)
3-5 line status. No full report.

### Comprehension Techniques
Entry-point tracing → Config-first → Doc-reality cross-check → Pattern recognition → POTIMP/archive awareness.
Full methodology: `references/AUDIT_PROTOCOL.md`

---

## Mode 2: Architect

Write/maintain the 5-doc system. Always Cartographer before Architect.

### The Five Documents (all in `/docs`)
Template: `references/UNIVERSAL_TEMPLATE.md`

| File | Purpose | Peak |
|------|---------|------|
| INDEX.md | Entry point, quick-start | Always |
| ARCHITECTURE.md | Technical map, element notes | MVP+ |
| USER_EXPERIENCE.md | User guides, vision | Creative / Prod+ |
| PLANNING.md | Backlog, ideas addendum | Seed / MVP |
| HISTORY.md | Session log + changelog (append-only, newest first) | MVP+ |

### Principles
Read before write. Update only on meaningful change. Append-only for HISTORY.
No scattered files → ARCHITECTURE Element Notes. Handover-first. Adaptive depth.

### End-of-Session
1. HISTORY → log + changelog | 2. PLANNING → backlog + ideas
3. ARCHITECTURE → element notes | 4. Headers in changed files
5. **PULSE.json → always**

---

## Mode 3: Scribe

Co-author documents, proposals, specs, and internal comms through
structured workflows.

### When Scribe Activates
- "write/draft a proposal/spec/decision doc/RFC/PRD"
- "write a 3P update / status report / newsletter / FAQ"
- "help me write [any structured document]"
- Any substantial writing task beyond simple doc maintenance

### Scribe Workflow: Co-Authored Documents

For proposals, specs, decision docs, technical docs:

**Stage 1 — Context Gathering:**
1. Ask meta-context: doc type, audience, desired impact, template/format, constraints
2. User info-dumps (stream-of-consciousness, links, files — whatever's efficient)
3. Ask 5-10 clarifying questions based on gaps
4. Exit when edge cases and trade-offs can be discussed without needing basics

**Stage 2 — Refinement & Structure:**
1. Agree on sections (suggest 3-5 based on doc type if user unsure)
2. Create scaffold with placeholders
3. Per section: clarify → brainstorm 5-20 options → user curates → draft → iterate
4. Use `str_replace` for edits, never reprint whole doc
5. After 3 stable iterations on a section: ask what can be removed
6. At 80%+ done: full-doc review for flow, redundancy, filler

**Stage 3 — Reader Testing:**
Predict 5-10 reader questions → test against doc (fresh context, no memory bleed):
- If sub-agents available: test automatically, report results
- If not: guide user to test in fresh conversation
Fix gaps found. Exit when reader questions are answered correctly.

### Scribe Workflow: Internal Communications

For 3P updates, newsletters, FAQs, status reports, incident reports:
Read `references/COMMS_FORMATS.md` for specific formatting and workflow per type.

**General flow:**
1. Identify comm type → load format from references
2. Clarify scope (team, time period, audience)
3. Gather info (user provides, or pull from available integrations)
4. Draft in strict format
5. Review for conciseness and accuracy

### Scribe Principles
- Direct and procedural, not salesy
- User has agency to skip stages or go freeform at any point
- Brainstorming stays in conversation, not artifacts
- Each iteration should make meaningful improvement
- Quality over speed

---

## Trifecta Signals

Full protocol: `references/TRIFECTA_PROTOCOL.md`

**Emits:** `drift_detected` → Synk | `architecture_changed` → Solid8 | `stale_project` → Both
**Consumes:** `sync_completed` (Synk) → ≥Standard | `files_consolidated` (Solid8) → update structure | `redundancy_found` (Solid8) → flag in audit

---

## Anti-Patterns
- Template-stamping empty sections on seed projects
- One-sentence sections (fold or skip)
- Ignoring existing READMEs (absorb them)
- Rewriting HISTORY (append-only)
- Silent findings (report drift)
- PULSE neglect (always update, even quick visits)
- Rushing Scribe stages (each exists for a reason)
- Printing entire docs for small edits (use str_replace)

---

*⁰ Formerly: project-docs (unnamed, pre-v1) → Logger v1.0 → DevCom5 v1.0.
The "5" honors the five-document system at its core. DevCom5 supersedes
the Anthropic example skills `doc-coauthoring` and `internal-comms`.*
