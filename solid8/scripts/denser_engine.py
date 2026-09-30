#!/usr/bin/env python3
"""
Denser Engine v1.3 — Consolidation Analysis
2026-09-30 | For: solid8 skill v1.3 (v1.2 2026-09-30, v1.1 2026-09-15, v1.0 2026-02-10)
Updated: 2026-09-30 04:05 ET — sprawl found across folders, copy numbers, wrong-typed PULSE fields, target check
Updated: 2026-09-30 04:53 ET — a backup is compared as the kind of file it backs up (cfg.json.bak as JSON)
Updated: 2026-09-30 05:37 ET — a backup of a binary is binary, every trailing backup marker is removed, --pulse warns when docs is a file and says a PULSE holding no object holds none
Updated: 2026-09-30 06:09 ET — an --json file that cannot be written is answered with the reason and exit 1, and --pulse still records the scan
Updated: 2026-09-30 07:28 ET — a junction or link inside the target is named and not followed; an empty --json name is answered; a signal stamped with Z is pruned on every Python
Updated: 2026-09-30 13:43 ET — a file that cannot be read is named with the reason and left out, never fingerprinted as empty; a link to a file is named and not followed, a dangling one as such; each candidate file is read once, so a same-size group of hundreds compares in seconds; PULSE stamps are read by one grammar on every Python, and a consumed signal whose stamp cannot be read is pruned with a note; a PULSE saved with a BOM is read; --details below zero is an error
Updated: 2026-09-30 14:32 ET — a file that becomes unreadable between the scan and the compare is named with the reason; the --json proposal caps each cluster's comparisons at 50 and says how many were left out; the timestamp grammar is read exactly as the protocol pins it; everything written is LF
Updated: 2026-09-30 15:25 ET — --details says how many comparisons a cluster holds past its first five; --json's help names the cap of 50 per cluster
Updated: 2026-09-30 17:09 ET — nothing is archived or recorded through a junction or link: create_archive refuses an archive folder, or a folder on the way to it or to an original, that is one, and --pulse refuses a docs or PULSE.json that is one, each naming it
Updated: 2026-09-30 17:46 ET — create_archive checks every path before anything is made (absolute, '..', outside the target or a device: ValueError; a missing original: FileNotFoundError), and asks an archive folder outside the target, and every folder above it, whether it is a link

Fingerprints every file under a folder, compares likely redundant pairs across
the full similarity spectrum, and builds a consolidation proposal. It never
deletes, moves or merges anything: the only thing it writes is an archive
(create_archive), an optional --json proposal, and an optional PULSE update.

Comparison:
  text/code   line-set Jaccard with superset detection
  Markdown    each line keyed by its heading, so moved sections count as change
  JSON        flattened key paths and values, key order ignored
  binary      hash only; never a content tier
  A backup (.bak, .old, .backup, .orig, ~, any number of them) is read as the file it
  backs up: cfg.json.bak as JSON, doc.pdf.bak as a binary.
Files under ARCHIVE/Archive/Archives/archive or POTIMP are intentional: they are
reported only as exact duplicates, or as the subset of a live file.

CLI:
  python denser_engine.py TARGET [--details N] [--json OUT] [--pulse]
  an --json OUT that cannot be written, or an empty name, is answered with the reason,
  exit 1; --pulse still runs; --details takes a count of 0 or more
  A junction or link inside TARGET, to a folder or a file, is named and never followed,
  so a loop cannot repeat files (a dangling one is named as such); a folder that cannot
  be listed and a file that cannot be read are named with the reason, never read as
  absent or empty. Nothing is archived or recorded through a junction or link: an
  archive folder, a folder on the way to it or to an original, a docs or a PULSE.json
  that is one is refused, naming it (--pulse then says the PULSE was not written).
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

BINARY_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp", ".zip", ".skill",
    ".7z", ".gz", ".tar", ".exe", ".dll", ".so", ".pyc", ".docx", ".xlsx", ".pptx",
    ".mp3", ".mp4", ".wav", ".mov", ".woff", ".woff2", ".ttf", ".otf", ".sqlite", ".db",
}


IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003  # a Windows junction
# The one timestamp grammar every engine reads (docs/TRIFECTA.md, Lifecycle): extended
# ISO-8601, the date, T or a space, the time to the minute or the second, an optional
# fraction, then an offset, Z or nothing. Read here, never by fromisoformat, whose reach
# differs between Pythons (3.10 reads neither Z nor a basic-format stamp; 3.11 reads both).
ISO_8601 = re.compile(r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,9}))?)?"
                      r"(Z|[+-]\d{2}:\d{2})?$")  # exactly as pinned: no z, no +0000, no comma fraction
COMPARISONS_CAP = 50  # per cluster in the proposal, as the PULSE map is capped per tier


def _say(text: str = "") -> None:
    """Print without dying on a console that cannot encode the emoji."""
    try:
        print(text)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "ascii"
        print(text.encode(enc, "replace").decode(enc))


def _stamp(text, local: timezone) -> datetime:
    """A signal's timestamp as an aware time, read the same way on every Python by the
    grammar the protocol pins (ISO_8601 above): a fraction is cut to microseconds, an offset
    or Z is kept, and a stamp with neither is local time. Anything else, a basic-format stamp
    or a number included, raises ValueError; so does a date that does not exist."""
    m = ISO_8601.match(text) if isinstance(text, str) else None
    if not m:
        raise ValueError(f"not an extended ISO-8601 timestamp: {text!r}")
    y, mo, d, h, mi, s, frac, off = m.groups()
    if off is None:
        tz = local
    elif off == "Z":
        tz = timezone.utc
    else:
        delta = timedelta(hours=int(off[1:3]), minutes=int(off[-2:]))
        tz = timezone(delta if off[0] == "+" else -delta)
    return datetime(int(y), int(mo), int(d), int(h), int(mi), int(s or 0),
                    int((frac or "0")[:6].ljust(6, "0")), tzinfo=tz)


def _older(stamp: datetime, cutoff: datetime) -> bool:
    """stamp < cutoff, for a stamp at the edge of the calendar too (year 1 or 9999, where
    adjusting for the offset overflows): there the year decides."""
    try:
        return stamp < cutoff
    except OverflowError:
        return stamp.year < cutoff.year


def _is_link(path: Path) -> bool:
    """True for a Windows junction or a symbolic link, to a folder or a file: something the
    walk must not enter or read, since it may loop back into the target or reach outside it."""
    if os.path.islink(path):
        return True
    isjunction = getattr(os.path, "isjunction", None)  # Python 3.12+
    if isjunction is not None:
        return isjunction(path)
    try:  # below 3.12, a junction is a folder with the mount-point reparse tag
        return getattr(os.lstat(path), "st_reparse_tag", 0) == IO_REPARSE_TAG_MOUNT_POINT
    except OSError:
        return False


class LinkRefused(OSError):
    """A write, or a read into an archive, that would pass through a junction or link:
    refused with the link named, never followed."""


def _no_link_between(root: Path, target: Path, what: str) -> None:
    """Raise LinkRefused when anything below root, down to and including target, is a
    junction or link, asked of the disk now."""
    at = Path(root)
    for part in Path(target).relative_to(root).parts:
        at = at / part
        if _is_link(at):
            raise LinkRefused(f"{at} is a junction or link; {what} never goes through one")


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
    comparisons_left_out: int = 0  # over every cluster, past COMPARISONS_CAP each

    def to_dict(self) -> Dict:
        return {
            "project": self.project, "timestamp": self.timestamp,
            "files_analyzed": self.files_analyzed, "tier_counts": self.tier_counts,
            "removable_duplicates": self.removable_duplicates,
            "potential_reduction_percent": round(self.potential_reduction, 1),
            "name_sprawl": self.name_sprawl, "archive_sprawl": self.archive_sprawl,
            "comparisons_cap": COMPARISONS_CAP, "comparisons_left_out": self.comparisons_left_out,
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
    # Every trailing marker, so cfg.json.bak.old and cfg.json.orig~ both come back to cfg.json.
    BACKUP_PATTERN = re.compile(r"(?:\.(?:bak|old|backup|orig)|~)+$", re.IGNORECASE)

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
        self.unreadable: List[str] = []  # "rel: cannot be read (reason)" / "rel: cannot be listed (reason)"
        self.not_followed: List[str] = []
        self._compared: Set[frozenset] = set()
        self._units_of: Dict[str, Optional[Set[str]]] = {}  # each candidate file read once per compare_all

    # ── Phase 1: Discovery ──────────────────────────────────────────
    def scan(self) -> Dict[str, FileFingerprint]:
        """Scan the target folder and build the fingerprint inventory."""
        self.fingerprints.clear()
        self.unreadable.clear()
        self.not_followed.clear()
        for file_path in self._walk_files(self.target_dir):
            rel = file_path.relative_to(self.target_dir).as_posix()
            fp = self._fingerprint(file_path, rel)
            if fp is not None:
                self.fingerprints[rel] = fp
        return self.fingerprints

    def _walk_files(self, root: Path):
        """Walk the tree, skipping build artifacts and hidden entries; a folder that cannot be
        listed is named in self.unreadable with the reason; a junction or link, to a folder
        or a file, is named in self.not_followed and never entered or read: one back into
        the target would show every file again, level after level."""
        def rel(path) -> str:
            try:
                return Path(path).relative_to(root).as_posix()
            except ValueError:
                return str(path)

        def onerror(err):
            self.unreadable.append(f"{rel(getattr(err, 'filename', None) or root)}: cannot be listed ({err.strerror or err})")
        for dirpath, dirnames, filenames in os.walk(root, onerror=onerror):
            here = Path(dirpath)
            walked = [d for d in dirnames if not d.startswith(".") and d not in self.SKIP_DIRS]
            links = [d for d in walked if _is_link(here / d)]  # a skipped one (node_modules) goes unnamed
            self.not_followed += [rel(here / d) for d in sorted(links)]
            dirnames[:] = sorted(d for d in walked if d not in links)
            for name in sorted(filenames):
                if name.startswith("."):
                    continue
                p = here / name
                if _is_link(p):
                    self.not_followed.append(rel(p) + ("" if p.exists() else " (its target is missing)"))
                    continue
                yield p

    def _fingerprint(self, path: Path, relative: str) -> Optional[FileFingerprint]:
        """The file's fingerprint, or None when it cannot be read (held by another process, an
        ACL deny, gone mid-scan): then it is named in self.unreadable with the reason, never
        fingerprinted as an empty file."""
        try:
            stat = path.stat()
            binary = self._is_binary(path)
            digest = self._hash_file(path)
            line_count = 0 if binary else self._count_lines(path)
        except OSError as e:
            self.unreadable.append(f"{relative}: cannot be read ({e.strerror or e})")
            return None
        parts = Path(relative).parts[:-1]
        return FileFingerprint(
            path=path, relative=relative, hash=digest, size=stat.st_size, line_count=line_count,
            extension=self._kind_suffix(path), name_pattern=self._detect_pattern(path.name),
            modified=stat.st_mtime, binary=binary,
            protected=any(p.lower() in self.ARCHIVE_DIRS or p.upper().startswith("POTIMP") for p in parts),
        )

    @staticmethod
    def _hash_file(path: Path) -> str:
        """SHA-256 of a file; raises OSError when it cannot be read, never an empty hash."""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @classmethod
    def _kind_suffix(cls, path: Path) -> str:
        """The suffix of the kind of file this is; a backup is the kind it backs up: doc.pdf.bak is .pdf."""
        return Path(cls.BACKUP_PATTERN.sub("", path.name)).suffix.lower()

    @classmethod
    def _is_binary(cls, path: Path) -> bool:
        if cls._kind_suffix(path) in BINARY_EXTENSIONS:
            return True
        with open(path, "rb") as f:
            return b"\x00" in f.read(8192)

    @staticmethod
    def _count_lines(path: Path) -> int:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)

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
        and a version, copy or backup name against its base name in any folder. Each
        candidate file is read once and its units kept for every pair it is in, so a
        same-size group of hundreds (exported logs, screenshots, fixed-size records) is
        read hundreds of times, not hundreds of thousands."""
        self.comparisons.clear()
        self._compared.clear()
        self._units_of.clear()

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
        units_a, units_b = self._cached_units(rel_a), self._cached_units(rel_b)
        if units_a is None or units_b is None:
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

    def _cached_units(self, rel: str) -> Optional[Set[str]]:
        """The units of a fingerprinted file, read once per compare_all; None when it could
        not be read (held by another process since the scan): then it is named in
        self.unreadable with the reason, once, and read no more; its pairs get no tier."""
        if rel not in self._units_of:
            try:
                self._units_of[rel] = self._units(self.fingerprints[rel].path)
            except OSError as e:
                self._units_of[rel] = None
                self.unreadable.append(f"{rel}: cannot be read ({e.strerror or e})")
        return self._units_of[rel]

    def _units(self, path: Path) -> Set[str]:
        """Comparable units for a file: flattened JSON pairs, heading-keyed Markdown lines, or lines."""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        ext = self._kind_suffix(path)  # a backup is read as the kind it backs up: cfg.json.bak is JSON
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
            for g in groups.values():  # a near-duplicate cluster of n files holds n(n-1)/2 comparisons: capped
                total = len(g["comparisons"])
                proposal.comparisons_left_out += max(0, total - COMPARISONS_CAP)
                proposal.clusters.append({"tier": tier, "files": sorted(g["files"]),
                                          "comparisons": g["comparisons"][:COMPARISONS_CAP],
                                          "comparisons_total": total, "comparisons_left_out": max(0, total - COMPARISONS_CAP)})

        proposal.removable_duplicates = sum(len(g) - 1 for g in self._group_by_hash().values())
        total = len(self.fingerprints)
        proposal.potential_reduction = proposal.removable_duplicates / total * 100 if total else 0.0

        for rel, fp in self.fingerprints.items():
            if fp.name_pattern:
                proposal.name_sprawl.setdefault(fp.name_pattern, []).append(rel)
        for rel, fp in self.fingerprints.items():
            if fp.path.suffix.lower() == ".zip":  # a zip itself; a backup of one (pack.zip.bak) is backup sprawl
                sibling_dir = fp.path.with_suffix("")
                siblings = [r for r, o in self.fingerprints.items()
                            if r != rel and o.path.parent == fp.path.parent and o.path.stem == fp.path.stem]
                if sibling_dir.is_dir() or siblings:
                    proposal.archive_sprawl.append({"zip": rel, "beside": siblings or [sibling_dir.name + "/"]})
        return proposal

    # ── Archive ─────────────────────────────────────────────────────
    def create_archive(self, files: List[str], archive_dir: Path, reason: str) -> Path:
        """Law #3, archive before action: copy originals with a manifest and rollback notes.
        Nothing is written into, or read for, the archive through a junction or link: an
        archive folder, or a folder on the way to it or to an original, that is one raises
        LinkRefused, naming it; for an archive folder outside the target, the folder itself
        and every folder above it are asked. Before anything is made, a path that is
        absolute, holds '..' or lies outside the target raises ValueError, and a missing
        original FileNotFoundError."""
        ts = datetime.now().strftime("%Y-%m-%dT%H%M%S")
        # every path first, before anything is made: one that is absolute, holds "..", or lies
        # outside the target is refused (ValueError), and a missing original too
        # (FileNotFoundError), so an archive holds every file it names or does not exist
        root = os.path.normcase(str(self.target_dir))
        for rel in files:
            p = Path(rel)
            if not rel or rel == "." or p.is_absolute() or p.anchor or ".." in p.parts:
                raise ValueError(f"{rel!r} is not a path inside {self.target_dir}; nothing archived")
            where = os.path.normcase(os.path.abspath(self.target_dir / rel))
            if not where.startswith(root.rstrip(os.sep) + os.sep):
                raise ValueError(f"{rel!r} lies outside {self.target_dir}; nothing archived")
            if not (self.target_dir / rel).is_file():
                raise FileNotFoundError(f"{rel}: no such file under {self.target_dir}; nothing archived")
        archive_dir = Path(archive_dir).absolute()
        # an archive inside the target is checked from the target down; one the caller put
        # elsewhere, from that folder down, and the folder itself and every folder above it
        # are asked too (where it lies is the caller's choice, but never through a link)
        if archive_dir.is_relative_to(self.target_dir):
            base = self.target_dir
        else:
            base = archive_dir
            for p in (archive_dir, *archive_dir.parents):
                if _is_link(p):
                    raise LinkRefused(f"{p} is a junction or link; an archive never goes through one")
        _no_link_between(base, archive_dir, "an archive")
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
                _no_link_between(self.target_dir, src, "an archive")
                target = dest / rel
                _no_link_between(base, target, "an archive")  # before its folders are made or it is written
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)
                manifest["files"][rel] = {"hash": self._hash_file(src), "size": src.stat().st_size, "action": reason}
        lines = [f"# Rollback: {reason}", "", f"Archive created: {ts}", "",
                 "To restore, copy each file below from this folder back to the same relative path under:",
                 f"`{self.target_dir}`", ""]
        lines += [f"- `{rel}`" for rel in manifest["files"]]
        for name, text in (("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False)),
                           ("rollback.md", "\n".join(lines) + "\n")):
            _no_link_between(base, dest / name, "an archive")  # asked just before each write
            (dest / name).write_text(text, encoding="utf-8", newline="\n")
        return dest


# ── PULSE.json (Trifecta Protocol v3.0) ───────────────────────────────
def update_pulse(project_dir, fields: Dict, signals: Iterable[Tuple[str, str, str]] = ()) -> Optional[Path]:
    """Merge solid8's keys and signals into docs/PULSE.json, keeping every other key.

    A PULSE.json that does not parse, or holds no object ([], null), is left
    untouched and None is returned.
    One that parses but holds a wrong-typed field (cross_skill not an object,
    pending_signals null) is handled as if that field were empty, and says so.
    A signal is pruned when it is consumed (JSON true, nothing else) and its
    timestamp, read by the protocol's grammar, is older than seven days; a consumed
    signal whose timestamp cannot be read is pruned with a note; an unconsumed
    signal, and an entry that is not an object, is never touched.
    A docs that is a file raises NotADirectoryError naming it, before anything
    is written; the CLI reports that, and any other OSError, as a warning. So does a
    docs or PULSE.json that is a junction or link (LinkRefused): the PULSE is never read
    or written through one."""
    path = Path(project_dir) / "docs" / "PULSE.json"
    for p in (path.parent, path):
        if _is_link(p):
            raise LinkRefused(f"{p} is a junction or link; the PULSE is never written through one")
    if path.parent.exists() and not path.parent.is_dir():
        raise NotADirectoryError(f"{path.parent} is a file, not a folder")
    data: Dict = {}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))  # some editors save a BOM
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
    local = datetime.now().astimezone().tzinfo
    cutoff = datetime.now(local) - timedelta(days=7)
    kept = []
    for s in pending:
        if not isinstance(s, dict) or s.get("consumed") is not True:
            kept.append(s)
            continue
        try:
            old = _older(_stamp(s.get("timestamp"), local), cutoff)
        except ValueError:
            _say(f"   ⚠️  pruned a consumed signal ({s.get('signal') or s.get('type') or 'unnamed'}) "
                 f"whose timestamp is not extended ISO-8601: {s.get('timestamp')!r}")
            continue
        if not old:
            kept.append(s)
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    for signal, to, details in signals:
        kept.append({"from": "solid8", "signal": signal, "to": to, "timestamp": now,
                     "details": details, "consumed": False})
    cs["pending_signals"] = kept
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return path


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Solid8 Denser engine: consolidation analysis (read-only).")
    ap.add_argument("target", nargs="?", default=".")
    ap.add_argument("--details", type=int, default=0, metavar="N", help="show the top N clusters (0 or more)")
    ap.add_argument("--json", metavar="OUT", help="write the proposal as JSON, comparisons capped at 50 per cluster")
    ap.add_argument("--pulse", action="store_true", help="record the scan in TARGET/docs/PULSE.json")
    args = ap.parse_args(argv)

    if args.details < 0:  # a negative count would slice the list from the end, silently
        _say(f"✗ --details takes a count of clusters to show, 0 or more: got {args.details}")
        return 1
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
        for entry in engine.unreadable:
            _say(f"      {entry}")
    if engine.not_followed:
        _say(f"   ⚠️  junctions or links not followed: {', '.join(engine.not_followed)}")
    order = {t: i for i, t in enumerate("SABCD")}
    for c in sorted(proposal.clusters, key=lambda c: (order[c["tier"]], -len(c["files"])))[:args.details]:
        _say(f"\n   [{c['tier']}] " + " | ".join(c["files"]))
        for comp in c["comparisons"][:5]:
            _say(f"       {comp['similarity']:.2f} {comp['relationship']}: {comp['delta']}")
        if c["comparisons_total"] > 5:  # the terminal shows five; the rest are counted, never dropped silently
            _say(f"       … and {c['comparisons_total'] - 5} more comparison(s) in this cluster")
    json_written = True
    if args.json is not None:  # an empty name ("--json ''", an empty shell variable) is still given
        try:
            if not args.json.strip():
                raise OSError("no file name given")
            Path(args.json).write_text(json.dumps(proposal.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
        except OSError as e:  # a missing folder, a folder in its place, no permission to write
            _say(f"\n   ✗ Proposal not written ({e})")
            json_written = False
        else:
            capped = (f" (comparisons capped at {COMPARISONS_CAP} per cluster; {proposal.comparisons_left_out} left out)"
                      if proposal.comparisons_left_out else "")
            _say(f"\n   📋 Proposal written: {args.json}{capped}")
    if args.pulse:  # the scan is still recorded; only the proposal file failed
        rmap: Dict[str, List[List[str]]] = {}
        for comp in engine.comparisons:
            rmap.setdefault(comp.tier, []).append([comp.file_a, comp.file_b])
        rmap = {t: pairs[:50] for t, pairs in rmap.items()}
        found = sum(tc.values())
        try:
            written = update_pulse(engine.target_dir,
                                   {"solid8_last_run": proposal.timestamp, "solid8_redundancy_map": rmap},
                                   [("redundancy_found", "devcom5", f"{found} redundant pair(s)")] if found else [])
        except OSError as e:  # docs is a file, PULSE.json is a folder, no permission to write
            _say(f"   ⚠️  PULSE.json not written ({e})")
        else:
            _say("   📡 PULSE updated" if written else "   ⚠️  PULSE.json does not hold a JSON object; left untouched")
    return 0 if json_written else 1


if __name__ == "__main__":
    sys.exit(main())
