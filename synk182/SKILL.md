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
**Auto-rollback:** any item that fails a verification layer after copying — or raises anything while being verified — is restored from the backup on the spot, and reported; a rollback that fails is reported with the backup to restore by hand, and the run exits 1.
**Nothing writes without approval:** the dashboard and the plan are read-only.

## Workflow

1. **Inventory** — Scan both copies, fingerprint all files (skips `.git`, `node_modules`, build output, caches and the folder name `ARCHIVE`, where Synk writes its own backups — at a copy's root in any spelling where the file system folds case, as on Windows and default macOS, since `archive/` is that same folder there, and then it is named on the dashboard; `.git`, `.hg`, `.svn` and `node_modules` fold the same way there, so `.GIT/` is `.git/`, while a build-output name is skipped only as spelled, so a project's `Build/` or `Dist/` is compared like any folder; a nested `archive/`, and a project's other archive-named folders, are content and stay in sync on every file system, while Solid8 protects them from consolidation). A junction or link inside either copy, to a folder or a file, is never followed (a dangling one is named as such), a folder that cannot be listed or a file that cannot be read is never read as absent or empty, and a file where the `ARCHIVE` folder goes is not compared: each is named on the dashboard as not compared, with its reason. Where both copies fold case, a name that differs only in case between them (`Readme.md` and `README.md`) is one file, compared under the user copy's spelling and named as the same file in different case
2. **Compare** — Classify by tier + direction (with adaptive depth adjustment); two copies that hold the same lines with different line endings are classed `line_endings`, each side's convention named, never as a merge (endings that differ line by line inside the same mix are said to differ within the file); two copies that differ only in a UTF-8 byte-order mark are said so, the side carrying it named
3. **Propose** — Dashboard: `🔄 ✓12 identical | ⚠️2 superset | 🔀3 merge | ⏎1 line endings | ➕3 new`; show diffs for every merge and superset
4. **Execute** — After approval: backup → copy or merged write → verify (six layers) → roll back failures → log
5. **Report** — `🔄 Synced: [n] | Verified: ✓ | Archive: [path]`, then write PULSE

## Scripts

**`scripts/synk_engine.py`** — the engine behind the workflow. Read-only unless told to apply.

```bash
python scripts/synk_engine.py USER_COPY WORKING_COPY                    # dashboard
python scripts/synk_engine.py USER_COPY WORKING_COPY --plan plan.json   # numbered plan, nothing written
python scripts/synk_engine.py USER_COPY WORKING_COPY --diff path/in/project.md    # --diff=-name for a name that starts with a dash
python scripts/synk_engine.py USER_COPY WORKING_COPY --apply plan.json --approve 2,5 [--pulse]
```

- Plan items carry `direction`: set for one-sided files; `null` for merges, supersets and line-ending-only pairs until the user decides. To apply a merge, write the merged file into one copy, set that item's direction to the other copy in the plan, and approve its id. An approved item whose direction is still `null`, or is not `user_to_working` or `working_to_user`, is skipped with that reason, and the run exits 1.
- An item is refused before any backup or write when its path leaves either copy (absolute, `..`, drive-relative or UNC forms), ends in a separator or a space, on Windows holds a form Windows reserves (a segment ending in a dot or a space, a `:` stream, `<>"|?*`) or names a device as the running Windows maps it (a bare `NUL` on Windows 11; `con.txt` too on Windows 10, so the engine asks the OS rather than keeping a list), lies in a folder the scan skips (`.git`, `node_modules`, the root's `ARCHIVE`, in any spelling the file system folds; a build-output folder as spelled), passes through or names a junction or link on either side, names a folder rather than a file (`sub`, or `.` for the copy itself), when its source or the file its destination would replace cannot be read, or when its destination changed since the plan was written — a file that appeared, or was edited, after `--plan`: re-plan. A destination that already holds the source's content, whatever the item's status, is reported as already applied, and not counted as a failure: nothing is written, the run can exit 0, and `--pulse` sends no `sync_conflict` for it. The source is copied as it is at apply time: the plan pins the destination, not the source. Each refusal is reported and the run exits 1. An `--approve` id that names no plan item, an id that appears twice in a hand-edited plan, `--approve` without `--apply`, `--plan` beside `--apply`, `--diff` beside `--plan`, `--apply` or `--pulse`, a `--threshold` outside 0 to 1, and the same folder given for both copies are errors that stop the run before anything is written. A `--plan` file that cannot be written (a missing folder, or a folder in its place) is answered with the reason and exit 1, and a `--pulse` beside it still records the scan. An empty name given to `--plan`, `--apply` or `--diff` is answered the same way, and a hand-edited plan whose ids are not whole numbers or whose hashes are not objects is refused before anything is written; a plan saved with a UTF-8 BOM is read. When no backup folder can be made (a file named `ARCHIVE` in the user's copy), or a backup fails midway (whatever is raised), every approved item is refused, nothing is written and no archive folder is left behind. `--diff` refuses a path that leaves the copies or names a link, names a file it cannot read, and says when the copies differ only in line endings (by convention, or line by line within the file) or only in a byte-order mark; a byte-order mark on one side is named beside any other difference too, on the dashboard, in the plan and by `--diff`, so it is never copied or stripped without a word. Everything the engine writes (the plan, the archive's files, `docs/PULSE.json`) is LF on every platform.
- `--approve new` approves every one-sided file at once — still an explicit approval, so show the list first. It names each item it leaves out, with the reason: `docs/PULSE.json`, which each copy keeps for itself (approve it by id to copy it), and any item it refuses (a path that leaves the copies, names a device or a form Windows reserves, lies in a skipped folder or passes through a link, or an item with no path), which is counted as refused and makes the run exit 1.
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

*⁰ Formerly: unnamed sync utility (pre-v1) → Synk v1.0 → v2.0 → Synk v3.0 → Synk182 v3.1 (2026-09-15: any two copies, not one sandbox; the engine now really backs up, applies, verifies and rolls back) → Synk182 v3.2 (2026-09-30: part of The Triad; the description says what it is not for beside Solid8, git, a repo's own rules and verafox; freeware) → Synk182 v3.3 (2026-09-30: the engine refuses a plan item whose path leaves either copy or names a folder, or whose destination changed since the plan, never deletes a folder on rollback, emits sync_completed and new_files_synced only when they are true, treats a wrong-typed PULSE field as empty with a note, answers a bad folder, plan, approval or diff path with a message, keeps docs/PULSE.json out of --approve new, skips an approved item with no direction with its reason and exit 1, refuses --plan beside --apply and --diff beside another action, and warns instead of failing when docs is a file, answers a --plan file it cannot write with the reason, and names an item with no path by its id; it names and does not follow a junction or link, names a folder it cannot list and a file where ARCHIVE goes, refuses an apply that cannot make its backup and a hand-edited plan before any write, answers an empty --plan, --apply or --diff name, and prunes a signal stamped with Z on every Python; a file that cannot be read is named and left out, never read as empty, and an item naming one is refused; a backup that fails refuses every item and leaves no archive; any exception in verification rolls the copy back, and a failed rollback names the backup; where the file system folds case, any spelling of ARCHIVE is Synk's folder and Readme.md / README.md are one file; copies that differ only in line endings are said so, and --diff refuses a path outside the copies; a link to a file is named and not followed; PULSE stamps are read by one grammar on every Python; a plan path in a skipped folder, a duplicate id and a --threshold outside 0 to 1 are refused; a skipped folder in any spelling the file system folds, a link on either side, a form Windows reserves and an item already applied, whatever its status, are refused before any write; line endings that differ within a file and a byte-order mark alone are named as such; anything raised while backing up refuses every item; the timestamp grammar is read exactly as the protocol pins it, and everything the engine writes is LF; the not-for pointers name kinds of work rather than private skills; updated 2026-09-30 15:25 ET: device names are asked of the running Windows, --approve new exits 1 on what it refuses, Build/ and a nested archive/ sync, already applied is not a failure, and a byte-order mark is named beside any other difference).
Synk has no prior alias. It has always been Synk. That's the joke.*
