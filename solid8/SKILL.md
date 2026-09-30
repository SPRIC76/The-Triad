---
name: solid8
description: >-
  Solid8 (Denser): consolidates a project's sprawl without losing anything.
  Finds exact duplicates, supersets, near-duplicates and overlap across files -
  version sprawl such as _v1 and _v2, copy sprawl such as - Copy or (2), backup
  sprawl such as .bak or .old, and a file sitting beside a zip of itself - then
  proposes the categorically minimum structure that still holds the project's
  full intent and scope, with a diff for every merge and the originals archived
  first under ARCHIVE/. Use whenever the user says solid8, s8 or denser; asks
  to consolidate, deduplicate, merge similar files, clean up, shrink or reduce
  sprawl; says there are too many files, copies or versions; or when a scan
  shows obvious redundancy, or older versions may hold overlooked integrations
  or undervalued assets. Standalone; works with DevCom5 and Synk182 through
  docs/PULSE.json. Not for keeping two copies of a project in agreement
  (Synk182), absorbing an outside tool as your own (verafox Mutate), or memory
  notes (a memory-consolidation tool).
license: Freeware
metadata:
  version: "1.3"
  updated: "2026-09-30"
---

# Solid8 — The 'Shrinksmith' Alchemist 
 "Call me **Denser** if it's not getting through to you."
> *Similar to a dancer phonetically, although I'm not a dancer. I do not dance, nor will I chance to lapse with you in proper trance.*

**Turns mess and sprawl into essence; Distillation, not deletion.**

**"Consolidated" means:** (for all intents and purposes of this skill)
the categorically minimum necessary structure/framework/directory/files/data/docs 
that hierarchically convey and contain the full intent and scope of the project.
Common synonyms (explicit/context-dependent): unite, merge, combine, integrate, unify, 
strengthen, centralize, concentrate, compile, collate, organize.

**Missing or consumable components count too:** an older version can hold an integration or asset the current one lost. Surface it; never let consolidation bury it.


## Similarity Tiers

| Tier | Similarity | Action | Review |
|------|-----------|--------|--------|
| S | 100% (hash) | Auto-flag, safe to remove | Confirmation only |
| A | >100% | Merge to superset | ⚠️ Full diff |
| B | 80-99% | Intelligent merge | Mandatory diff |
| C | 60-79% | Analyze & propose | User assessment |
| D | 30-59% | Flag only | Informational |
| — | <30% | Ignore | — |

## Pipeline

### Phase 1: Discovery
**Per-file fingerprint:** SHA-256, size, line count, extension, name pattern, modified timestamp.

**Pattern detection:** Version sprawl (`_v1`/`_v2`), copy sprawl (`- Copy`/`(2)`),
backup sprawl (`.bak`/`.old`), archive sprawl (file + zip of same).

### Phase 2: Comparison

| Type | Method | Fallback |
|------|--------|----------|
| Text/Code | Line-set Jaccard + superset detection | Hash |
| Markdown | Section-aware: each line compared under its heading | Line set |
| JSON | Structural: flattened key paths and values, order ignored | Line set if it does not parse |
| YAML | Line set (structural only by hand) | Hash |
| Binary | Hash only — never a content tier | Size |

Superset detection: File A contains every line of B + more → A is superset.
A backup (`.bak`, `.old`, `.backup`, `.orig`, `~`) is compared as the kind of file it backs up: `cfg.json.bak` as JSON, `guide.md.bak` as Markdown, `doc.pdf.bak` as a binary, by hash only. Every trailing marker is removed, so `cfg.json.bak.old` and `cfg.json.orig~` both meet `cfg.json`.

### Phase 3: Classification → Tier assignment, cluster grouping.

### Phase 4: Proposal
```
⚗️ Consolidation Proposal: [Name]
🟢 Exact dupes: [n] | 🟡 Supersets: [n] | 🔵 Near-dupes: [n] | ⚪ Overlap: [n]
📦 Reduction: ~[n]% fewer files | Review items: [n]
[Per-tier detail with diffs and preservation notes]
```

## Three-Tier Adaptive Depth

### Tier 1: Baseline from PULSE
| Condition | Scan Level |
|-----------|-----------|
| `solid8_last_run` < 7 days, no signals | **Quick** — hash comparison only, flag exact dupes |
| 1-4 weeks or new files synced | **Standard** — full similarity analysis |
| >1 month or stale_project signal | **Thorough** — deep content comparison + version sprawl analysis |

### Tier 2: Adaptive Mid-Scan
**Downshift:** Thorough scan finds <3 files with >60% similarity → compress to Quick report.
**Upshift:** Quick scan finds >5 hash-duplicate clusters → escalate to Standard.
Standard scan finds superset relationships → escalate to Thorough for those clusters.

**Report shifts:** `⚗️ Depth adjusted: Thorough → Quick (project already lean)`

### Tier 3: Cross-Skill Signals
`new_files_synced` from Synk182 → ≥ Standard (check new overlaps).
`architecture_changed` from DevCom5 → check if structure changes obsoleted files.
`stale_project` from DevCom5 → Thorough.
`docs_created` from DevCom5 → the new docs are doc-worthy; never consolidate them.

## Safety: Three Laws

1. **Nothing deleted without explicit user approval.**
2. **Every consolidation provably lossless.** Merged = all unique content from both.
3. **Archive before action.** `[project]/ARCHIVE/solid8-[timestamp]/` with manifest + originals + rollback.md.

| Tier | Auto-Execute |
|------|-------------|
| S | After batch confirmation |
| A-C | Never |
| D | N/A (info only) |

## Version Sprawl Handler

On version sequences (`_v1` through `_vN`):
1. Identify canonical (highest version — but verify: largest? most recent?)
2. Diff canonical vs predecessors: strict subsets? unique content?
3. Classify: pure subset → archive | unique content → review | diverged → flag
4. Propose with evidence.

## Context Awareness

**POTIMP:** Intentional staging. Don't flag unless changes fully absorbed into main. The engine reports a POTIMP file only as an exact duplicate or as the subset of a main file.
**Archives:** Intentionally preserved. Flag only if exact dupe of current. The engine applies this to any folder named `ARCHIVE`, `Archive`, `Archives` or `archive`.
**Doc files:** Respect DevCom5 flags. Don't consolidate doc-worthy files.
Flag scattered READMEs for 5-doc absorption.
**A copy is not always sprawl:** a folder that is another environment's copy of the project (a worktree, a deployed copy, another machine's) is Synk182's to reconcile, not Solid8's to collapse.
**Outside tools and memory notes are not sprawl either:** absorbing someone else's skill or tool as your own is Mutate's job (verafox, in The Proof Pack); a memory folder is your memory-consolidation tool's.
**Inside an archive, nothing is consolidated:** two archived files, one a superset of the other, are left as they are. The engine reports a protected file only as an exact duplicate, or as the subset of a live file.

## Scripts

**`scripts/denser_engine.py`** — the analysis engine. Read-only except `create_archive` and `--pulse`.

```bash
python scripts/denser_engine.py <target_dir>                       # tier counts
python scripts/denser_engine.py <target_dir> --details 20          # plus the top clusters with files and similarity
python scripts/denser_engine.py <target_dir> --json proposal.json  # full proposal for review or tooling
python scripts/denser_engine.py <target_dir> --pulse               # record the scan in docs/PULSE.json
```

- `DenserEngine(target).scan()` → `.compare_all()` → `.generate_proposal()`; `.create_archive(files, archive_dir, reason)` copies originals with `manifest.json` and `rollback.md` before any merge or removal.
- Skips `.git`, `node_modules`, build output, caches, and every dot-prefixed folder or file; groups candidates by hash, by base name (version, copy and backup markers removed) within a folder, and by size, and pairs a version, copy or backup name with its base name in any other folder. A copy number has one to three digits, so `(2024)` is a year, not a copy. A junction or link inside the target is named and never followed, so a loop cannot repeat files.
- A `--json` file that cannot be written (a missing folder, or a folder in its place), or an empty `--json` name, is answered with the reason and exit 1, after the report; a `--pulse` beside it still records the scan.
- `--pulse` writes `solid8_last_run` and `solid8_redundancy_map`, emits `redundancy_found` to DevCom5 when anything is found, keeps every other key, and never touches a PULSE that does not parse or holds no JSON object, and says so. A wrong-typed field (`"pending_signals": null`) is treated as empty with a note; when no PULSE exists one is created holding only `cross_skill`, which DevCom5 fills out at its next Deep pass. When `docs` is a file, or the PULSE cannot be written, the scan still reports and says the PULSE was not written.

The SKILL.md methodology applies whether using the engine or manual analysis.

## Trifecta Signals

Full protocol: [references/TRIFECTA_PROTOCOL.md](references/TRIFECTA_PROTOCOL.md)

**Emits:** `files_consolidated` → DevCom5 | `redundancy_found` → DevCom5 | `archive_recommended` → DevCom5 | `consolidation_complete` → Synk182
**Consumes:** `new_files_synced` (Synk182) → rescan | `architecture_changed` (DevCom5) → check obsolescence | `stale_project` (DevCom5) → full assessment | `docs_created` (DevCom5) → protect
**PULSE writes:** `solid8_last_run`, `solid8_files_consolidated`, `solid8_redundancy_map`

## Under-the-Hood Display
**Scan:** `⚗️ Scanning [n] files | Clusters: [n]`
**Proposal:** `⚗️ Dupes: [n] | Supersets: [n] | Near: [n] | Reduction: ~[n]%`
**Complete:** `⚗️ Consolidated: [n] archived, [n] merged | Rollback: [path]`

## Anti-Patterns
- Deleting without archiving
- Treating all versions as redundant
- Ignoring POTIMP/staging
- Consolidating across environments (Synk182's job)
- Merging without review above Tier S
- Byte-comparing docs (use section-aware diff)
- Consolidating build artifacts
- Calling something a duplicate by its name alone — compare the content

---

*⁰ Formerly: Denser v1.0 (unnamed concept, pre-v1) → Solid8 v1.0 → Solid8 v1.1 (2026-09-15: triggers moved into the description; engine fixes for backups, copy names, binaries, JSON and Markdown, archives, and Windows consoles) → Solid8 v1.2 (2026-09-30: part of The Triad; the description says what it is not for beside Synk182, verafox and a memory tool; the engine no longer proposes a superset pair that lies wholly inside an archive; freeware) → Solid8 v1.3 (2026-09-30: version, copy and backup sprawl is found across folders; a backup, with every trailing marker removed, is compared as the kind of file it backs up, so a backup of a binary is binary; a year in parentheses is not a copy number; a wrong-typed PULSE field is treated as empty with a note; a target that is not a folder is an error; --pulse warns instead of failing when docs is a file, and --json answers a file it cannot write, or an empty name, with the reason; a junction or link is named and not followed, and a signal stamped with Z is pruned on every Python; the not-for pointers name kinds of work rather than private skills).
"Solid8" — solid as in consolidated, 8 as in the infinity symbol ∞ rotated,
representing the endless cycle of project entropy that this skill tames.
The Denser alias persists for when subtlety isn't working.*
