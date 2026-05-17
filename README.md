# Skills Trifecta — DevCom5, Synk182, Solid8

Three [Cursor](https://cursor.com) / Claude **agent skills** that keep projects **understood**, **in sync**, and **lean** — coordinated via `docs/PULSE.json`.

| Skill | Alias | Role | Core question |
|-------|-------|------|----------------|
| **DevCom5** | Logger | Docs, audit, comms | What does this project know about itself? |
| **Synk182** | Symphonous Strategist | Bidirectional sync | Are the copies in agreement? |
| **Solid8** | Denser / Shrinksmith | Consolidation | What can be unified without losing meaning? |

Full cross-skill protocol: [docs/TRIFECTA.md](docs/TRIFECTA.md)

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

**Voice:** Reflective, structured, overwatch-oriented.

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

*Note: The "A. Blinken" attribution is fictional wordplay — not affiliation with any real person.*

**Voice:** Surgical, paranoid-safe, symphonic (precision + harmony). The name is the joke: sink ↔ sync.

**Highlights:**
- Similarity spectrum 0% to >100% with six-layer verification
- 60% merge threshold; mandatory review above 60%; ultra-careful superset handling
- Three-tier backup, auto-rollback, archives at `[project]/ARCHIVE/synk-[timestamp]/`
- Status: `🔄` for scans, rigor shifts, completion

**Not Synk:** Single-file edits, in-directory moves, redundancy consolidation (→ Solid8).

**Script:** `python synk182/scripts/synk_engine.py` (optional engine for large projects).

---

## Solid8 — The Shrinksmith Alchemist

> *"Similar to a dancer phonetically, although I'm not a dancer. I do not dance, nor will I chance to lapse with you in proper trance."*

**Call me Denser** if it's not getting through.

**Voice:** Alchemist / distiller — **distillation, not deletion**.

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
