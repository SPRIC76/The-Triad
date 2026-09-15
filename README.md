# Skills Trifecta — DevCom5, Synk182, Solid8

Three [Cursor](https://cursor.com) / Claude **agent skills** that keep projects **understood**, **in sync**, and **lean** — coordinated via `docs/PULSE.json`.

| Skill | Alias | Role | Core question |
|-------|-------|------|----------------|
| **DevCom5** | Logger | Docs, audit, comms | What does this project know about itself? |
| **Synk182** | Symphonous Strategist | Agreement between two copies | Are the copies in agreement? |
| **Solid8** | Denser / Shrinksmith | Consolidation | What can be unified without losing meaning? |

Full cross-skill protocol: [docs/TRIFECTA.md](docs/TRIFECTA.md)

## Install via skills.sh CLI

```bash
npx skills add SPRIC76/skills-trifecta
```

**Badge snippet:**

```markdown
[![skills.sh](https://skills.sh/b/SPRIC76/skills-trifecta)](https://skills.sh/SPRIC76/skills-trifecta)
```

## Install (Cursor)

Copy each skill folder to **personal** skills (all projects) or **project** skills (repo-only):

```text
# Personal (~/.cursor/skills/)
devcom5/
synk182/
solid8/

# Project (.cursor/skills/<name>/)
```

**Requirements:** Python 3.10+ optional, for `synk182/scripts/synk_engine.py` and `solid8/scripts/denser_engine.py` (standard library only).

## Install (Claude)

### claude.ai and Claude Desktop

1. Package each skill folder as `<name>.skill` — a zip archive with `<name>/SKILL.md` at its root. [SC2](https://github.com/SPRIC76/sc2)'s `package_dual.py` validates and packages in one step.
2. Upload each `.skill` in your skill settings, or drag it into Claude Desktop.
3. Confirm the three skills appear in your skills.

### Claude Code

Copy `devcom5/`, `synk182/` and `solid8/` into `~/.claude/skills/` (all projects) or `.claude/skills/` (one project).

## IDE and agent compatibility

These skills are markdown instruction packs (`SKILL.md` + optional `references/` + optional `scripts/`), so they can work in most agent-capable environments:

| Environment | Works? | How to use |
|-------------|--------|------------|
| Cursor | Yes | Copy folders into `~/.cursor/skills/` or `.cursor/skills/` |
| claude.ai / Claude Desktop | Yes | Upload or drag in a `.skill` package per skill |
| Claude Code | Yes | Copy folders into `~/.claude/skills/` or `.claude/skills/` |
| Other IDEs with skill/plugin support | Usually | Import/copy each skill folder according to that IDE's skill format |
| Plain IDE with no agent skill system | Limited | Use docs/scripts manually; auto-trigger behavior will not apply |

For non-Cursor, non-Claude IDEs, the critical requirement is support for instruction-based agent skills. If unsupported, you can still reuse the workflow docs and Python scripts manually.

## Recommended workflows

- **Full trifecta:** DevCom5 (Cartographer) → Synk182 → Solid8 → DevCom5 (Architect)
- **Docs + lean:** DevCom5 → Solid8 → DevCom5
- **Docs + sync:** DevCom5 (Cartographer) → Synk182 → DevCom5 (Architect)
- **Sync + lean:** Synk182 → Solid8

## Safety (general use)

These skills **guide an AI agent** — they do not auto-run destructive actions.

- **Synk182** and **Solid8** require explicit user approval for merges and consolidation.
- Synk182's engine writes nothing until it applies plan items you approved, and backs up each file first.
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

**Triggers:** `devcom5`, `dc5`, `logger`, documentation, project status, catch-up, proposals, 3P updates, newsletters, and more (see the description in `devcom5/SKILL.md`).

**References:** `devcom5/references/` — audit protocol, universal template, comms formats.

---

## Synk182 — The Symphonous Strategist

> *Categorically and formally forumulated to link between sink, sync, and Blink182*

**Highlights:**
- Any two copies of a project: a sandbox or upload, a mounted or synced folder, a git worktree, another machine's copy, a deployed copy
- Similarity spectrum 0% to >100% with six-layer verification
- 60% merge threshold; mandatory review above 60%; supersets never auto-resolved
- Backs up every file before overwriting (`[project]/ARCHIVE/synk-[timestamp]/`, with manifest and rollback notes), applies only approved items, and rolls back any copy that fails verification
- Status: `🔄` for scans, rigor shifts, completion

**Not Synk:** Single-file edits, in-directory moves, redundancy consolidation (→ Solid8), git branch merges (→ git).

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
- Finds version (`_v2`), copy (`- Copy`, `(2)`) and backup (`.bak`, `.old`) sprawl; compares Markdown by section, JSON by structure, binaries by hash; treats archive and POTIMP folders as intentional
- **Solid8** = solid + ∞ rotated — tames endless project entropy
- Formerly Denser v1.0
- Status: `⚗️`

**Script:** `python solid8/scripts/denser_engine.py <target_dir> [--details N] [--json proposal.json]` (read-only analysis; archives before any change).

---

## Repository layout

```text
devcom5/     SKILL.md + references/
synk182/     SKILL.md + references/ + scripts/
solid8/      SKILL.md + references/ + scripts/
docs/        TRIFECTA.md
```

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2025 SPRIC76.
