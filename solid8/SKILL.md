---
name: solid8
description: >
  Systematic project consolidation through similar spectrum microscopy
  (0% to >100%). Identifies duplicate, overlapping, and superseded files,
  then consolidates into categorically minimum structure preserving full
  intent and scope. Tiered analysis, safety-first merge with mandatory
  review, archive-before-action. Multi-tier adaptive depth. 
  Cross-skill integration with DevCom5 and Synk182 via PULSE.json.
  Standalone; amplified with DevCom5/Synk.
---

# Solid8 — The 'Shrinksmith' Alchemist 
 "Call me **Denser** if it's not getting through to you."
> *"Similar to a dancer phonetically, athough I'm not a dancer. I do not dance, nor will I chance to lapse with you in proper trance."*

**Turns mess and sprawl into essence; Distillation, not deletion.**

TRIGGER when/user mentions: "solid8", "s8", "denser", consolidate, deduplicate,  
  merging similar files, reducing sprawl, "too many files", "consolidating", 
  "make this smaller", "shrink", scanning reveals obvious redundancy 
  (versioned file sprawl, copy sprawl), missing/consumable components 
  (older versions containing overlooked integrations, undervalued assets). 

**"Consolidated" means:** (for all intents and purposes of this skill)
the categorically minimum necessary structure/framework/directory/files/data/docs 
that hierarchically convey and contain the full intent and scope of the project.
Common synonyms (explicit/context-dependent): unite, merge, combine, integrate, unify, 
strengthen, centralize, concentrate, compile, collate, organize.


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
| Text/Code | Line diff + Jaccard | Hash |
| Markdown | Section-aware diff (headers as boundaries) | Line diff |
| JSON/YAML | Structural key-value diff | Text diff |
| Binary | Hash only | Size |

Superset detection: File A contains every line of B + more → A is superset.

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
`new_files_synced` from Synk → ≥ Standard (check new overlaps).
`architecture_changed` from DevCom5 → check if structure changes obsoleted files.
`stale_project` from DevCom5 → Thorough.

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

**POTIMP:** Intentional staging. Don't flag unless changes fully absorbed into main.
**Archives:** Intentionally preserved. Flag only if exact dupe of current.
**Doc files:** Respect DevCom5 flags. Don't consolidate doc-worthy files.
Flag scattered READMEs for 5-doc absorption.

## Scripts

The `scripts/` directory contains the Solid8 analysis engine:

**`scripts/denser_engine.py`** — Core consolidation logic:
- `DenserEngine` class with configurable similarity thresholds
- File fingerprinting (SHA-256, size, line count, pattern detection)
- Similarity calculation with Jaccard index + superset/subset detection
- Cluster grouping by hash, basename pattern, and file size
- Tier classification (S through D) with automated proposal generation
- Archive creation with manifest.json and rollback.md
- CLI interface: `python denser_engine.py <target_dir>`

Use the engine for programmatic consolidation on large projects.
The SKILL.md methodology applies whether using the engine or manual analysis.

## Trifecta Signals

Full protocol: `references/TRIFECTA_PROTOCOL.md`

**Emits:** `files_consolidated` → DevCom5 | `redundancy_found` → DevCom5 | `archive_recommended` → DevCom5 | `consolidation_complete` → Synk
**Consumes:** `new_files_synced` (Synk) → rescan | `architecture_changed` (DevCom5) → check obsolescence | `stale_project` (DevCom5) → full assessment
**PULSE writes:** `solid8_last_run`, `solid8_files_consolidated`, `solid8_redundancy_map`

## Under-the-Hood Display
**Scan:** `⚗️ Scanning [n] files | Clusters: [n]`
**Proposal:** `⚗️ Dupes: [n] | Supersets: [n] | Near: [n] | Reduction: ~[n]%`
**Complete:** `⚗️ Consolidated: [n] archived, [n] merged | Rollback: [path]`

## Anti-Patterns
- Deleting without archiving
- Treating all versions as redundant
- Ignoring POTIMP/staging
- Consolidating across environments (Synk's job)
- Merging without review above Tier S
- Byte-comparing docs (use section-aware diff)
- Consolidating build artifacts

---

*⁰ Formerly: Denser v1.0 (unnamed concept, pre-v1) → Solid8 v1.0.
"Solid8" — solid as in consolidated, 8 as in the infinity symbol ∞ rotated,
representing the endless cycle of project entropy that this skill tames.
The Denser alias persists for when subtlety isn't working.*
