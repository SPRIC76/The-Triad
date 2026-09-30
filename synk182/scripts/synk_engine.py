#!/usr/bin/env python3
"""
Synk Engine v2.1 — compare two copies of a project, plan, back up, apply, verify.
2026-09-15 | For: synk182 skill v3.3 (v2.0 2026-09-15 for v3.1; v1.0 2026-02-10 compared only)
Updated: 2026-09-30 04:05 ET — plan paths bounded to the copies, stale plan refused, wrong-typed PULSE fields, CLI messages
Updated: 2026-09-30 04:53 ET — folder targets refused, rollback never deletes a folder, unknown --approve ids and one folder given twice are errors, an unparseable PULSE is reported, sync_completed and new_files_synced only when true
Updated: 2026-09-30 05:37 ET — an approved item with no direction exits 1 with its reason, an item with no path is named by its id, --plan with --apply and --diff with another action are errors, --pulse warns when docs is a file and says a PULSE holding no object holds none
Updated: 2026-09-30 06:09 ET — a --plan file that cannot be written is answered with the reason and exit 1, and --pulse still records the scan; the --approve new listing names an item with no path by its id
Updated: 2026-09-30 07:28 ET — a junction or link inside either copy, a folder that cannot be listed and a file where ARCHIVE goes are named and not compared; apply refuses before any write when no backup can be made; a hand-edited plan (an id that is not a whole number, hashes that are not an object) is refused; an empty --plan, --apply or --diff name is answered; a signal stamped with Z is pruned on every Python
Updated: 2026-09-30 13:43 ET — a file that cannot be read is named with the reason and left out of the comparison, never read as empty, and an item that names one is refused; a backup that fails refuses every item and leaves no archive; any exception in verification rolls the copy back, and a failed rollback names the backup; where the file system folds case, any spelling of ARCHIVE is Synk's folder and Readme.md / README.md are one file; copies that differ only in line endings are said so on the dashboard, in the plan and by --diff, which also refuses a path outside the copies and names a file it cannot read; a link to a file is named and not followed, a dangling one as such; PULSE stamps are read by one grammar on every Python, and a consumed signal whose stamp cannot be read is pruned with a note; a plan path in a folder the scan skips, one ending in a separator or a space, and a duplicate id are refused; --threshold outside 0..1 is an error; a plan or PULSE saved with a BOM is read; an already-applied item says so
Updated: 2026-09-30 14:32 ET — a skipped folder in any spelling the file system folds, a link on either side, a form Windows reserves and an item already applied, whatever its status, are refused before any write; line endings that differ within a file and a byte-order mark alone are named as such, on the dashboard, in the plan and by --diff; anything raised while backing up refuses every item and leaves no archive; a nested archive/ is named as a folder, not as Synk's own; the timestamp grammar is read exactly as the protocol pins it; everything written is LF
Updated: 2026-09-30 15:25 ET — device names are asked of the running OS (os.path.abspath), never listed, so con.txt, aux/ and COM1 sync on Windows 11 and NUL is refused on every Windows; --approve new counts each item it refuses and exits 1; only .git, .hg, .svn, node_modules and the root's ARCHIVE fold case, so Build/ and a nested archive/ are compared and synced; an item already applied is reported as such at exit 0, with no sync_conflict; a byte-order mark is named beside any other difference; link answers are asked once per prefix, the destination hashed once and each refusal computed once
Updated: 2026-09-30 15:58 ET — no link or refusal answer outlives the public call that asked it, and each destination's folders are asked again, uncached, just before its write, so a junction made after new_ids, refusal or the checks is refused; only \\\\.\\ is a device: roots given as \\\\?\\C:\\... are used in their plain form and sync; a folder skipped as spelled in one copy and spelled otherwise in the other is named, not offered; a nested ARCHIVE/ is content; --approve new with nothing left to approve exits 0; apply-report.json holds --approve new's refusals

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
        (--diff=-name for a name that starts with a dash); copies that hold the same
        lines are said to differ in line endings, only in a byte-order mark, or in bytes
        no line shows, and a BOM on one side is named beside any other difference; a path
        that leaves the copies, and a file that cannot be read, are answered with exit 1
  python synk_engine.py USER_DIR WORKING_DIR --apply plan.json --approve 3,7
        back up, copy each approved item in its direction, verify six layers,
        roll back any item that fails; --approve new approves every one-sided file, and
        names each one it leaves out (docs/PULSE.json by design; any other is refused,
        written to apply-report.json, and exits 1; with nothing left to approve, it says
        so, exit 0); an item whose path leaves either copy, lies in a folder the scan
        skips, ends in a separator or a space, names a device or a form Windows reserves,
        or names a folder, whose source or destination cannot be read, or whose
        destination changed since the plan was written, is refused before any backup or
        write, and so is one whose destination folder became a junction or link since
        (asked again, uncached, just before the write); roots given as \\\\?\\C:\\... are
        used in their plain form, where the OS maps devices; one already applied is
        reported as such, exit 0; the source is copied as it is
        at apply time; an id that names no plan item, or one that appears twice, stops
        the run before anything is applied; an approved item with no direction, or a
        direction that is not user_to_working or working_to_user, is skipped with its
        reason, and exits 1
  --plan, --diff and --apply are separate runs; --diff takes no --pulse;
        a --plan file that cannot be written, or an empty name given to --plan,
        --apply or --diff, is answered with the reason, exit 1; a plan whose ids are
        not whole numbers or whose hashes are not objects is refused before any write;
        when no backup folder can be made (a file named ARCHIVE), or a backup fails
        midway, nothing is written and no archive folder is left behind; any exception
        while verifying a copy rolls it back, and a rollback that fails names the backup
        to restore by hand
  Not compared, and named on the dashboard: a junction or link inside either copy, to
        a folder or a file (never followed, so a loop cannot repeat paths; a dangling
        one is named as such), a folder that cannot be listed or a file that cannot be
        read (named with the reason, never read as absent or empty), and a file in the
        place of the ARCHIVE folder. Where the file system folds case (Windows, default
        macOS), any spelling of ARCHIVE at a copy's root is Synk's backup folder, skipped
        and named (a nested archive/ or ARCHIVE/ is content), .git, .hg, .svn and
        node_modules are skipped in any spelling (build-output names only as spelled, and
        one skipped as spelled in one copy but spelled otherwise in the other is named:
        "skipped: spelled build in the user copy and Build in the working copy; rename one
        to sync it"), and a file whose name differs only in case between the copies is one
        item
  --threshold 0.6 (between 0 and 1)   --pulse (write results to USER_DIR/docs/PULSE.json)
"""

import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import stat
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Dict, Iterable, List, Optional, Tuple

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
    "bin", "obj", "dist", "build", ".next", ".cache", ".pytest_cache", "ARCHIVE",
}
# the skip names folded where the file system folds case: there .GIT/ IS .git/ (a hook under
# it runs) and NODE_MODULES/ is node_modules/. Build/, Dist/ or Bin/ is often authored content,
# so a build-output name is skipped only as spelled; ARCHIVE folds only at a copy's root.
FOLDED_SKIPS = {".git", ".hg", ".svn", "node_modules"}
LAYERS = ["existence", "hash", "size", "timestamp", "line_count", "content"]
TIMESTAMP_TOLERANCE_S = 2.0
DIRECTIONS = ("user_to_working", "working_to_user")
PULSE_REL = "docs/PULSE.json"
IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003  # a Windows junction
PULSE_UNTOUCHED = "  ⚠️ PULSE.json does not hold a JSON object; left untouched, so this run is not recorded there"
# The one timestamp grammar every engine reads (docs/TRIFECTA.md, Lifecycle): extended
# ISO-8601, the date, T or a space, the time to the minute or the second, an optional
# fraction, then an offset, Z or nothing. Read here, never by fromisoformat, whose reach
# differs between Pythons (3.10 reads neither Z nor a basic-format stamp; 3.11 reads both).
ISO_8601 = re.compile(r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,9}))?)?"
                      r"(Z|[+-]\d{2}:\d{2})?$")  # exactly as pinned: no z, no +0000, no comma fraction
BOM = b"\xef\xbb\xbf"
# characters Windows reserves in a path segment: a copy under such a name lands somewhere
# else (a trailing dot or space is stripped), in a stream (a colon), or fails. Device names
# are not listed: which names are devices differs between Windows versions (Windows 11 maps
# only a bare NUL; Windows 10 also con.txt), so the running OS is asked (refusal, below).
WINDOWS_FORBIDDEN = set('<>:"|?*') | {chr(i) for i in range(32)}


def _plain(root: str) -> Optional[str]:
    """A root without the \\\\?\\ prefix a caller may give it (\\\\?\\C:\\x is C:\\x, and
    \\\\?\\UNC\\server\\share is \\\\server\\share), or None when it has no plain form (a volume
    mounted by GUID). Under a \\\\?\\ root Windows maps no device name, so NUL written there
    is a real file ordinary tools cannot delete: devices are asked of the plain form."""
    if not root.startswith("\\\\?\\"):
        return root
    rest = root[4:]
    if rest[:4].upper() == "UNC\\":
        return "\\\\" + rest[4:]
    return rest if PureWindowsPath(rest).drive[1:2] == ":" else None


def _within(where: str, root: str) -> bool:
    """Whether where (as os.path.abspath gives it) is root or lies under it: a device,
    \\\\.\\NUL, lies under no root. Compared as the OS compares names (os.path.normcase)."""
    w, r = os.path.normcase(where), os.path.normcase(root).rstrip("\\/")
    return w == r or w.startswith(r + os.sep) or (os.altsep is not None and w.startswith(r + os.altsep))


def _say(text: str = "") -> None:
    """Print without dying on a console that cannot encode the emoji."""
    try:
        print(text)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "ascii"
        print(text.encode(enc, "replace").decode(enc))


def _hash(path: Path) -> str:
    """SHA-256 of a file. Raises OSError when it cannot be read: an unreadable file is
    named, never hashed as empty and compared."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_binary(path: Path) -> bool:
    with open(path, "rb") as f:
        return b"\x00" in f.read(8192)


def _lines(path: Path) -> List[str]:
    """The text lines of a file, a leading UTF-8 BOM dropped (a mark, not a line)."""
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        return f.read().splitlines()


def _ending(data: bytes) -> str:
    """How a text file's bytes (its BOM already dropped) end their lines, said for two
    copies that hold the same lines: CRLF, LF, CR, mixed (which ones) or none, and whether
    the last line has one."""
    crlf = data.count(b"\r\n")
    kinds = [k for k, n in (("CRLF", crlf), ("LF", data.count(b"\n") - crlf), ("CR", data.count(b"\r") - crlf)) if n]
    kind = kinds[0] if len(kinds) == 1 else "mixed (" + " and ".join(kinds) + ")" if kinds else "none"
    return kind + (", no final newline" if data and not data.endswith((b"\n", b"\r")) else "")


def _terminators(data: bytes) -> List[bytes]:
    """Each line's ending, in order, so two files that end their lines in the same mix can
    still be told apart line by line (a\\r\\nb\\n against a\\nb\\r\\n)."""
    return [re.search(rb"\r\n|\r|\n|$", line).group() for line in data.splitlines(keepends=True)]


def _bom_sides(u: Path, w: Path) -> Optional[Dict]:
    """Which side carries a UTF-8 byte-order mark, when exactly one does; else None. Asked
    of every text pair that differs, whatever else differs, so a BOM is never copied or
    stripped without a word."""
    def has(p: Path) -> bool:
        with open(p, "rb") as f:
            return f.read(3) == BOM
    bu, bw = has(u), has(w)
    return {"user": bu, "working": bw} if bu != bw else None


def _bom_words(bom: Dict) -> str:
    carrier, other = ("user", "working") if bom["user"] else ("working", "user")
    return f"the {carrier} copy carries a UTF-8 BOM, the {other} copy none"


def _same_lines_differ(u: Path, w: Path) -> Dict:
    """What tells two copies apart when a line diff shows nothing and the hashes differ:
    their line endings by convention ("line_endings", each side's named), line endings
    that differ line by line inside the same mix ("line_endings", within), only a UTF-8
    byte-order mark ("bom", which side carries it; a BOM alone against an empty file too),
    or bytes no line shows ("bytes"). Endings are read past a BOM, and a BOM that differs
    beside another difference is named too ("bom" beside the relationship)."""
    bu, bw = u.read_bytes().removeprefix(BOM), w.read_bytes().removeprefix(BOM)
    bom = _bom_sides(u, w)
    extra = {"bom": bom} if bom else {}
    eu, ew = _ending(bu), _ending(bw)
    if eu != ew:
        return {"relationship": "line_endings", "endings": {"user": eu, "working": ew}, "within": False, **extra}
    if _terminators(bu) != _terminators(bw):
        return {"relationship": "line_endings", "endings": {"user": eu, "working": ew}, "within": True, **extra}
    if bom and bu == bw:
        return {"relationship": "bom", "bom": bom}
    return {"relationship": "bytes", **extra}


def _said_apart(rel: str, d: Dict) -> str:
    """The one line --diff prints for a pair that holds the same lines."""
    e = d.get("endings", {})
    also = f"; they differ in a byte-order mark too: {_bom_words(d['bom'])}" if d.get("bom") and d["relationship"] != "bom" else ""
    if d["relationship"] == "line_endings" and d["within"]:
        return f"user/{rel} and working/{rel} hold the same lines; line endings differ within the file: user {e['user']}, working {e['working']}{also}"
    if d["relationship"] == "line_endings" and also:
        return f"user/{rel} and working/{rel} hold the same lines; line endings differ: user {e['user']}, working {e['working']}{also}"
    if d["relationship"] == "line_endings":
        return f"user/{rel} and working/{rel} differ only in line endings: user {e['user']}, working {e['working']}"
    if d["relationship"] == "bom":
        return f"user/{rel} and working/{rel} differ only in a byte-order mark: {_bom_words(d['bom'])}"
    return f"user/{rel} and working/{rel} hold the same lines in different bytes (an encoding difference no line diff shows){also}"


def _readable(path: Path) -> Optional[str]:
    """None when the file opens and its first bytes read; otherwise the OS reason. A file
    held by another process, or denied by an ACL, fails here, before any backup or copy."""
    try:
        with open(path, "rb") as f:
            f.read(65536)
    except OSError as e:
        return f"cannot be read ({e.strerror or e})"
    return None


def _folds_case(folder: Path) -> bool:
    """True where the file system folds case at folder (Windows, default macOS): the
    folder's own name in another case reaches the same entry. Asked of the folder, not of
    the OS, so a case-sensitive volume mounted on Windows answers for itself; a name with
    no letters asks its parent; a drive's root answers with os.path.normcase."""
    p = Path(folder)
    while p.name and p.name.swapcase() == p.name:
        p = p.parent
    if not p.name:
        return os.path.normcase("A") != "A"
    other = p.with_name(p.name.swapcase())
    try:
        return other.exists() and os.path.samefile(other, p)
    except OSError:
        return False


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _whole(value) -> bool:
    """True for a plan id as --plan writes it: a whole number (1, or 1.0), not "1", [1] or true."""
    return type(value) is int or (type(value) is float and value.is_integer())


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


def _is_link(path) -> bool:
    """True for a Windows junction or a symbolic link, to a folder or a file: something the
    scan must not enter or read, since it may loop back into the copy or reach outside it.
    One lstat answers both on every Python (os.path.islink and os.path.isjunction each make
    their own): a link's mode, or a junction's mount-point reparse tag."""
    try:
        st = os.lstat(path)
    except (OSError, ValueError):
        return False
    return stat.S_ISLNK(st.st_mode) or getattr(st, "st_reparse_tag", 0) == IO_REPARSE_TAG_MOUNT_POINT


class SynkEngine:
    """Bidirectional comparison and verified copying across the full similarity spectrum."""

    def __init__(self, user_dir: str, working_dir: str, threshold: float = 0.60,
                 skip_dirs: Optional[Iterable[str]] = None):
        # a root given as \\?\C:\... or \\?\UNC\... is used in its plain form, where devices
        # are what the OS says they are; one with no plain form keeps its prefix
        self.user_dir, self.working_dir = (Path(_plain(str(r)) or str(r)) for r in
                                           (Path(user_dir).resolve(), Path(working_dir).resolve()))
        self.threshold = threshold  # Correction #2
        self.skip_dirs = set(SKIP_DIRS if skip_dirs is None else skip_dirs)
        self.archive_root = self.user_dir / "ARCHIVE"  # respelled as it is on disk by _archive_root
        self.user_files: Dict[str, Dict] = {}
        self.working_files: Dict[str, Dict] = {}
        self.not_compared: List[Dict] = []
        self._skipped_as_spelled: Dict[str, List[str]] = {"user": [], "working": []}
        self.results: Optional[Dict] = None
        self._folds: Dict[Path, bool] = {}
        self._folded = {d.lower() for d in self.skip_dirs if d.lower() in FOLDED_SKIPS}
        # a path prefix's link answer and device answer, kept only within one public call
        # (apply, new_ids, left_out_of_new) and dropped at its end: None between calls, so
        # nothing a caller asked earlier outlives a junction that appeared since
        self._links: Optional[Dict[str, bool]] = None
        self._devices: Optional[Dict[str, str]] = None
        # the OS is asked about devices under each root's plain form (a stand-in drive root
        # for one with none: device names are mapped by name, not by where they lie)
        self._device_roots = [_plain(str(r)) or os.path.abspath(os.sep) for r in (self.user_dir, self.working_dir)]

    def _folds_case(self, root: Path) -> bool:
        if root not in self._folds:
            self._folds[root] = _folds_case(root)
        return self._folds[root]

    def _is_link(self, path: str) -> bool:
        if self._links is None:
            return _is_link(path)
        if path not in self._links:
            self._links[path] = _is_link(path)
        return self._links[path]

    def _device_at(self, plain: str, parts: Tuple[str, ...]) -> str:
        """Where the OS puts plain/parts (os.path.abspath), asked once per prefix in a call."""
        key = os.path.join(plain, *parts)
        if self._devices is None:
            return os.path.abspath(key)
        if key not in self._devices:
            self._devices[key] = os.path.abspath(key)
        return self._devices[key]

    @contextmanager
    def _one_call(self):
        """Link answers cached for the length of one public call, built at its start and
        dropped at its end; a call made inside another shares the outer one's."""
        outer = self._links is None
        if outer:
            self._links, self._devices = {}, {}
        try:
            yield
        finally:
            if outer:
                self._links = self._devices = None

    def _link_on_the_way(self, root: Path, rel: str) -> Optional[str]:
        """The first prefix of rel under root that is a junction or link, asked of the disk
        now, never of a cache: checked immediately before each write."""
        parts, base = PureWindowsPath(rel).parts, str(root)
        for i in range(1, len(parts) + 1):
            if _is_link(os.path.join(base, *parts[:i])):
                return "/".join(parts[:i])
        return None

    def _spells_archive(self, name: str, root: Path) -> bool:
        """Whether name, at a copy's root, is Synk's ARCHIVE: the exact name, or any spelling
        of it where the file system folds case (there archive/ and Archive/ ARE that folder).
        Below the root only the exact ARCHIVE is skipped; a nested archive/ is content."""
        return name == "ARCHIVE" or (name.upper() == "ARCHIVE" and self._folds_case(root))

    def _skipped(self, name: str, root: Path, top: bool = False) -> bool:
        """Whether name is a folder the scan skips in root: an exact skip name, or, where the
        file system folds case, any spelling of a version-control or package folder (there
        .GIT/ IS .git/, and a hook under it runs) or, at the copy's root (top), of ARCHIVE.
        ARCHIVE is Synk's only at the root: a nested ARCHIVE/, exactly so spelled, is content."""
        if name in self.skip_dirs:
            return top or name != "ARCHIVE"
        if not self._folds_case(root):
            return False
        low = name.lower()
        return low in self._folded or (top and low == "archive" and "ARCHIVE" in self.skip_dirs)

    def _archive_root(self) -> Path:
        """user_dir/ARCHIVE as it is on disk: where the file system folds case, an existing
        archive/ or Archive/ is that folder, and it is used and printed under its own spelling."""
        if self._folds_case(self.user_dir):
            try:
                for name in os.listdir(self.user_dir):
                    if name.upper() == "ARCHIVE":
                        self.archive_root = self.user_dir / name
                        break
            except OSError:
                pass
        return self.archive_root

    # ── Inventory ──────────────────────────────────────────────────────
    def _scan_directory(self, root: Path, other_root: Path, side: str) -> Dict[str, Dict]:
        """Fingerprint every file under root. A junction or link (to a folder or a file), a
        folder that cannot be listed, a file that cannot be read, a file named ARCHIVE at the
        top (where Synk's backups go) and, where the file system folds case, an archive/ in
        any spelling at the top are not read: each is added to self.not_compared with its
        reason. A nested archive/ is content, and a build-output name (bin, dist, build, ...)
        is skipped only as spelled."""
        files: Dict[str, Dict] = {}
        if not root.is_dir():
            return files

        def skip(path, reason: str) -> None:
            try:
                rel = Path(path).relative_to(root).as_posix()
            except ValueError:
                rel = str(path)
            self.not_compared.append({"side": side, "path": rel, "reason": reason})

        def unlistable(err: OSError) -> None:
            skip(err.filename or root, f"cannot be listed ({err.strerror or err})")

        for dirpath, dirnames, filenames in os.walk(root, onerror=unlistable):
            here = Path(dirpath)
            kept = []
            for d in sorted(dirnames):
                if d in self.skip_dirs and (here == root or d != "ARCHIVE"):  # a nested ARCHIVE/ is content
                    self._skipped_as_spelled[side].append((here / d).relative_to(root).as_posix())
                    continue
                if here == root and "ARCHIVE" in self.skip_dirs and self._spells_archive(d, root):  # archive/ on Windows or macOS
                    skip(here / d, f"Synk's ARCHIVE folder, spelled {d}, on a file system that folds case; skipped as ARCHIVE is")
                elif self._skipped(d, root):  # .GIT/ or NODE_MODULES/ where the file system folds case
                    continue
                elif _is_link(here / d):  # a junction back into the copy loops; one elsewhere leaves it
                    skip(here / d, "a junction or link; not followed")
                elif (here / d).resolve() != other_root:
                    kept.append(d)
            dirnames[:] = kept
            for name in sorted(filenames):
                p = here / name
                if here == root and self._spells_archive(name, root):
                    skip(p, f"a file named {name}, where Synk's ARCHIVE folder goes" if side == "user"
                         else f"a file named {name}; ARCHIVE is skipped as a folder in either copy")
                    continue
                if _is_link(p):
                    skip(p, "a junction or link; not followed" if p.exists() else "a link whose target is missing; not followed")
                    continue
                try:
                    st = p.stat()
                    files[p.relative_to(root).as_posix()] = {
                        "path": p, "size": st.st_size, "mtime": st.st_mtime,
                        "hash": _hash(p), "binary": _is_binary(p),
                    }
                except OSError as e:  # held by another process, denied by an ACL, gone mid-scan
                    skip(p, f"cannot be read ({e.strerror or e})")
        return files

    # ── Compare ────────────────────────────────────────────────────────
    def scan_and_compare(self, quiet: bool = False) -> Dict:
        """Fingerprint both copies and classify every path. Read-only.

        A path under anything either copy did not read (self.not_compared) is left out of
        the comparison in both, since what the unread side holds there is unknown. Where
        both copies fold case, a name that differs only in case between them (Readme.md
        and README.md) is one file, compared under the user copy's spelling."""
        self.not_compared = []
        self._skipped_as_spelled = {"user": [], "working": []}
        self.user_files = self._scan_directory(self.user_dir, self.working_dir, "user")
        self.working_files = self._scan_directory(self.working_dir, self.user_dir, "working")
        if self._folds_case(self.user_dir) and self._folds_case(self.working_dir):
            self._name_spelled_apart()
        unread = [n["path"] for n in self.not_compared]

        def read_in_both(rel: str) -> bool:
            return not any(u == "." or rel == u or rel.startswith(u + "/") for u in unread)

        self.user_files = {r: f for r, f in self.user_files.items() if read_in_both(r)}
        self.working_files = {r: f for r, f in self.working_files.items() if read_in_both(r)}
        if self._folds_case(self.user_dir) and self._folds_case(self.working_dir):
            by_fold = {r.lower(): r for r in self.working_files}
            for rel in list(self.user_files):
                other = by_fold.get(rel.lower())
                if other is not None and other != rel and rel not in self.working_files:
                    self.working_files[rel] = dict(self.working_files.pop(other), name=other)
        counts = dict.fromkeys(("identical", "superset", "merge", "line_endings", "different", "user_only", "working_only"), 0)
        files = {}
        for rel in sorted(set(self.user_files) | set(self.working_files)):
            u, w = self.user_files.get(rel), self.working_files.get(rel)
            try:
                a = self._analyze_file_pair(rel, u, w)
            except OSError as e:  # readable at the scan, not now
                side = "working" if w and e.filename and Path(e.filename) == w["path"] else "user"
                self.not_compared.append({"side": side, "path": rel, "reason": f"cannot be read ({e.strerror or e})"})
                continue
            if w and w.get("name") and w["name"] != rel:
                a["names"] = {"user": rel, "working": w["name"]}
            counts[a["status"]] += 1
            files[rel] = a
        self.results = {"total": len(files), **counts, "files": files, "not_compared": list(self.not_compared)}
        if not quiet:
            self._dashboard()
        return self.results

    def _name_spelled_apart(self) -> None:
        """Where both copies fold case, a folder skipped as spelled in one copy (build/) whose
        other spelling is content in the other (Build/) is one folder spelled two ways: it is
        named as not compared, and its files are left out of the plan. Otherwise the file
        would read as missing from a copy that holds it, and no apply or re-plan could help."""
        sides = (("user", self.user_files, "working", self.working_files),
                 ("working", self.working_files, "user", self.user_files))
        named = set()
        for side, _, other, other_files in sides:
            skipped = {s.lower(): s for s in self._skipped_as_spelled[side]}
            if not skipped:
                continue
            for rel in other_files:
                parts = rel.split("/")[:-1]
                for i in range(1, len(parts) + 1):
                    p = "/".join(parts[:i])
                    s = skipped.get(p.lower())
                    if s is not None and s != p and (other, p) not in named:
                        named.add((other, p))
                        spelled = {side: s, other: p}
                        self.not_compared.append({"side": other, "path": p, "reason": (
                            f"skipped: spelled {spelled['user']} in the user copy and {spelled['working']} "
                            "in the working copy; rename one to sync it")})

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
        if lu == lw:  # a line diff shows nothing: line endings, a byte-order mark, or bytes no line shows
            layers.update(line_count=True, content=False)
            apart = _same_lines_differ(u["path"], w["path"])
            status = "line_endings" if apart["relationship"] == "line_endings" else "different"
            return {"status": status, "similarity": 1.0, "hash_match": False, "newer": newer, "layers": layers, **apart}
        layers.update(line_count=len(lu) == len(lw), content=False)
        similarity, relationship = self._calculate_extended_similarity(lu, lw)
        if relationship in ("a_superset", "b_superset"):
            status = "superset"  # Correction #3
        elif similarity >= self.threshold:
            status = "merge"  # Correction #2 (includes 100% line-set match with a different hash)
        else:
            status = "different"
        bom = _bom_sides(u["path"], w["path"])  # the line diff reads past a BOM: name it
        return {"status": status, "relationship": relationship, "similarity": similarity,
                "hash_match": False, "newer": newer, "layers": layers, **({"bom": bom} if bom else {})}

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
             f"| ⏎{r['line_endings']} line endings | ✗{r['different']} different "
             f"| ➕{r['user_only']} only in user copy | ➕{r['working_only']} only in working copy")
        for rel, a in r["files"].items():
            if a["status"] != "identical":
                sim = f"{a['similarity']:.0%}" if a["relationship"] not in ("missing", "binary", "bytes", "bom") else a["relationship"]
                extra = f"  (newer: {a['newer']})" if a["newer"] else ""
                if "endings" in a:
                    extra += ("  (line endings differ within the file: " if a.get("within") else "  (") + \
                        f"user {a['endings']['user']}, working {a['endings']['working']})"
                if a["relationship"] == "bom":
                    extra += f"  (only a byte-order mark: the {'user' if a['bom']['user'] else 'working'} copy carries a UTF-8 BOM)"
                elif "bom" in a:
                    extra += f"  (and a byte-order mark: {_bom_words(a['bom'])})"
                if "names" in a:
                    extra += f"  (same file, different case: working copy spells it {a['names']['working']})"
                _say(f"   {a['status']:<13} {sim:>8}  {rel}{extra}")
        for n in r["not_compared"]:
            _say(f"   ⚠️ not compared, in either copy: {n['side']} copy's {n['path']} ({n['reason']})")

    def diff(self, rel: str) -> str:
        """A unified diff of one path or, when the copies hold the same lines, what differs
        instead: line endings (by convention, or line by line within the file), a final
        newline, only a UTF-8 byte-order mark, or bytes no line shows. A BOM on one side only
        is named beside any other difference too (the line diff reads past it). A side with
        no such file is empty. Raises OSError for a file that cannot be read."""
        u, w = self.user_dir / rel, self.working_dir / rel
        lu, lw = (_lines(u) if u.is_file() else []), (_lines(w) if w.is_file() else [])
        both = u.is_file() and w.is_file()
        if lu == lw and both and _hash(u) != _hash(w):
            return _said_apart(rel, _same_lines_differ(u, w))
        text = "\n".join(difflib.unified_diff(lu, lw, f"user/{rel}", f"working/{rel}", lineterm=""))
        bom = _bom_sides(u, w) if both else None
        return f"note: {_bom_words(bom)} (a byte-order mark no line below shows)\n{text}" if bom else text

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
            "line_endings": (None, "STANDARD", "identical text; the copies differ only in line endings (ENDINGS): choose the convention the file keeps, then set the direction"),
            "different": (None, "MANUAL", "low similarity or binary: choose a side or keep both under different names"),
        }
        for rel, a in self.results["files"].items():
            if a["status"] == "identical":
                continue
            n += 1
            direction, review, note = notes[a["status"]]
            if "endings" in a:
                note = note.replace("ENDINGS", f"user {a['endings']['user']}, working {a['endings']['working']}")
                if a.get("within"):
                    note = note.replace("the copies differ only in line endings", "line endings differ within the file")
            if a["relationship"] == "bom":
                review, note = "STANDARD", (f"identical text; only a byte-order mark differs (the "
                                            f"{'user' if a['bom']['user'] else 'working'} copy carries a UTF-8 BOM): "
                                            "choose the convention the file keeps, then set the direction")
            elif "bom" in a:
                note = note.replace("differ only in line endings", "differ in line endings") + \
                    f"; a byte-order mark differs too: {_bom_words(a['bom'])}"
            if "names" in a:
                note += f"; same file, different case: the working copy spells it {a['names']['working']}"
            actions.append({"id": n, "path": rel, "status": a["status"], "relationship": a["relationship"],
                            "similarity": round(a["similarity"], 3), "newer": a["newer"],
                            "direction": direction, "review": review, "note": note,
                            # what each side held when the plan was written: apply refuses an
                            # item whose destination has changed since (the source may change:
                            # a merge is written into one side, then sent to the other)
                            "hashes": {"user": (self.user_files.get(rel) or {}).get("hash"),
                                       "working": (self.working_files.get(rel) or {}).get("hash")}})
        return actions

    def refusal(self, rel) -> Optional[str]:
        """Why a plan path may not be written, or None when it names a file inside the copies.

        A plan file is data the user may have edited by hand: the path must be relative,
        with no '..', drive, UNC or root prefix, must not end in a separator or a space, on
        Windows must hold no form Windows reserves (a segment ending in a dot or a space, a
        ':' stream, <>"|?*: the copy would land under another name, in a stream, or fail
        after the backup was made), must not name a device at any prefix as the running OS
        maps it (os.path.abspath puts it outside the copy, at \\\\.\\: NUL on Windows 11,
        con.txt too on Windows 10; asked of the copy's plain form when it was given as
        \\\\?\\C:\\...), must resolve under each copy, must not lie in a folder the scan skips
        (so nothing is written where nothing is compared), must not pass through or name a
        junction or link on either side (the scan never follows one), and must not name a
        folder in either copy ('sub', or '.' for the copy itself)."""
        if not isinstance(rel, str) or not rel.strip():
            return "no path"
        if rel != rel.strip() or rel[-1] in "/\\":
            return "path ends in a separator or a space, or begins with one"
        win, posix = PureWindowsPath(rel), PurePosixPath(rel)
        if win.drive or win.root or posix.root:
            return "absolute, drive-relative or UNC path"
        if any(part in ("..", "") for part in win.parts):
            return "path leaves the copy ('..')"
        if os.name == "nt":
            for part in win.parts:
                if part[-1] in ". " or set(part) & WINDOWS_FORBIDDEN:
                    return f"path holds a form Windows reserves ({part!r}: a segment ending in a dot or a space, a ':' stream, or <>\"|?*)"
        for plain in dict.fromkeys(self._device_roots):
            for i in range(1, len(win.parts) + 1):  # asked of the OS, at every prefix: a folder named NUL fails too
                where = self._device_at(plain, win.parts[:i])
                if not _within(where, plain):  # the OS put it elsewhere: \\.\NUL, a device
                    return f"path names a device Windows reserves ({'/'.join(win.parts[:i])} is {where} to this OS)"
        for i, part in enumerate(win.parts[:-1]):
            if any(self._skipped(part, root, top=i == 0) for root in (self.user_dir, self.working_dir)):
                return f"path lies in a folder the scan skips ({part})"
        for root in (self.user_dir, self.working_dir):
            base = str(root)
            for i in range(1, len(win.parts) + 1):
                if self._is_link(os.path.join(base, *win.parts[:i])):
                    return f"a junction or link on the {'user' if root == self.user_dir else 'working'} side ({'/'.join(win.parts[:i])}); never followed"
            # no prefix is a link and no segment is '..', so the path resolves where it is spelled
            if not _within(os.path.abspath(os.path.join(base, *win.parts)), base):
                return "path resolves outside the copy"
        if any((root / rel).is_dir() for root in (self.user_dir, self.working_dir)):
            return "names a folder, not a file"
        return None

    def _unreadable(self, act: Dict) -> Optional[str]:
        """Why an item cannot be copied: its source, or the file its destination would replace
        (which the backup must read), cannot be read. A source that is gone is left to the
        copy, which fails and is rolled back."""
        for side in ("user", "working"):
            p = (self.user_dir if side == "user" else self.working_dir) / act["path"]
            if p.is_file():
                why = _readable(p)
                if why:
                    return f"the {side} copy's {act['path']} {why}"
        return None

    def _premise(self, act: Dict) -> Optional[Tuple[str, str]]:
        """("already", why) when the destination already holds the source's content, whatever
        the item's status (nothing to do, and not a failure); ("changed", why) when it no
        longer matches the plan it came from (refused: re-plan); None when it matches. The
        destination is hashed once; the source only when the plan's hash no longer matches."""
        to_working = act["direction"] == "user_to_working"
        side = "working" if to_working else "user"
        dst = (self.working_dir if to_working else self.user_dir) / act["path"]
        src = (self.user_dir if to_working else self.working_dir) / act["path"]
        dst_hash = _hash(dst) if dst.is_file() else None
        already = ("already", f"the {side} copy holds this content; nothing to do")
        one_sided = act.get("status") in ("user_only", "working_only")
        hashes = act.get("hashes")
        bad = "hashes" in act and hashes is not None and not isinstance(hashes, dict)  # a hand edit
        planned_match = "hashes" in act and not bad and dst_hash == (hashes or {}).get(side)  # plans before v2.1 carry none
        if planned_match and not (one_sided and dst.exists()):
            return None
        if dst_hash is not None and src.is_file() and _hash(src) == dst_hash:
            return already
        if bad:
            return ("changed", "its hashes are not an object, as --plan writes them; re-plan")
        if one_sided and dst.exists():
            return ("changed", f"the {side} copy now has this file; re-plan")
        if "hashes" in act:
            return ("changed", f"the {side} copy changed since the plan; re-plan")
        return None

    def new_ids(self, plan: List[Dict]) -> List[int]:
        """What --approve new approves: every one-sided item whose path stays inside the copies,
        except docs/PULSE.json, which each copy keeps for itself (approve it by id to copy it).
        An answer here is not reused by apply(), which asks again."""
        return self._split_new(plan)[0]

    def left_out_of_new(self, plan: List[Dict]) -> List[Tuple[Dict, str, bool]]:
        """Each one-sided item --approve new leaves out: (item, why, refused). docs/PULSE.json
        is left out by design (refused False); every other one is refused, and the run exits 1."""
        return self._split_new(plan)[1]

    def _split_new(self, plan: List[Dict]) -> Tuple[List[int], List[Tuple[Dict, str, bool]]]:
        """new_ids(plan) and left_out_of_new(plan) from one pass: each path asked once."""
        ids, out = [], []
        with self._one_call():
            for a in plan:
                if a.get("status") not in ("user_only", "working_only"):
                    continue
                why = self.refusal(a.get("path"))
                if why:
                    out.append((a, why, True))
                elif a.get("path") == PULSE_REL:
                    out.append((a, "each copy keeps its own; approve it by id to copy it", False))
                else:
                    ids.append(a["id"])
        return ids, out

    # ── Backup ─────────────────────────────────────────────────────────
    def _new_archive_dir(self) -> Tuple[Path, bool]:
        """A fresh folder under the user copy's ARCHIVE, as it is spelled on disk, and whether
        ARCHIVE itself was made for it (so a backup that fails can leave nothing behind)."""
        root = self._archive_root()
        if root.exists() and not root.is_dir():
            raise NotADirectoryError(f"{root} is a file, not a folder: move it aside, then apply again")
        created = not root.exists()
        stamp = datetime.now().strftime("%Y-%m-%dT%H%M%S")
        dest = root / f"synk-{stamp}"
        i = 1
        while dest.exists():
            i += 1
            dest = root / f"synk-{stamp}-{i}"
        dest.mkdir(parents=True)
        return dest, created

    def _discard_archive(self, dest: Path, created_root: bool) -> str:
        """Remove a backup folder that never got its manifest, and ARCHIVE itself when this run
        made it: an archive holds its manifest or does not exist. Says what could not be removed."""
        shutil.rmtree(dest, ignore_errors=True)
        if created_root:
            try:
                dest.parent.rmdir()
            except OSError:
                pass
        return f"; {dest} could not be removed and holds no manifest" if dest.exists() else ""

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
            elif src.exists():  # a folder: not backed up, and never listed for deletion
                entry["folder"] = True
            manifest["files"][f"{side}:{rel}"] = entry
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
        lines = ["# Rollback", "", f"Archive created: {manifest['timestamp']}", "",
                 "To undo, copy each file under this folder's `user/` or `working/` back to the same",
                 "relative path in that copy, and delete any file listed as not having existed.", ""]
        for key, e in manifest["files"].items():
            side_name, rel = key.split(":", 1)
            root_name = self.user_dir if side_name == "user" else self.working_dir
            how = ("restore from `" + f"{side_name}/{rel}`" if e["existed"] else
                   "a folder, not a file: leave it as it is" if e.get("folder") else "did not exist: delete it")
            lines.append(f"- `{root_name / rel}` — {how}")
        (dest / "rollback.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    def backup(self, paths: List[str], side: str) -> Path:
        """Copy the named files of one side ('user' or 'working') into a new archive folder;
        when one cannot be copied, the folder is removed and the OSError raised."""
        if side not in ("user", "working"):
            raise ValueError("side must be 'user' or 'working'")
        for rel in paths:  # checked before the archive folder exists, so a refusal leaves nothing behind
            why = self.refusal(rel)
            if why:
                raise ValueError(f"{rel}: {why}")
        dest, created = self._new_archive_dir()
        try:
            self._backup_into(dest, paths, side)
        except Exception:  # anything raised (a MemoryError included): an archive holds its manifest or does not exist
            self._discard_archive(dest, created)
            raise
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

    def apply(self, plan: List[Dict], approved_ids: Iterable[int], refused: Iterable[Dict] = ()) -> Dict:
        """Execute approved actions that have a direction; back up first, roll back on failure.
        refused: items a caller already refused ({"path", "reason"}, as --approve new's left-out
        ones), recorded first in the report and in the archive's apply-report.json.

        An item whose path leaves either copy, lies in a folder the scan skips or names a
        folder, whose source or destination cannot be read, or whose destination changed
        since the plan was written, is refused before any backup or write. When a backup
        fails, every item is refused and no archive folder is left behind. Any exception
        while verifying a copy rolls it back; a rollback that fails is reported with the
        backup to restore by hand. An item whose destination already holds its source's
        content is reported in already_applied: nothing to do, and not a failure. Link answers
        are asked afresh by each call, and each destination's folders are asked again,
        uncached, immediately before its write: a junction that appears is never followed."""
        with self._one_call():
            return self._apply(plan, approved_ids, refused)

    def _apply(self, plan: List[Dict], approved_ids: Iterable[int], refused: Iterable[Dict]) -> Dict:
        approved = set(approved_ids)
        report = {"applied": [], "already_applied": [], "skipped": [], "refused": [dict(r) for r in refused],
                  "rolled_back": [], "rollback_failed": [], "archive": None}
        todo = []
        for act in plan:
            if act["id"] not in approved:
                continue
            name = act.get("path") or f"item {act.get('id')}"  # a hand-edited item may have no path
            direction = act.get("direction")
            if direction not in DIRECTIONS:
                if direction is None:
                    why = "no direction chosen; review first"
                    said = "no direction chosen; review it, then set its direction in the plan"
                else:
                    why = said = f"direction {direction!r} is not user_to_working or working_to_user"
                report["skipped"].append({"path": act.get("path"), "reason": why})
                _say(f"  ⏭️ Skipped {name}: {said}")
                continue
            premise = None
            try:
                why = self.refusal(act.get("path")) or self._unreadable(act)
                if not why:
                    premise = self._premise(act)
                    why = premise[1] if premise and premise[0] == "changed" else None
            except OSError as e:  # changed under us between the checks
                why = f"cannot be read ({e.strerror or e})"
            if premise and premise[0] == "already":
                report["already_applied"].append({"path": act["path"], "direction": direction})
                _say(f"  ℹ️ Already applied {name}: {premise[1]}")
            elif why:
                report["refused"].append({"path": act.get("path"), "reason": why})
                _say(f"  ✗ Refused {name}: {why}")
            else:
                todo.append(act)
        if not todo:
            return report
        try:
            dest, created_root = self._new_archive_dir()
        except OSError as e:  # ARCHIVE is a file, or cannot be made: with no backup, nothing is written
            for act in todo:
                report["refused"].append({"path": act["path"], "reason": f"no backup can be made: {e}"})
            _say(f"  ✗ Refused {len(todo)} item(s), nothing written: no backup can be made: {e}")
            return report
        try:
            for side, direction in (("working", "user_to_working"), ("user", "working_to_user")):
                paths = [a["path"] for a in todo if a["direction"] == direction]
                if paths:
                    self._backup_into(dest, paths, side)
        except Exception as e:  # anything raised while backing up: with no complete backup, nothing is written
            why = f"{e}" if isinstance(e, OSError) else f"{type(e).__name__}: {e}"
            left = self._discard_archive(dest, created_root)
            for act in todo:
                report["refused"].append({"path": act["path"], "reason": f"no backup could be made: {why}"})
            _say(f"  ✗ Refused {len(todo)} item(s), nothing written: no backup could be made ({why}){left}")
            return report
        report["archive"] = str(dest)
        for act in todo:
            to_working = act["direction"] == "user_to_working"
            src_root, dst_root = (self.user_dir, self.working_dir) if to_working else (self.working_dir, self.user_dir)
            side = "working" if to_working else "user"
            src, dst = src_root / act["path"], dst_root / act["path"]
            link = self._link_on_the_way(dst_root, act["path"])  # asked of the disk now, not of a cache
            if link:
                why = f"a junction or link on the {side} side ({link}) appeared before the write; never followed"
                report["refused"].append({"path": act["path"], "reason": why})
                _say(f"  ✗ Refused {act['path']}: {why}")
                continue
            existed = dst.is_file()
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            except Exception as e:
                failed = [f"copy error: {e}"]
            else:
                try:
                    failed = self._verify_copy(src, dst)
                except Exception as e:  # anything raised while verifying (a MemoryError included) fails the copy
                    failed = [f"verification error: {type(e).__name__}: {e}"]
            if failed:
                backup = dest / side / act["path"]
                try:
                    if existed:
                        shutil.copy2(backup, dst)
                    elif dst.is_file():  # never a folder: only a file this copy created is removed
                        dst.unlink()
                except Exception as e:
                    report["rollback_failed"].append({"path": act["path"], "backup": str(backup) if existed else None,
                                                      "reason": f"{', '.join(failed)}; the rollback failed too: {e}"})
                    _say(f"  ‼️ NOT rolled back {act['path']} (failed: {', '.join(failed)}; the rollback failed too: {e}): "
                         + (f"restore it by hand from {backup}" if existed else f"delete {dst} by hand"))
                else:
                    report["rolled_back"].append(act["path"])
                    _say(f"  ↩️ Rolled back {act['path']} (failed: {', '.join(failed)})")
            else:
                report["applied"].append({"path": act["path"], "direction": act["direction"],
                                          "created": not existed, "verified": list(LAYERS)})
                _say(f"  ✓ {act['direction']}: {act['path']} (six layers verified)")
        try:
            (dest / "apply-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
        except OSError as e:
            _say(f"  ⚠️ apply-report.json not written ({e}); the lines above are the record")
        return report


# ── PULSE.json (Trifecta Protocol v3.0) ───────────────────────────────
def update_pulse(project_dir, fields: Dict, signals: Iterable[Tuple[str, str, str]] = ()) -> Optional[Path]:
    """Merge synk182's keys and signals into docs/PULSE.json, keeping every other key.

    A PULSE.json that does not parse, or holds no object ([], null), is left
    untouched and None is returned:
    DevCom5 owns rebuilding it, and overwriting would destroy its history.
    One that parses but holds a wrong-typed field (cross_skill not an object,
    pending_signals null) is handled as if that field were empty, and says so.
    A signal is pruned when it is consumed (JSON true, nothing else) and its
    timestamp, read by the protocol's grammar, is older than seven days; a consumed
    signal whose timestamp cannot be read is pruned with a note; an unconsumed
    signal, and an entry that is not an object, is never touched.
    A docs that is a file raises NotADirectoryError naming it, before anything
    is written; the CLI reports that, and any other OSError, as a warning."""
    path = Path(project_dir) / "docs" / "PULSE.json"
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
            _say("  ⚠️ PULSE cross_skill is not an object; treated as empty")
        cs = data["cross_skill"] = {}
    cs.update(fields)
    pending = cs.get("pending_signals")
    if not isinstance(pending, list):
        if "pending_signals" in cs:
            _say("  ⚠️ PULSE pending_signals is not a list; treated as empty")
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
            _say(f"  ⚠️ pruned a consumed signal ({s.get('signal') or s.get('type') or 'unnamed'}) "
                 f"whose timestamp is not extended ISO-8601: {s.get('timestamp')!r}")
            continue
        if not old:
            kept.append(s)
    now = _now_iso()
    for signal, to, details in signals:
        kept.append({"from": "synk182", "signal": signal, "to": to, "timestamp": now,
                     "details": details, "consumed": False})
    cs["pending_signals"] = kept
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return path


def _record_pulse(project_dir, fields: Dict, signals: Iterable[Tuple[str, str, str]]) -> None:
    """--pulse for the CLI: update the PULSE, or say why this run is not recorded there."""
    try:
        written = update_pulse(project_dir, fields, signals)
    except OSError as e:  # docs is a file, PULSE.json is a folder, no permission to write
        _say(f"  ⚠️ PULSE.json not written ({e}), so this run is not recorded there")
        return
    if not written:
        _say(PULSE_UNTOUCHED)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Synk182 engine: compare, plan, back up, apply, verify.")
    ap.add_argument("user_dir")
    ap.add_argument("working_dir")
    ap.add_argument("--threshold", type=float, default=0.60, help="merge threshold, between 0 and 1 (0.6)")
    ap.add_argument("--plan", metavar="OUT_JSON", help="write the plan to this file")
    ap.add_argument("--diff", metavar="REL_PATH", help="print a unified diff for one path (--diff=-name for a leading dash)")
    ap.add_argument("--apply", metavar="PLAN_JSON", help="apply approved items from a plan file")
    ap.add_argument("--approve", default="", help="comma-separated plan ids, or 'new' for every one-sided file")
    ap.add_argument("--pulse", action="store_true", help="record results in USER_DIR/docs/PULSE.json")
    args = ap.parse_args(argv)

    if not 0 <= args.threshold <= 1:  # nan fails both sides; 2 would never merge, -1 always
        _say(f"✗ --threshold must be between 0 and 1: got {args.threshold}")
        return 1
    # a flag given an empty value ("--plan ''", from an empty shell variable) is still given
    plan_out, plan_in, diff_rel = (v is not None for v in (args.plan, args.apply, args.diff))
    if args.approve.strip() and not plan_in:
        _say("✗ --approve works only with --apply PLAN_JSON; nothing was applied")
        return 1
    if plan_out and plan_in:  # one of them would be dropped without a word
        _say("✗ --plan and --apply are separate runs: write the plan, review it, then apply it; nothing was done")
        return 1
    beside_diff = [flag for flag, on in (("--plan", plan_out), ("--apply", plan_in), ("--pulse", args.pulse)) if on]
    if diff_rel and beside_diff:
        _say(f"✗ --diff shows one file and writes nothing: run it without {', '.join(beside_diff)}; nothing was done")
        return 1
    for label, folder in (("user copy", args.user_dir), ("working copy", args.working_dir)):
        if not Path(folder).is_dir():
            _say(f"✗ The {label} is not a folder: {folder}")
            return 1
    if Path(args.user_dir).samefile(args.working_dir):  # one path typed twice is not two copies in agreement
        _say(f"✗ The user copy and the working copy are the same folder: {args.user_dir}")
        return 1
    synk = SynkEngine(args.user_dir, args.working_dir, threshold=args.threshold)
    for flag, value in (("--diff", args.diff), ("--apply", args.apply)):
        if value is not None and not value.strip():
            _say(f"✗ {flag} was given an empty name; nothing was done")
            return 1
    if diff_rel:
        why = synk.refusal(args.diff)  # the same bounds as a plan path: never a file outside the copies
        if why:
            _say(f"✗ --diff {args.diff}: {why}")
            return 1
        if not any((root / args.diff).is_file() for root in (synk.user_dir, synk.working_dir)):
            _say(f"✗ {args.diff} exists in neither copy")
            return 1
        try:
            _say(synk.diff(args.diff))
        except OSError as e:
            _say(f"✗ {args.diff} cannot be read ({e.strerror or e}): {e.filename}")
            return 1
        return 0
    results = synk.scan_and_compare(quiet=plan_in)
    drift = results["total"] != results["identical"]
    if plan_in:
        try:
            plan = json.loads(Path(args.apply).read_text(encoding="utf-8-sig"))  # some editors save a BOM
        except (OSError, ValueError) as e:
            _say(f"✗ Cannot read the plan {args.apply}: {e}")
            return 1
        # a whole-number id, as --plan writes it (1.0 is the same id): "1" was applied by
        # --approve new but not by --approve 1, and [1] could not be looked up at all
        if not isinstance(plan, list) or not all(isinstance(a, dict) and _whole(a.get("id")) for a in plan):
            _say(f"✗ {args.apply} is not a plan: expected a list of items, each with a whole-number id, as --plan writes it")
            return 1
        seen, twice = set(), []
        for a in plan:  # a duplicated id (a hand edit) would apply its item twice
            if a["id"] in seen and a["id"] not in twice:
                twice.append(a["id"])
            seen.add(a["id"])
        if twice:
            _say(f"✗ {args.apply}: id {', '.join(map(str, twice))} appears twice; each id names one item, as --plan writes them; nothing applied")
            return 1
        left_out = []  # one-sided items 'new' refuses: each is named, and the run exits 1
        if args.approve.strip().lower() == "new":
            ids, left = synk._split_new(plan)
            for a, why, refused in left:
                name = a.get("path") or f"item {a.get('id')}"  # named as apply() names it
                _say(f"  ⏭️ Not in 'new': {name} ({why})")
                if refused:
                    left_out.append({"path": a.get("path"), "reason": why})
            if not ids and not left_out:  # nothing to do is a clean run, whatever it leaves to an id
                _say("Nothing else to approve: docs/PULSE.json is left to an explicit id." if any(
                    a.get("path") == PULSE_REL and a.get("status") in ("user_only", "working_only") for a in plan)
                     else "Nothing new to approve: no file is in one copy only.")
                return 0
        else:
            try:
                ids = [int(x) for x in args.approve.split(",") if x.strip()]
            except ValueError:
                _say(f"✗ --approve takes plan ids separated by commas, or 'new': got {args.approve!r}")
                return 1
            unknown = [i for i in ids if i not in [a["id"] for a in plan]]
            if unknown:  # a mistyped id must not read as a clean run
                _say(f"✗ No item in {args.apply} has id {', '.join(map(str, unknown))}; nothing applied")
                return 1
        if not ids and not left_out:
            _say("Nothing approved: pass --approve with plan ids.")
            return 1
        # left-out items are counted, signaled, written to apply-report.json and fail like any refusal
        report = synk.apply(plan, ids, refused=left_out)
        _say(f"🔄 Synced: {len(report['applied'])} | Rolled back: {len(report['rolled_back'])} "
             f"| Refused: {len(report['refused'])} | Skipped: {len(report['skipped'])} | Archive: {report['archive']}"
             + (f" | Already applied: {len(report['already_applied'])}" if report["already_applied"] else "")
             + (f" | NOT rolled back: {len(report['rollback_failed'])}" if report["rollback_failed"] else ""))
        if args.pulse:
            # sync_completed only when something was written: DevCom5 reads it as a sync that happened
            sigs = [("sync_completed", "devcom5", f"{len(report['applied'])} file(s) written")] if report["applied"] else []
            conflicts = (report["rolled_back"] + [f"{r['path']} ({r['reason']})" for r in report["refused"]]
                         + [f"{r['path']} (not rolled back; restore from {r['backup']})" for r in report["rollback_failed"]])
            if conflicts:
                sigs.append(("sync_conflict", "devcom5", ", ".join(conflicts)))
            created = [a["path"] for a in report["applied"] if a["created"]]  # an overwrite is not a new file
            if created:
                sigs.append(("new_files_synced", "solid8", ", ".join(created)))
            _record_pulse(synk.user_dir, {"synk_last_run": _now_iso(), "synk_drift_detected": drift,
                                          "synk_files_changed": len(report["applied"])}, sigs)
        # an approved item that was not written, for whatever reason, is not a clean run
        return 1 if report["rolled_back"] or report["refused"] or report["skipped"] or report["rollback_failed"] else 0
    plan = synk.plan()
    plan_written = True
    if plan_out:
        try:
            if not args.plan.strip():
                raise OSError("no file name given")
            Path(args.plan).write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
        except OSError as e:  # a missing folder, a folder in its place, no permission to write
            _say(f"✗ Plan not written ({e})")
            plan_written = False
        else:
            _say(f"📋 Plan written: {args.plan} ({len(plan)} item(s); nothing changed on disk)")
    if args.pulse:  # the scan is still recorded; only the plan file failed
        _record_pulse(synk.user_dir, {"synk_last_run": _now_iso(), "synk_drift_detected": drift},
                      [("environment_diverged", "devcom5", f"{len(plan)} path(s) differ")] if drift else [])
    return 0 if plan_written else 1


if __name__ == "__main__":
    sys.exit(main())
