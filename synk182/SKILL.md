---
name: synk182
description: >-
  Synk182 (Synk): keeps two copies of a project in agreement without losing
  work - the user's copy and a working copy such as a sandbox or upload, a
  mounted or cloud-synced folder, a git worktree, another machine's copy, or a
  deployed copy of something developed elsewhere. Compares every file across
  the full similarity spectrum from identical to superset, proposes each change
  with its evidence, backs up into ARCHIVE/ before writing, verifies every
  write six ways and rolls back on failure. Only an exact hash match skips
  review. Use whenever the user says synk, s182, synk182 or synk it; asks to
  sync, mirror, push or pull files between two folders or machines; asks which
  copy is newer; says files are different, out of date or missing on one side;
  or when DevCom5 or Solid8 signal that copies have drifted. Not for redundancy
  inside one copy (Solid8), not for git merges or the rules of working in a
  repo (git, a repo-rules skill), and not for what two versions can do rather
  than what their files hold (verafox).
license: Freeware
metadata:
  version: "3.3"
  updated: "2026-09-30"
---

# Synk182 — The Symphonous Strategist
 Formerly **nothing**
> *Formally a link between sink, and sync. "Who thinks this shi don't stink? let that sync in" signed- A. Blinken.*

**Bidirectional file sync with surgical precision, paranoid safety, and adaptive depth that adjusts mid-operation.**

## Immutable Corrections (User-Specified)

1. Mandatory review for >60% similar (only 100% hash match skips review)
2. 60% threshold for intelligent merge (not 75%)
3. >100% superset/subset = ultra-careful handling, maximum scrutiny

## When the Request Is Ambiguous

| Level | Phrases | Action |
|-------|---------|--------|
| 🟢 Immediate | "sync my project/files", "synchronize", "keep in sync" | Activate |
| 🟡 Confirm | "update my project files" | Clarify: Synk or direct edits? |
| 🔴 Clarify | "files are different", "don't see my file" | Offer Synk |
| ❌ Not Synk | Create/edit single files, move within dir, redundancy (→ Solid8), branch merges (→ git), repo and worktree rules (→ your repository's own rules), what a version can do rather than what its files hold (→ verafox, in The Proof Pack) | — |

**Name the two copies first.** Say which is the user's copy (authority) and which is the working copy, in the user's words. Most sync damage starts with the two being swapped.

## Similarity Spectrum

| Range | Relationship | Action | Review |
|-------|-------------|--------|--------|
| >100% | Superset/subset | Ultra-careful merge | ⚠️ MAXIMUM |
| 100% | Identical (hash) | Nothing to do | None (only case) |
| 60-99% | High similarity | Intelligent merge | Mandatory |
| <60% | Low similarity | Manual/skip | Variable |
| — | Binary, not identical | Choose a side or keep both | Manual |
| — | Only on one side | Copy after approval | Standard |

## Six-Layer Verification

| # | Layer | Catches |
|---|-------|---------|
| 1 | Existence | Missing files, deletions |
| 2 | Hash (SHA-256) | Any content change — **gatekeeper**: match = skip 3-6 |
| 3 | Size | Truncation, corruption |
| 4 | Timestamp | Stale versions (2-second tolerance for filesystem rounding) |
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
`docs_created` from DevCom5 → include the new docs in the next comparison.

## Safety

**Backup before every write:** each file an apply will overwrite is copied first into `[user copy]/ARCHIVE/synk-[timestamp]/<side>/` with `manifest.json`, `rollback.md` and `apply-report.json`. Files that did not exist are recorded so rollback deletes them.
**Full-project backup:** before a large or first sync, copy the whole project aside first — the engine backs up per file, not per project.
**Auto-rollback:** any item that fails a verification layer after copying is restored from the backup on the spot, and reported.
**Nothing writes without approval:** the dashboard and the plan are read-only.

## Workflow

1. **Inventory** — Scan both copies, fingerprint all files (skips `.git`, `node_modules`, build output, caches and the exact folder name `ARCHIVE`, where Synk writes its own backups; a project's other archive-named folders are content and stay in sync, while Solid8 protects them from consolidation)
2. **Compare** — Classify by tier + direction (with adaptive depth adjustment)
3. **Propose** — Dashboard: `🔄 ✓12 identical | ⚠️2 superset | 🔀3 merge | ➕3 new`; show diffs for every merge and superset
4. **Execute** — After approval: backup → copy or merged write → verify (six layers) → roll back failures → log
5. **Report** — `🔄 Synced: [n] | Verified: ✓ | Archive: [path]`, then write PULSE

## Scripts

**`scripts/synk_engine.py`** — the engine behind the workflow. Read-only unless told to apply.

```bash
python scripts/synk_engine.py USER_COPY WORKING_COPY                    # dashboard
python scripts/synk_engine.py USER_COPY WORKING_COPY --plan plan.json   # numbered plan, nothing written
python scripts/synk_engine.py USER_COPY WORKING_COPY --diff path/in/project.md
python scripts/synk_engine.py USER_COPY WORKING_COPY --apply plan.json --approve 2,5 [--pulse]
```

- Plan items carry `direction`: set for one-sided files; `null` for merges and supersets until the user decides. To apply a merge, write the merged file into one copy, set that item's direction to the other copy in the plan, and approve its id. An approved item whose direction is still `null` is skipped with that reason, and the run exits 1.
- An item is refused before any backup or write when its path leaves either copy (absolute, `..`, drive-relative or UNC forms), names a folder rather than a file (`sub`, or `.` for the copy itself), or when its destination changed since the plan was written — a file that appeared, or was edited, after `--plan`: re-plan. Each refusal is reported and the run exits 1. An `--approve` id that names no plan item, `--approve` without `--apply`, `--plan` beside `--apply`, `--diff` beside `--plan`, `--apply` or `--pulse`, and the same folder given for both copies are errors that stop the run before anything is written.
- `--approve new` approves every one-sided file at once — still an explicit approval, so show the list first. It leaves out an escaping path, and `docs/PULSE.json`, which each copy keeps for itself (approve it by id to copy it).
- `--pulse` writes `synk_last_run`, `synk_drift_detected` and the signals below into `USER_COPY/docs/PULSE.json`, plus `synk_files_changed` after an apply, keeping every other key. After an apply, `sync_completed` is emitted only when a file was written, and `new_files_synced` names only the files the apply created, not the ones it overwrote. A wrong-typed field (`"pending_signals": null`) is treated as empty with a note; a PULSE that does not parse, or holds no JSON object, is never touched, and the run says so; when none exists one is created holding only `cross_skill`, which DevCom5 fills out at its next Deep pass. When `docs` is a file, or the PULSE cannot be written, the run warns that it is not recorded there, and an apply still reports what it wrote.
- The same operations are available as `SynkEngine(...).scan_and_compare()`, `.plan()`, `.diff()`, `.backup()`, `.apply()`, with `.refusal(path)` and `.new_ids(plan)` for the checks above.

## Merge Strategies

**Standard (60-99%):** Shared base → user-unique + working-unique → merged → diff for review.
**Superset (>100%):** Identify superset → identify delta → assess intent → present with preview → **never auto-resolve**.
**Configs (JSON/YAML):** Structural key-value diff → user version as authority.

## Trifecta Signals

Full protocol: [references/TRIFECTA_PROTOCOL.md](references/TRIFECTA_PROTOCOL.md)

**Emits:** `sync_completed` → DevCom5 | `sync_conflict` → DevCom5 | `environment_diverged` → DevCom5 | `new_files_synced` → Solid8
**Consumes:** `drift_detected` (DevCom5) → ↑rigor | `consolidation_complete` (Solid8) → new baseline | `stale_project` (DevCom5) → Thorough | `docs_created` (DevCom5) → include
**PULSE writes:** `synk_last_run`, `synk_drift_detected`, `synk_files_changed`

## Anti-Patterns
- Syncing build artifacts (node_modules, bin/, obj/)
- Auto-resolving superset merges
- Syncing mid-edit (verify saved first)
- Assuming newer = better
- Swapping which copy is the user's
- Copying secrets (`.env`, keys) into a copy the user did not mean to hold them
- Consolidating during sync (Solid8's job)
- Skipping verification layers

---

*⁰ Formerly: unnamed sync utility (pre-v1) → Synk v1.0 → v2.0 → Synk v3.0 → Synk182 v3.1 (2026-09-15: any two copies, not one sandbox; the engine now really backs up, applies, verifies and rolls back) → Synk182 v3.2 (2026-09-30: part of The Triad; the description says what it is not for beside Solid8, git, a repo's own rules and verafox; freeware) → Synk182 v3.3 (2026-09-30: the engine refuses a plan item whose path leaves either copy or names a folder, or whose destination changed since the plan, never deletes a folder on rollback, emits sync_completed and new_files_synced only when they are true, treats a wrong-typed PULSE field as empty with a note, answers a bad folder, plan, approval or diff path with a message, keeps docs/PULSE.json out of --approve new, skips an approved item with no direction with its reason and exit 1, refuses --plan beside --apply and --diff beside another action, and warns instead of failing when docs is a file; the not-for pointers name kinds of work rather than private skills).
Synk has no prior alias. It has always been Synk. That's the joke.*
