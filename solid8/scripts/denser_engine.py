"""
Denser Engine v1.0 — Consolidation Analysis
2026-02-10 | For: denser skill v1.0

Core logic for file fingerprinting, similarity analysis, cluster detection,
and consolidation proposal generation. Mirrors SKILL.md methodology.
"""

import hashlib
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import difflib
import json
from datetime import datetime


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

    def to_dict(self) -> Dict:
        return {
            'path': str(self.path), 'relative': self.relative,
            'hash': self.hash, 'size': self.size,
            'line_count': self.line_count, 'extension': self.extension,
            'name_pattern': self.name_pattern, 'modified': self.modified
        }


@dataclass
class ComparisonResult:
    """Result of comparing two files."""
    file_a: str
    file_b: str
    tier: str          # S, A, B, C, D, or '-'
    similarity: float  # 0.0 to >1.0
    relationship: str  # identical, a_superset, b_superset, standard, unrelated
    delta_summary: str = ""

    def to_dict(self) -> Dict:
        return {
            'file_a': self.file_a, 'file_b': self.file_b,
            'tier': self.tier, 'similarity': self.similarity,
            'relationship': self.relationship, 'delta': self.delta_summary
        }


@dataclass
class ConsolidationProposal:
    """Full consolidation proposal for a project."""
    project: str
    timestamp: str
    files_analyzed: int
    clusters: List[Dict] = field(default_factory=list)
    tier_counts: Dict[str, int] = field(default_factory=lambda: {
        'S': 0, 'A': 0, 'B': 0, 'C': 0, 'D': 0
    })
    potential_reduction: float = 0.0


class DenserEngine:
    """
    File consolidation engine with full similarity spectrum analysis.

    Thresholds (from SKILL.md):
    - Tier S: 100% (hash match)
    - Tier A: >100% (superset/subset)
    - Tier B: 80-99%
    - Tier C: 60-79%
    - Tier D: 30-59%
    - Ignore: <30%
    """

    # Patterns for sprawl detection
    VERSION_PATTERN = re.compile(r'[_-]v(\d+)', re.IGNORECASE)
    COPY_PATTERN = re.compile(r'[\s\-]*(?:copy|Copy|\(\d+\))')
    BACKUP_PATTERN = re.compile(r'\.(bak|old|backup|orig)$', re.IGNORECASE)

    # Directories to always skip
    SKIP_DIRS = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv',
        'bin', 'obj', 'dist', 'build', '.next', '.cache'
    }

    def __init__(self, target_dir: str, threshold_b: float = 0.80,
                 threshold_c: float = 0.60, threshold_d: float = 0.30):
        self.target_dir = Path(target_dir)
        self.threshold_b = threshold_b
        self.threshold_c = threshold_c
        self.threshold_d = threshold_d
        self.fingerprints: Dict[str, FileFingerprint] = {}
        self.comparisons: List[ComparisonResult] = []

    # ── Phase 1: Discovery ──────────────────────────────────────────

    def scan(self) -> Dict[str, FileFingerprint]:
        """Scan target directory and build fingerprint inventory."""
        self.fingerprints.clear()
        for file_path in self._walk_files(self.target_dir):
            rel = str(file_path.relative_to(self.target_dir))
            fp = self._fingerprint(file_path, rel)
            self.fingerprints[rel] = fp
        return self.fingerprints

    def _walk_files(self, root: Path):
        """Walk directory, skipping build artifacts and hidden dirs."""
        for item in sorted(root.iterdir()):
            if item.name.startswith('.') or item.name in self.SKIP_DIRS:
                continue
            if item.is_dir():
                yield from self._walk_files(item)
            elif item.is_file():
                yield item

    def _fingerprint(self, path: Path, relative: str) -> FileFingerprint:
        """Create fingerprint for a single file."""
        stat = path.stat()
        return FileFingerprint(
            path=path, relative=relative,
            hash=self._hash_file(path),
            size=stat.st_size,
            line_count=self._count_lines(path),
            extension=path.suffix.lower(),
            name_pattern=self._detect_pattern(path.stem),
            modified=stat.st_mtime
        )

    def _hash_file(self, path: Path) -> str:
        sha256 = hashlib.sha256()
        try:
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except (OSError, PermissionError):
            return ""

    def _count_lines(self, path: Path) -> int:
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                return sum(1 for _ in f)
        except (OSError, PermissionError):
            return 0

    def _detect_pattern(self, stem: str) -> Optional[str]:
        if self.VERSION_PATTERN.search(stem):
            return 'version'
        if self.COPY_PATTERN.search(stem):
            return 'copy'
        if self.BACKUP_PATTERN.search(stem):
            return 'backup'
        return None

    # ── Phase 2: Comparison ─────────────────────────────────────────

    def compare_all(self) -> List[ComparisonResult]:
        """Compare files within detected clusters."""
        self.comparisons.clear()

        # Group by hash for Tier S (exact dupes)
        hash_groups = self._group_by_hash()
        for h, files in hash_groups.items():
            if len(files) > 1:
                for i, a in enumerate(files):
                    for b in files[i+1:]:
                        self.comparisons.append(ComparisonResult(
                            file_a=a, file_b=b, tier='S',
                            similarity=1.0, relationship='identical'
                        ))

        # Group by base name pattern for sprawl detection
        name_groups = self._group_by_basename()
        for base, files in name_groups.items():
            if len(files) > 1:
                for i, a in enumerate(files):
                    for b in files[i+1:]:
                        if self._already_compared(a, b):
                            continue
                        result = self._compare_pair(a, b)
                        if result.tier != '-':
                            self.comparisons.append(result)

        # Same-size files (potential dupes with different names)
        size_groups = self._group_by_size()
        for size, files in size_groups.items():
            if len(files) > 1 and size > 100:  # Skip tiny files
                for i, a in enumerate(files):
                    for b in files[i+1:]:
                        if self._already_compared(a, b):
                            continue
                        result = self._compare_pair(a, b)
                        if result.tier != '-':
                            self.comparisons.append(result)

        return self.comparisons

    def _compare_pair(self, rel_a: str, rel_b: str) -> ComparisonResult:
        """Compare two files and classify into tier."""
        fp_a = self.fingerprints[rel_a]
        fp_b = self.fingerprints[rel_b]

        # Hash identity check
        if fp_a.hash == fp_b.hash:
            return ComparisonResult(rel_a, rel_b, 'S', 1.0, 'identical')

        # Content comparison
        try:
            lines_a = self._read_lines(fp_a.path)
            lines_b = self._read_lines(fp_b.path)
        except (OSError, PermissionError):
            return ComparisonResult(rel_a, rel_b, '-', 0.0, 'unreadable')

        similarity, relationship = self._calculate_similarity(lines_a, lines_b)

        # Classify into tier
        if relationship in ('a_superset', 'b_superset'):
            tier = 'A'
            delta = self._summarize_delta(lines_a, lines_b, relationship)
        elif similarity >= self.threshold_b:
            tier = 'B'
            delta = f"{similarity:.0%} similar, {abs(len(lines_a)-len(lines_b))} line difference"
        elif similarity >= self.threshold_c:
            tier = 'C'
            delta = f"{similarity:.0%} overlap"
        elif similarity >= self.threshold_d:
            tier = 'D'
            delta = f"{similarity:.0%} conceptual overlap"
        else:
            tier = '-'
            delta = ""

        return ComparisonResult(rel_a, rel_b, tier, similarity, relationship, delta)

    def _calculate_similarity(self, lines_a: List[str],
                              lines_b: List[str]) -> Tuple[float, str]:
        """Calculate similarity with superset detection."""
        set_a = set(line.strip() for line in lines_a if line.strip())
        set_b = set(line.strip() for line in lines_b if line.strip())

        if not set_a or not set_b:
            return 0.0, 'empty'

        # Superset detection
        if set_b.issubset(set_a) and set_a != set_b:
            extra = len(set_a - set_b)
            return 1.0 + (extra / max(len(set_b), 1)) * 0.5, 'a_superset'
        if set_a.issubset(set_b) and set_a != set_b:
            extra = len(set_b - set_a)
            return 1.0 + (extra / max(len(set_a), 1)) * 0.5, 'b_superset'

        # Jaccard similarity
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union) if union else 0.0, 'standard'

    def _summarize_delta(self, lines_a, lines_b, relationship) -> str:
        set_a = set(l.strip() for l in lines_a if l.strip())
        set_b = set(l.strip() for l in lines_b if l.strip())
        if relationship == 'a_superset':
            extra = len(set_a - set_b)
            return f"A is superset: contains all of B + {extra} unique lines"
        else:
            extra = len(set_b - set_a)
            return f"B is superset: contains all of A + {extra} unique lines"

    # ── Grouping Helpers ────────────────────────────────────────────

    def _group_by_hash(self) -> Dict[str, List[str]]:
        groups: Dict[str, List[str]] = {}
        for rel, fp in self.fingerprints.items():
            if fp.hash:
                groups.setdefault(fp.hash, []).append(rel)
        return groups

    def _group_by_basename(self) -> Dict[str, List[str]]:
        """Group files by base name (strip version/copy/backup suffixes)."""
        groups: Dict[str, List[str]] = {}
        for rel, fp in self.fingerprints.items():
            stem = fp.path.stem
            base = self.VERSION_PATTERN.sub('', stem)
            base = self.COPY_PATTERN.sub('', base)
            key = f"{Path(rel).parent}/{base}{fp.extension}"
            groups.setdefault(key, []).append(rel)
        return groups

    def _group_by_size(self) -> Dict[int, List[str]]:
        groups: Dict[int, List[str]] = {}
        for rel, fp in self.fingerprints.items():
            groups.setdefault(fp.size, []).append(rel)
        return groups

    def _already_compared(self, a: str, b: str) -> bool:
        return any(
            (c.file_a == a and c.file_b == b) or
            (c.file_a == b and c.file_b == a)
            for c in self.comparisons
        )

    def _read_lines(self, path: Path) -> List[str]:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.readlines()

    # ── Phase 3-4: Classification & Proposal ────────────────────────

    def generate_proposal(self) -> ConsolidationProposal:
        """Generate consolidation proposal from comparisons."""
        proposal = ConsolidationProposal(
            project=self.target_dir.name,
            timestamp=datetime.now().isoformat(),
            files_analyzed=len(self.fingerprints)
        )

        # Count by tier
        for comp in self.comparisons:
            if comp.tier in proposal.tier_counts:
                proposal.tier_counts[comp.tier] += 1

        # Build clusters
        clusters: Dict[str, Dict] = {}
        for comp in self.comparisons:
            key = f"{comp.tier}:{comp.file_a}"
            if key not in clusters:
                clusters[key] = {
                    'tier': comp.tier, 'files': {comp.file_a, comp.file_b},
                    'comparisons': []
                }
            clusters[key]['files'].add(comp.file_b)
            clusters[key]['comparisons'].append(comp.to_dict())

        proposal.clusters = [
            {'tier': v['tier'], 'files': sorted(v['files']),
             'comparisons': v['comparisons']}
            for v in clusters.values()
        ]

        # Estimate reduction
        removable = proposal.tier_counts['S']  # Exact dupes are safe
        total = len(self.fingerprints)
        proposal.potential_reduction = (removable / total * 100) if total else 0

        return proposal

    # ── Archive ─────────────────────────────────────────────────────

    def create_archive(self, files: List[str], archive_dir: Path,
                       reason: str) -> Path:
        """Archive files before consolidation. Law #3: archive before action."""
        ts = datetime.now().strftime('%Y-%m-%dT%H%M%S')
        dest = archive_dir / f"denser-{ts}"
        dest.mkdir(parents=True, exist_ok=True)

        manifest = {
            'timestamp': ts, 'reason': reason,
            'files': {}
        }

        for rel in files:
            fp = self.fingerprints.get(rel)
            if fp and fp.path.exists():
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(fp.path, target)
                manifest['files'][rel] = {
                    'hash': fp.hash, 'size': fp.size,
                    'action': reason
                }

        with open(dest / 'manifest.json', 'w') as f:
            json.dump(manifest, f, indent=2)

        with open(dest / 'rollback.md', 'w') as f:
            f.write(f"# Rollback: {reason}\n\n")
            f.write(f"Archive created: {ts}\n\n")
            f.write("To restore, copy files from this directory back to:\n")
            f.write(f"`{self.target_dir}`\n\n")
            for rel in files:
                f.write(f"- `{rel}`\n")

        return dest


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    engine = DenserEngine(target)
    print(f"⚗️ Scanning {target}...")
    engine.scan()
    print(f"   {len(engine.fingerprints)} files fingerprinted")
    engine.compare_all()
    proposal = engine.generate_proposal()
    print(f"\n⚗️ Consolidation Proposal: {proposal.project}")
    print(f"   🟢 Exact dupes (S): {proposal.tier_counts['S']}")
    print(f"   🟡 Supersets (A):   {proposal.tier_counts['A']}")
    print(f"   🔵 Near-dupes (B):  {proposal.tier_counts['B']}")
    print(f"   ⚪ Overlap (C):     {proposal.tier_counts['C']}")
    print(f"   ℹ️  Conceptual (D):  {proposal.tier_counts['D']}")
    print(f"   📦 Reduction: ~{proposal.potential_reduction:.0f}%")
