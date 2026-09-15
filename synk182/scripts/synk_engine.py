#!/usr/bin/env python3
"""
Synk Engine v2.0 — compare two copies of a project, plan, back up, apply, verify.
2026-09-15 | For: synk182 skill v3.1 (v1.0 2026-02-10 compared only)

Two copies: the USER copy (the one the user treats as authority) and the
WORKING copy (a sandbox or upload, a mounted or cloud-synced folder, a git
worktree, another machine's copy, a deployed copy). Nothing here writes until
apply() is called with the ids the user approved.

The three user-specified corrections hold throughout:
  1. Only a 100% hash match skips review.
  2. 60% is the threshold for intelligent merge (not 75%).
  3. Superset/subset (over 100%) gets maximum scrutiny and is never auto-resolved.

CLI (read-only unless --apply):
  python synk_engine.py USER_DIR WORKING_DIR                    dashboard
  python synk_engine.py USER_DIR WORKING_DIR --plan plan.json   write the plan
  python synk_engine.py USER_DIR WORKING_DIR --diff REL/PATH    unified diff of one file
  python synk_engine.py USER_DIR WORKING_DIR --apply plan.json --approve 3,7
        back up, copy each approved item in its direction, verify six layers,
        roll back any item that fails; --approve new approves every one-sided file
  --threshold 0.6   --pulse (write results to USER_DIR/docs/PULSE.json)
"""

import argparse
import difflib
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
    "bin", "obj", "dist", "build", ".next", ".cache", ".pytest_cache", "ARCHIVE",
}
LAYERS = ["existence", "hash", "size", "timestamp", "line_count", "content"]
TIMESTAMP_TOLERANCE_S = 2.0
DIRECTIONS = ("user_to_working", "working_to_user")


def _say(text: str = "") -> None:
    """Print without dying on a console that cannot encode the emoji."""
    try:
        print(text)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "ascii"
        print(text.encode(enc, "replace").decode(enc))


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return ""


def _is_binary(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return b"\x00" in f.read(8192)
    except OSError:
        return False


def _lines(path: Path) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    except OSError:
        return []


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class SynkEngine:
    """Bidirectional comparison and verified copying across the full similarity spectrum."""

    def __init__(self, user_dir: str, working_dir: str, threshold: float = 0.60,
                 skip_dirs: Optional[Iterable[str]] = None):
        self.user_dir = Path(user_dir).resolve()
        self.working_dir = Path(working_dir).resolve()
        self.threshold = threshold  # Correction #2
        self.skip_dirs = set(SKIP_DIRS if skip_dirs is None else skip_dirs)
        self.archive_root = self.user_dir / "ARCHIVE"
        self.user_files: Dict[str, Dict] = {}
        self.working_files: Dict[str, Dict] = {}
        self.results: Optional[Dict] = None

    # ── Inventory ──────────────────────────────────────────────────────
    def _scan_directory(self, root: Path, other_root: Path) -> Dict[str, Dict]:
        files: Dict[str, Dict] = {}
        if not root.is_dir():
            return files
        for dirpath, dirnames, filenames in os.walk(root):
            here = Path(dirpath)
            dirnames[:] = sorted(d for d in dirnames
                                 if d not in self.skip_dirs and (here / d).resolve() != other_root)
            for name in sorted(filenames):
                p = here / name
                try:
                    st = p.stat()
                except OSError:
                    continue
                files[p.relative_to(root).as_posix()] = {
                    "path": p, "size": st.st_size, "mtime": st.st_mtime,
                    "hash": _hash(p), "binary": _is_binary(p),
                }
        return files

    # ── Compare ────────────────────────────────────────────────────────
    def scan_and_compare(self, quiet: bool = False) -> Dict:
        """Fingerprint both copies and classify every path. Read-only."""
        self.user_files = self._scan_directory(self.user_dir, self.working_dir)
        self.working_files = self._scan_directory(self.working_dir, self.user_dir)
        counts = dict.fromkeys(("identical", "superset", "merge", "different", "user_only", "working_only"), 0)
        files = {}
        for rel in sorted(set(self.user_files) | set(self.working_files)):
            a = self._analyze_file_pair(rel, self.user_files.get(rel), self.working_files.get(rel))
            counts[a["status"]] += 1
            files[rel] = a
        self.results = {"total": len(files), **counts, "files": files}
        if not quiet:
            self._dashboard()
        return self.results

    def _analyze_file_pair(self, rel: str, u: Optional[Dict], w: Optional[Dict]) -> Dict:
        if not u or not w:
            return {"status": "user_only" if u else "working_only", "relationship": "missing",
                    "similarity": 0.0, "hash_match": False, "newer": None, "layers": {"existence": False}}
        layers = {
            "existence": True,
            "hash": u["hash"] == w["hash"],
            "size": u["size"] == w["size"],
            "timestamp": abs(u["mtime"] - w["mtime"]) <= TIMESTAMP_TOLERANCE_S,
        }
        newer = None if layers["timestamp"] else ("user" if u["mtime"] > w["mtime"] else "working")
        if layers["hash"]:  # Correction #1: the only case that skips review
            layers.update(line_count=True, content=True)
            return {"status": "identical", "relationship": "identical", "similarity": 1.0,
                    "hash_match": True, "newer": newer, "layers": layers}
        if u["binary"] or w["binary"]:
            layers.update(line_count=False, content=False)
            return {"status": "different", "relationship": "binary", "similarity": 0.0,
                    "hash_match": False, "newer": newer, "layers": layers}
        lu, lw = _lines(u["path"]), _lines(w["path"])
        layers.update(line_count=len(lu) == len(lw), content=False)
        similarity, relationship = self._calculate_extended_similarity(lu, lw)
        if relationship in ("a_superset", "b_superset"):
            status = "superset"  # Correction #3
        elif similarity >= self.threshold:
            status = "merge"  # Correction #2 (includes 100% line-set match with a different hash)
        else:
            status = "different"
        return {"status": status, "relationship": relationship, "similarity": similarity,
                "hash_match": False, "newer": newer, "layers": layers}

    @staticmethod
    def _calculate_extended_similarity(content_a: List[str], content_b: List[str]) -> Tuple[float, str]:
        """Line-set similarity; over 1.0 means one side holds all of the other plus more."""
        set_a = {line.rstrip() for line in content_a if line.strip()}
        set_b = {line.rstrip() for line in content_b if line.strip()}
        if set_a == set_b:
            return 1.0, "standard"
        if set_b <= set_a:
            return (1.5 if not set_b else 1.0 + len(set_a - set_b) / len(set_b) * 0.5), "a_superset"
        if set_a <= set_b:
            return (1.5 if not set_a else 1.0 + len(set_b - set_a) / len(set_a) * 0.5), "b_superset"
        union = set_a | set_b
        return len(set_a & set_b) / len(union), "standard"

    def _dashboard(self) -> None:
        r = self.results
        _say(f"🔄 Synk: {self.user_dir}  ⇄  {self.working_dir}")
        _say(f"   ✓{r['identical']} identical | ⚠️{r['superset']} superset | 🔀{r['merge']} merge "
             f"| ✗{r['different']} different | ➕{r['user_only']} only in user copy "
             f"| ➕{r['working_only']} only in working copy")
        for rel, a in r["files"].items():
            if a["status"] != "identical":
                sim = f"{a['similarity']:.0%}" if a["relationship"] not in ("missing", "binary") else a["relationship"]
                _say(f"   {a['status']:<13} {sim:>8}  {rel}" + (f"  (newer: {a['newer']})" if a["newer"] else ""))

    def diff(self, rel: str) -> str:
        u, w = self.user_dir / rel, self.working_dir / rel
        return "\n".join(difflib.unified_diff(_lines(u), _lines(w), f"user/{rel}", f"working/{rel}", lineterm=""))

    # ── Plan ───────────────────────────────────────────────────────────
    def plan(self) -> List[Dict]:
        """One proposed action per non-identical path. Read-only; nothing is approved here."""
        if self.results is None:
            self.scan_and_compare(quiet=True)
        actions, n = [], 0
        notes = {
            "user_only": ("user_to_working", "STANDARD", "new in the user copy"),
            "working_only": ("working_to_user", "STANDARD", "new in the working copy"),
            "superset": (None, "MAXIMUM", "one copy holds all of the other plus more: decide which is intended; never auto-resolve"),
            "merge": (None, "MANDATORY", "merge from the diff, then set the direction for the merged file"),
            "different": (None, "MANUAL", "low similarity or binary: choose a side or keep both under different names"),
        }
        for rel, a in self.results["files"].items():
            if a["status"] == "identical":
                continue
            n += 1
            direction, review, note = notes[a["status"]]
            actions.append({"id": n, "path": rel, "status": a["status"], "relationship": a["relationship"],
                            "similarity": round(a["similarity"], 3), "newer": a["newer"],
                            "direction": direction, "review": review, "note": note})
        return actions

    # ── Backup ─────────────────────────────────────────────────────────
    def _new_archive_dir(self) -> Path:
        stamp = datetime.now().strftime("%Y-%m-%dT%H%M%S")
        dest = self.archive_root / f"synk-{stamp}"
        i = 1
        while dest.exists():
            i += 1
            dest = self.archive_root / f"synk-{stamp}-{i}"
        dest.mkdir(parents=True)
        return dest

    def _backup_into(self, dest: Path, paths: List[str], side: str) -> None:
        root = self.user_dir if side == "user" else self.working_dir
        manifest_path = dest / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else \
            {"timestamp": _now_iso(), "user_dir": str(self.user_dir), "working_dir": str(self.working_dir), "files": {}}
        for rel in paths:
            src = root / rel
            entry = {"side": side, "existed": src.is_file()}
            if src.is_file():
                target = dest / side / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)
                entry.update(hash=_hash(src), size=src.stat().st_size)
            manifest["files"][f"{side}:{rel}"] = entry
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        lines = ["# Rollback", "", f"Archive created: {manifest['timestamp']}", "",
                 "To undo, copy each file under this folder's `user/` or `working/` back to the same",
                 "relative path in that copy, and delete any file listed as not having existed.", ""]
        for key, e in manifest["files"].items():
            side_name, rel = key.split(":", 1)
            root_name = self.user_dir if side_name == "user" else self.working_dir
            lines.append(f"- `{root_name / rel}` — " + ("restore from `" + f"{side_name}/{rel}`" if e["existed"] else "did not exist: delete it"))
        (dest / "rollback.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def backup(self, paths: List[str], side: str) -> Path:
        """Copy the named files of one side ('user' or 'working') into a new archive folder."""
        if side not in ("user", "working"):
            raise ValueError("side must be 'user' or 'working'")
        dest = self._new_archive_dir()
        self._backup_into(dest, paths, side)
        return dest

    # ── Apply + verify ─────────────────────────────────────────────────
    def _verify_copy(self, src: Path, dst: Path) -> List[str]:
        """Return the layers that failed; empty means all six held."""
        failed = []
        if not dst.is_file():
            return list(LAYERS)
        if _hash(src) != _hash(dst):
            failed.append("hash")
        s, d = src.stat(), dst.stat()
        if s.st_size != d.st_size:
            failed.append("size")
        if abs(s.st_mtime - d.st_mtime) > TIMESTAMP_TOLERANCE_S:
            failed.append("timestamp")
        try:
            sb, db = src.read_bytes(), dst.read_bytes()
            if sb.count(b"\n") != db.count(b"\n"):
                failed.append("line_count")
            if sb != db:
                failed.append("content")
        except OSError:
            failed += ["line_count", "content"]
        return failed

    def apply(self, plan: List[Dict], approved_ids: Iterable[int]) -> Dict:
        """Execute approved actions that have a direction; back up first, roll back on failure."""
        approved = set(approved_ids)
        report = {"applied": [], "skipped": [], "rolled_back": [], "archive": None}
        todo = []
        for act in plan:
            if act["id"] not in approved:
                continue
            if act.get("direction") not in DIRECTIONS:
                report["skipped"].append({"path": act["path"], "reason": "no direction chosen; review first"})
            else:
                todo.append(act)
        if not todo:
            return report
        dest = self._new_archive_dir()
        report["archive"] = str(dest)
        for side, direction in (("working", "user_to_working"), ("user", "working_to_user")):
            paths = [a["path"] for a in todo if a["direction"] == direction]
            if paths:
                self._backup_into(dest, paths, side)
        for act in todo:
            to_working = act["direction"] == "user_to_working"
            src_root, dst_root = (self.user_dir, self.working_dir) if to_working else (self.working_dir, self.user_dir)
            side = "working" if to_working else "user"
            src, dst = src_root / act["path"], dst_root / act["path"]
            existed = dst.is_file()
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                failed = self._verify_copy(src, dst)
            except OSError as e:
                failed = [f"copy error: {e}"]
            if failed:
                if existed:
                    shutil.copy2(dest / side / act["path"], dst)
                elif dst.exists():
                    dst.unlink()
                report["rolled_back"].append(act["path"])
                _say(f"  ↩️ Rolled back {act['path']} (failed: {', '.join(failed)})")
            else:
                report["applied"].append({"path": act["path"], "direction": act["direction"], "verified": list(LAYERS)})
                _say(f"  ✓ {act['direction']}: {act['path']} (six layers verified)")
        (dest / "apply-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return report


# ── PULSE.json (Trifecta Protocol v3.0) ───────────────────────────────
def update_pulse(project_dir, fields: Dict, signals: Iterable[Tuple[str, str, str]] = ()) -> Optional[Path]:
    """Merge synk182's keys and signals into docs/PULSE.json, keeping every other key.

    A PULSE.json that does not parse is left untouched and None is returned:
    DevCom5 owns rebuilding it, and overwriting would destroy its history."""
    path = Path(project_dir) / "docs" / "PULSE.json"
    data: Dict = {}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return None
        if not isinstance(data, dict):
            return None
    cs = data.setdefault("cross_skill", {})
    cs.update(fields)
    pending = cs.setdefault("pending_signals", [])
    cutoff = datetime.now().astimezone() - timedelta(days=7)
    kept = []
    for s in pending:
        try:
            old = s.get("consumed") and datetime.fromisoformat(s.get("timestamp", "")) < cutoff
        except (TypeError, ValueError):
            old = False
        if not old:
            kept.append(s)
    now = _now_iso()
    for signal, to, details in signals:
        kept.append({"from": "synk182", "signal": signal, "to": to, "timestamp": now,
                     "details": details, "consumed": False})
    cs["pending_signals"] = kept
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Synk182 engine: compare, plan, back up, apply, verify.")
    ap.add_argument("user_dir")
    ap.add_argument("working_dir")
    ap.add_argument("--threshold", type=float, default=0.60)
    ap.add_argument("--plan", metavar="OUT_JSON", help="write the plan to this file")
    ap.add_argument("--diff", metavar="REL_PATH", help="print a unified diff for one path")
    ap.add_argument("--apply", metavar="PLAN_JSON", help="apply approved items from a plan file")
    ap.add_argument("--approve", default="", help="comma-separated plan ids, or 'new' for every one-sided file")
    ap.add_argument("--pulse", action="store_true", help="record results in USER_DIR/docs/PULSE.json")
    args = ap.parse_args(argv)

    synk = SynkEngine(args.user_dir, args.working_dir, threshold=args.threshold)
    if args.diff:
        _say(synk.diff(args.diff))
        return 0
    results = synk.scan_and_compare(quiet=bool(args.apply))
    drift = results["total"] != results["identical"]
    if args.apply:
        plan = json.loads(Path(args.apply).read_text(encoding="utf-8"))
        if args.approve.strip().lower() == "new":
            ids = [a["id"] for a in plan if a["status"] in ("user_only", "working_only")]
        else:
            ids = [int(x) for x in args.approve.split(",") if x.strip()]
        if not ids:
            _say("Nothing approved: pass --approve with plan ids.")
            return 1
        report = synk.apply(plan, ids)
        _say(f"🔄 Synced: {len(report['applied'])} | Rolled back: {len(report['rolled_back'])} "
             f"| Skipped: {len(report['skipped'])} | Archive: {report['archive']}")
        if args.pulse:
            sigs = [("sync_completed", "devcom5", f"{len(report['applied'])} file(s) written")]
            if report["rolled_back"]:
                sigs.append(("sync_conflict", "devcom5", ", ".join(report["rolled_back"])))
            if any(a["path"] for a in report["applied"]):
                sigs.append(("new_files_synced", "solid8", ", ".join(a["path"] for a in report["applied"])))
            update_pulse(synk.user_dir, {"synk_last_run": _now_iso(), "synk_drift_detected": drift,
                                         "synk_files_changed": len(report["applied"])}, sigs)
        return 1 if report["rolled_back"] else 0
    plan = synk.plan()
    if args.plan:
        Path(args.plan).write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
        _say(f"📋 Plan written: {args.plan} ({len(plan)} item(s); nothing changed on disk)")
    if args.pulse:
        update_pulse(synk.user_dir, {"synk_last_run": _now_iso(), "synk_drift_detected": drift},
                     [("environment_diverged", "devcom5", f"{len(plan)} path(s) differ")] if drift else [])
    return 0


if __name__ == "__main__":
    sys.exit(main())
