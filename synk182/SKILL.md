---
name: synk182
description: >
  Intelligent multi-layer file synchronization between user's project directory
  and Claude's working environment. 
  Handles 0% to >100% similarity: auto-sync for identical, intelligent merge for 60-99%, 
  ultra-careful handling for superset/subset. 
  Six-layer verification, three-tier backup, auto-rollback.
  Multi-tier adaptive depth (adjusts rigor during scan based on findings).
  Cross-skill integration with DevCom5 and Solid8 via PULSE.json.
  Standalone; amplified with DevCom5 / Solid8.
  
---

# Synk182 — The Symphonous Strategist
 Formerly **nothing**
> *Formally a link between sink, and sync. *"Who thinks this shi don't stink? let that sync in" signed- A. Blinken.*

**Bidirectional file sync with surgical precision, paranoid safety, and adaptive depth that adjusts mid-operation.**

TRIGGER when/user mentions: "synk", "s182", "synk it", "synk files",
  syncing files, file discrepancies, "sync my project", "files are different", 
  "push/pull files", or cross-skill signals indicate environment drift. 


## Immutable Corrections (User-Specified)

1. Mandatory review for >60% similar (only 100% hash match skips review)
2. 60% threshold for intelligent merge (not 75%)
3. >100% superset/subset = ultra-careful handling, maximum scrutiny

## Triggers

| Level | Phrases | Action |
|-------|---------|--------|
| 🟢 Immediate | "sync my project/files", "synchronize", "keep in sync" | Activate |
| 🟡 Confirm | "update my project files" | Clarify: Synk or direct edits? |
| 🔴 Clarify | "files are different", "don't see my file" | Offer Synk |
| ❌ Not Synk | Create/edit single files, move within dir, redundancy (→ Solid8) | — |

## Similarity Spectrum

| Range | Relationship | Action | Review |
|-------|-------------|--------|--------|
| >100% | Superset/subset | Ultra-careful merge | ⚠️ MAXIMUM |
| 100% | Identical (hash) | Auto-sync | None (only case) |
| 60-99% | High similarity | Intelligent merge | Mandatory |
| <60% | Low similarity | Manual/skip | Variable |

## Six-Layer Verification

| # | Layer | Catches |
|---|-------|---------|
| 1 | Existence | Missing files, deletions |
| 2 | Hash (SHA-256) | Any content change — **gatekeeper**: match = skip 3-6 |
| 3 | Size | Truncation, corruption |
| 4 | Timestamp | Stale versions |
| 5 | Line count | Partial writes |
| 6 | Content diff | Specific changes |

## Three-Tier Adaptive Depth

### Tier 1: Baseline from PULSE
| Condition | Rigor |
|-----------|-------|
| `synk_last_run` < 24h, no signals | **Quick** — hash check only, skip unchanged |
| 1-7 days or minor signals | **Standard** — full six-layer on all files |
| >7 days or drift signals | **Thorough** — six-layer + relationship analysis + merge candidates |

### Tier 2: Adaptive Mid-Scan
**Downshift:** Quick scan finds 95%+ identical → summary report, skip detailed diff.
**Upshift:** Quick scan finds >10 non-identical files → escalate to Thorough.
Standard scan finds superset relationships → escalate to Thorough for those clusters.

**Report shifts:** `🔄 Rigor adjusted: Quick → Standard (15 files differ)`

### Tier 3: Cross-Skill Signals
`drift_detected` from DevCom5 → ≥ Standard.
`consolidation_complete` from Solid8 → new baseline, full comparison.
`stale_project` from DevCom5 → Thorough.

## Safety

**Three-tier backup:** Full project → per-file → incremental checkpoints.
**Auto-rollback:** On any verification failure post-operation.
**Archive:** `[project]/ARCHIVE/synk-[timestamp]/` with manifest.json, originals, rollback.md.

## Workflow

1. **Inventory** — Scan both environments, fingerprint all files
2. **Compare** — Classify by tier + direction (with adaptive depth adjustment)
3. **Propose** — Dashboard: `🔄 ✓12 identical | ⚠️2 superset | 🔀3 merge | ➕3 new`
4. **Execute** — After approval: backup → sync/merge → verify (six layers) → log
5. **Report** — `🔄 Synced: [n] | Verified: ✓ | Archive: [path]`

## Scripts

**`scripts/synk_engine.py`** — Core synchronization engine:
- `SynkEngine` class for bidirectional file sync
- SHA-256 fingerprinting and six-layer verification
- Similarity calculation with configurable thresholds
- Merge proposal generation with conflict detection
- Archive creation with manifest and rollback support

## Merge Strategies

**Standard (60-99%):** Shared base → user-unique + working-unique → merged → diff for review.
**Superset (>100%):** Identify superset → identify delta → assess intent → present with preview → **never auto-resolve**.
**Configs (JSON/YAML):** Structural key-value diff → user version as authority.

## Trifecta Signals

Full protocol: `references/TRIFECTA_PROTOCOL.md`

**Emits:** `sync_completed` → DevCom5 | `sync_conflict` → DevCom5 | `environment_diverged` → DevCom5 | `new_files_synced` → Solid8
**Consumes:** `drift_detected` (DevCom5) → ↑rigor | `consolidation_complete` (Solid8) → new baseline | `stale_project` (DevCom5) → Thorough
**PULSE writes:** `synk_last_run`, `synk_drift_detected`, `synk_files_changed`

## Anti-Patterns
- Syncing build artifacts (node_modules, bin/, obj/)
- Auto-resolving superset merges
- Syncing mid-edit (verify saved first)
- Assuming newer = better
- Consolidating during sync (Solid8's job)
- Skipping verification layers

---

*⁰ Formerly: unnamed sync utility (pre-v1) → Synk v1.0 → v2.0 → Synk v3.0.
Synk has no prior alias. It has always been Synk. That's the joke.*
