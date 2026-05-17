# Trifecta Protocol
<!-- v2.0 | 2026-02-10 | Shared across DevCom5, Synk, Solid8 -->

Cross-skill integration via `docs/PULSE.json` signals.
Each skill is standalone; amplified together.

## Roles

| Skill | Role | Core Question |
|-------|------|---------------|
| 📜 **DevCom5** (Logger) | State, trajectory, gaps, comms | What does this project know about itself? |
| 🔄 **Synk** | Environment agreement | Are the copies in agreement? |
| ⚗️ **Solid8** (Denser) | Redundancy elimination | What can be unified without losing meaning? |

## Communication: PULSE.json `cross_skill`

```json
{
  "cross_skill": {
    "synk_last_run": "ISO-8601|null", "synk_drift_detected": false,
    "solid8_last_run": "ISO-8601|null", "solid8_files_consolidated": 0,
    "pending_signals": [
      { "from": "devcom5", "signal": "drift_detected",
        "timestamp": "ISO-8601", "details": "context", "consumed": false }
    ]
  }
}
```

**Lifecycle:** Emit `consumed: false` → Consumer reads, acts, sets `consumed: true` →
Prune consumed signals >7 days. Signals are advisory, not commands.

## Signal Catalog

**DevCom5 emits:** `drift_detected` → Synk | `architecture_changed` → Solid8 | `stale_project` → Both | `docs_created` → Both

**Synk emits:** `sync_completed` → DevCom5 | `sync_conflict` → DevCom5 | `environment_diverged` → DevCom5 | `new_files_synced` → Solid8

**Solid8 emits:** `files_consolidated` → DevCom5 | `redundancy_found` → DevCom5 | `archive_recommended` → DevCom5 | `consolidation_complete` → Synk

## Multi-Tier Depth Interaction

All three skills use three-tier adaptive depth:
- Tier 1 (staleness/baseline) sets initial rigor
- Tier 2 (adaptive mid-scan) adjusts based on findings mid-operation
- Tier 3 (cross-skill signals) overrides **upward only**

Tiers compound, not replace. A Pulse-depth scan can escalate to Deep if
Synk reports drift AND mid-scan finds new files.

## Workflows

**Full trifecta:** DevCom5(Cartographer) → Synk → Solid8 → DevCom5(Architect)
**DevCom5+Synk:** DevCom5(Cart) → Synk → DevCom5(Arch)
**DevCom5+Solid8:** DevCom5(Cart) → Solid8 → DevCom5(Arch)
**Synk+Solid8:** Synk → Solid8

## Safety

1. No skill overwrites another's output without user approval
2. Signals are advisory — user has final say
3. Each skill writes only its own PULSE sections; preserve unknown fields
4. Corrupt/missing PULSE → graceful fallback to standalone
5. All cross-skill actions visible in under-the-hood display
