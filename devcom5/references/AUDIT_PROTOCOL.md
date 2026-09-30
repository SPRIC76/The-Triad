# Audit Protocol
<!-- DevCom5 v1.3 | 2026-02-10 | Updated: 2026-09-30 04:05 ET — header follows the skill's version | Updated: 2026-09-30 17:09 ET — staging folders named by their job -->

Read for Thorough/Deep scans. Pulse/Standard use SKILL.md instructions only.

## Adaptive Depth: Mid-Scan Rules

Before completing each phase, evaluate whether depth should shift:

**Downshift triggers** (save tokens):
- Phase 1 finds <5% file changes since last digest → downshift one level
- Phase 2 finds zero drift between docs and reality → compress report
- 3+ consecutive digests with "no significant changes" → suggest skip-to-action

**Upshift triggers** (catch problems):
- Phase 1 finds >20% file count change → upshift to Deep
- Phase 2 finds doc-reality drift → upshift to at least Thorough
- New files not in last snapshot → upshift one level
- Corrupted/missing PULSE fields → upshift to Deep (rebuild baseline)

Always report shifts: `📡 Depth adjusted: [from] → [to] ([reason])`

---

## Phase 1: Structural Scan

**Step 1 — Directory Inventory** (tree depth 3-4):
Categorize: source dirs, configs, docs, assets, tests, archives and staging folders,
build artifacts, orphan root files. Compare against last digest snapshot.

**Step 2 — Technology Fingerprint** from configs + extensions:
Language(s), frameworks, package manager, build system, runtime reqs, services.

**Step 3 — Maturity Signals:**

| Signal | Indicates |
|--------|-----------|
| No tests | Seed/early MVP |
| `.env.example` | MVP+ (deploy-aware) |
| CI/CD configs | Production |
| Version archives / staging folders | Mature iteration |
| Stale lock files | Potentially abandoned |
| High TODO density | MVP with known debt |

**→ Evaluate downshift/upshift before Phase 2.**

## Phase 2: Content Analysis

**Step 4 — Entry Point Trace:**
Find main/index/app → follow 2-3 import levels. One-paragraph architecture summary.

**Step 5 — Config Deep-Read:**
All configs in full. These reveal architecture faster than source.

**Step 6 — Documentation Audit:**
Every existing doc. Assess: accuracy, completeness, freshness, audience, drift.
**Drift detection is highest-value finding. Always flag explicitly.**

**Step 7 — Trajectory Mining:**
Git log (if accessible), changelogs, staging folders and ideas, backlog/TODO files,
archive folders, conversation/digest history.

**→ Evaluate downshift/upshift before Phase 3.**

## Phase 3: Synthesis

**Step 8 — Classification:**
Domain/Maturity/Complexity. State confidence. Ambiguous → pick the
classification that produces more useful docs.

**Step 9 — State Assessment:**
Working / Broken-Incomplete / In-Progress / Blocked / At-Risk.
Evidence-based; mark speculation clearly.

**Step 10 — Gap Analysis:**

| Gap | Question |
|-----|----------|
| Knowledge | What does the builder know that isn't written? |
| Onboarding | Could someone new get this running from docs alone? |
| Architecture | Are key decisions explained or just implemented? |
| Planning | Is the roadmap visible or only in someone's head? |
| History | Could you reconstruct why things are this way? |

**Step 11 — Prioritize Actions:**
Rank: (impact × urgency) / effort.
Seed → capture intent. Production → accuracy. Legacy → everything.

## Report Rules

- Depth-appropriate tone: Thorough = structured, 1-2 ¶/section. Deep = comprehensive.
- Say "unclear from scan" — never guess.
- Lead with conflicts and drift.
- Acknowledge good shape when earned.
