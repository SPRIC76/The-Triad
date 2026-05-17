# Skills Trifecta — DevCom5, Synk182, Solid8

Three [Cursor](https://cursor.com) / Claude **agent skills** that keep projects **understood**, **in sync**, and **lean** — coordinated via `docs/PULSE.json`.

| Skill | Alias | Role | Core question |
|-------|-------|------|----------------|
| **DevCom5** | Logger | Docs, audit, comms | What does this project know about itself? |
| **Synk182** | Symphonous Strategist | Bidirectional sync | Are the copies in agreement? |
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

**Requirements:** Python 3.10+ optional, for `synk182/scripts/synk_engine.py` and `solid8/scripts/denser_engine.py`.

## Install (Claude Desktop)

Use one of these methods:

### Method A: Drag-and-drop package (if you create `.skill` files)

1. Package each skill folder as `<name>.skill` (zip archive format).
2. Open Claude Desktop and drag the `.skill` file into the app.
3. Confirm the skill is installed and visible in your available skills.

### Method B: Manual folder install

1. Locate your Claude skills directory from Claude settings or docs.
2. Copy `devcom5/`, `synk182/`, and `solid8/` into that skills directory.
3. Restart Claude Desktop so it reloads skills.

If your Claude environment uses managed skill paths (for example `/mnt/skills/user/`), place each skill folder there.

## IDE and agent compatibility

These skills are markdown instruction packs (`SKILL.md` + optional `references/` + optional `scripts/`), so they can work in most agent-capable environments:

| Environment | Works? | How to use |
|-------------|--------|------------|
| Cursor | Yes | Copy folders into `~/.cursor/skills/` or `.cursor/skills/` |
| Claude Desktop | Yes | Drag `.skill` package or copy folders into Claude skills path |
| Claude Code / agent runtimes | Yes | Place folders in the runtime skills directory |
| Other IDEs with skill/plugin support | Usually | Import/copy each skill folder according to that IDE's skill format |
| Plain IDE with no agent skill system | Limited | Use docs/scripts manually; auto-trigger behavior will not apply |

For non-Cursor, non-Claude IDEs, the critical requirement is support for instruction-based agent skills. If unsupported, you can still reuse the workflow docs and Python scripts manually.

## Recommended workflows

- **Full trifecta:** DevCom5 (Cartographer) → Synk182 → Solid8 → DevCom5 (Architect)
- **Docs + lean:** DevCom5 → Solid8 → DevCom5
- **Sync + lean:** Synk182 → Solid8

## Safety (general use)

These skills **guide an AI agent** — they do not auto-run destructive actions.

- **Synk182** and **Solid8** require explicit user approval for merges and consolidation.
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
- Status: `📡 DevCom5: [staleness] | Depth: … | Docs: [n/5]`

**Triggers:** `devcom5`, `dc5`, `logger`, documentation, project status, catch-up, proposals, 3P updates, newsletters, and more (see `devcom5/SKILL.md`).

**References:** `devcom5/references/` — audit protocol, universal template, comms formats.

---

## Synk182 — The Symphonous Strategist

> *Categorically and formally forumulated to link between sink, sync, and Blink182*

**Highlights:**
- Similarity spectrum 0% to >100% with six-layer verification
- 60% merge threshold; mandatory review above 60%; ultra-careful superset handling
- Three-tier backup, auto-rollback, archives at `[project]/ARCHIVE/synk-[timestamp]/`
- Status: `🔄` for scans, rigor shifts, completion

**Not Synk:** Single-file edits, in-directory moves, redundancy consolidation (→ Solid8).

**Script:** `python synk182/scripts/synk_engine.py` (optional engine for large projects).

---

## Solid8 — The Shrinksmith Alchemist

**Call me Denser** if it's not getting through.

> *"Similar to a dancer phonetically, although I'm not a dancer. I do not dance, nor will I chance to lapse with you in proper trance."*

**Highlights:**
- Tier S–D similarity pipeline; three laws (no delete without approval, lossless merge, archive first)
- **Solid8** = solid + ∞ rotated — tames endless project entropy
- Formerly Denser v1.0
- Status: `⚗️`

**Script:** `python solid8/scripts/denser_engine.py <target_dir>` (optional engine).

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
