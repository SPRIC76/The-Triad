# Communications Formats Reference
<!-- DevCom5 v1.3 | 2026-02-10 | Scribe mode reference | Updated: 2026-09-30 04:05 ET — header follows the skill's version | Updated: 2026-09-30 17:09 ET — 3P defined in its heading -->

Scribe mode uses these formats for internal communications.

---

## Progress, Plans and Problems (3P) Updates

**Audience:** Executives, leadership, teammates with some context.
**Read time:** 30-60 seconds. **Tone:** Matter-of-fact, data-driven.

### Workflow
1. Confirm team name and time period (usually weekly)
2. Gather: Progress (past week), Plans (next week), Problems (blockers)
3. Draft in strict format. Metrics where possible.

### Format (strict — never deviate)
```
[emoji] [Team Name] ([Date Range])
Progress: [1-3 sentences. Focus: shipped, milestones, completions.]
Plans: [1-3 sentences. Focus: top priorities, high-urgency items.]
Problems: [1-3 sentences. Focus: blockers, resource gaps, risks.]
```

**Scale rule:** Bigger team = less granular. Match granularity to scope.

---

## Company Newsletter

**Audience:** Entire company. **Length:** ~20-25 bullets.
**Tone:** "We" tense. Short, linkable.

### Workflow
1. Gather: announcements, shipped work, leadership posts, press, milestones
2. Cluster into 3-5 sections
3. Each bullet: 1-2 sentences max. Include links where possible.
4. Prioritize company-wide impact over team-specific details.

### Format
```
:megaphone: Company Announcements
- [Bullet with link]

:dart: Progress on Priorities
- [Area]
    - [Sub-bullet]

:pillar: Leadership Updates
- [Bullet with link]

:thread: Social / Recognition
- [Bullet]
```

---

## FAQ Compilations

**Audience:** All employees. **Tone:** Professional, approachable.

### Format
```
- **Q:** [Question — 1 sentence]
  **A:** [Answer — 1-2 sentences. Link to source if available.]
```

Base answers on official communications. Flag uncertainty clearly.

---

## Status Reports / Project Updates

**Audience:** Stakeholders, sponsors.

### Format
```
## [Project Name] Status Report — [Date]
**Status:** 🟢 On Track | 🟡 At Risk | 🔴 Blocked

### Accomplishments
- [Completed items with metrics]

### Risks & Issues
- [Risk]: [Impact] | [Mitigation]

### Next Period
- [Planned work with owners]

### Decisions Needed
- [Blockers requiring stakeholder input]
```

---

## Incident Reports

**Audience:** Technical leads, affected stakeholders. **Tone:** Factual, blameless.

### Format
```
## Incident Report: [Title] — [Date]
**Severity:** P0-P3 | **Duration:** [start-end] | **Impact:** [who/what]

### Timeline
- [HH:MM] [Event/Response/Resolution]

### Root Cause
[Technical explanation, blameless]

### Action Items
- [ ] [Prevention measure] — Owner: [name] — Due: [date]
```

---

## General Internal Communications

For anything not matching above: ask target audience, purpose, tone, format.
Apply: clear, concise, active voice, important info first, include links.
