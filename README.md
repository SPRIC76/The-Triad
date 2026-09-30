<!-- Version 2.0 | Deps: none | Parent: The Triad (skills-trifecta README at 19a8722) | Path: . | Filename: README.md | Updated: 2026-09-30 01:15 ET — renamed The Triad; an agent skill pack for any host; freeware; versions named | Updated: 2026-09-30 01:37 ET — the address is SPRIC76/The-Triad; the MK1 Made footer | Updated: 2026-09-30 04:05 ET — v1.3: not-for pointers name kinds of work, verafox linked in The Proof Pack; versions 1.3 / 3.3 / 1.3 | Updated: 2026-09-30 13:43 ET — the pack's own checks named: a vocabulary ratchet over its Markdown and an optional private-name deny-list | Updated: 2026-09-30 15:59 ET — DevCom5's triggers say progress, plans and problems updates, not 3P updates -->
# The Triad — DevCom5, Synk182, Solid8

An **agent skill pack**: three skills that keep projects **understood**, **in sync**, and **lean** — coordinated via `docs/PULSE.json`. Each skill is a folder in the Agent Skills format (`SKILL.md`, with `references/` and `scripts/` beside it), so it works in any agent host that reads one. Known until commit 19a8722 as *Skills Trifecta*.

| Skill | Alias | Role | Core question |
|-------|-------|------|----------------|
| **DevCom5** | Logger | Docs, audit, comms | What does this project know about itself? |
| **Synk182** | Symphonous Strategist | Agreement between two copies | Are the copies in agreement? |
| **Solid8** | Denser / Shrinksmith | Consolidation | What can be unified without losing meaning? |

**Versions:** DevCom5 1.3 · Synk182 3.3 · Solid8 1.3 · Trifecta Protocol 3.0.

Full cross-skill protocol: [docs/TRIFECTA.md](docs/TRIFECTA.md)

## Install via skills.sh CLI

```bash
npx skills add SPRIC76/The-Triad
```

**Badge snippet:**

```markdown
[![skills.sh](https://skills.sh/b/SPRIC76/The-Triad)](https://skills.sh/SPRIC76/The-Triad)
```

## Install by hand (any agent host)

Copy `devcom5/`, `synk182/` and `solid8/` into the folder your agent reads skills from. Each folder stands alone; the three coordinate only through the project's own `docs/PULSE.json`.

**Requirements:** Python 3.10+ optional, for `synk182/scripts/synk_engine.py` and `solid8/scripts/denser_engine.py` (standard library only).

### Cursor

**Personal** skills (all projects) or **project** skills (repo-only):

```text
# Personal (~/.cursor/skills/)
devcom5/
synk182/
solid8/

# Project (.cursor/skills/<name>/)
```

### claude.ai and Claude Desktop

1. Package each skill folder as `<name>.skill` — a zip archive with `<name>/SKILL.md` at its root. [Skillshaper (sc2)](https://github.com/SPRIC76/Skillshaper)'s `package_dual.py` validates and packages in one step.
2. Upload each `.skill` in your skill settings, or drag it into Claude Desktop.
3. Confirm the three skills appear in your skills.

### Claude Code

Copy `devcom5/`, `synk182/` and `solid8/` into `~/.claude/skills/` (all projects) or `.claude/skills/` (one project).

## Host compatibility

These skills are markdown instruction packs (`SKILL.md` + optional `references/` + optional `scripts/`), so they work wherever an agent reads skill folders:

| Host | Works? | How to use |
|------|--------|------------|
| Any agent that reads Agent Skills folders | Yes | Copy each skill folder into its skills folder |
| Cursor | Yes | Copy folders into `~/.cursor/skills/` or `.cursor/skills/` |
| claude.ai / Claude Desktop | Yes | Upload or drag in a `.skill` package per skill |
| Claude Code | Yes | Copy folders into `~/.claude/skills/` or `.claude/skills/` |
| Other IDEs and agents with skill or plugin support | Usually | Import or copy each skill folder according to that host's skill format |
| Plain IDE with no agent skill system | Limited | Use docs/scripts manually; auto-trigger behavior will not apply |

For any other host, the one requirement is support for instruction-based agent skills. Without it, you can still reuse the workflow docs and Python scripts by hand.

## Recommended workflows

- **Full trifecta:** DevCom5 (Cartographer) → Synk182 → Solid8 → DevCom5 (Architect)
- **Docs + lean:** DevCom5 → Solid8 → DevCom5
- **Docs + sync:** DevCom5 (Cartographer) → Synk182 → DevCom5 (Architect)
- **Sync + lean:** Synk182 → Solid8

## Safety (general use)

These skills **guide an AI agent** — they do not auto-run destructive actions.

- **Synk182** and **Solid8** require explicit user approval for merges and consolidation.
- Synk182's engine writes nothing until it applies plan items you approved, backs up each file first, and refuses an item whose path leaves the copies or whose target changed since the plan was written.
- Archives are written under `[project]/ARCHIVE/` before risky operations.
- Review archives and proposals before deleting anything.

---

## DevCom5 — Logger

> *Far from the woods and a lager, look farther. One might never glimpse a forest through the trees, never stood tall, aye, they'd bend at their knees*

**Three modes:** Cartographer (read/diagnose) · Architect (5-doc system) · Scribe (proposals, specs, internal comms).

**Highlights:**
- Adaptive depth: Pulse → Standard → Thorough → Deep (can shift mid-scan)
- Digest system via `docs/PULSE.json` — read first, write last
- Five-document framework in `/docs`: INDEX, ARCHITECTURE, USER_EXPERIENCE, PLANNING, HISTORY
- Maintains a project's existing documentation system instead of creating a parallel one
- Status: `📡 DevCom5: [staleness] | Depth: … | Docs: [n/5]`

**Triggers:** `devcom5`, `dc5`, `logger`, documentation, project status, catch-up, README and changelog updates, proposals, progress, plans and problems updates, newsletters, and more (see the description in `devcom5/SKILL.md`).

**Not DevCom5:** proving a change works or grading its evidence ([verafox](https://github.com/SPRIC76/The-Proof-Pack), in The Proof Pack), a person's own knowledge base outside a project (a knowledge-search skill), rendering diagrams (a diagramming skill).

**References:** `devcom5/references/` — audit protocol, universal template, comms formats.

---

## Synk182 — The Symphonous Strategist

> *Categorically and formally formulated to link between sink, sync, and Blink182*

**Highlights:**
- Any two copies of a project: a sandbox or upload, a mounted or synced folder, a git worktree, another machine's copy, a deployed copy
- Similarity spectrum 0% to >100% with six-layer verification
- 60% merge threshold; mandatory review above 60%; supersets never auto-resolved
- Backs up every file before overwriting (`[project]/ARCHIVE/synk-[timestamp]/`, with manifest and rollback notes), applies only approved items, and rolls back any copy that fails verification
- Status: `🔄` for scans, rigor shifts, completion

**Not Synk:** Single-file edits, in-directory moves, redundancy consolidation (→ Solid8), git branch merges (→ git), repo and worktree rules (→ your repository's own rules), what a version can do rather than what its files hold (→ [verafox](https://github.com/SPRIC76/The-Proof-Pack), in The Proof Pack).

**Script:**

```bash
python synk182/scripts/synk_engine.py USER_COPY WORKING_COPY                    # dashboard, read-only
python synk182/scripts/synk_engine.py USER_COPY WORKING_COPY --plan plan.json   # numbered plan, nothing written
python synk182/scripts/synk_engine.py USER_COPY WORKING_COPY --apply plan.json --approve 2,5
```

---

## Solid8 — The Shrinksmith Alchemist

**Call me Denser** if it's not getting through.

> *"Similar to a dancer phonetically, although I'm not a dancer. I do not dance, nor will I chance to lapse with you in proper trance."*

**Highlights:**
- Tier S–D similarity pipeline; three laws (no delete without approval, lossless merge, archive first)
- Finds version (`_v2`), copy (`- Copy`, `(2)`) and backup (`.bak`, `.old`) sprawl; compares Markdown by section, JSON by structure, binaries by hash; treats archive and POTIMP folders as intentional, and never proposes a merge inside one
- **Solid8** = solid + ∞ rotated — tames endless project entropy
- Formerly Denser v1.0
- Status: `⚗️`

**Not Solid8:** two copies of a project (→ Synk182), absorbing an outside tool as your own (→ [verafox](https://github.com/SPRIC76/The-Proof-Pack) Mutate, in The Proof Pack), memory notes (→ your memory-consolidation tool).

**Script:** `python solid8/scripts/denser_engine.py <target_dir> [--details N] [--json proposal.json]` (read-only analysis; archives before any change).

---

## Repository layout

```text
devcom5/     SKILL.md + references/
synk182/     SKILL.md + references/ + scripts/
solid8/      SKILL.md + references/ + scripts/
docs/        TRIFECTA.md
tests/       test_triad.py — kept tests for the engines, the skill folders and this pack (never shipped inside a skill);
             the pack's own checks: every name-shaped token in its Markdown must be in a committed vocabulary,
             and TRIAD_PRIVATE_NAMES may name a deny-list kept outside the repository
```

Run the tests from this folder: `python -B -m unittest discover -s tests -v`

## License

Freeware — see [LICENSE](LICENSE). Copyright (c) 2026 MK1 Enterprise. Free to download and use; please link to this repository rather than rehosting it. Versions up to commit 19a8722 were released under MIT and keep it.

---

The Triad · [Freeware](LICENSE)

[MK1 Made](https://mk1made.us) • *deliberately designed, intelligently refined*
<p align="right">Artificer Intelligence</p>
