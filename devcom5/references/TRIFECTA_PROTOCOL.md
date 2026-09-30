# Trifecta Protocol
<!-- v3.0 | 2026-09-15 | Byte-identical in DevCom5, Synk182 and Solid8 (v2.0 2026-02-10) | Updated: 2026-09-30 04:50 ET — Safety 4 says what a missing or unparseable PULSE leads to | Updated: 2026-09-30 07:28 ET — which signal timestamps are pruned: an offset or Z, and none read as local time -->

Cross-skill integration through one file in the project: `docs/PULSE.json`.
Each skill works alone; together they cover the whole cycle.

## Roles

| Skill | Role | Core Question |
|-------|------|---------------|
| 📜 **DevCom5** (Logger) | State, trajectory, gaps, comms | What does this project know about itself? |
| 🔄 **Synk182** (Synk) | Agreement between copies | Are the copies in agreement? |
| ⚗️ **Solid8** (Denser) | Redundancy elimination | What can be unified without losing meaning? |

## Communication: PULSE.json `cross_skill`

DevCom5 owns everything outside `cross_skill`. Inside it, each skill writes only its own keys, and every skill keeps keys it does not recognise — other skills add sections of their own.

```json
{
  "cross_skill": {
    "synk_last_run": "ISO-8601|null", "synk_drift_detected": false, "synk_files_changed": 0,
    "solid8_last_run": "ISO-8601|null", "solid8_files_consolidated": 0, "solid8_redundancy_map": {},
    "pending_signals": [
      { "from": "devcom5", "signal": "drift_detected", "to": "synk182",
        "timestamp": "ISO-8601", "details": "context", "consumed": false }
    ]
  }
}
```

| Key | Written by | Meaning |
|-----|-----------|---------|
| `synk_last_run` | Synk182 | When a sync or comparison last ran |
| `synk_drift_detected` | Synk182 | The copies disagreed at that run |
| `synk_files_changed` | Synk182 | Files written by the last apply |
| `solid8_last_run` | Solid8 | When a consolidation scan last ran |
| `solid8_files_consolidated` | Solid8 | Files archived or merged by the last run |
| `solid8_redundancy_map` | Solid8 | Open findings: `{"S": [[file, file]], "A": [...], ...}` |
| `pending_signals` | any | Advisory messages between skills |

**Lifecycle:** Emit `consumed: false` → Consumer reads, acts, sets `consumed: true` →
Prune consumed signals >7 days. A `timestamp` is ISO-8601 with an offset or `Z`
(`2026-09-30T14:12:00Z`); one with neither is read as local time. Read the signal name
from `signal`; writers before v3.0 sometimes used `type`, so fall back to it. Signals are
advisory, not commands.

## Signal Catalog

| From | Signal | To | Consumer's response |
|------|--------|----|---------------------|
| DevCom5 | `drift_detected` | Synk182 | Rigor at least Standard |
| DevCom5 | `architecture_changed` | Solid8 | Check whether the structure change made files obsolete |
| DevCom5 | `stale_project` | Both | Thorough |
| DevCom5 | `docs_created` | Both | Solid8 treats the new docs as doc-worthy and never consolidates them; Synk182 includes them in its next comparison |
| Synk182 | `sync_completed` | DevCom5 | Next digest at least Standard |
| Synk182 | `sync_conflict` | DevCom5 | Flag in the audit |
| Synk182 | `environment_diverged` | DevCom5 | Flag in the audit; at least Thorough |
| Synk182 | `new_files_synced` | Solid8 | Rescan for new overlaps, at least Standard |
| Solid8 | `files_consolidated` | DevCom5 | Update the structure map and ARCHITECTURE element notes |
| Solid8 | `redundancy_found` | DevCom5 | Flag in the audit |
| Solid8 | `archive_recommended` | DevCom5 | Put the recommendation in PLANNING for the user |
| Solid8 | `consolidation_complete` | Synk182 | New baseline; full comparison next run |

## Multi-Tier Depth Interaction

All three skills use three-tier adaptive depth:
- Tier 1 (staleness/baseline) sets initial rigor
- Tier 2 (adaptive mid-scan) adjusts based on findings mid-operation
- Tier 3 (cross-skill signals) overrides **upward only**

Tiers compound, not replace. A Pulse-depth scan can escalate to Deep if
Synk reports drift AND mid-scan finds new files.

## Workflows

**Full trifecta:** DevCom5(Cartographer) → Synk182 → Solid8 → DevCom5(Architect)
**DevCom5+Synk182:** DevCom5(Cart) → Synk182 → DevCom5(Arch)
**DevCom5+Solid8:** DevCom5(Cart) → Solid8 → DevCom5(Arch)
**Synk182+Solid8:** Synk182 → Solid8

## Safety

1. No skill overwrites another's output without user approval
2. Signals are advisory — user has final say
3. Each skill writes only its own PULSE keys; preserve unknown fields
4. Missing PULSE → Synk182 or Solid8 creates `docs/PULSE.json` holding only `cross_skill`, and DevCom5 fills out the rest at its next Deep pass. A PULSE that does not parse is never overwritten: Synk182 and Solid8 leave it untouched, say so and work standalone; DevCom5 keeps it as `PULSE.corrupt.json` before it rebuilds the baseline
5. All cross-skill actions visible in under-the-hood display
