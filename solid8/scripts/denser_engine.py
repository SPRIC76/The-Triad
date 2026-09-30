#!/usr/bin/env python3
"""
Denser Engine v1.3 — Consolidation Analysis
2026-09-30 | For: solid8 skill v1.3 (v1.2 2026-09-30, v1.1 2026-09-15, v1.0 2026-02-10)
Updated: 2026-09-30 04:05 ET — sprawl found across folders, copy numbers, wrong-typed PULSE fields, target check

Fingerprints every file under a folder, compares likely redundant pairs across
the full similarity spectrum, and builds a consolidation proposal. It never
deletes, moves or merges anything: the only thing it writes is an archive
(create_archive), an optional --json proposal, and an optional PULSE update.

Comparison:
  text/code   line-set Jaccard with superset detection
  Markdown    each line keyed by its heading, so moved sections count as change
  JSON        flattened key paths and values, key order ignored
  binary      hash only; never a content tier
Files under ARCHIVE/Archive/Archives/archive or POTIMP are intentional: they are
reported only as exact duplicates, or as the subset of a live file.

CLI:
  python denser_engine.py TARGET [--details N] [--json OUT] [--pulse]
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

BINARY_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp", ".zip", ".skill",
    ".7z", ".gz", ".tar", ".exe", ".dll", ".so", ".pyc", ".docx", ".xlsx", ".pptx",
    ".mp3", ".mp4", ".wav", ".mov", ".woff", ".woff2", ".ttf", ".otf", ".sqlite", ".db",
}


def _say(text: str = "") -> None:
    """Print without dying on a console that cannot encode the emoji."""
    try:
        print(text)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "ascii"
        print(text.encode(enc, "replace").decode(enc))


@dataclass
class FileFingerprint:
    """Per-file fingerprint collected during Phase 1: Discovery."""
    path: Path
    relative: str
    hash: str
    size: int
    line_count: int
    extension: str
    name_pattern: Optional[str]  # 'version', 'copy', 'backup', or None
    modified: float
    binary: bool = False
    protected: bool = False  # under an archive or POTIMP folder

    def to_dict(self) -> Dict:
        return {
            "relative": self.relative, "hash": self.hash, "size": self.size,
            "line_count": self.line_count, "extension": self.extension,
            "name_pattern": self.name_pattern, "modified": self.modified,
            "binary": self.binary, "protected": self.protected,
        }


@dataclass
class ComparisonResult:
    """Result of comparing two files."""
    file_a: str
    file_b: str
    tier: str          # S, A, B, C, D, or '-'
    similarity: float  # 0.0 to >1.0
    relationship: str  # identical, a_superset, b_superset, standard, binary, empty, unreadable
    delta_summary: str = ""

    def to_dict(self) -> Dict:
        return {
            "file_a": self.file_a, "file_b": self.file_b, "tier": self.tier,
            "similarity": round(self.similarity, 4), "relationship": self.relationship,
            "delta": self.delta_summary,
        }


@dataclass
class ConsolidationProposal:
    """Full consolidation proposal for a project."""
    project: str
    timestamp: str
    files_analyzed: int
    clusters: List[Dict] = field(default_factory=list)
    tier_counts: Dict[str, int] = field(default_factory=lambda: {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0})
    removable_duplicates: int = 0
    potential_reduction: float = 0.0
    name_sprawl: Dict[str, List[str]] = field(default_factory=dict)
    archive_sprawl: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "project": self.project, "timestamp": self.timestamp,
            "files_analyzed": self.files_analyzed, "tier_counts": self.tier_counts,
            "removable_duplicates": self.removable_duplicates,
            "potential_reduction_percent": round(self.potential_reduction, 1),
            "name_sprawl": self.name_sprawl, "archive_sprawl": self.archive_sprawl,
            "clusters": self.clusters,
        }


class DenserEngine:
    """
    File consolidation engine with full similarity spectrum analysis.

    Tiers (from SKILL.md): S 100% hash · A superset (>100%) · B 80-99% ·
    C 60-79% · D 30-59% · below 30% ignored.
    """

    VERSION_PATTERN = re.compile(r"[_\-\s.]v\d+(?:\.\d+)*(?=$|[_\-\s.])", re.IGNORECASE)
    # A copy number has one to three digits: "(2024)" is a year, not a copy.
    COPY_PATTERN = re.compile(r"(?:\s*-\s*copy(?:\s*\(\d{1,3}\))?|\s*\(\d{1,3}\)|[_\s]copy\d*)$", re.IGNORECASE)
    BACKUP_PATTERN = re.compile(r"(?:\.(?:bak|old|backup|orig)|~)$", re.IGNORECASE)

    SKIP_DIRS = {
        "node_modules", ".git", "__pycache__", ".venv", "venv", "bin", "obj",
        "dist", "build", ".next", ".cache", ".pytest_cache",
    }
    ARCHIVE_DIRS = {"archive", "archives"}
    SIZE_FLOOR = 100  # same-size grouping ignores files this small

    def __init__(self, target_dir: str, threshold_b: float = 0.80,
                 threshold_c: float = 0.60, threshold_d: float = 0.30):
        self.target_dir = Path(target_dir).resolve()
        self.threshold_b = threshold_b
        self.threshold_c = threshold_c
        self.threshold_d = threshold_d
        self.fingerprints: Dict[str, FileFingerprint] = {}
        self.comparisons: List[ComparisonResult] = []
        self.unreadable: List[str] = []
        self._compared: Set[frozenset] = set()

    # ── Phase 1: Discovery ──────────────────────────────────────────
    def scan(self) -> Dict[str, FileFingerprint]:
        """Scan the target folder and build the fingerprint inventory."""
        self.fingerprints.clear()
        self.unreadable.clear()
        for file_path in self._walk_files(self.target_dir):
            rel = file_path.relative_to(self.target_dir).as_posix()
            fp = self._fingerprint(file_path, rel)
            if fp is not None:
                self.fingerprints[rel] = fp
        return self.fingerprints

    def _walk_files(self, root: Path):
        """Walk the tree, skipping build artifacts, hidden entries and unreadable folders."""
        def onerror(err):
            self.unreadable.append(str(getattr(err, "filename", err)))
        for dirpath, dirnames, filenames in os.walk(root, onerror=onerror):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d not in self.SKIP_DIRS)
            for name in sorted(filenames):
                if not name.startswith("."):
                    yield Path(dirpath) / name

    def _fingerprint(self, path: Path, relative: str) -> Optional[FileFingerprint]:
        try:
            stat = path.stat()
        except OSError:
            self.unreadable.append(relative)
            return None
        binary = self._is_binary(path)
        parts = Path(relative).parts[:-1]
        return FileFingerprint(
            path=path, relative=relative, hash=self._hash_file(path), size=stat.st_size,
            line_count=0 if binary else self._count_lines(path),
            extension=path.suffix.lower(), name_pattern=self._detect_pattern(path.name),
            modified=stat.st_mtime, binary=binary,
            protected=any(p.lower() in self.ARCHIVE_DIRS or p.upper().startswith("POTIMP") for p in parts),
        )

    @staticmethod
    def _hash_file(path: Path) -> str:
        sha256 = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except OSError:
            return ""

    @staticmethod
    def _is_binary(path: Path) -> bool:
        if path.suffix.lower() in BINARY_EXTENSIONS:
            return True
        try:
            with open(path, "rb") as f:
                return b"\x00" in f.read(8192)
        except OSError:
            return False

    @staticmethod
    def _count_lines(path: Path) -> int:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return sum(1 for _ in f)
        except OSError:
            return 0

    def _detect_pattern(self, name: str) -> Optional[str]:
        """Classify a file NAME (with extension) as backup, copy or version sprawl."""
        if self.BACKUP_PATTERN.search(name):
            return "backup"
        stem = Path(name).stem
        if self.COPY_PATTERN.search(stem):
            return "copy"
        if self.VERSION_PATTERN.search(stem):
            return "version"
        return None

    def _base_name(self, name: str) -> str:
        """The name with backup, copy and version markers removed: report_v2 - Copy.md.bak → report.md."""
        name = self.BACKUP_PATTERN.sub("", name)
        p = Path(name)
        stem = self.COPY_PATTERN.sub("", p.stem)
        stem = self.VERSION_PATTERN.sub("", stem)
        return (stem + p.suffix).lower()

    # ── Phase 2: Comparison ─────────────────────────────────────────
    def compare_all(self) -> List[ComparisonResult]:
        """Compare candidate pairs: same hash, same base name in a folder, same size,
        and a version, copy or backup name against its base name in any folder."""
        self.comparisons.clear()
        self._compared.clear()

        for files in self._group_by_hash().values():
            for i, a in enumerate(files):
                for b in files[i + 1:]:
                    self._compared.add(frozenset((a, b)))
                    self.comparisons.append(ComparisonResult(a, b, "S", 1.0, "identical", "exact duplicate"))

        candidates = list(self._group_by_basename().values()) + \
            [g for size, g in self._group_by_size().items() if size > self.SIZE_FLOOR]
        pairs = [(a, b) for files in candidates for i, a in enumerate(files) for b in files[i + 1:]]
        pairs += self._sprawl_pairs_across_folders()
        for a, b in pairs:
            key = frozenset((a, b))
            if key in self._compared:
                continue
            self._compared.add(key)
            result = self._compare_pair(a, b)
            if result.tier != "-":
                self.comparisons.append(result)
        return self.comparisons

    def _compare_pair(self, rel_a: str, rel_b: str) -> ComparisonResult:
        """Compare two files and classify them into a tier."""
        fp_a, fp_b = self.fingerprints[rel_a], self.fingerprints[rel_b]
        if fp_a.hash and fp_a.hash == fp_b.hash:
            return ComparisonResult(rel_a, rel_b, "S", 1.0, "identical", "exact duplicate")
        if fp_a.binary or fp_b.binary:
            return ComparisonResult(rel_a, rel_b, "-", 0.0, "binary")
        try:
            units_a, units_b = self._units(fp_a.path), self._units(fp_b.path)
        except OSError:
            return ComparisonResult(rel_a, rel_b, "-", 0.0, "unreadable")

        similarity, relationship = self._calculate_similarity(units_a, units_b)
        if relationship in ("a_superset", "b_superset"):
            tier = "A"
            extra = len(units_a - units_b) if relationship == "a_superset" else len(units_b - units_a)
            delta = f"{'A' if relationship == 'a_superset' else 'B'} is superset: holds all of the other + {extra} unique lines"
        elif similarity >= self.threshold_b:
            tier, delta = "B", f"{similarity:.0%} similar, {len(units_a ^ units_b)} lines differ"
        elif similarity >= self.threshold_c:
            tier, delta = "C", f"{similarity:.0%} overlap"
        elif similarity >= self.threshold_d:
            tier, delta = "D", f"{similarity:.0%} conceptual overlap"
        else:
            tier, delta = "-", ""

        # Archives and POTIMP are intentional: only an exact copy, or a protected
        # file that a LIVE file fully contains, is worth reporting. Two protected
        # files, one inside the other, stay where they are (v1.2).
        if tier != "-" and (fp_a.protected or fp_b.protected):
            subset_protected = (relationship == "a_superset" and fp_b.protected and not fp_a.protected) or \
                               (relationship == "b_superset" and fp_a.protected and not fp_b.protected)
            if not subset_protected:
                return ComparisonResult(rel_a, rel_b, "-", similarity, relationship, "protected folder")
        return ComparisonResult(rel_a, rel_b, tier, similarity, relationship, delta)

    def _units(self, path: Path) -> Set[str]:
        """Comparable units for a file: flattened JSON pairs, heading-keyed Markdown lines, or lines."""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        ext = path.suffix.lower()
        if ext == ".json":
            try:
                return set(self._flatten_json(json.loads(text)))
            except ValueError:
                pass
        if ext in (".md", ".markdown"):
            units, heading = set(), ""
            for line in text.splitlines():
                s = line.strip()
                if not s:
                    continue
                if s.startswith("#"):
                    heading = s
                    units.add(s)
                else:
                    units.add(f"{heading} :: {s}")
            return units
        return {line.strip() for line in text.splitlines() if line.strip()}

    def _flatten_json(self, value, prefix: str = "") -> Iterable[str]:
        if isinstance(value, dict):
            if not value:
                yield f"{prefix}={{}}"
            for k, v in value.items():
                yield from self._flatten_json(v, f"{prefix}.{k}" if prefix else str(k))
        elif isinstance(value, list):
            if not value:
                yield f"{prefix}=[]"
            for i, v in enumerate(value):
                yield from self._flatten_json(v, f"{prefix}[{i}]")
        else:
            yield f"{prefix}={json.dumps(value, ensure_ascii=False)}"

    @staticmethod
    def _calculate_similarity(set_a: Set[str], set_b: Set[str]) -> Tuple[float, str]:
        """Jaccard similarity; over 1.0 when one side holds all of the other plus more."""
        if not set_a or not set_b:
            return 0.0, "empty"
        if set_a == set_b:
            return 1.0, "standard"
        if set_b < set_a:
            return 1.0 + len(set_a - set_b) / len(set_b) * 0.5, "a_superset"
        if set_a < set_b:
            return 1.0 + len(set_b - set_a) / len(set_a) * 0.5, "b_superset"
        return len(set_a & set_b) / len(set_a | set_b), "standard"

    # ── Grouping Helpers ────────────────────────────────────────────
    def _group_by_hash(self) -> Dict[str, List[str]]:
        groups: Dict[str, List[str]] = {}
        for rel, fp in self.fingerprints.items():
            if fp.hash:
                groups.setdefault(fp.hash, []).append(rel)
        return {h: g for h, g in groups.items() if len(g) > 1}

    def _group_by_basename(self) -> Dict[str, List[str]]:
        groups: Dict[str, List[str]] = {}
        for rel, fp in self.fingerprints.items():
            key = f"{Path(rel).parent.as_posix()}/{self._base_name(fp.path.name)}"
            groups.setdefault(key, []).append(rel)
        return {k: g for k, g in groups.items() if len(g) > 1}

    def _sprawl_pairs_across_folders(self) -> List[Tuple[str, str]]:
        """Version, copy and backup sprawl that crossed a folder boundary: a marked file
        against every file of the same base name in any other folder (v1.3). Two
        unmarked files that merely share a name are left to the per-folder and same-size
        groupings, so a README.md in every folder is never paired with itself."""
        by_base: Dict[str, List[str]] = {}
        for rel, fp in self.fingerprints.items():
            by_base.setdefault(self._base_name(fp.path.name), []).append(rel)
        pairs = []
        for files in by_base.values():
            if len({Path(r).parent for r in files}) < 2:
                continue
            for i, a in enumerate(files):
                for b in files[i + 1:]:
                    if self.fingerprints[a].name_pattern or self.fingerprints[b].name_pattern:
                        pairs.append((a, b))
        return pairs

    def _group_by_size(self) -> Dict[int, List[str]]:
        groups: Dict[int, List[str]] = {}
        for rel, fp in self.fingerprints.items():
            groups.setdefault(fp.size, []).append(rel)
        return {s: g for s, g in groups.items() if len(g) > 1}

    # ── Phase 3-4: Classification & Proposal ────────────────────────
    def generate_proposal(self) -> ConsolidationProposal:
        proposal = ConsolidationProposal(
            project=self.target_dir.name,
            timestamp=datetime.now().astimezone().isoformat(timespec="seconds"),
            files_analyzed=len(self.fingerprints),
        )
        for comp in self.comparisons:
            if comp.tier in proposal.tier_counts:
                proposal.tier_counts[comp.tier] += 1

        # One cluster per connected group of files within a tier.
        for tier in "SABCD":
            parent: Dict[str, str] = {}

            def find(x):
                while parent.setdefault(x, x) != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x
            comps = [c for c in self.comparisons if c.tier == tier]
            for c in comps:
                parent[find(c.file_a)] = find(c.file_b)
            groups: Dict[str, Dict] = {}
            for c in comps:
                g = groups.setdefault(find(c.file_a), {"tier": tier, "files": set(), "comparisons": []})
                g["files"].update((c.file_a, c.file_b))
                g["comparisons"].append(c.to_dict())
            for g in groups.values():
                proposal.clusters.append({"tier": tier, "files": sorted(g["files"]), "comparisons": g["comparisons"]})

        proposal.removable_duplicates = sum(len(g) - 1 for g in self._group_by_hash().values())
        total = len(self.fingerprints)
        proposal.potential_reduction = proposal.removable_duplicates / total * 100 if total else 0.0

        for rel, fp in self.fingerprints.items():
            if fp.name_pattern:
                proposal.name_sprawl.setdefault(fp.name_pattern, []).append(rel)
        for rel, fp in self.fingerprints.items():
            if fp.extension == ".zip":
                sibling_dir = fp.path.with_suffix("")
                siblings = [r for r, o in self.fingerprints.items()
                            if r != rel and o.path.parent == fp.path.parent and o.path.stem == fp.path.stem]
                if sibling_dir.is_dir() or siblings:
                    proposal.archive_sprawl.append({"zip": rel, "beside": siblings or [sibling_dir.name + "/"]})
        return proposal

    # ── Archive ─────────────────────────────────────────────────────
    def create_archive(self, files: List[str], archive_dir: Path, reason: str) -> Path:
        """Law #3, archive before action: copy originals with a manifest and rollback notes."""
        ts = datetime.now().strftime("%Y-%m-%dT%H%M%S")
        archive_dir = Path(archive_dir)
        dest = archive_dir / f"solid8-{ts}"
        n = 1
        while dest.exists():
            n += 1
            dest = archive_dir / f"solid8-{ts}-{n}"
        dest.mkdir(parents=True)

        manifest = {"timestamp": ts, "reason": reason, "source": str(self.target_dir), "files": {}}
        for rel in files:
            fp = self.fingerprints.get(rel)
            src = fp.path if fp else self.target_dir / rel
            if src.is_file():
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)
                manifest["files"][rel] = {"hash": self._hash_file(src), "size": src.stat().st_size, "action": reason}
        (dest / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

        lines = [f"# Rollback: {reason}", "", f"Archive created: {ts}", "",
                 "To restore, copy each file below from this folder back to the same relative path under:",
                 f"`{self.target_dir}`", ""]
        lines += [f"- `{rel}`" for rel in manifest["files"]]
        (dest / "rollback.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return dest


# ── PULSE.json (Trifecta Protocol v3.0) ───────────────────────────────
def update_pulse(project_dir, fields: Dict, signals: Iterable[Tuple[str, str, str]] = ()) -> Optional[Path]:
    """Merge solid8's keys and signals into docs/PULSE.json, keeping every other key.

    A PULSE.json that does not parse is left untouched and None is returned.
    One that parses but holds a wrong-typed field (cross_skill not an object,
    pending_signals null) is handled as if that field were empty, and says so."""
    path = Path(project_dir) / "docs" / "PULSE.json"
    data: Dict = {}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return None
        if not isinstance(data, dict):
            return None
    cs = data.get("cross_skill")
    if not isinstance(cs, dict):
        if cs is not None:
            _say("   ⚠️  PULSE cross_skill is not an object; treated as empty")
        cs = data["cross_skill"] = {}
    cs.update(fields)
    pending = cs.get("pending_signals")
    if not isinstance(pending, list):
        if "pending_signals" in cs:
            _say("   ⚠️  PULSE pending_signals is not a list; treated as empty")
        pending = []
    cutoff = datetime.now().astimezone() - timedelta(days=7)
    kept = []
    for s in pending:
        try:
            old = s.get("consumed") and datetime.fromisoformat(s.get("timestamp", "")) < cutoff
        except (AttributeError, TypeError, ValueError):
            old = False  # an entry that is not an object is kept as it is
        if not old:
            kept.append(s)
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    for signal, to, details in signals:
        kept.append({"from": "solid8", "signal": signal, "to": to, "timestamp": now,
                     "details": details, "consumed": False})
    cs["pending_signals"] = kept
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Solid8 Denser engine: consolidation analysis (read-only).")
    ap.add_argument("target", nargs="?", default=".")
    ap.add_argument("--details", type=int, default=0, metavar="N", help="show the top N clusters")
    ap.add_argument("--json", metavar="OUT", help="write the full proposal as JSON")
    ap.add_argument("--pulse", action="store_true", help="record the scan in TARGET/docs/PULSE.json")
    args = ap.parse_args(argv)

    if not Path(args.target).is_dir():
        _say(f"✗ The target is not a folder: {args.target}")
        return 1
    engine = DenserEngine(args.target)
    _say(f"⚗️ Scanning {engine.target_dir} ...")
    engine.scan()
    engine.compare_all()
    proposal = engine.generate_proposal()
    tc = proposal.tier_counts
    _say(f"   {proposal.files_analyzed} files fingerprinted | Clusters: {len(proposal.clusters)}")
    _say(f"\n⚗️ Consolidation Proposal: {proposal.project}")
    _say(f"   🟢 Exact dupes (S): {tc['S']}")
    _say(f"   🟡 Supersets (A):   {tc['A']}")
    _say(f"   🔵 Near-dupes (B):  {tc['B']}")
    _say(f"   ⚪ Overlap (C):     {tc['C']}")
    _say(f"   ℹ️  Conceptual (D):  {tc['D']}")
    _say(f"   📦 Reduction: ~{proposal.potential_reduction:.0f}% ({proposal.removable_duplicates} exact duplicate file(s))")
    for kind, files in sorted(proposal.name_sprawl.items()):
        _say(f"   🏷️  {kind} names: {len(files)}")
    if proposal.archive_sprawl:
        _say(f"   🗜️  zips beside their contents: {len(proposal.archive_sprawl)}")
    if engine.unreadable:
        _say(f"   ⚠️  unreadable: {len(engine.unreadable)}")
    order = {t: i for i, t in enumerate("SABCD")}
    for c in sorted(proposal.clusters, key=lambda c: (order[c["tier"]], -len(c["files"])))[:args.details]:
        _say(f"\n   [{c['tier']}] " + " | ".join(c["files"]))
        for comp in c["comparisons"][:5]:
            _say(f"       {comp['similarity']:.2f} {comp['relationship']}: {comp['delta']}")
    if args.json:
        Path(args.json).write_text(json.dumps(proposal.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        _say(f"\n   📋 Proposal written: {args.json}")
    if args.pulse:
        rmap: Dict[str, List[List[str]]] = {}
        for comp in engine.comparisons:
            rmap.setdefault(comp.tier, []).append([comp.file_a, comp.file_b])
        rmap = {t: pairs[:50] for t, pairs in rmap.items()}
        found = sum(tc.values())
        written = update_pulse(engine.target_dir,
                               {"solid8_last_run": proposal.timestamp, "solid8_redundancy_map": rmap},
                               [("redundancy_found", "devcom5", f"{found} redundant pair(s)")] if found else [])
        _say("   📡 PULSE updated" if written else "   ⚠️  PULSE.json did not parse; left untouched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
