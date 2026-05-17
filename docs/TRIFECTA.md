# Trifecta Protocol

<!-- v2.0 | 2026-02-10 | Shared across DevCom5, Synk182, Solid8 -->

Cross-skill integration via `docs/PULSE.json` signals.
Each skill is standalone; amplified together.

## Roles

| Skill | Role | Core Question |
|-------|------|---------------|
| **DevCom5** (Logger) | State, trajectory, gaps, comms | What does this project know about itself? |
| **Synk182** | Environment agreement | Are the copies in agreement? |
| **Solid8** (Denser) | Redundancy elimination | What can be unified without losing meaning? |

## Communication: PULSE.json `cross_skill`

```json
{
  "cross_skill": {
    "synk_last_run": "ISO-8601|null",
    "synk_drift_detected": false,
    "solid8_last_run": "ISO-8601|null",
    "solid8_files_consolidated": 0,
    "pending_signals": [
      {
        "from": "devcom5",
        "signal": "drift_detected",
        "timestamp": "ISO-8601",
        "details": "context",
        "consumed": false
      }
    ]
  }
}
```

**Lifecycle:** Emit `consumed: false` → Consumer reads, acts, sets `consumed: true` →
Prune consumed signals older than 7 days. Signals are advisory, not commands.

## Signal Catalog

**DevCom5 emits:** `drift_detected` → Synk182 | `architecture_changed` → Solid8 | `stale_project` → Both | `docs_created` → Both

**Synk182 emits:** `sync_completed` → DevCom5 | `sync_conflict` → DevCom5 | `environment_diverged` → DevCom5 | `new_files_synced` → Solid8

**Solid8 emits:** `files_consolidated` → DevCom5 | `redundancy_found` → DevCom5 | `archive_recommended` → DevCom5 | `consolidation_complete` → Synk182

## Recommended Workflows

| Flow | Sequence |
|------|----------|
| Full trifecta | DevCom5 (Cartographer) → Synk182 → Solid8 → DevCom5 (Architect) |
| Docs + lean | DevCom5 → Solid8 → DevCom5 |
| Sync + lean | Synk182 → Solid8 |
| Docs + sync | DevCom5 (Cartographer) → Synk182 → DevCom5 (Architect) |

## Safety

1. No skill overwrites another's output without user approval.
2. Signals are advisory — the user has final say.
3. Each skill writes only its own PULSE sections; preserve unknown fields.
4. Corrupt or missing PULSE → graceful fallback to standalone mode.
5. All cross-skill actions should be visible in agent status output.
