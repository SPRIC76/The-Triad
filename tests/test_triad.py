"""Version 1.3 | Deps: stdlib; Skillshaper's validate_skill.py when present | Parent: The Triad (DevCom5 1.3, Synk182 3.3, Solid8 1.3) | Path: tests | Filename: test_triad.py | Created: 2026-09-30 01:12 ET - kept tests for the pack: the two engines, the three skill folders, and the pack's own ratchets. | Updated: 2026-09-30 04:05 ET - v1.3: red-first cases from the v1.2 review (bounded plan paths, stale plans, wrong-typed PULSE fields, CLI messages, copy numbers, sprawl across folders, pointer and version ratchets); comments read for a public reader; both engines checked for personal paths. | Updated: 2026-09-30 04:53 ET - red-first cases from the second v1.3 review: folder targets and rollback, backups read as the file they back up, unknown --approve ids, one folder given twice, an unparseable PULSE reported, signals only when true, protocol safety rule 4; the pointer check is an allow-list, so the test names no private skill. | Updated: 2026-09-30 05:37 ET - red-first cases from the third v1.3 review: --pulse when docs is a file, a PULSE holding no object, an approved item with no direction, an item with only an id named by its id, --plan beside --apply and --diff beside another action, a backup of a binary, backups with two markers; the pointer check reads what a pointer names, in any of its forms, rather than its first word. | Updated: 2026-09-30 06:09 ET - red-first cases from the fourth v1.3 review: a --plan or --json file that cannot be written, an item with no path in the --approve new listing; the pointer check reads the "X tool/helper/plugin" form, verbs beyond "use", possessives and subjects, loose names, Task/Need/Tool tables, wrapped clauses and a bare arrow's name, leaves slot words, counts and the pack's flows alone, and every allowed kind must be read from the pack. | Updated: 2026-09-30 07:28 ET - red-first cases from the fifth v1.3 review: the pointer check tells a skill name from English's own hyphenated words by form, with a short ratcheted list of lexicalized compounds, keeps a realistic-prose corpus green and reads a one-word name after a verb again; an empty --plan, --apply, --diff or --json name, a file named ARCHIVE, hand-edited plan ids and hashes, junctions and links, a folder that cannot be listed, and signals stamped with Z. | Updated: 2026-09-30 13:43 ET - v1.2: the pointer check's grammar reader is retired for two exact mechanisms, a vocabulary ratchet over every name-shaped token in the pack's Markdown and a private-name deny-list read from TRIAD_PRIVATE_NAMES, both driven on every form the reviews listed and on the a9f9b3a export; red-first cases from the sixth v1.3 review: a file that cannot be read (held by another process), a backup that fails midway, an exception in verification and a rollback that fails, ARCHIVE in any case and case-only name pairs where the file system folds case, line-ending-only differences and --diff outside the copies, links to files, PULSE stamps in every shape on every Python, plan paths in skipped folders, flag values and hand edits, same-size groups read once, --details below zero, a PULSE with a BOM. | Updated: 2026-09-30 14:32 ET - red-first cases from the seventh v1.3 review: the vocabulary ratchet reads CamelCase, dotted names, bare, dot-folder and Windows paths, hex letters with one digit, v8, x_y, a date in a name and any script (its 28 forms kept in REVIEW7_FORMS), the deny-list folds accents and every separator including none and a soft wrap, the stale check reads with the tokenizer and kinds of work have their own list; skipped folders folded where the file system folds case, mixed endings and a BOM named, Windows-reserved plan paths, links in a plan or --diff, already applied for two-sided items, any exception in the backup phase, a file unreadable at compare time, the capped --json proposal, the exact ISO-8601 grammar and LF output.

Run from the pack folder:  python -B -m unittest discover -s tests -v

Root: the folder above tests/, or TRIAD_ROOT when set, so the same file runs
against an older copy of the pack and shows which cases go red there.
Validator: Skillshaper's, at SC2_VALIDATOR or ~/.agents/skills/sc2/scripts/validate_skill.py;
its cases are skipped when it is absent.

Lives outside the skill folders on purpose (Skillshaper, section 5): a tests/
folder inside a skill would make every deployed copy differ from the development
copy. The engine cases came from the 2026-09-15 upgrade, where each one was a real
defect first; the pack cases were written red on commit 19a8722 of skills-trifecta.
"""

import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

# Importing the skills' scripts must not leave __pycache__ inside a skill folder.
sys.dont_write_bytecode = True

ROOT = Path(os.environ.get("TRIAD_ROOT") or Path(__file__).resolve().parent.parent).resolve()
VALIDATOR = Path(os.environ.get("SC2_VALIDATOR")
                 or Path.home() / ".agents" / "skills" / "sc2" / "scripts" / "validate_skill.py")
SKILLS = ("devcom5", "synk182", "solid8")
CALL_WORDS = {"devcom5": ("devcom5", "dc5", "logger"),
              "synk182": ("synk", "s182", "synk it"),
              "solid8": ("solid8", "s8", "denser")}
# Skills a "not for" may name: the pack's own, and verafox, which is public in The
# Proof Pack. Anything else is described as a kind of work, never named.
SIBLINGS = ("verafox", "DevCom5", "Synk182", "Solid8")
PROOF_PACK = "https://github.com/SPRIC76/The-Proof-Pack"


def _load(name, rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write(root, rel, text="", data=None):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if data is not None:
        p.write_bytes(data)
    else:
        p.write_text(text, encoding="utf-8")
    return p


def _run_cp1252(script, *args):
    """Run a script the way a stock Windows console does: stdout encoded cp1252."""
    env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
    return subprocess.run([sys.executable, "-B", str(script), *map(str, args)],
                          capture_output=True, env=env, timeout=120)


def _link_folder(link, target):
    """Make link a junction to target (a symbolic link where there are no junctions);
    False when this machine makes neither."""
    if os.name == "nt":
        return subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                              capture_output=True, timeout=60).returncode == 0
    try:
        os.symlink(target, link, target_is_directory=True)
        return True
    except OSError:
        return False


def _unlistable(folder):
    """An os.walk that cannot list folder, as when an ACL denies it to the user. The fifth
    v1.3 review drove a real deny with icacls; a kept test does not change a machine's ACLs."""
    real, folder = os.walk, Path(folder).resolve()

    def walk(top, topdown=True, onerror=None, followlinks=False):
        for dirpath, dirnames, filenames in real(top, topdown, None, followlinks):
            if Path(dirpath).resolve() == folder:
                if onerror:
                    onerror(PermissionError(13, "Access is denied", str(folder)))
                dirnames[:] = []
                continue
            yield dirpath, dirnames, filenames
    return walk


def _old_signals(consumed_by):
    """A PULSE's consumed signals, a month old in three ISO-8601 forms (Z, +00:00, no offset)
    and a day old with Z, named by form."""
    old, recent = datetime.now() - timedelta(days=30), datetime.now() - timedelta(days=1)
    stamps = {"z": old.strftime("%Y-%m-%dT%H:%M:%SZ"), "utc": old.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
              "naive": old.strftime("%Y-%m-%dT%H:%M:%S"), "recent": recent.strftime("%Y-%m-%dT%H:%M:%SZ")}
    return json.dumps({"cross_skill": {"pending_signals": [
        {"from": "devcom5", "signal": s, "to": consumed_by, "timestamp": t, "consumed": True}
        for s, t in stamps.items()]}})


def _folds_case(folder):
    """True where the file system folds case at folder (Windows, default macOS): the folder's
    own name in another case reaches the same entry. Asked of the folder, not of the OS, so a
    case-sensitive volume mounted on Windows answers for itself."""
    other = Path(folder).with_name(Path(folder).name.swapcase())
    try:
        return other.exists() and os.path.samefile(other, folder)
    except OSError:
        return False


def _hold_unreadable(test, path, sweep):
    """Make path unreadable to this process for real, the way the sixth v1.3 review drove it:
    on Windows another process holds an exclusive byte-range lock on it, so a read fails with
    Permission denied (an ACL deny fails the same way, at open; a kept test does not change a
    machine's ACLs); elsewhere its mode is 000 (skipped as root, who reads anything). Undone
    when the test ends, and sweep (the test's temp folder, which tearDown could not empty while
    the file was held) is removed then."""
    path = Path(path)
    if os.name == "nt":
        scratch = Path(tempfile.mkdtemp())
        locker = _write(scratch, "locker.py", "import msvcrt, sys, time\nf = open(sys.argv[1], 'r+b')\n"
                        "msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1 << 20)\nprint('locked', flush=True)\n"
                        "time.sleep(120)\n")
        p = subprocess.Popen([sys.executable, "-B", str(locker), str(path)], stdout=subprocess.PIPE)
        test.addCleanup(shutil.rmtree, sweep, True)
        test.addCleanup(shutil.rmtree, scratch, True)
        test.addCleanup(p.wait)
        test.addCleanup(p.kill)
        test.assertEqual(p.stdout.readline().strip(), b"locked")
    else:
        if getattr(os, "geteuid", lambda: 1)() == 0:
            test.skipTest("running as root: every file is readable")
        os.chmod(path, 0)
        test.addCleanup(shutil.rmtree, sweep, True)
        test.addCleanup(os.chmod, path, 0o644)
    with test.assertRaises(OSError):
        path.read_bytes()


def _frontmatter(skill):
    """The raw frontmatter of a SKILL.md, read the way a strict host reads it.

    Returns a dict: style ('block', 'line' or 'other'), description (joined text),
    metadata (raw 'key: value' strings under metadata:), license (raw value or None).
    """
    text = (ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        raise AssertionError(f"{skill}: no frontmatter")
    lines = m.group(1).splitlines()
    out = {"style": "other", "description": "", "metadata": {}, "license": None}
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("description:"):
            val = line[len("description:"):].strip()
            if val in (">-", ">", ">+", "|", "|-", "|+"):
                # Any block scalar is read, so the words can be checked; only the
                # '>-' form counts as the listing-safe style.
                out["style"] = "block" if val == ">-" else "other-block"
                block = []
                i += 1
                while i < len(lines) and lines[i].startswith((" ", "\t")):
                    block.append(lines[i].strip())
                    i += 1
                out["description"] = " ".join(block)
                continue
            if val:
                out["style"] = "line"
                out["description"] = val
        elif line.startswith("license:"):
            out["license"] = line[len("license:"):].strip()
        elif line.startswith("metadata:"):
            i += 1
            while i < len(lines) and lines[i].startswith((" ", "\t")):
                km = re.match(r"^\s+([A-Za-z0-9_-]+):\s*(.*)$", lines[i])
                if km:
                    out["metadata"][km.group(1)] = km.group(2)
                i += 1
            continue
        i += 1
    return out


# ── the pack's own vocabulary ────────────────────────────────────────────────
# The pack's Markdown may name a skill only when a reader can reach it: the pack's own,
# or a public one (the v1.2 review found four private names). Two exact mechanisms catch
# a private name, neither reading grammar (five rounds of grammar never converged):
#   1. A vocabulary ratchet over the pack's own text: every name-shaped token in every
#      tracked .md file must be in VOCABULARY_NAMES (where a pointer may point),
#      VOCABULARY_KINDS (a kind of work the pack names in place of a skill: "a
#      knowledge-search skill") or VOCABULARY_WORDS (every other name-shaped token the
#      pack's text uses); an unknown token fails with file:line and REMEDY. Every entry
#      must still be produced by the tokenizer from the pack's text (a stale entry
#      fails), so the lists hold only what is used; PLAIN_NAMES are the two public
#      targets with no shape (git, verafox), checked as whole words instead.
#   2. A private-name deny-list read from outside the repository: the file named by
#      TRIAD_PRIVATE_NAMES (one name per line, # comments), matched whole-word and
#      case-insensitive in every file of the pack, with accents folded (prívate reads
#      private) and any run of hyphens, underscores, dashes, spaces, tabs, no-break
#      spaces or line breaks between the name's letters, or none at all (privatenotes,
#      private--notes, jot book, a soft wrap), so every spelling of it is found (a dot is
#      part of a name, not a separator: list private.notes as such; a letter or digit
#      joined to either end, jotbooks or jotbook2, is another word). It
#      catches the one-word names no shape can; unset, its test is skipped with a
#      visible reason. Nothing in the repository names a private name or says where the
#      list lives. The example names in this file (jotbook, notetaker, private-notes,
#      memo-sweeper, notes2go, memo7, the rest of POINTER_FORMS and REVIEW7_FORMS) are
#      made up; a real deny-list must never list one of them, since this file is scanned
#      too: a collision is a red on tests/test_triad.py, and the example is what gets
#      renamed.
# Name-shaped (_name_shaped), after a dash of any kind is read as a hyphen, the case is
# folded and edge punctuation and every known file extension (EXTENSIONS: cfg.json.bak
# reads cfg) are dropped: a token with an internal hyphen or underscore (x_y included),
# letters and digits mixed (notes2go, v8, face2face), a dotted token with letters on both
# sides of a dot (private.notes, notes.v2, mk1made.us), a token with an internal
# lower-to-upper case change before folding (NoteTaker, jotBook), a name holding a date
# (notes-2026-09-30) and a name in any script (café-notes). Not names: a version with a
# dot (v1.3), a commit hash (7 to 40 hex characters holding a letter and two or more
# digits: 19a8722; one digit among hex letters is a name, face2face), a date or time
# standing alone, an all-digit range (60-99), and one-letter parts joined by hyphens or
# dots (A-C, e.g.). Each segment of a path is a token too, so an unmarked name in a path
# is caught: a run is a path when it holds a backslash (C:\Users\me\.agents\skills\x), or
# a slash with a trailing slash, a leading /, ./, ../ or ~/, a segment holding a dot (a
# file name, a dot-folder: .agents/skills/x, .cursor/skills/x) or a segment naming a
# skills folder (SKILL_HOMES: skills/x); a slash in prose (read/comprehend) is not a path.
VOCABULARY_NAMES = frozenset("""
    devcom5 synk182 solid8 dc5 s8 s182 the-triad skills-trifecta spric76 mk1 mk1made.us
    the-proof-pack github.com skillshaper sc2 package_dual doc-coauthoring internal-comms
    cursor claude claude.ai""".split())
VOCABULARY_KINDS = frozenset("knowledge-search repo-rules memory-consolidation".split())
PLAIN_NAMES = ("git", "verafox")
VOCABULARY_WORDS = frozenset("""
    2-second 24h 3p 5-doc anti-patterns append-only apply-report architecture_changed archive
    archive-named archive_dir archive_recommended at-risk audit_protocol auto-downshift auto-execute
    auto-flag auto-resolve auto-resolved auto-resolving auto-rollback auto-run auto-trigger
    auto-upshift bin blink182 broken-incomplete byte-comparing byte-identical carry-forward catch-up
    cloud-synced co-author co-authored co-authors comms_formats company-wide compare_all config-first
    consolidation_complete context-dependent create_archive cross-check cross-skill cross_skill
    data-driven deep-read denser_engine deny-list deploy-aware depth-appropriate depth_actual depth_requested
    digest_history doc-reality doc-worthy docs docs_created docs_exist docs_missing docs_stale
    dot-prefixed drift_detected drift_flags drive-relative end-of-session entry-point
    environment_diverged evidence-based files_consolidated five-document full-doc full-project
    generate_proposal hand-edited handover-first hash-duplicate high-urgency highest-value in
    in-directory in-progress info-dumps instruction-based iso-8601 iso-8601-et key-value last_audit
    last_context last_depth last_mode last_seen line-ending-only line-set line_endings matter-of-fact
    maturity-based meta-context mid-edit mid-operation mid-scan multi-tier name-shaped near-dupes
    near-duplicates new_files_synced new_ids
    node_modules non-identical not-for obj one-line one-paragraph one-sentence one-sided p0-p3 path
    pending_signals per-component per-file per-tier pre-v1 private-name project project-docs pulse
    pulse-depth pulse-level pulse_version quick-start re-plan read-only recommended_next redundancy_found
    references repo-only same-size scan_and_compare scripts section-aware session_count sha-256 single-file
    six-layer skill skills skip-to-action small_team solid8_files_consolidated solid8_last_run
    solid8_redundancy_map stale_project start-end step-by-step stream-of-consciousness sub-agents
    sub-bullet sync_completed sync_conflict synk_drift_detected synk_engine synk_files_changed
    synk_last_run target_dir team-specific template-stamp template-stamping test_triad tests
    three-tier trade-offs triad_private_names trifecta trifecta_protocol ultra-careful under-the-hood
    universal_template user-facing user-specified user-unique user_copy user_experience user_to_working
    utf-8 working-unique working_copy working_to_user wrong-typed yyyy-mm-dd
    denserengine synkengine macos pulse.corrupt env.example v1 v2 byte-order near-duplicate lpt1
    comparisons_cap comparisons_left_out comparisons_total""".split())
REMEDY = ("English or the pack's own word? add it to VOCABULARY_WORDS; a kind of work named in "
          "place of a skill? VOCABULARY_KINDS; a skill? it must be in the pack or public (VOCABULARY_NAMES)")
EXTENSIONS = frozenset("""
    md markdown json py txt zip skill sh bak old orig backup yml yaml html htm css js ts pdf png jpg
    jpeg gif svg csv log lock toml ini cfg xml exe dll so pyc tar gz 7z docx xlsx pptx mp3 mp4 wav
    mov woff woff2 ttf otf sqlite db ico bmp webp""".split())
SKILL_HOMES = frozenset("skills plugins agents commands extensions".split())

_DASHES = str.maketrans(dict.fromkeys("‐‑‒–", "-"))
# a date or time standing alone (not glued to a name by a letter, digit or hyphen)
_STAMP = re.compile(r"(?<![\w-])(?:\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?"
                    r"|\d{1,2}:\d{2}(?::\d{2})?)(?![\w-])")
_RUN = re.compile(r"[\w.\-/~\\]+")
_CAMEL = re.compile(r"[a-z][A-Z][A-Za-z]")
_VERSION_TOKEN = re.compile(r"v\d+(?:\.\d+)+\+?")
_HEX = re.compile(r"[0-9a-f]{7,40}")


def _fold(segment):
    """A token as the vocabulary spells it: dashes as hyphens, case folded, edge
    punctuation and every trailing known file extension dropped (cfg.json.bak reads cfg)."""
    tok = segment.translate(_DASHES).lower().strip("_.-~")
    while True:
        stem, dot, ext = tok.rpartition(".")
        if not (dot and stem and ext in EXTENSIONS):
            return tok
        tok = stem.rstrip(".")


def _name_shaped(segment):
    """The name a token spells when its shape is a name's (the block above), else None."""
    tok = _fold(segment)
    if not any(c.isalpha() for c in tok) or " " in tok:
        return None
    if _VERSION_TOKEN.fullmatch(tok) or (_HEX.fullmatch(tok) and len(re.findall(r"\d", tok)) >= 2):
        return None
    if _CAMEL.search(segment.translate(_DASHES).strip("_.-~")) or "_" in tok:
        return tok
    parts = re.split(r"[-.]", tok)
    if len(parts) > 1:
        return None if all(p.isdigit() for p in parts) or all(len(p) <= 1 for p in parts) else tok
    return tok if re.search(r"\d", tok) else None


def _is_path(run, before):
    """Whether a run of path characters is a path (the block above) rather than prose."""
    segs = re.split(r"[/\\]", run)
    return "\\" in run or ("/" in run and (
        run.endswith("/") or any("." in s.strip(".") or (s.startswith(".") and len(s) > 1) for s in segs)
        or any(s.lower() in SKILL_HOMES for s in segs)
        or (before in " \t(`[\"'<:" and re.match(r"(?:\.{0,2}|~)/", run) is not None)))


def _name_shaped_tokens(text):
    """(line number, token) for every name-shaped token in a Markdown text, in order."""
    text = _STAMP.sub(" ", text.replace("\r\n", "\n").translate(_DASHES))
    found = []
    for n, line in enumerate(text.split("\n"), 1):
        for m in _RUN.finditer(line):
            run, before = m.group(), line[m.start() - 1] if m.start() else " "
            is_path = _is_path(run, before)
            for seg in re.split(r"[/\\]", run):
                tok = _name_shaped(seg)
                if tok is None and is_path:
                    seg = _fold(seg)
                    tok = seg if len(seg) > 1 and any(c.isalpha() for c in seg) else None
                if tok:
                    found.append((n, tok))
    return found


def _markdown_files(root):
    return [p for p in sorted(Path(root).rglob("*.md"), key=Path.as_posix) if ".git" not in p.parts]


def _produced_tokens(root):
    """Every name-shaped token the pack's Markdown produces, as a set."""
    return {tok for p in _markdown_files(root) for _, tok in _name_shaped_tokens(p.read_text(encoding="utf-8"))}


def _unknown_tokens(root):
    """'file:line: token' for every name-shaped token in the pack's Markdown that is in
    no vocabulary list, once per file and token."""
    known = VOCABULARY_NAMES | VOCABULARY_KINDS | VOCABULARY_WORDS | set(PLAIN_NAMES)
    out = []
    for p in _markdown_files(root):
        seen = set()
        for n, tok in _name_shaped_tokens(p.read_text(encoding="utf-8")):
            if tok not in known and tok not in seen:
                seen.add(tok)
                out.append(f"{p.relative_to(root).as_posix()}:{n}: {tok}")
    return out


def _pack_files(root):
    """Every file of the pack (a git export has no .git): all but .git, __pycache__ and bytecode."""
    return [p for p in sorted(Path(root).rglob("*"), key=Path.as_posix) if p.is_file() and p.suffix not in (".pyc", ".pyo")
            and not {".git", "__pycache__"} & set(p.parts)]


def _read_private_names(path):
    """The deny-list: one name per line, blank lines and # comments skipped, case folded."""
    lines = (l.strip() for l in Path(path).read_text(encoding="utf-8-sig").splitlines())
    return [l.lower() for l in lines if l and not l.startswith("#")]


def _fold_text(text):
    """Text as the deny-list reads it: compatibility-decomposed (NFKD), combining marks
    dropped (prívate reads private, a ligature reads its letters), case folded."""
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)).lower()


_JOIN = r"[-_‐‑‒–\s]*"


def _private_name_pattern(name):
    """Whole-word on folded text: the name's letters and digits in order, with any run of
    hyphens, underscores, dashes or whitespace (a line break included) between them, or
    none: private-notes matches privatenotes, private--notes, private notes and a soft
    wrap; jotbook matches jot-book and jot book. A letter or digit joined to either end
    (jotbooks, jotbook2) is another word."""
    chars = [re.escape(c) for c in _fold_text(name) if c not in "-_‐‑‒–" and not c.isspace()]
    return re.compile(r"(?<![a-z0-9])" + _JOIN.join(chars) + r"(?![a-z0-9])")


def _private_name_hits(root, names):
    """'file:line: name' for every listed name found in any file of the pack, once per
    file, line and name (a name wrapped over two lines is reported at the first)."""
    patterns = [(i, n, _private_name_pattern(n)) for i, n in enumerate(names)]
    out = set()
    for fi, p in enumerate(_pack_files(root)):
        text = _fold_text(p.read_bytes().decode("utf-8", "replace"))
        rel = p.relative_to(root).as_posix()
        for i, n, pat in patterns:
            for m in pat.finditer(text):
                out.add((fi, rel, text.count("\n", 0, m.start()) + 1, i, n))
    return [f"{rel}:{line}: {n}" for _, rel, line, _, n in sorted(out)]
# Every pointer form an earlier review or probe listed (the v1.2 to sixth v1.3 reviews:
# arrows, tables under many headers, clauses, headings, labels, links, paths, code spans,
# every spelling and dash), each with the made-up names it holds. Injected into a copy of
# the pack, a name with a mark goes red through the vocabulary and a listed one through
# the deny-list; the form no longer matters, which is the point.
POINTER_FORMS = {
    'Not for diagrams (private-helper).': ['private-helper'],
    '| x | redundancy (→ internal-notes) |': ['internal-notes'],
    '**Not Synk:** repo rules (git, house-rules), the rest': ['house-rules'],
    '| Ask | Skill |\n|-----|-------|\n| Tidy notes | memo-sweeper |': ['memo-sweeper'],
    'description: >-\n  Does things. Not for proofs\n  (github-helper).': ['github-helper'],
    '| x | notes (→ the private-notes skill) |': ['private-notes'],
    '| x | notes (→ a private-notes skill) |': ['private-notes'],
    '| x | notes (→ in private-notes) |': ['private-notes'],
    '| x | notes (→ your private-notes skill) |': ['private-notes'],
    '| x | notes (→ `private-notes`) |': ['private-notes'],
    '| x | notes (→ Solid8 or private-notes) |': ['private-notes'],
    '| x | notes (-> private-notes) |': ['private-notes'],
    '| x | notes (→ notetaker) |': ['notetaker'],
    'Not for notes (the private-notes skill).': ['private-notes'],
    'Not for notes (see private-notes).': ['private-notes'],
    'Not for notes (private-notes (v2)).': ['private-notes'],
    'Not for notes; use private-notes instead.': ['private-notes'],
    'Not for notes. Use notetaker for those.': ['notetaker'],
    '**Not Synk:** notes, use private-notes for those': ['private-notes'],
    '| ask | skill |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    '| Ask | Skill | Why |\n|---|---|---|\n| Notes | notetaker | because |': ['notetaker'],
    '| Ask | Skill |\n|---|---|\n| Notes | [private-notes](https://example.org) |': ['private-notes'],
    '| x | notes (→ your private-notes tool) |': ['private-notes'],
    '| x | notes (→ the private-notes plugin) |': ['private-notes'],
    'Not for notes (a private-notes helper).': ['private-notes'],
    'Not for notes; see private-notes.': ['private-notes'],
    'Not for notes; load private-notes first.': ['private-notes'],
    'Not for notes: private-notes handles those.': ['private-notes'],
    "Not for notes (that is private-notes's job).": ['private-notes'],
    '| x | notes (→ Private-Notes), memos (→ memo_sweeper) |': ['private-notes', 'memo-sweeper'],
    '| Task | Skill |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    '| Need | Use |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    '| Ask | Tool |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    'Not for notes\n(private-notes).': ['private-notes'],
    'Not for notes → private-notes\n- memos -> memo-sweeper.': ['private-notes', 'memo-sweeper'],
    'Not for notes — private-notes.': ['private-notes'],
    'Not for notes: private-notes.': ['private-notes'],
    'Not for notes; leave those to private-notes.': ['private-notes'],
    'Not for notes; those belong to private-notes.': ['private-notes'],
    'Not for notes; open private-notes.': ['private-notes'],
    'Not for notes; prefer private-notes.': ['private-notes'],
    'Not for notes; install private-notes first.': ['private-notes'],
    'Not for notes; switch to private-notes.': ['private-notes'],
    'Not for notes; reach for private-notes.': ['private-notes'],
    'Not for notes; that is what private-notes is for.': ['private-notes'],
    'Not for notes; private-notes exists for that.': ['private-notes'],
    'Not for notes; do those with private-notes.': ['private-notes'],
    'Not for notes; go through private-notes.': ['private-notes'],
    'Not for notes; take those from private-notes.': ['private-notes'],
    'Not for notes; those are done by private-notes.': ['private-notes'],
    'Not for notes; hand those off to private-notes.': ['private-notes'],
    'Not for notes; delegate to private-notes.': ['private-notes'],
    'Not for notes; defer to private-notes.': ['private-notes'],
    'Not for notes → use private-notes.': ['private-notes'],
    'Not for notes: `private-notes`.': ['private-notes'],
    'Not for notes. Private-notes keeps those.': ['private-notes'],
    'Not for notes (that is private-notes’s job).': ['private-notes'],
    'Not meant for notes (private-notes).': ['private-notes'],
    '## Not for\n\n- Notes (private-notes)\n- Merges (git)': ['private-notes'],
    '**Not for:**\n- memos (memo-sweeper)': ['memo-sweeper'],
    'Out of scope: notes (private-notes).': ['private-notes'],
    '| Ask | Handled by |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    '| Need | Skill to use |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    '| Ask | Which skill |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    '| When | Use |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    '| Ask | Skill: |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    '| Ask | Skill |\n|---|---|\n| Notes | private-notes v2 |': ['private-notes'],
    '| Ask | Skill |\n|---|---|\n| Notes | _private-notes_ |': ['private-notes'],
    '| x | notes (→ private-notes v2) |': ['private-notes'],
    '| Ask | Skill |\n|---|---|\n| Notes | jotbook v2 |': ['jotbook'],
    '| x | notes (→ jotbook 2.1) |': ['jotbook'],
    'Not for notes; use notetaker.': ['notetaker'],
    'Not for notes; use notes2go.': ['notes2go'],
    "Not for notes; that is notetaker's job.": ['notetaker'],
    'Not for notes; notetaker handles those.': ['notetaker'],
    '| x | notes (→ use private-notes) |': ['private-notes'],
    'Not for notes, use private-notes instead.': ['private-notes'],
    'Not for notes: use private-notes': ['private-notes'],
    'Not for notes. Use private-notes for those.': ['private-notes'],
    '| Ask | Skill |\n|-----|-------|\n| Notes | the private-notes skill |': ['private-notes'],
    '| Ask | Skill |\n|-----|-------|\n| Notes | [private-notes](https://example.org) |': ['private-notes'],
    '| Ask | Skill | Why |\n|-----|-------|-----|\n| Notes | private-notes | because |': ['private-notes'],
    '| Ask  |  Skill |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    'Not for: notes (private-notes).': ['private-notes'],
    '| x | notes (→ gitnotes-helper) |': ['gitnotes-helper'],
    '| x | notes (→ jotbook) |': ['jotbook'],
    '| x | notes (→ annotator-skill) |': ['annotator-skill'],
    '| x | notes (→ thesaurus-skill) |': ['thesaurus-skill'],
    '| x | notes (→ indexer) |': ['indexer'],
    'Not for notes; try private-notes.': ['private-notes'],
    'Not for notes; run private-notes.': ['private-notes'],
    'Not for notes; the private-notes skill does those.': ['private-notes'],
    'Not for notes. See private-notes for those.': ['private-notes'],
    "Not for notes (private-notes's job).": ['private-notes'],
    'Not for notes (private-notes handles those).': ['private-notes'],
    'Not for notes (use private-notes).': ['private-notes'],
    'Not for notes (`private-notes`).': ['private-notes'],
    '| x | notes (→ Private-Notes) |': ['private-notes'],
    '| x | notes (→ private_notes) |': ['private-notes'],
    'Not for notes → private-notes': ['private-notes'],
    '- notes → private-notes': ['private-notes'],
    '**Not Synk:** notes\n(→ private-notes)': ['private-notes'],
    "| x | notes (→ Solid8's engine, private-notes) |": ['private-notes'],
    '| x | notes (→ e.g. private-notes) |': ['private-notes'],
    '| x | notes (→ private-notes, when small) |': ['private-notes'],
    '| x | notes (→ a private-notes tool) |': ['private-notes'],
    'Not for notes (a private-notes tool).': ['private-notes'],
    'Not for notes (your private-notes tool).': ['private-notes'],
    'Not for notes (a private-notes skill).': ['private-notes'],
    '| x | notes (→ a private-notes helper) |': ['private-notes'],
    'Not for notes (a private-notes plugin).': ['private-notes'],
    '## Not for\n- Notes (private-notes)\n- Merges (git)': ['private-notes'],
    '## Not for\n- notes → private-notes\n- merges → git': ['private-notes'],
    '| Ask | Skill |\n|---|---|\n| Notes | **private-notes** |': ['private-notes'],
    'Not for notes; use private-notes.': ['private-notes'],
    'Not for notes; the\nprivate-notes skill does those.': ['private-notes'],
    '- Not for notes\n  (private-notes).': ['private-notes'],
    'description: >-\n  Not for notes; see\n  private-notes for those.': ['private-notes'],
    '### Notes → private-notes': ['private-notes'],
    'Not for notes → private-notes, which keeps them.': ['private-notes'],
    '| Ask | Skill |\r\n|---|---|\r\n| Notes | private-notes |\r\n': ['private-notes'],
    'Not for notes (private-notes).\r\nNext line.\r\n': ['private-notes'],
    'Not for notes; use Private-Notes.': ['private-notes'],
    'Not for notes; use private_notes.': ['private-notes'],
    'Not for notes; use private notes.': ['private-notes'],
    'Not for notes; use PRIVATE-NOTES.': ['private-notes'],
    'Not for notes; use the private-notes extension.': ['private-notes'],
    'Not for notes; ask the private-notes agent.': ['private-notes'],
    'Not for notes; run the private-notes command.': ['private-notes'],
    'Not for notes; the private-notes MCP server does those.': ['private-notes'],
    'Not for notes; the private-notes workflow covers it.': ['private-notes'],
    'Not for notes; use the private-notes add-on.': ['private-notes'],
    'Not for notes — that lives in private-notes now.': ['private-notes'],
    'Not for notes; private-notes already covers it.': ['private-notes'],
    'Not for notes; use private-notes with care.': ['private-notes'],
    'Not for notes; use private-notes on those.': ['private-notes'],
    'Not for notes; use private-notes as usual.': ['private-notes'],
    'Not for notes; use private-notes via its CLI.': ['private-notes'],
    'Not for notes; use private-notes in that case.': ['private-notes'],
    'Not for notes; use private-notes directly.': ['private-notes'],
    'Not for notes; use private-notes from the menu.': ['private-notes'],
    'Not for notes; see private-notes/README.md.': ['private-notes'],
    'Not for notes; run `skills/private-notes/SKILL.md`.': ['private-notes'],
    'Not for notes; run /private-notes.': ['private-notes'],
    'Not for notes; see [the notes skill](https://github.com/someone/private-notes).': ['private-notes'],
    'Not for notes; see [private-notes][pn].\n\n[pn]: https://example.org': ['private-notes'],
    'Not for notes [private-notes].': ['private-notes'],
    '## Not for notes\n\nUse private-notes for those.': ['private-notes'],
    '### Not for\n\nNotes and memos: use private-notes.': ['private-notes'],
    'Not for notes, memos or to-do lists.\nUse private-notes for those.': ['private-notes'],
    'Not for notes.\nPrivate-notes keeps those.': ['private-notes'],
    '| Task | Owner |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    '| Task | Handled by |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    '| Topic | Go to |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    '| Concern | Delegate to |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    '| If you need | Then use |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    '| Situation | Use |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    '| Problem | Solution |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    '| For | Use |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    '| Want | Use |\n|---|---|\n| Notes | private-notes |': ['private-notes'],
    'Not for notes: notetaker.': ['notetaker'],
    'Not for notes — notetaker.': ['notetaker'],
    'Not for notes; leave those to notetaker.': ['notetaker'],
    'Not for notes; switch to notes2go.': ['notes2go'],
    'Not for notes; those belong to notetaker.': ['notetaker'],
    'Not for notes → notetaker.': ['notetaker'],
    'Not for notes; use the notetaker skill.': ['notetaker'],
    'Not for notes; use the jotbook skill.': ['jotbook'],
    'Not for notes; use the jotbook plugin.': ['jotbook'],
    'Not for notes; use jotbook2.': ['jotbook2'],
    "Not for notes; that is memo7's job.": ['memo7'],
    'Not for notes; memo7 handles those.': ['memo7'],
    'Not for notes (memo7).': ['memo7'],
    'Not for notes; use private‑notes.': ['private-notes'],
    'Not for notes; use private–notes.': ['private-notes'],
}


# ─────────────────────────────────────────────────────────────── solid8
class Solid8Engine(unittest.TestCase):
    def setUp(self):
        self.mod = _load("denser_engine", "solid8/scripts/denser_engine.py")
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def engine(self):
        e = self.mod.DenserEngine(self.tmp)
        e.scan()
        e.compare_all()
        return e

    def test_backup_suffix_is_detected(self):
        _write(self.tmp, "notes.txt", "a\nb\n")
        _write(self.tmp, "notes.txt.bak", "a\nb\nc\n")
        e = self.engine()
        self.assertEqual(e.fingerprints["notes.txt.bak"].name_pattern, "backup")
        pair = {frozenset((c.file_a, c.file_b)) for c in e.comparisons}
        self.assertIn(frozenset(("notes.txt", "notes.txt.bak")), pair)

    def test_word_containing_copy_is_not_copy_sprawl(self):
        _write(self.tmp, "copywriting.md", "# Copy\nline one\n")
        _write(self.tmp, "writing.md", "# Other\nsomething else entirely\n")
        e = self.engine()
        self.assertIsNone(e.fingerprints["copywriting.md"].name_pattern)
        _write(self.tmp, "report - Copy.md", "x\n")
        e = self.engine()
        self.assertEqual(e.fingerprints["report - Copy.md"].name_pattern, "copy")

    def test_a_year_in_parentheses_is_not_copy_sprawl(self):
        # Break it catches: any trailing "(digits)" read as a copy number, so
        # "Budget (2024).txt" and "Budget (2025).txt" came back as copy sprawl on
        # every run (seen 2026-09-30). A copy number has one to three digits.
        _write(self.tmp, "Budget (2024).txt", "a\n")
        _write(self.tmp, "Budget (2025).txt", "b\n")
        _write(self.tmp, "Budget (2).txt", "c\n")
        e = self.engine()
        self.assertIsNone(e.fingerprints["Budget (2024).txt"].name_pattern)
        self.assertIsNone(e.fingerprints["Budget (2025).txt"].name_pattern)
        self.assertEqual(e.fingerprints["Budget (2).txt"].name_pattern, "copy")

    def test_binary_files_are_hash_only(self):
        blob = bytes(range(256)) * 8
        _write(self.tmp, "a.bin", data=blob + b"\x00tail-a")
        _write(self.tmp, "b.bin", data=blob + b"\x00tail-b")
        e = self.engine()
        tiers = [c.tier for c in e.comparisons if {c.file_a, c.file_b} == {"a.bin", "b.bin"}]
        self.assertEqual(tiers, [], "different binaries must not get a content-similarity tier")

    def test_json_is_compared_structurally(self):
        _write(self.tmp, "cfg.json", json.dumps({"a": 1, "b": {"c": 2, "d": 3}}, indent=2))
        _write(self.tmp, "cfg_v2.json", json.dumps({"b": {"d": 3, "c": 2}, "a": 1}))
        e = self.engine()
        comp = [c for c in e.comparisons if {c.file_a, c.file_b} == {"cfg.json", "cfg_v2.json"}]
        self.assertEqual(len(comp), 1)
        self.assertEqual(comp[0].tier, "B")
        self.assertGreaterEqual(comp[0].similarity, 0.999)

    def test_a_backup_is_compared_as_the_kind_of_file_it_backs_up(self):
        # Break it catches: the comparison unit picked from the file's own suffix,
        # so cfg.json.bak was read as raw lines against cfg.json read as JSON, and
        # guide.md.bak as raw lines against guide.md read by heading. The units
        # never overlap, and the very pair the engine formed by base name got no
        # tier (found by the second v1.3 review). A backup that differs only in
        # formatting is the case a user expects caught.
        cfg = {"a": 1, "b": {"c": 2, "d": 3}}
        _write(self.tmp, "cfg.json", json.dumps(cfg, indent=2))
        _write(self.tmp, "cfg.json.bak", json.dumps(cfg))
        guide = "# Guide\n\nline one\n\nline two\n\n## Part\n\nline three\n"
        _write(self.tmp, "docs/guide.md", guide)
        _write(self.tmp, "docs/guide.md.bak", guide.replace("\n\n", "\n"))
        e = self.engine()
        for pair in (("cfg.json", "cfg.json.bak"), ("docs/guide.md", "docs/guide.md.bak")):
            with self.subTest(pair=pair):
                comp = [c for c in e.comparisons if {c.file_a, c.file_b} == set(pair)]
                self.assertEqual([c.tier for c in comp], ["B"])
                self.assertGreaterEqual(comp[0].similarity, 0.999)

    def test_a_backup_with_two_markers_meets_its_live_file(self):
        # Break it catches: the backup marker stripped once, so cfg.json.bak.bak
        # and cfg.json.bak.old met only each other (base cfg.json.bak, read as raw
        # lines) and cfg.json.orig~ met nothing (found by the third v1.3 review).
        # Every marker is stripped: each backup meets cfg.json and is read as JSON.
        cfg = {"a": 1, "b": {"c": 2, "d": 3}, "e": [1, 2]}
        _write(self.tmp, "cfg.json", json.dumps(cfg, indent=2))
        backups = {"cfg.json.bak.bak": json.dumps(cfg), "cfg.json.bak.old": json.dumps(cfg, indent=1),
                   "cfg.json.orig~": json.dumps(cfg, indent=4)}
        for rel, text in backups.items():
            _write(self.tmp, rel, text)
        e = self.engine()
        for rel in backups:
            with self.subTest(backup=rel):
                self.assertEqual(e._base_name(rel), "cfg.json")
                comp = [c for c in e.comparisons if {c.file_a, c.file_b} == {"cfg.json", rel}]
                self.assertEqual([c.tier for c in comp], ["B"])
                self.assertGreaterEqual(comp[0].similarity, 0.999)

    def test_a_backup_of_a_binary_is_binary(self):
        # Break it catches: the binary check and the fingerprint's extension read
        # the backup's own suffix, so a PDF backup with no null byte in its first
        # 8 KiB was fingerprinted as text and got a content tier: doc2.pdf.bak and
        # doc3.pdf.orig came back one tier-B cluster (found by the third v1.3
        # review). A binary never gets a content tier, backed up or not.
        pdf = "%PDF-1.4\n" + "".join(f"{i} 0 obj << /Type /Page /N {i} >> endobj\n" for i in range(40)) + "%%EOF\n"
        _write(self.tmp, "doc.pdf", pdf)
        _write(self.tmp, "doc.pdf.bak", pdf + "trailer << >>\n")
        _write(self.tmp, "doc2.pdf.bak", pdf.replace("/N 3 ", "/N 33 "))
        _write(self.tmp, "doc3.pdf.orig", pdf.replace("/N 5 ", "/N 55 "))
        e = self.engine()
        for rel in ("doc.pdf.bak", "doc2.pdf.bak", "doc3.pdf.orig"):
            with self.subTest(file=rel):
                fp = e.fingerprints[rel]
                self.assertEqual((fp.binary, fp.extension, fp.line_count), (True, ".pdf", 0))
        self.assertEqual([(c.file_a, c.file_b, c.tier) for c in e.comparisons], [])

    def test_archive_folder_is_named_for_solid8_and_utf8(self):
        _write(self.tmp, "é-notes.txt", "x\n")
        e = self.engine()
        dest = e.create_archive(["é-notes.txt"], Path(self.tmp) / "ARCHIVE", "test")
        self.assertTrue(dest.name.startswith("solid8-"), dest.name)
        self.assertIn("é-notes.txt", (dest / "rollback.md").read_text(encoding="utf-8"))
        self.assertTrue((dest / "manifest.json").is_file())

    def test_archived_copies_only_count_when_identical(self):
        # Same size (over the engine's 100-byte floor), all but one line shared:
        # the size grouping compares them, so an engine that ignores archive
        # status reports a B-tier near-duplicate here.
        body = "# A\n" + "".join(f"line number {i:02d} of the doc\n" for i in range(10))
        _write(self.tmp, "doc.md", body + "final line A\n")
        _write(self.tmp, "ARCHIVE/old/doc.md", body + "final line B\n")
        e = self.engine()
        non_s = [c for c in e.comparisons if c.tier != "S" and any("ARCHIVE" in f for f in (c.file_a, c.file_b))]
        self.assertEqual(non_s, [])

    def test_archived_subset_of_a_live_file_is_still_reported(self):
        # The one archive case worth reporting: a live file holds all of an
        # archived one plus more. Guards the case below from over-reaching.
        # The two are the same size (over the 100-byte floor) so the engine
        # compares them at all: it only pairs files by hash, by base name inside
        # one folder, or by equal size.
        shared = "".join(f"shared line {i:02d}\n" for i in range(10))
        _write(self.tmp, "report.txt", shared + "unique line 01\n")
        _write(self.tmp, "ARCHIVE/old/report_v0.txt", shared + "shared line 00\n")
        e = self.engine()
        tiers = [c.tier for c in e.comparisons
                 if {c.file_a, c.file_b} == {"report.txt", "ARCHIVE/old/report_v0.txt"}]
        self.assertEqual(tiers, ["A"])

    def test_superset_pair_inside_an_archive_is_not_reported(self):
        # Break it catches: two files that both live under ARCHIVE/, one a
        # superset of the other, proposed for consolidation. Archives are
        # intentional (SKILL.md, Context Awareness) and the engine's docstring
        # says a protected file is reported only as an exact duplicate or as the
        # subset of a LIVE file. Found 2026-09-30 driving the engine on a fixture:
        # ARCHIVE/old/report.md | ARCHIVE/old/report_v0.md came back as tier A.
        body = "# Report\n" + "".join(f"line {i}\n" for i in range(10))
        _write(self.tmp, "ARCHIVE/old/report.md", body + "more\n")
        _write(self.tmp, "ARCHIVE/old/report_v0.md", body)
        e = self.engine()
        inside = [(c.file_a, c.file_b, c.tier) for c in e.comparisons
                  if c.file_a.startswith("ARCHIVE/") and c.file_b.startswith("ARCHIVE/")]
        self.assertEqual(inside, [])

    def test_version_sprawl_is_found_across_folders(self):
        # Break it catches: version, copy and backup sprawl that crossed a folder
        # boundary never compared, because candidates were grouped by base name
        # inside one folder only. Seen 2026-09-30: report_v2.md at the root and
        # drafts/report_v1.md, a strict subset of a different size, gave
        # "Clusters: 0" while the same pair in one folder gave tier A.
        body = "# Report\n" + "".join(f"line {i}\n" for i in range(10))
        _write(self.tmp, "report_v2.md", body + "more\n")
        _write(self.tmp, "drafts/report_v1.md", body)
        # Unmarked files that merely share a name across folders are not sprawl:
        # a README.md in every folder is never paired with itself.
        _write(self.tmp, "a/README.md", "# A\n" + "".join(f"alpha {i}\n" for i in range(10)))
        _write(self.tmp, "b/README.md", "# B\n" + "".join(f"beta {i}\n" for i in range(10)) + "and one more\n")
        e = self.engine()
        tiers = [c.tier for c in e.comparisons if {c.file_a, c.file_b} == {"report_v2.md", "drafts/report_v1.md"}]
        self.assertEqual(tiers, ["A"])
        self.assertNotIn(frozenset(("a/README.md", "b/README.md")), e._compared)

    def test_cli_survives_a_cp1252_console(self):
        _write(self.tmp, "a.txt", "same\n")
        _write(self.tmp, "a - Copy.txt", "same\n")
        r = _run_cp1252(ROOT / "solid8/scripts/denser_engine.py", self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))

    def test_cli_refuses_a_target_that_is_not_a_folder(self):
        # Break it catches: a mistyped path read as a clean project ("0 files
        # fingerprinted", exit 0), seen 2026-09-30; it is an error that names the path.
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(Path(self.tmp) / "nope")])
        self.assertEqual(rc, 1)
        self.assertIn("not a folder", out.getvalue())
        self.assertIn("nope", out.getvalue())

    def test_cli_writes_json_proposal(self):
        _write(self.tmp, "a.txt", "same\n")
        _write(self.tmp, "a - Copy.txt", "same\n")
        out = Path(self.tmp) / "proposal.json"
        r = _run_cp1252(ROOT / "solid8/scripts/denser_engine.py", self.tmp, "--json", out)
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))
        data = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(data["tier_counts"]["S"], 1)

    def test_pulse_with_a_wrong_typed_field_is_treated_as_empty_with_a_note(self):
        # Same break as the Synk182 case: "pending_signals": null crashed --pulse
        # with a TypeError (seen 2026-09-30); handled as empty, said so.
        for broken in ({"project": "X", "cross_skill": {"pending_signals": None}},
                       {"project": "X", "cross_skill": ["not", "an", "object"]}):
            with self.subTest(pulse=json.dumps(broken)):
                _write(self.tmp, "docs/PULSE.json", json.dumps(broken))
                out = io.StringIO()
                with redirect_stdout(out):
                    path = self.mod.update_pulse(self.tmp, {"solid8_last_run": "2026-09-30T00:00:00-04:00"},
                                                 [("redundancy_found", "devcom5", "1 pair")])
                self.assertIsNotNone(path)
                data = json.loads(Path(path).read_text(encoding="utf-8"))
                self.assertEqual(data["project"], "X")
                self.assertEqual([s["signal"] for s in data["cross_skill"]["pending_signals"]], ["redundancy_found"])
                self.assertIn("treated as empty", out.getvalue())

    def test_cli_pulse_when_docs_is_a_file_warns(self):
        # Break it catches: --pulse in a project whose docs is a file printing the
        # whole proposal and then dying on an uncaught FileExistsError (found by
        # the third v1.3 review). The run says why nothing was recorded.
        docs = _write(self.tmp, "docs", "a file, not a folder\n")
        _write(self.tmp, "a.txt", "same\n")
        _write(self.tmp, "a - Copy.txt", "same\n")
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([self.tmp, "--pulse"])
        self.assertEqual(rc, 0)
        self.assertIn("Consolidation Proposal", out.getvalue())
        self.assertIn("not a folder", out.getvalue())
        self.assertEqual(docs.read_text(encoding="utf-8"), "a file, not a folder\n")

    def test_cli_pulse_says_when_the_pulse_holds_no_object(self):
        # Break it catches: "PULSE.json did not parse" for a PULSE that parses but
        # is not an object ("[]", "null", "0"), a claim the run cannot make (the
        # third v1.3 review). The file is left untouched and the words are true.
        _write(self.tmp, "a.txt", "same\n")
        for text in ("{not json", "[]"):
            with self.subTest(pulse=text):
                p = _write(self.tmp, "docs/PULSE.json", text)
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.mod.main([self.tmp, "--pulse"])
                self.assertEqual(rc, 0)
                self.assertIn("PULSE.json does not hold a JSON object; left untouched", out.getvalue())
                self.assertEqual(p.read_text(encoding="utf-8"), text)

    def test_cli_json_that_cannot_be_written_says_so_and_still_records_the_pulse(self):
        # Break it catches: --json OUT into a missing folder, or onto a folder,
        # printing the whole proposal and then a FileNotFoundError or
        # PermissionError traceback, with a --pulse beside it never reached (found
        # by the fourth v1.3 review). The run says why, records the scan, exits 1.
        _write(self.tmp, "a.txt", "same\n")
        _write(self.tmp, "a - Copy.txt", "same\n")
        (Path(self.tmp) / "taken").mkdir()
        pulse = Path(self.tmp) / "docs" / "PULSE.json"
        for out_path in ("no-such-folder/proposal.json", "taken"):
            with self.subTest(json=out_path):
                if pulse.exists():
                    pulse.unlink()
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.mod.main([self.tmp, "--json", str(Path(self.tmp) / out_path), "--pulse"])
                self.assertEqual(rc, 1)
                self.assertIn("Proposal not written", out.getvalue())
                self.assertIn("PULSE updated", out.getvalue())
                self.assertIn("solid8_last_run", pulse.read_text(encoding="utf-8"))

    def test_cli_json_given_an_empty_name_says_so(self):
        # Break it catches: --json "" (an empty shell variable) dropped without a word:
        # the proposal printed, nothing written, exit 0 (found by the fifth v1.3
        # review). It is answered as a proposal that cannot be written.
        _write(self.tmp, "a.txt", "same\n")
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([self.tmp, "--json", "", "--pulse"])
        self.assertEqual(rc, 1)
        self.assertIn("Proposal not written (no file name given)", out.getvalue())
        self.assertIn("solid8_last_run", (Path(self.tmp) / "docs" / "PULSE.json").read_text(encoding="utf-8"))

    def test_a_junction_inside_the_target_is_named_and_not_followed(self):
        # Break it catches: a junction walked as a folder: one back to the target gave
        # "64 files fingerprinted", 2016 exact duplicates and a ~98% reduction, all one
        # file seen through the loop (found by the fifth v1.3 review). A link the walk
        # skips anyway (node_modules, as a package manager links it) goes unnamed.
        _write(self.tmp, "a.txt", "one\n")
        if not _link_folder(Path(self.tmp) / "loop", self.tmp):
            self.skipTest("this machine makes neither a junction nor a symbolic link")
        self.assertTrue(_link_folder(Path(self.tmp) / "node_modules", self.tmp))
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([self.tmp])
        self.assertEqual(rc, 0)
        self.assertIn("Exact dupes (S): 0", out.getvalue())
        self.assertRegex(out.getvalue(), r"not followed.*loop")
        e = self.engine()
        self.assertEqual(sorted(e.fingerprints), ["a.txt"])
        self.assertEqual(e.not_followed, ["loop"])

    def test_pulse_prunes_old_consumed_signals_whatever_their_offset_form(self):
        # Same break as the Synk182 case: a month-old consumed signal stamped with Z
        # kept on Python 3.10, and one with no offset kept on every version.
        _write(self.tmp, "docs/PULSE.json", _old_signals("solid8"))
        path = self.mod.update_pulse(self.tmp, {"solid8_last_run": "x"})
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.assertEqual([s["signal"] for s in data["cross_skill"]["pending_signals"]], ["recent"])

    def test_a_file_that_cannot_be_read_is_named_with_its_reason_not_fingerprinted_as_empty(self):
        # Break it catches: a file that exists but cannot be read (held by another
        # process, or an ACL deny) fingerprinted with hash "" and 0 lines, "2 files
        # fingerprinted", no unreadable line, and grouped as a normal file (the sixth
        # v1.3 review, S3 and S4). It is left out of the fingerprints and named with the
        # OS reason, on the engine and after the CLI's count.
        _write(self.tmp, "held.txt", "user line 1\nuser line 2\n")
        _write(self.tmp, "free.txt", "same\n")
        _hold_unreadable(self, Path(self.tmp) / "held.txt", self.tmp)
        e = self.engine()
        self.assertEqual(sorted(e.fingerprints), ["free.txt"])
        self.assertEqual(len(e.unreadable), 1)
        self.assertRegex(e.unreadable[0], r"^held\.txt: cannot be read \(.+\)$")
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([self.tmp])
        self.assertEqual(rc, 0)
        self.assertIn("1 files fingerprinted", out.getvalue())
        self.assertRegex(out.getvalue(), r"unreadable: 1\n.*held\.txt: cannot be read \(")

    def test_a_file_link_is_named_and_not_followed_a_dangling_one_too(self):
        # Break it catches: a symbolic link to a file inside the target fingerprinted with
        # the target's content (a duplicate of itself), and a dangling one counted as
        # "unreadable: 1" with no name (the sixth v1.3 review, S5c). Both are named among
        # the links not followed, the dangling one as such, and neither is fingerprinted.
        _write(self.tmp, "a.txt", "a\n" * 60)
        try:
            os.symlink(Path(self.tmp) / "a.txt", Path(self.tmp) / "link.txt")
            os.symlink(Path(self.tmp) / "no-such.txt", Path(self.tmp) / "dangling.txt")
        except OSError as e:
            self.skipTest(f"this machine cannot make a file symlink ({e})")
        e = self.engine()
        self.assertEqual(sorted(e.fingerprints), ["a.txt"])
        self.assertEqual(e.unreadable, [])
        self.assertEqual(e.not_followed, ["dangling.txt (its target is missing)", "link.txt"])
        self.assertEqual(e.comparisons, [])

    def test_same_size_files_are_each_read_once_not_once_per_pair(self):
        # Break it catches: 700 files of one size, all different, in one folder taking
        # 51 s for "Clusters: 0" because every pair read both files again (the sixth v1.3
        # review, S12). Each candidate file is read once and the pairs compare the cached
        # units, so the run takes seconds and finds the same pairs: here a near-duplicate
        # pair of the same size is still tier B.
        n = 300
        for i in range(n):
            _write(self.tmp, f"note-{i:04d}.txt", f"note {i:04d} " + "x" * 100 + "\n" + f"second line {i:04d}\n")
        body = "".join(f"shared line {i:02d}\n" for i in range(10))
        _write(self.tmp, "pair-a.txt", body + "only in a\n")
        _write(self.tmp, "pair-b.txt", body + "only in b\n")
        e = self.mod.DenserEngine(self.tmp)
        e.scan()
        with mock.patch.object(e, "_units", wraps=e._units) as units:
            e.compare_all()
        self.assertLessEqual(units.call_count, n + 2, "a candidate file is read once")
        self.assertEqual([(c.file_a, c.file_b, c.tier) for c in e.comparisons], [("pair-a.txt", "pair-b.txt", "B")])

    def test_cli_details_below_zero_is_answered(self):
        # Break it catches: --details -1 printing every cluster but the last, and -3 one
        # (a negative slice), at rc 0 (the sixth v1.3 review, S12). It is an error.
        _write(self.tmp, "a.txt", "same\n")
        _write(self.tmp, "a - Copy.txt", "same\n")
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([self.tmp, "--details", "-1"])
        self.assertEqual(rc, 1)
        self.assertIn("--details", out.getvalue())
        self.assertNotIn("Consolidation Proposal", out.getvalue())

    def test_a_pulse_saved_with_a_bom_is_read(self):
        # Break it catches: a PULSE.json some editors save with a UTF-8 BOM answered
        # "does not hold a JSON object; left untouched" (the sixth v1.3 review, S6): the
        # reason was wrong, and the run went unrecorded. It is read, and written back
        # without the mark.
        _write(self.tmp, "a.txt", "same\n")
        p = _write(self.tmp, "docs/PULSE.json", data=b"\xef\xbb\xbf" + b'{"project": "X", "cross_skill": {"pending_signals": []}}')
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([self.tmp, "--pulse"])
        self.assertEqual(rc, 0)
        self.assertIn("PULSE updated", out.getvalue())
        raw = p.read_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(json.loads(raw.decode("utf-8"))["project"], "X")
        self.assertIn("solid8_last_run", raw.decode("utf-8"))


    def test_a_file_unreadable_at_compare_time_is_named_not_dropped_without_a_word(self):
        # Break it catches: a file readable at the scan and unreadable at the compare (held
        # by another process between the two) swallowed into a "-" tier and dropped from
        # the comparisons with engine.unreadable empty, so the CLI printed unreadable for
        # nothing (the seventh v1.3 review, probe7_solid8b). It is named with the OS reason,
        # once, like a file unreadable at the scan.
        body = "".join(f"shared line {i:02d}\n" for i in range(10))
        for name, tail in (("a.txt", "only in a\n"), ("b.txt", "only in b\n"), ("c.txt", "only in c\n")):
            _write(self.tmp, name, body + tail)
        e = self.mod.DenserEngine(self.tmp)
        e.scan()
        real = e._units

        def units(path):
            if path.name == "c.txt":
                raise PermissionError(13, "Permission denied", str(path))
            return real(path)
        with mock.patch.object(e, "_units", units):
            e.compare_all()
        self.assertEqual(e.unreadable, ["c.txt: cannot be read (Permission denied)"])
        self.assertEqual([(c.file_a, c.file_b, c.tier) for c in e.comparisons], [("a.txt", "b.txt", "B")])
        out = io.StringIO()
        with mock.patch.object(self.mod.DenserEngine, "_units", lambda self_, p: units(p)), redirect_stdout(out):
            rc = self.mod.main([self.tmp])
        self.assertEqual(rc, 0)
        self.assertRegex(out.getvalue(), r"unreadable: 1\n\s+c\.txt: cannot be read \(Permission denied\)")

    def test_json_proposal_caps_comparisons_per_cluster_and_says_how_many_were_left_out(self):
        # Break it catches: a near-duplicate cluster of 700 files writing 244,650
        # comparisons, a 59 MB proposal.json (the seventh v1.3 review, T3c), while --pulse's
        # map was capped at 50 pairs per tier. A cluster's comparisons are capped at the
        # same 50, the proposal states the cap and each capped cluster says how many were
        # left out, in the file and on the terminal.
        for i in range(15):
            _write(self.tmp, f"dup-{i:02d}.txt", "same\n")
        out_file = Path(self.tmp) / "proposal.json"
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([self.tmp, "--json", str(out_file)])
        self.assertEqual(rc, 0)
        data = json.loads(out_file.read_text(encoding="utf-8"))
        self.assertEqual(data["comparisons_cap"], 50)
        self.assertEqual(data["tier_counts"]["S"], 105)
        cluster, = data["clusters"]
        self.assertEqual(len(cluster["files"]), 15)
        self.assertEqual((len(cluster["comparisons"]), cluster["comparisons_total"], cluster["comparisons_left_out"]), (50, 105, 55))
        self.assertRegex(out.getvalue(), r"Proposal written: .*\(comparisons capped at 50 per cluster; 55 left out\)")


# ─────────────────────────────────────────────────────────────── synk182
class Synk182Engine(unittest.TestCase):
    def setUp(self):
        self.mod = _load("synk_engine", "synk182/scripts/synk_engine.py")
        self.tmp = tempfile.mkdtemp()
        self.u = Path(self.tmp) / "user"
        self.w = Path(self.tmp) / "work"
        self.u.mkdir()
        self.w.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def synk(self):
        return self.mod.SynkEngine(str(self.u), str(self.w))

    def test_empty_file_does_not_crash(self):
        _write(self.u, "empty.txt", "")
        _write(self.w, "empty.txt", "now has text\n")
        with redirect_stdout(io.StringIO()):
            r = self.synk().scan_and_compare()
        self.assertIn("empty.txt", r["files"])

    def test_build_and_vcs_folders_are_skipped(self):
        _write(self.u, "node_modules/x.js", "1")
        _write(self.u, ".git/HEAD", "ref")
        _write(self.u, "src/app.py", "print(1)\n")
        with redirect_stdout(io.StringIO()):
            r = self.synk().scan_and_compare()
        self.assertEqual(sorted(r["files"]), ["src/app.py"])

    def test_scan_is_read_only(self):
        _write(self.u, "a.txt", "one\n")
        before = sorted(p.as_posix() for p in Path(self.tmp).rglob("*"))
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            s.plan()
        after = sorted(p.as_posix() for p in Path(self.tmp).rglob("*"))
        self.assertEqual(before, after)

    def test_backup_really_contains_the_originals(self):
        _write(self.u, "a.txt", "user version\n")
        _write(self.w, "a.txt", "work version\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            dest = s.backup(["a.txt"], side="working")
        self.assertEqual((dest / "working" / "a.txt").read_text(encoding="utf-8"), "work version\n")
        self.assertTrue((dest / "manifest.json").is_file())
        self.assertTrue((dest / "rollback.md").is_file())

    def test_apply_copies_only_what_was_approved_and_verifies(self):
        _write(self.u, "new.txt", "brand new\n")
        _write(self.u, "other.txt", "not approved\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan = s.plan()
            ids = [a["id"] for a in plan if a["path"] == "new.txt"]
            report = s.apply(plan, ids)
        self.assertTrue((self.w / "new.txt").is_file())
        self.assertFalse((self.w / "other.txt").exists())
        self.assertEqual(report["applied"][0]["verified"], ["existence", "hash", "size", "timestamp", "line_count", "content"])

    def test_superset_is_never_auto_resolved(self):
        _write(self.u, "s.txt", "a\nb\n")
        _write(self.w, "s.txt", "a\nb\nc\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            r = s.scan_and_compare()
            plan = s.plan()
        self.assertEqual(r["files"]["s.txt"]["relationship"], "b_superset")
        act = [a for a in plan if a["path"] == "s.txt"][0]
        self.assertEqual(act["review"], "MAXIMUM")
        self.assertIsNone(act["direction"])

    def test_failed_verification_rolls_back(self):
        _write(self.u, "a.txt", "user\n")
        _write(self.w, "a.txt", "working original\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan = s.plan()
            act = [a for a in plan if a["path"] == "a.txt"][0]
            act["direction"] = "user_to_working"
            s._verify_copy = lambda src, dst: ["hash"]  # force a failure
            report = s.apply(plan, [act["id"]])
        self.assertEqual(report["rolled_back"], ["a.txt"])
        self.assertEqual((self.w / "a.txt").read_text(encoding="utf-8"), "working original\n")

    def test_plan_path_outside_the_copies_is_refused_before_any_write(self):
        # Break it catches: a plan item whose path leaves the copies, approved by
        # id, writing outside them. Seen 2026-09-30 driving the engine with the
        # copies under different parents: "../victim.txt" overwrote a file
        # beside the working copy and its backup landed at the archive root
        # instead of under working/. Every escaping form is refused before any
        # backup or write, and nothing is reported as verified.
        u, w = Path(self.tmp) / "a" / "user", Path(self.tmp) / "b" / "work"
        _write(u, "keep.txt", "one\n")
        _write(Path(self.tmp), "a/victim.txt", "from the user side\n")
        victim = _write(Path(self.tmp), "b/victim.txt", "untouched\n")
        escaping = ["../victim.txt", "sub/../../victim.txt", "..\\victim.txt", str(victim),
                    "/victim.txt", "C:victim.txt", "\\\\server\\share\\victim.txt"]
        with redirect_stdout(io.StringIO()):
            s = self.mod.SynkEngine(str(u), str(w))
            s.scan_and_compare()
            plan = s.plan()
            bad = [{"id": 90 + i, "path": p, "status": "user_only", "direction": "user_to_working"}
                   for i, p in enumerate(escaping)]
            report = s.apply(plan + bad, [b["id"] for b in bad])
        self.assertEqual(victim.read_text(encoding="utf-8"), "untouched\n")
        self.assertEqual(report["applied"], [])
        self.assertEqual(sorted(r["path"] for r in report["refused"]), sorted(escaping))
        self.assertIsNone(report["archive"], "nothing was written, so no archive folder is made")
        self.assertFalse((u / "ARCHIVE").exists())
        with self.assertRaises(ValueError):
            s.backup(["../victim.txt"], side="working")
        self.assertFalse((u / "ARCHIVE").exists(), "a refused backup leaves no archive folder behind")

    def test_stale_plan_never_overwrites_a_file_that_appeared_after_it(self):
        # Break it catches: a plan applied without re-checking its premise. Seen
        # 2026-09-30 driving the engine: late.txt, planned as "new in the user
        # copy", appeared in the working copy after --plan and --apply replaced
        # it with the user version, reported "six layers verified". The item is
        # refused and the run says to re-plan; the same holds when the
        # destination of any item changed since the plan was written.
        _write(self.u, "late.txt", "user version\n")
        _write(self.u, "edited.txt", "user\n")
        _write(self.w, "edited.txt", "working at plan time\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan = s.plan()
            _write(self.w, "late.txt", "written after the plan\n")
            _write(self.w, "edited.txt", "working, edited after the plan\n")
            for act in plan:
                act["direction"] = "user_to_working"
            report = s.apply(plan, [a["id"] for a in plan])
        self.assertEqual((self.w / "late.txt").read_text(encoding="utf-8"), "written after the plan\n")
        self.assertEqual((self.w / "edited.txt").read_text(encoding="utf-8"), "working, edited after the plan\n")
        self.assertEqual(report["applied"], [])
        self.assertEqual(sorted(r["path"] for r in report["refused"]), ["edited.txt", "late.txt"])
        for r in report["refused"]:
            self.assertIn("re-plan", r["reason"])

    def test_plan_item_naming_a_folder_is_refused_before_anything_is_touched(self):
        # Break it catches: a plan item naming a folder inside the copies ("sub",
        # or "." for the copy itself) passed the path and premise checks; the copy
        # failed, the rollback called unlink() on the folder, and the run died on
        # a PermissionError traceback, leaving an archive behind (found by the
        # second v1.3 review). It is refused before any backup or write, with a
        # message and exit 1.
        _write(self.u, "keep.txt", "one\n")
        _write(self.w, "keep.txt", "one\n")
        _write(self.w, "sub/inner.txt", "inner\n")
        (self.u / "sub").mkdir()
        plan = [{"id": 1, "path": "sub", "status": "merge", "direction": "working_to_user"},
                {"id": 2, "path": ".", "status": "merge", "direction": "user_to_working"}]
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            report = s.apply(plan, [1, 2])
        self.assertEqual(report["applied"], [])
        self.assertEqual(sorted(r["path"] for r in report["refused"]), [".", "sub"])
        for r in report["refused"]:
            self.assertIn("folder", r["reason"])
        self.assertIsNone(report["archive"])
        self.assertFalse((self.u / "ARCHIVE").exists())
        self.assertTrue((self.u / "sub").is_dir())
        self.assertEqual((self.w / "sub/inner.txt").read_text(encoding="utf-8"), "inner\n")
        plan_file = _write(self.tmp, "plan.json", json.dumps(plan))
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", "1,2"])
        self.assertEqual(rc, 1)
        self.assertIn("folder", out.getvalue())
        self.assertFalse((self.u / "ARCHIVE").exists())

    def test_rollback_never_deletes_or_offers_to_delete_a_folder(self):
        # Break it catches: the rollback of a failed copy calling unlink() on a
        # destination that is a folder, and rollback.md listing that existing
        # folder as "did not exist: delete it" (found by the second v1.3 review).
        # The refusal above keeps folders out of apply; this holds even for an
        # item that gets past it.
        _write(self.w, "sub/inner.txt", "inner\n")
        _write(self.u, "sub/mine.txt", "mine\n")
        plan = [{"id": 1, "path": "sub", "status": "merge", "direction": "working_to_user"}]
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            s.refusal = lambda rel: None  # force the item past the checks
            report = s.apply(plan, [1])
        self.assertEqual(report["rolled_back"], ["sub"])
        self.assertEqual((self.u / "sub/mine.txt").read_text(encoding="utf-8"), "mine\n")
        note = (Path(report["archive"]) / "rollback.md").read_text(encoding="utf-8")
        line = [l for l in note.splitlines() if l.startswith("- `") and "sub`" in l]
        self.assertEqual(len(line), 1, note)
        self.assertNotIn("delete", line[0])

    def test_bulk_approve_new_skips_an_escaping_item(self):
        _write(self.u, "new.txt", "brand new\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan = s.plan()
        plan.append({"id": 99, "path": "../victim.txt", "status": "user_only", "direction": "user_to_working"})
        ids = s.new_ids(plan)
        self.assertEqual(ids, [a["id"] for a in plan if a["path"] == "new.txt"])

    def test_bulk_approve_new_leaves_the_pulse_file_to_an_explicit_id(self):
        # Break it catches: 'new' copying docs/PULSE.json across when it exists on
        # one side only; --pulse then writes only the user copy's, so the two
        # differ on every later run. It stays approvable by its id.
        _write(self.u, "docs/PULSE.json", "{}\n")
        _write(self.u, "new.txt", "brand new\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan = s.plan()
        self.assertEqual(s.new_ids(plan), [a["id"] for a in plan if a["path"] == "new.txt"])

    def test_pulse_update_keeps_other_skills_keys(self):
        _write(self.u, "docs/PULSE.json", json.dumps({
            "project": "X", "heartbeat": {"session_count": 4},
            "cross_skill": {"another_skill": {"version": "5.1.0"}, "pending_signals": []}}))
        path = self.mod.update_pulse(self.u, {"synk_last_run": "2026-09-15T17:00:00-04:00"},
                                     [("sync_completed", "devcom5", "1 file")])
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.assertEqual(data["heartbeat"], {"session_count": 4})
        self.assertEqual(data["cross_skill"]["another_skill"], {"version": "5.1.0"})
        sig = data["cross_skill"]["pending_signals"][0]
        self.assertEqual((sig["from"], sig["signal"], sig["to"], sig["consumed"]),
                         ("synk182", "sync_completed", "devcom5", False))

    def test_corrupt_pulse_is_left_alone(self):
        p = _write(self.u, "docs/PULSE.json", "{not json")
        self.assertIsNone(self.mod.update_pulse(self.u, {"synk_last_run": "x"}, []))
        self.assertEqual(p.read_text(encoding="utf-8"), "{not json")

    def test_pulse_with_a_wrong_typed_field_is_treated_as_empty_with_a_note(self):
        # Break it catches: a PULSE that parses but holds "pending_signals": null
        # (or a cross_skill that is not an object) crashing --pulse with a
        # TypeError. Seen 2026-09-30 driving both engines. Handled as empty,
        # said so, and the keys DevCom5 owns are kept.
        for broken in ({"project": "X", "cross_skill": {"pending_signals": None}},
                       {"project": "X", "cross_skill": "not an object"}):
            with self.subTest(pulse=json.dumps(broken)):
                _write(self.u, "docs/PULSE.json", json.dumps(broken))
                out = io.StringIO()
                with redirect_stdout(out):
                    path = self.mod.update_pulse(self.u, {"synk_last_run": "2026-09-30T00:00:00-04:00"},
                                                 [("sync_completed", "devcom5", "1 file")])
                self.assertIsNotNone(path)
                data = json.loads(Path(path).read_text(encoding="utf-8"))
                self.assertEqual(data["project"], "X")
                self.assertEqual([s["signal"] for s in data["cross_skill"]["pending_signals"]], ["sync_completed"])
                self.assertIn("treated as empty", out.getvalue())

    def test_cli_pulse_says_when_the_pulse_does_not_parse(self):
        # Break it catches: --pulse beside a docs/PULSE.json that does not parse,
        # or is not an object, saying nothing and exiting 0, so the user is never
        # told the run was not recorded (found by the second v1.3 review). The
        # file is left untouched and the run says so, as Solid8's does; the same
        # holds after an apply. "[]" parses, so the words say the file holds no
        # JSON object rather than that it did not parse (the third v1.3 review).
        _write(self.u, "a.txt", "x\n")
        _write(self.w, "a.txt", "y\n")
        _write(self.u, "new.txt", "brand new\n")
        for text in ("{not json", "[]"):
            with self.subTest(pulse=text):
                p = _write(self.u, "docs/PULSE.json", text)
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.mod.main([str(self.u), str(self.w), "--pulse"])
                self.assertEqual(rc, 0)
                self.assertIn("PULSE.json does not hold a JSON object; left untouched", out.getvalue())
                self.assertEqual(p.read_text(encoding="utf-8"), text)
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan_file = _write(self.tmp, "plan.json", json.dumps(s.plan()))
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", "new", "--pulse"])
        self.assertEqual(rc, 0)
        self.assertTrue((self.w / "new.txt").is_file())
        self.assertIn("PULSE.json does not hold a JSON object; left untouched", out.getvalue())

    def test_cli_pulse_when_docs_is_a_file_warns_and_still_reports_the_apply(self):
        # Break it catches: --pulse in a project whose docs is a file dying on an
        # uncaught FileExistsError; after an apply the files were written and
        # "Synced: 2" printed, then the traceback, so the run's last word was a
        # traceback and the apply went unrecorded (found by the third v1.3 review).
        docs = _write(self.u, "docs", "a file, not a folder\n")
        _write(self.u, "new.txt", "brand new\n")
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--pulse"])
        self.assertEqual(rc, 0)
        self.assertIn("not a folder", out.getvalue())
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan_file = _write(self.tmp, "plan.json", json.dumps(s.plan()))
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", "new", "--pulse"])
        self.assertEqual(rc, 0)
        self.assertIn("Synced: 2", out.getvalue())
        self.assertIn("not a folder", out.getvalue().split("Synced: 2", 1)[1])
        self.assertTrue((self.w / "new.txt").is_file())
        self.assertEqual(docs.read_text(encoding="utf-8"), "a file, not a folder\n")

    def _pulse_signals(self):
        data = json.loads((self.u / "docs/PULSE.json").read_text(encoding="utf-8"))
        return {s["signal"]: s["details"] for s in data["cross_skill"]["pending_signals"]}

    def test_pulse_after_a_wholly_refused_apply_emits_no_sync_completed(self):
        # Break it catches: after an apply in which every item was refused (a
        # stale plan), --pulse still emitted sync_completed, "0 file(s) written",
        # beside sync_conflict; DevCom5 reads sync_completed as a sync that
        # happened (found by the second v1.3 review).
        _write(self.u, "late.txt", "user version\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan_file = _write(self.tmp, "plan.json", json.dumps(s.plan()))
        _write(self.w, "late.txt", "written after the plan\n")
        with redirect_stdout(io.StringIO()):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", "1", "--pulse"])
        self.assertEqual(rc, 1)
        self.assertEqual(sorted(self._pulse_signals()), ["sync_conflict"])

    def test_new_files_synced_names_only_files_the_apply_created(self):
        # Break it catches: new_files_synced emitted for every applied path, so
        # overwriting a file present on both sides (a merge, a superset) told
        # Solid8 of a new file that was not new (found by the second v1.3 review).
        _write(self.u, "m.txt", "a\nb\nc\nd\ne\n")
        _write(self.w, "m.txt", "a\nb\nc\nd\nf\n")
        _write(self.u, "s.txt", "a\nb\nc\n")
        _write(self.w, "s.txt", "a\nb\n")
        _write(self.u, "new.txt", "brand new\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan = s.plan()
        for act in plan:
            act["direction"] = "user_to_working"
        plan_file = _write(self.tmp, "plan.json", json.dumps(plan))
        ids = ",".join(str(a["id"]) for a in plan)
        with redirect_stdout(io.StringIO()):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", ids, "--pulse"])
        self.assertEqual(rc, 0)
        sigs = self._pulse_signals()
        self.assertEqual(sigs["sync_completed"], "3 file(s) written")
        self.assertEqual(sigs["new_files_synced"], "new.txt")

    def test_no_personal_paths_in_the_engines(self):
        # One person's profile folder in a script (C:\Users\someone, /home/someone)
        # breaks on every other machine and discloses the account name; a sandbox
        # path such as /home/claude is a stale marker. Both engines are checked.
        user_path = re.compile(r"(?:[A-Za-z]:\\{1,2}Users\\{1,2}|/Users/|/home/)"
                               r"(?!(?:Public|Default|All Users)\b)([A-Za-z0-9._-]+)")
        for rel in ("synk182/scripts/synk_engine.py", "solid8/scripts/denser_engine.py"):
            with self.subTest(script=rel):
                self.assertEqual(user_path.findall((ROOT / rel).read_text(encoding="utf-8")), [])

    def test_cli_survives_a_cp1252_console(self):
        _write(self.u, "a.txt", "x\n")
        r = _run_cp1252(ROOT / "synk182/scripts/synk_engine.py", self.u, self.w)
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))

    def test_cli_refuses_a_copy_that_is_not_a_folder(self):
        # Break it catches: a mistyped path read as an empty copy ("✓0 identical",
        # exit 0), seen 2026-09-30; it is an error that names the path.
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u / "nope"), str(self.w)])
        self.assertEqual(rc, 1)
        self.assertIn("not a folder", out.getvalue())
        self.assertIn("nope", out.getvalue())

    def test_cli_refuses_the_same_folder_as_both_copies(self):
        # Break it catches: the same folder given for both copies read as two
        # copies in agreement ("✓1 identical", exit 0), so a second path mistyped
        # onto the first reads as a clean sync (found by the second v1.3 review).
        _write(self.u, "a.txt", "x\n")
        for second in (str(self.u), os.path.join(str(self.u), "."), str(self.w / ".." / "user")):
            with self.subTest(second=second):
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.mod.main([str(self.u), second])
                self.assertEqual(rc, 1)
                self.assertIn("same folder", out.getvalue())

    def test_cli_answers_a_bad_plan_or_approval_with_a_message(self):
        # Break it catches: raw tracebacks for --apply nope.json (FileNotFoundError)
        # and --approve 1,x (ValueError), seen 2026-09-30.
        _write(self.u, "a.txt", "x\n")
        plan = _write(self.u, "plan.json", "[]")
        for argv, word in (([str(self.u), str(self.w), "--apply", str(self.u / "nope.json"), "--approve", "1"], "nope.json"),
                           ([str(self.u), str(self.w), "--apply", str(plan), "--approve", "1,x"], "1,x"),
                           ([str(self.u), str(self.w), "--apply", str(_write(self.u, "bad.json", "{}")), "--approve", "1"], "list")):
            with self.subTest(argv=argv):
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.mod.main(argv)
                self.assertEqual(rc, 1)
                self.assertIn(word, out.getvalue())

    def test_cli_approve_with_an_id_in_no_plan_item_is_an_error(self):
        # Break it catches: --approve 999 (or -1) against a plan with no such id
        # printing "Synced: 0 | ... | Archive: None" and exiting 0, so a mistyped
        # id read as a clean run (found by the second v1.3 review). It is an error
        # that names the id, and nothing is applied, not even the ids that exist.
        _write(self.u, "new.txt", "brand new\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan_file = _write(self.tmp, "plan.json", json.dumps(s.plan()))
        for approve in ("999", "-1", "1,999"):
            with self.subTest(approve=approve):
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", approve])
                self.assertEqual(rc, 1)
                self.assertIn(approve.split(",")[-1], out.getvalue())
                self.assertFalse((self.w / "new.txt").exists())
                self.assertFalse((self.u / "ARCHIVE").exists())

    def test_cli_approved_item_without_a_direction_says_so_and_exits_1(self):
        # Break it catches: approving a merge whose direction is still null (as
        # --plan writes every merge and superset) printing only "Synced: 0 | ... |
        # Skipped: 1" and exiting 0; the reason sat in the report dict, never
        # printed (found by the third v1.3 review). The run names the item and
        # why, and exits 1, as when an approved item is refused.
        _write(self.u, "m.txt", "a\nb\nc\nd\ne\n")
        _write(self.w, "m.txt", "a\nb\nc\nd\nf\n")
        _write(self.u, "new.txt", "brand new\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan = s.plan()
        plan_file = _write(self.tmp, "plan.json", json.dumps(plan))
        merge = [a["id"] for a in plan if a["path"] == "m.txt"][0]
        new = [a["id"] for a in plan if a["path"] == "new.txt"][0]
        for approve in (str(merge), f"{merge},{new}"):
            with self.subTest(approve=approve):
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", approve])
                self.assertEqual(rc, 1)
                self.assertRegex(out.getvalue(), r"m\.txt.*no direction")
                self.assertEqual((self.w / "m.txt").read_text(encoding="utf-8"), "a\nb\nc\nd\nf\n")

    def test_cli_plan_item_with_only_an_id_is_answered_with_a_message(self):
        # Break it catches: a hand-edited item with an id and nothing else,
        # [{"id": 1}], crashing --apply ... --approve 1 on KeyError: 'path'
        # (found by the third v1.3 review), while the same item with a direction
        # was answered "Refused None: no path". An item with no path is named by
        # its id, so the user can find it in the plan.
        _write(self.u, "a.txt", "x\n")
        for item, words in (({"id": 1}, "item 1: no direction"),
                            ({"id": 1, "direction": "user_to_working"}, "item 1: no path")):
            with self.subTest(item=item):
                plan_file = _write(self.tmp, "plan.json", json.dumps([item]))
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", "1"])
                self.assertEqual(rc, 1)
                self.assertIn(words, out.getvalue())
                self.assertNotRegex(out.getvalue(), r"(?:Skipped|Refused) None")

    def test_cli_plan_beside_apply_is_an_error(self):
        # Break it catches: --plan OUT given beside --apply dropped without a word:
        # the apply ran, exited 0, and OUT never appeared (found by the third v1.3
        # review). The two are separate runs; nothing is done and the run says so.
        _write(self.u, "new.txt", "brand new\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan_file = _write(self.tmp, "plan.json", json.dumps(s.plan()))
        out_file = Path(self.tmp) / "plan2.json"
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--plan", str(out_file),
                                "--apply", str(plan_file), "--approve", "new"])
        self.assertEqual(rc, 1)
        self.assertIn("--plan", out.getvalue())
        self.assertIn("--apply", out.getvalue())
        self.assertFalse((self.w / "new.txt").exists())
        self.assertFalse(out_file.exists())

    def test_cli_plan_that_cannot_be_written_says_so_and_still_records_the_pulse(self):
        # Break it catches: --plan OUT into a missing folder, or onto a folder,
        # printing the dashboard and then a FileNotFoundError or PermissionError
        # traceback, with a --pulse beside it never reached, while SKILL.md says a
        # bad plan path is answered with a message (the fourth v1.3 review).
        _write(self.u, "a.txt", "one\n")
        _write(self.w, "a.txt", "two\n")
        (Path(self.tmp) / "taken").mkdir()
        pulse = self.u / "docs" / "PULSE.json"
        for out_path in ("no-such-folder/plan.json", "taken"):
            with self.subTest(plan=out_path):
                if pulse.exists():
                    pulse.unlink()
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.mod.main([str(self.u), str(self.w), "--plan", str(Path(self.tmp) / out_path), "--pulse"])
                self.assertEqual(rc, 1)
                self.assertIn("Plan not written", out.getvalue())
                self.assertIn("synk_last_run", pulse.read_text(encoding="utf-8"))

    def test_approve_new_names_an_item_without_a_path_by_its_id(self):
        # Break it catches: the --approve new listing naming a hand-edited item by
        # its path, so "path": null printed "Not in 'new': None (no path)" and ""
        # printed an empty name, while apply() names the same item "item 9" (found
        # by the fourth v1.3 review). The rest of 'new' is still applied.
        _write(self.u, "new.txt", "brand new\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan = s.plan()
        plan += [{"id": 9, "status": "user_only", "path": None, "direction": "user_to_working"},
                 {"id": 10, "status": "user_only", "path": "", "direction": "user_to_working"}]
        plan_file = _write(self.tmp, "plan.json", json.dumps(plan))
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", "new"])
        self.assertEqual(rc, 0)
        self.assertIn("Not in 'new': item 9 (no path)", out.getvalue())
        self.assertIn("Not in 'new': item 10 (no path)", out.getvalue())
        self.assertTrue((self.w / "new.txt").is_file())

    def test_cli_plan_given_an_empty_name_says_so(self):
        # Break it catches: --plan "" (an empty shell variable) dropped without a word:
        # the dashboard printed, nothing written, exit 0 (found by the fifth v1.3
        # review). It is answered as a plan that cannot be written, and --pulse still
        # records the scan.
        _write(self.u, "new.txt", "brand new\n")
        # the same drop for --apply and --diff, the other flags that take a name
        for extra, words in ((["--plan", "", "--pulse"], "Plan not written (no file name given)"),
                             (["--apply", ""], "--apply was given an empty name"),
                             (["--diff", ""], "--diff was given an empty name")):
            with self.subTest(flag=extra[0]):
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.mod.main([str(self.u), str(self.w), *extra])
                self.assertEqual(rc, 1)
                self.assertIn(words, out.getvalue())
        self.assertIn("synk_last_run", (self.u / "docs" / "PULSE.json").read_text(encoding="utf-8"))
        self.assertFalse((self.w / "new.txt").exists())

    def test_a_file_named_archive_is_not_compared_and_apply_refuses_before_any_write(self):
        # Break it catches: a FILE named ARCHIVE in the user copy, where the backups go,
        # listed as an item of its own and ending --apply --approve new in a raw
        # FileExistsError traceback (found by the fifth v1.3 review). It is named and
        # left out of the plan, and the apply is refused before anything is written.
        _write(self.u, "ARCHIVE", "not a folder")
        _write(self.u, "new.txt", "brand new\n")
        out = io.StringIO()
        with redirect_stdout(out):
            s = self.synk()
            r = s.scan_and_compare()
            plan_file = _write(self.tmp, "plan.json", json.dumps(s.plan()))
        self.assertEqual(sorted(r["files"]), ["new.txt"])
        self.assertRegex(out.getvalue(), r"not compared.*ARCHIVE")
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", "new"])
        self.assertEqual(rc, 1)
        self.assertIn("ARCHIVE is a file, not a folder", out.getvalue())
        self.assertFalse((self.w / "new.txt").exists())
        self.assertEqual((self.u / "ARCHIVE").read_text(encoding="utf-8"), "not a folder")

    def test_cli_hand_edited_plan_fields_are_refused_before_any_write(self):
        # Break it catches: a hand-edited plan whose hashes are not an object ("abc", 5)
        # or whose id is not a whole number ([1], "1") passing the shape check, then an
        # AttributeError or TypeError traceback, or "1" applied by --approve new while
        # --approve 1 said no item has id 1 (found by the fifth v1.3 review).
        _write(self.u, "a.txt", "x\n")
        item = {"id": 1, "path": "a.txt", "status": "user_only", "direction": "user_to_working",
                "hashes": {"user": None, "working": None}}
        for bad, approve, words in (({**item, "hashes": "abc"}, "1", "hashes"), ({**item, "hashes": "abc"}, "new", "hashes"),
                                    ({**item, "hashes": 5}, "1", "hashes"), ({**item, "id": [1]}, "new", "whole-number id"),
                                    ({**item, "id": "1"}, "new", "whole-number id"), ({**item, "id": "1"}, "1", "whole-number id")):
            with self.subTest(item=bad, approve=approve):
                plan_file = _write(self.tmp, "plan.json", json.dumps([bad]))
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", approve])
                self.assertEqual(rc, 1)
                self.assertIn(words, out.getvalue())
                self.assertFalse((self.w / "a.txt").exists())
                self.assertFalse((self.u / "ARCHIVE").exists())

    def test_a_junction_inside_a_copy_is_named_and_not_followed(self):
        # Break it catches: a junction walked as a folder: one back to the user copy gave
        # 63 phantom paths (loop/a.txt, loop/loop/a.txt, ...) and a 63-item plan (found
        # by the fifth v1.3 review). It is named and not followed, and nothing under its
        # path is compared or planned in either copy. A link the scan skips anyway
        # (node_modules, as a package manager links it) goes unnamed.
        _write(self.u, "a.txt", "one\n")
        _write(self.w, "loop/b.txt", "only here\n")
        if not _link_folder(self.u / "loop", self.u):
            self.skipTest("this machine makes neither a junction nor a symbolic link")
        self.assertTrue(_link_folder(self.u / "node_modules", self.u))
        out = io.StringIO()
        with redirect_stdout(out):
            s = self.synk()
            r = s.scan_and_compare()
            plan = s.plan()
        self.assertEqual(sorted(r["files"]), ["a.txt"])
        self.assertEqual([a["path"] for a in plan], ["a.txt"])
        self.assertEqual([(n["side"], n["path"]) for n in r["not_compared"]], [("user", "loop")])
        self.assertRegex(out.getvalue(), r"not compared.*loop.*not followed")

    def test_a_folder_that_cannot_be_listed_is_named_not_read_as_absent(self):
        # Break it catches: a folder in the user copy the user may not list (an ACL deny)
        # read as empty, so its files showed as only in the working copy and --approve
        # new copied into it (found by the fifth v1.3 review). It is named, and nothing
        # under its path is compared or planned in either copy.
        _write(self.u, "top.txt", "t\n")
        _write(self.w, "top.txt", "t\n")
        _write(self.u, "denied/a.txt", "same\n")
        _write(self.w, "denied/a.txt", "same\n")
        _write(self.w, "denied/b.txt", "only in working\n")
        out = io.StringIO()
        with mock.patch.object(self.mod.os, "walk", _unlistable(self.u / "denied")), redirect_stdout(out):
            s = self.synk()
            r = s.scan_and_compare()
            plan = s.plan()
        self.assertEqual(sorted(r["files"]), ["top.txt"])
        self.assertEqual(plan, [])
        self.assertEqual([(n["side"], n["path"]) for n in r["not_compared"]], [("user", "denied")])
        self.assertRegex(out.getvalue(), r"not compared.*denied.*cannot be listed")

    def test_pulse_prunes_old_consumed_signals_whatever_their_offset_form(self):
        # Break it catches: a month-old consumed signal stamped with a trailing Z pruned
        # on Python 3.11 and 3.12 but kept forever on 3.10 (fromisoformat reads Z only
        # from 3.11), and one with no offset kept on every version (found by the fifth
        # v1.3 review). Z is UTC on every version, and no offset is local time.
        _write(self.u, "docs/PULSE.json", _old_signals("synk182"))
        path = self.mod.update_pulse(self.u, {"synk_last_run": "x"})
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.assertEqual([s["signal"] for s in data["cross_skill"]["pending_signals"]], ["recent"])

    def test_cli_diff_beside_plan_apply_or_pulse_is_an_error(self):
        # Break it catches: --diff returning before anything else ran, so --plan,
        # --apply or --pulse given beside it were dropped without a word and the
        # run exited 0 (found while fixing the --plan/--apply case above).
        _write(self.u, "a.txt", "one\n")
        _write(self.w, "a.txt", "two\n")
        _write(self.u, "new.txt", "brand new\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan_file = _write(self.tmp, "plan.json", json.dumps(s.plan()))
        out_file = Path(self.tmp) / "plan2.json"
        for extra in (["--plan", str(out_file)], ["--apply", str(plan_file), "--approve", "new"], ["--pulse"]):
            with self.subTest(extra=extra[0]):
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.mod.main([str(self.u), str(self.w), "--diff", "a.txt", *extra])
                self.assertEqual(rc, 1)
                self.assertIn(extra[0], out.getvalue())
        self.assertFalse(out_file.exists())
        self.assertFalse((self.w / "new.txt").exists())
        self.assertFalse((self.u / "docs").exists())

    def test_cli_approve_without_apply_is_an_error(self):
        # Break it catches: --approve 1 without --apply silently ignored, the
        # dashboard printed and exit 0 (found by the second v1.3 review), so a
        # user who meant to apply reads that nothing needed doing.
        _write(self.u, "new.txt", "brand new\n")
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--approve", "1"])
        self.assertEqual(rc, 1)
        self.assertIn("--apply", out.getvalue())
        self.assertFalse((self.w / "new.txt").exists())

    def test_cli_diff_says_when_a_path_is_on_neither_side(self):
        # Break it catches: --diff for a path that exists in neither copy printing
        # an empty line and exiting 0, seen 2026-09-30.
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--diff", "ghost.txt"])
        self.assertEqual(rc, 1)
        self.assertIn("neither", out.getvalue())
        self.assertIn("ghost.txt", out.getvalue())

    def test_a_file_that_cannot_be_read_is_named_and_left_out_of_every_comparison_and_plan(self):
        # Break it catches: a file that exists but cannot be read (held by another
        # process, or an ACL deny on the file) hashed as "" and read as empty, so it was
        # compared as a 150% superset of itself, planned with MAXIMUM review, and --apply
        # onto it died in a shutil traceback that left an archive folder with no manifest
        # (the sixth v1.3 review, S3 and S4). It is named on the dashboard with the OS
        # reason and left out of both copies' comparison and of the plan; an item that
        # names it by hand is refused before any backup or write, whichever side cannot
        # be read; and --diff of it is answered.
        _write(self.u, "locked.txt", "user line 1\nuser line 2\n")
        _write(self.w, "locked.txt", "user line 1\nuser line 2\nwork line 3\n")
        _write(self.u, "free.txt", "same\n")
        _write(self.w, "free.txt", "same\n")
        _hold_unreadable(self, self.u / "locked.txt", self.tmp)
        out = io.StringIO()
        with redirect_stdout(out):
            s = self.synk()
            r = s.scan_and_compare()
            plan = s.plan()
        self.assertEqual(sorted(r["files"]), ["free.txt"])
        self.assertEqual(plan, [])
        self.assertEqual([(n["side"], n["path"]) for n in r["not_compared"]], [("user", "locked.txt")])
        self.assertRegex(r["not_compared"][0]["reason"], r"^cannot be read \(.+\)$")
        self.assertRegex(out.getvalue(), r"not compared.*locked\.txt.*cannot be read \(")
        for direction in ("working_to_user", "user_to_working"):
            with self.subTest(direction=direction):
                item = [{"id": 1, "path": "locked.txt", "status": "merge", "direction": direction,
                         "hashes": {"user": None, "working": None}}]
                out = io.StringIO()
                with redirect_stdout(out):
                    report = s.apply(item, [1])
                self.assertEqual(report["applied"], [])
                self.assertEqual([x["path"] for x in report["refused"]], ["locked.txt"])
                self.assertRegex(report["refused"][0]["reason"], r"user copy.*cannot be read \(")
                self.assertIsNone(report["archive"])
                self.assertFalse((self.u / "ARCHIVE").exists())
        self.assertEqual((self.w / "locked.txt").read_text(encoding="utf-8"), "user line 1\nuser line 2\nwork line 3\n")
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--diff", "locked.txt"])
        self.assertEqual(rc, 1)
        self.assertRegex(out.getvalue(), r"locked\.txt.*cannot be read \(")

    def test_a_backup_that_fails_midway_refuses_everything_and_leaves_no_archive(self):
        # Break it catches: the backup phase of an apply dying in a raw traceback on a file
        # it could not copy, leaving ARCHIVE/synk-<stamp>/ behind with a half-written
        # backup and no manifest.json, rollback.md or apply-report.json (the sixth v1.3
        # review, S3). Every item is refused with the reason, nothing is written to either
        # copy, and the archive holds its manifest or does not exist.
        _write(self.u, "a.txt", "user a\n")
        _write(self.w, "a.txt", "work a\n")
        _write(self.u, "b.txt", "user b\n")
        _write(self.w, "b.txt", "work b\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan = s.plan()
        for act in plan:
            act["direction"] = "user_to_working"
        real = shutil.copy2

        def copy2(src, dst, *a, **k):
            if Path(src).name == "b.txt" and "ARCHIVE" in Path(dst).parts:
                raise PermissionError(13, "Permission denied", str(src))
            return real(src, dst, *a, **k)
        out = io.StringIO()
        with mock.patch.object(self.mod.shutil, "copy2", copy2), redirect_stdout(out):
            report = s.apply(plan, [a["id"] for a in plan])
        self.assertEqual(report["applied"], [])
        self.assertEqual(sorted(x["path"] for x in report["refused"]), ["a.txt", "b.txt"])
        for x in report["refused"]:
            self.assertIn("no backup", x["reason"])
        self.assertIsNone(report["archive"])
        self.assertFalse((self.u / "ARCHIVE").exists(), "an archive holds its manifest or does not exist")
        self.assertEqual((self.w / "a.txt").read_text(encoding="utf-8"), "work a\n")
        self.assertEqual((self.w / "b.txt").read_text(encoding="utf-8"), "work b\n")
        self.assertIn("nothing written", out.getvalue())

    def test_an_exception_in_verification_after_a_copy_rolls_it_back(self):
        # Break it catches: a MemoryError (or any non-OSError) raised while verifying a copy
        # escaping apply() after the file was written: no rollback, no report line, no
        # apply-report.json (the sixth v1.3 review, S7, injected). Any exception in
        # verification rolls the copy back like a failed layer, names it, and the report
        # is still written; a copy that overwrote a file is restored from the backup.
        _write(self.u, "new.txt", "brand new\n")
        _write(self.u, "over.txt", "user\n")
        _write(self.w, "over.txt", "working original\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan = s.plan()
        for act in plan:
            act["direction"] = "user_to_working"
        real = Path.read_bytes

        def boom(path):
            if path.name in ("new.txt", "over.txt") and "ARCHIVE" not in path.parts:
                raise MemoryError("injected")
            return real(path)
        out = io.StringIO()
        with mock.patch.object(Path, "read_bytes", boom), redirect_stdout(out):
            report = s.apply(plan, [a["id"] for a in plan])
        self.assertEqual(sorted(report["rolled_back"]), ["new.txt", "over.txt"])
        self.assertEqual(report["applied"], [])
        self.assertFalse((self.w / "new.txt").exists())
        self.assertEqual((self.w / "over.txt").read_text(encoding="utf-8"), "working original\n")
        self.assertRegex(out.getvalue(), r"Rolled back new\.txt \(failed: verification error: MemoryError")
        self.assertTrue((Path(report["archive"]) / "apply-report.json").is_file())

    def test_a_rollback_that_fails_names_the_backup_to_restore_by_hand(self):
        # The other edge of the case above: when the restore itself fails, the item is
        # not reported as rolled back; the report and the run name the backup copy to
        # restore by hand, and the run exits 1.
        _write(self.u, "over.txt", "user\n")
        _write(self.w, "over.txt", "working original\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan = s.plan()
        plan[0]["direction"] = "user_to_working"
        s._verify_copy = lambda src, dst: ["hash"]
        real = shutil.copy2

        def copy2(src, dst, *a, **k):
            if "ARCHIVE" in Path(src).parts:
                raise PermissionError(13, "Permission denied", str(dst))
            return real(src, dst, *a, **k)
        out = io.StringIO()
        with mock.patch.object(self.mod.shutil, "copy2", copy2), redirect_stdout(out):
            report = s.apply(plan, [1])
        self.assertEqual(report["rolled_back"], [])
        self.assertEqual(report["applied"], [])
        self.assertEqual([x["path"] for x in report["rollback_failed"]], ["over.txt"])
        backup = Path(report["archive"]) / "working" / "over.txt"
        self.assertEqual(report["rollback_failed"][0]["backup"], str(backup))
        self.assertEqual(backup.read_text(encoding="utf-8"), "working original\n")
        self.assertRegex(out.getvalue(), r"over\.txt.*restore it by hand from .*over\.txt")

    def test_archive_in_another_case_is_synks_own_folder_where_the_file_system_folds_case(self):
        # Break it catches: on a case-insensitive file system (Windows, default macOS) a
        # project's own archive/ folder IS Synk's ARCHIVE, yet it was scanned as content:
        # the backups of an apply landed in it, the next scan planned them as user_only,
        # --approve new copied Synk's own manifests into the working copy, and every later
        # run grew it (the sixth v1.3 review, S11). Where the file system folds case, any
        # spelling of ARCHIVE is the backup folder: skipped in both copies and named on
        # the dashboard, the archive path printed as it is on disk, and a file so named
        # is named before planning and refuses the apply with its real path.
        if not _folds_case(self.u):
            self.skipTest("a case-sensitive file system: archive/ is a project folder there")
        _write(self.u, "archive/old.txt", "project content, both sides\n")
        _write(self.w, "archive/old.txt", "project content, both sides\n")
        _write(self.u, "a.txt", "user\n")
        _write(self.w, "a.txt", "work\n")
        out = io.StringIO()
        with redirect_stdout(out):
            s = self.synk()
            r = s.scan_and_compare()
            plan = s.plan()
        self.assertEqual(sorted(r["files"]), ["a.txt"])
        self.assertEqual(sorted((n["side"], n["path"]) for n in r["not_compared"]), [("user", "archive"), ("working", "archive")])
        self.assertRegex(out.getvalue(), r"not compared.*archive.*ARCHIVE")
        plan[0]["direction"] = "user_to_working"
        out = io.StringIO()
        with redirect_stdout(out):
            report = s.apply(plan, [plan[0]["id"]])
        self.assertEqual([a["path"] for a in report["applied"]], ["a.txt"])
        archive = Path(report["archive"])
        self.assertEqual(archive.parent.name, "archive", "the archive path is printed as it is on disk")
        self.assertTrue((archive / "manifest.json").is_file())
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            r = s.scan_and_compare()
            self.assertEqual(s.plan(), [])
        self.assertEqual(sorted(r["files"]), ["a.txt"])
        self.assertFalse(any("synk-" in p.as_posix() for p in self.w.rglob("*")), "no backup was synced as content")
        shutil.rmtree(self.u / "archive")
        _write(self.u, "Archive", "a file, not a folder")
        _write(self.u, "new.txt", "brand new\n")
        out = io.StringIO()
        with redirect_stdout(out):
            s = self.synk()
            r = s.scan_and_compare()
            plan_file = _write(self.tmp, "plan.json", json.dumps(s.plan()))
        self.assertEqual(sorted(r["files"]), ["a.txt", "new.txt"])
        self.assertRegex(out.getvalue(), r"not compared.*Archive.*ARCHIVE")
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", "new"])
        self.assertEqual(rc, 1)
        self.assertRegex(out.getvalue(), r"Archive is a file, not a folder")
        self.assertFalse((self.w / "new.txt").exists())

    def test_diff_says_when_copies_differ_only_in_line_endings_and_refuses_a_path_outside(self):
        # Break it catches: --diff of a file whose copies differ only in line endings
        # printing one empty line at rc 0 while the dashboard called it a merge (the line
        # sets match; the diff is of lines), and --diff ../x or --diff <absolute path>
        # printing the same empty line at rc 0 (the sixth v1.3 review, S6 and S12). The
        # dashboard, the plan and --diff all say the copies differ only in line endings,
        # naming each side's; a path that leaves the copies is refused at rc 1.
        _write(self.u, "crlf.txt", data=b"line 1\r\nline 2\r\nline 3\r\n")
        _write(self.w, "crlf.txt", data=b"line 1\nline 2\nline 3\n")
        _write(self.tmp, "outside.txt", "outside\n")
        out = io.StringIO()
        with redirect_stdout(out):
            s = self.synk()
            r = s.scan_and_compare()
            plan = s.plan()
        a = r["files"]["crlf.txt"]
        self.assertEqual((a["status"], a["relationship"], a["similarity"]), ("line_endings", "line_endings", 1.0))
        self.assertEqual(a["endings"], {"user": "CRLF", "working": "LF"})
        self.assertRegex(out.getvalue(), r"line_endings.*crlf\.txt.*user CRLF, working LF")
        self.assertEqual(r["line_endings"], 1)
        self.assertEqual(r["merge"], 0)
        self.assertEqual((plan[0]["status"], plan[0]["direction"]), ("line_endings", None))
        self.assertIn("line endings", plan[0]["note"])
        self.assertIn("user CRLF, working LF", plan[0]["note"])
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--diff", "crlf.txt"])
        self.assertEqual(rc, 0)
        self.assertIn("differ only in line endings: user CRLF, working LF", out.getvalue())
        self.assertNotIn("---", out.getvalue())
        for rel in ("../outside.txt", str(Path(self.tmp) / "outside.txt"), "sub/../../outside.txt"):
            with self.subTest(diff=rel):
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.mod.main([str(self.u), str(self.w), "--diff", rel])
                self.assertEqual(rc, 1)
                self.assertNotIn("outside\n", out.getvalue())
                self.assertRegex(out.getvalue(), r"--diff.*(leaves the copy|outside the copy|absolute)")

    def test_a_file_link_inside_a_copy_is_named_and_not_followed_a_dangling_one_too(self):
        # Break it catches: a symbolic link to a FILE inside a copy followed and copied as
        # a regular file holding the target's content, and a dangling one vanishing
        # without a word (the sixth v1.3 review, S5c); folder links were already named.
        # A link to a file is named like a link to a folder and never followed, and a
        # dangling one is named as such; nothing under either is compared or planned.
        _write(self.u, "a.txt", "a\n")
        try:
            os.symlink(self.u / "a.txt", self.u / "link.txt")
            os.symlink(self.u / "no-such.txt", self.u / "dangling.txt")
        except OSError as e:
            self.skipTest(f"this machine cannot make a file symlink ({e})")
        out = io.StringIO()
        with redirect_stdout(out):
            s = self.synk()
            r = s.scan_and_compare()
            plan = s.plan()
        self.assertEqual(sorted(r["files"]), ["a.txt"])
        self.assertEqual([a["path"] for a in plan], ["a.txt"])
        reasons = {n["path"]: n["reason"] for n in r["not_compared"]}
        self.assertEqual(sorted(reasons), ["dangling.txt", "link.txt"])
        self.assertIn("not followed", reasons["link.txt"])
        self.assertIn("missing", reasons["dangling.txt"])
        self.assertRegex(out.getvalue(), r"not compared.*dangling\.txt.*missing")

    def test_pulse_stamps_are_read_one_way_on_every_python_and_never_stop_the_run(self):
        # Break it catches: one consumed signal stamped 1969-12-31T23:59:59, or any 0001 /
        # 9999 stamp, raising OSError from .astimezone() on Windows, so --pulse of both
        # engines printed "PULSE.json not written ([Errno 22] Invalid argument)" on every
        # later run until the file was hand-edited; "consumed": "false" pruned as consumed;
        # and a basic-format or 7-digit-fraction stamp pruned on 3.11+ but kept on 3.10
        # (the sixth v1.3 review, S10). The rule, the same on every Python and written in
        # docs/TRIFECTA.md: a stamp is the extended ISO-8601 form with an offset, Z or
        # neither (local time), a fraction cut to microseconds; a consumed signal older
        # than seven days is pruned; a consumed signal whose stamp cannot be read is pruned
        # and the run says so; only JSON true is consumed; an unconsumed signal is never
        # touched; an entry that is not an object is kept.
        old = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
        signals = [("basic-z", (datetime.now() - timedelta(days=30)).strftime("%Y%m%dT%H%M%SZ"), True),
                   ("seven-frac-z", old + ".1234567Z", True), ("naive-1969", "1969-12-31T23:59:59", True),
                   ("naive-0001", "0001-01-01T00:00:00", True), ("aware-0001", "0001-01-01T00:00:00+00:00", True),
                   ("aware-9999", "9999-12-31T23:00:00+00:00", True), ("naive-9999", "9999-12-31T00:00:00", True),
                   ("plus-0930", old + "+09:30", True), ("space-sep-z", old.replace("T", " ") + "Z", True),
                   ("consumed-string-false", old + "Z", "false"), ("consumed-0", old + "Z", 0),
                   ("consumed-1", old + "Z", 1), ("empty", "", True), ("number", 1700000000, True),
                   ("month-13", old[:5] + "13" + old[7:], True),
                   # the grammar exactly as docs/TRIFECTA.md pins it: no lower-case z, no offset
                   # without a colon, no comma fraction (the seventh v1.3 review, S7)
                   ("lower-z", old + "z", True), ("compact-off", old + "+0000", True), ("comma-frac", old + ",5Z", True),
                   ("unconsumed-old", old + "Z", False), ("unconsumed-bad", "yesterday", False)]
        pulse = {"cross_skill": {"pending_signals": [
            {"from": "devcom5", "signal": n, "to": "x", "timestamp": t, "consumed": c} for n, t, c in signals] + ["not an object"]}}
        for rel in ("synk182/scripts/synk_engine.py", "solid8/scripts/denser_engine.py"):
            with self.subTest(engine=rel):
                mod = _load(Path(rel).stem, rel)
                p = _write(self.u, "docs/PULSE.json", json.dumps(pulse))
                out = io.StringIO()
                with redirect_stdout(out):
                    path = mod.update_pulse(self.u, {"probe_last_run": "x"})
                self.assertEqual(path, p)
                kept = json.loads(p.read_text(encoding="utf-8"))["cross_skill"]["pending_signals"]
                self.assertEqual([s["signal"] if isinstance(s, dict) else s for s in kept],
                                 ["aware-9999", "naive-9999", "consumed-string-false", "consumed-0", "consumed-1",
                                  "unconsumed-old", "unconsumed-bad", "not an object"])
                for name in ("basic-z", "empty", "number", "month-13", "lower-z", "compact-off", "comma-frac"):
                    self.assertRegex(out.getvalue(), rf"pruned.*{name}.*not .*ISO-8601")
                self.assertNotIn("not written", out.getvalue())

    def test_a_plan_item_inside_a_skipped_folder_is_refused_before_any_write(self):
        # Break it catches: a hand-edited plan item whose path lies in a folder the scan
        # skips (.git, node_modules, ARCHIVE, a nested one) applied as written: --approve
        # 1,2,3 wrote working/.git/hooks/pre-commit, working/node_modules/evil/index.js
        # and working/ARCHIVE/old.txt, "six layers verified" (the sixth v1.3 review, S9).
        # Such a path is refused before any backup or write, like '..' is.
        _write(self.u, ".git/hooks/pre-commit", "#!/bin/sh\necho hooked\n")
        _write(self.u, "node_modules/evil/index.js", "x\n")
        _write(self.u, "ARCHIVE/old.txt", "archived\n")
        _write(self.u, "sub/.git/config", "[core]\n")
        _write(self.u, "keep.txt", "one\n")
        paths = [".git/hooks/pre-commit", "node_modules/evil/index.js", "ARCHIVE/old.txt", "sub/.git/config"]
        if _folds_case(self.u):
            _write(self.u, "Archive/x.txt", "x\n")
            paths.append("Archive/x.txt")
        plan = [{"id": i + 1, "path": p, "status": "user_only", "direction": "user_to_working"} for i, p in enumerate(paths)]
        plan_file = _write(self.tmp, "plan.json", json.dumps(plan))
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve",
                                ",".join(str(a["id"]) for a in plan)])
        self.assertEqual(rc, 1)
        for p in paths:
            with self.subTest(path=p):
                self.assertRegex(out.getvalue(), rf"Refused {re.escape(p)}: .*skips")
                self.assertFalse((self.w / p).exists())
        self.assertEqual(sorted(p.name for p in self.w.iterdir()), [])

    def test_two_names_differing_only_in_case_are_one_file_where_the_file_system_folds_case(self):
        # Break it catches: user/Readme.md and work/README.md planned as two one-sided
        # items on a case-insensitive file system, both refused at apply ("now has this
        # file; re-plan"), and the re-plan planning the same two again, forever (the
        # sixth v1.3 review, S11). Where both copies fold case they are one file: compared
        # as one item under the user copy's spelling, named as the same file in different
        # case, applied once, and the next plan is empty.
        if not (_folds_case(self.u) and _folds_case(self.w)):
            self.skipTest("a case-sensitive file system: Readme.md and README.md are two files there")
        _write(self.u, "Readme.md", "# user readme\n")
        _write(self.w, "README.md", "# work readme\n")
        out = io.StringIO()
        with redirect_stdout(out):
            s = self.synk()
            r = s.scan_and_compare()
            plan = s.plan()
        self.assertEqual(sorted(r["files"]), ["Readme.md"])
        self.assertEqual(r["files"]["Readme.md"]["names"], {"user": "Readme.md", "working": "README.md"})
        self.assertEqual(r["files"]["Readme.md"]["status"], "different")
        self.assertRegex(out.getvalue(), r"Readme\.md.*same file, different case.*README\.md")
        self.assertEqual(len(plan), 1)
        self.assertIn("different case", plan[0]["note"])
        plan[0]["direction"] = "user_to_working"
        with redirect_stdout(io.StringIO()):
            report = s.apply(plan, [1])
        self.assertEqual([a["path"] for a in report["applied"]], ["Readme.md"])
        self.assertEqual({p.read_text(encoding="utf-8") for p in self.w.iterdir() if p.is_file()}, {"# user readme\n"})
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            self.assertEqual(s.plan(), [])

    def test_cli_flag_values_and_hand_edits_are_answered_not_applied_blindly(self):
        # Break it catches, each driven by the sixth v1.3 review (S9, S12): --threshold 2,
        # -1 or nan accepted (nan made every pair different); a duplicate id in a
        # hand-edited plan applied twice; direction USER_TO_WORKING answered "no direction
        # chosen"; a path ending in a separator written as "a.txt\"; a plan or a PULSE
        # saved with a UTF-8 BOM refused; an already-applied plan told to re-plan.
        _write(self.u, "a.txt", "a\n")
        _write(self.u, "b.txt", "b\n")
        for th in ("2", "-1", "nan", "inf"):
            with self.subTest(threshold=th):
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.mod.main([str(self.u), str(self.w), "--threshold", th])
                self.assertEqual(rc, 1)
                self.assertIn("--threshold", out.getvalue())
                self.assertIn("between 0 and 1", out.getvalue())
        items = [{"id": 5, "path": "b.txt", "status": "user_only", "direction": "user_to_working"},
                 {"id": 5, "path": "b.txt", "status": "user_only", "direction": "user_to_working"}]
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(_write(self.tmp, "dup.json", json.dumps(items))), "--approve", "5"])
        self.assertEqual(rc, 1)
        self.assertRegex(out.getvalue(), r"id 5 .*twice")
        self.assertFalse((self.w / "b.txt").exists())
        items = [{"id": 1, "path": "a.txt", "status": "user_only", "direction": "USER_TO_WORKING"},
                 {"id": 2, "path": "a.txt\\", "status": "user_only", "direction": "user_to_working"},
                 {"id": 3, "path": "a.txt/", "status": "user_only", "direction": "user_to_working"},
                 {"id": 4, "path": "a.txt ", "status": "user_only", "direction": "user_to_working"}]
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(_write(self.tmp, "odd.json", json.dumps(items))), "--approve", "1,2,3,4"])
        self.assertEqual(rc, 1)
        self.assertRegex(out.getvalue(), r"Skipped a\.txt: .*USER_TO_WORKING.* is not user_to_working or working_to_user")
        for p in ("a.txt\\", "a.txt/", "a.txt "):
            self.assertRegex(out.getvalue(), re.escape(f"Refused {p}: ") + r".*ends in a separator or a space")
        self.assertEqual(sorted(p.name for p in self.w.iterdir()), [])
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan = s.plan()
        bom = _write(self.tmp, "plan-bom.json", data=b"\xef\xbb\xbf" + json.dumps(plan).encode("utf-8"))
        _write(self.u, "docs/PULSE.json", data=b"\xef\xbb\xbf" + b'{"project": "X", "cross_skill": {"pending_signals": []}}')
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(bom), "--approve", "new", "--pulse"])
        self.assertEqual(rc, 0)
        self.assertTrue((self.w / "a.txt").is_file() and (self.w / "b.txt").is_file())
        self.assertNotIn("left untouched", out.getvalue())
        pulse = (self.u / "docs/PULSE.json").read_bytes()
        self.assertFalse(pulse.startswith(b"\xef\xbb\xbf"))
        self.assertIn("synk_files_changed", pulse.decode("utf-8"))
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(bom), "--approve", "new"])
        self.assertEqual(rc, 1)
        self.assertRegex(out.getvalue(), r"Refused a\.txt: already applied")
        self.assertNotIn("re-plan", out.getvalue())


    def test_a_plan_path_in_a_skipped_folder_in_another_case_is_refused_where_the_file_system_folds_case(self):
        # Break it catches: --approve on hand-edited items .GIT/hooks/pre-commit,
        # NODE_MODULES/evil.js and Node_Modules/evil.js written into the working copy,
        # "six layers verified", while .git/x and node_modules/x were refused (the seventh
        # v1.3 review, S4d): on a file system that folds case those ARE the skipped
        # folders, and a hook under .git/hooks runs at the next commit. Where the file
        # system folds case, every skipped name is folded, in the refusal and in the scan.
        if not _folds_case(self.u):
            self.skipTest("a case-sensitive file system: .GIT is another folder there")
        _write(self.u, ".git/hooks/pre-commit", "#!/bin/sh\necho hooked\n")
        _write(self.u, "node_modules/evil.js", "x\n")
        _write(self.u, "keep.txt", "one\n")
        _write(self.w, ".GIT/config", "[core]\n")
        _write(self.w, "NODE_MODULES/evil.js", "x\n")
        _write(self.w, "Node_Modules/other.js", "y\n")
        paths = [".GIT/hooks/pre-commit", "NODE_MODULES/evil.js", "Node_Modules/evil.js"]
        plan = [{"id": i + 1, "path": p, "status": "user_only", "direction": "user_to_working"} for i, p in enumerate(paths)]
        plan_file = _write(self.tmp, "plan.json", json.dumps(plan))
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", "1,2,3"])
        self.assertEqual(rc, 1)
        for p in paths:
            with self.subTest(path=p):
                self.assertRegex(out.getvalue(), rf"Refused {re.escape(p)}: .*skips")
        self.assertFalse((self.w / ".git" / "hooks").exists())
        self.assertEqual(sorted(p.name.lower() for p in self.w.iterdir()), [".git", "node_modules"])
        with redirect_stdout(io.StringIO()):
            r = self.synk().scan_and_compare()
        self.assertEqual(sorted(r["files"]), ["keep.txt"], "the scan folds the skipped names too")

    def test_same_lines_in_mixed_endings_or_with_a_bom_are_named_as_such(self):
        # Break it catches: user a\r\nb\n against working a\nb\r\n reported "different bytes"
        # with the plan note "low similarity or binary" and --diff calling it an encoding
        # difference, and a UTF-8 BOM on one side of a two-line file reported "different
        # 33%" (the seventh v1.3 review, S5). The first is line endings differing within
        # the file, said so on the dashboard, in the plan and by --diff, each side's mix
        # named; the second is identical text with only a byte-order mark, said so too.
        _write(self.u, "mixed.txt", data=b"a\r\nb\n")
        _write(self.w, "mixed.txt", data=b"a\nb\r\n")
        _write(self.u, "bom.txt", data=b"\xef\xbb\xbfline 1\nline 2\n")
        _write(self.w, "bom.txt", data=b"line 1\nline 2\n")
        out = io.StringIO()
        with redirect_stdout(out):
            s = self.synk()
            r = s.scan_and_compare()
            plan = {a["path"]: a for a in s.plan()}
        m = r["files"]["mixed.txt"]
        self.assertEqual((m["status"], m["relationship"], m["similarity"]), ("line_endings", "line_endings", 1.0))
        self.assertEqual(m["endings"], {"user": "mixed (CRLF and LF)", "working": "mixed (CRLF and LF)"})
        self.assertTrue(m["within"])
        self.assertRegex(out.getvalue(), r"line_endings.*mixed\.txt.*line endings differ within the file.*user mixed \(CRLF and LF\)")
        self.assertIn("line endings differ within the file", plan["mixed.txt"]["note"])
        self.assertIn("user mixed (CRLF and LF), working mixed (CRLF and LF)", plan["mixed.txt"]["note"])
        b = r["files"]["bom.txt"]
        self.assertEqual((b["status"], b["relationship"], b["similarity"]), ("different", "bom", 1.0))
        self.assertEqual(b["bom"], {"user": True, "working": False})
        self.assertRegex(out.getvalue(), r"different.*bom.*bom\.txt.*only a byte-order mark.*user copy carries")
        self.assertIn("only a byte-order mark", plan["bom.txt"]["note"])
        self.assertNotIn("low similarity", plan["bom.txt"]["note"])
        self.assertEqual((r["line_endings"], r["different"], r["merge"]), (1, 1, 0))
        for rel, words in (("mixed.txt", "line endings differ within the file: user mixed (CRLF and LF), working mixed (CRLF and LF)"),
                           ("bom.txt", "differ only in a byte-order mark: the user copy carries a UTF-8 BOM, the working copy none")):
            with self.subTest(diff=rel):
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.mod.main([str(self.u), str(self.w), "--diff", rel])
                self.assertEqual(rc, 0)
                self.assertIn(words, out.getvalue())
                self.assertNotIn("encoding", out.getvalue())

    def test_plan_paths_in_forms_windows_reserves_are_refused_before_any_write(self):
        # Break it catches: a plan path "a.txt." applied as work/a.txt (Windows strips a
        # trailing dot, so the plan named one file and the copy wrote another, and the six
        # layers passed through the same stripped name), and "a.txt:evil" (an NTFS stream)
        # creating an archive folder with a manifest and then rolling back on WinError 2
        # (the seventh v1.3 review, S9). On Windows a path whose segment ends in a dot,
        # holds ':' or another character Windows forbids, or names a device, is refused
        # before any backup or write, like a trailing separator is.
        if os.name != "nt":
            self.skipTest("these forms are ordinary names outside Windows")
        _write(self.u, "a.txt", "a\n")
        paths = ["a.txt.", "sub./a.txt", "a.txt:evil", "CON", "nul.txt", "sub/LPT1", "a<b.txt", "a|b.txt", "a?.txt"]
        plan = [{"id": i + 1, "path": p, "status": "user_only", "direction": "user_to_working"} for i, p in enumerate(paths)]
        plan_file = _write(self.tmp, "plan.json", json.dumps(plan))
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve",
                                ",".join(str(a["id"]) for a in plan)])
        self.assertEqual(rc, 1)
        for p in paths:
            with self.subTest(path=p):
                self.assertRegex(out.getvalue(), re.escape(f"Refused {p}: ") + r".*Windows reserves")
        self.assertEqual(sorted(p.name for p in self.w.iterdir()), [])
        self.assertFalse((self.u / "ARCHIVE").exists())
        self.assertIsNone(self.synk().refusal("a.txt"))

    def test_a_plan_item_naming_a_link_is_refused_and_diff_refuses_it_too(self):
        # Break it catches: the scan names a link to a file and does not follow it, but a
        # hand-edited plan item naming one was copied through as a regular file holding
        # the target's content, a dangling one made an archive folder and then rolled back,
        # and --diff of a link printed the target's diff at rc 0 (the seventh v1.3 review,
        # S6). A link anywhere in an item's path, on either side, is refused before any
        # backup or write, as the scan refuses to read it; --diff answers the same.
        _write(self.u, "real/a.txt", "a\n")
        _write(self.w, "real/a.txt", "b\n")
        if not _link_folder(self.u / "jn", self.u / "real"):
            self.skipTest("this machine makes neither a junction nor a symbolic link")
        items = {"jn/a.txt": "a folder link inside the copy"}
        try:
            os.symlink(self.u / "real" / "a.txt", self.u / "link.txt")
            os.symlink(self.u / "no-such.txt", self.w / "dangling.txt")
            items.update({"link.txt": "a file link", "dangling.txt": "a dangling link on the working side"})
        except OSError:
            pass  # no file symlinks without Developer Mode; the junction case still runs
        plan = [{"id": i + 1, "path": p, "status": "merge", "direction": "user_to_working",
                 "hashes": {"user": None, "working": None}} for i, p in enumerate(items)]
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            report = s.apply(plan, [a["id"] for a in plan])
        self.assertEqual(report["applied"], [])
        self.assertEqual(sorted(x["path"] for x in report["refused"]), sorted(items))
        for x in report["refused"]:
            with self.subTest(path=x["path"]):
                self.assertIn("link", x["reason"])
        self.assertIsNone(report["archive"])
        self.assertFalse((self.u / "ARCHIVE").exists())
        self.assertEqual((self.w / "real" / "a.txt").read_text(encoding="utf-8"), "b\n")
        self.assertFalse((self.w / "link.txt").exists())
        for rel in items:
            with self.subTest(diff=rel):
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.mod.main([str(self.u), str(self.w), "--diff", rel])
                self.assertEqual(rc, 1)
                self.assertIn("link", out.getvalue())
                self.assertNotIn("---", out.getvalue())

    def test_an_item_applied_twice_is_reported_as_already_applied_whatever_its_status(self):
        # Break it catches: a two-sided item (a merge or a different pair, hand-directed)
        # applied once, then --approve'd again from the same plan, answered "the working
        # copy changed since the plan; re-plan" at rc 1, with a sync_conflict signal,
        # though the destination held exactly the source (the seventh v1.3 review, S11);
        # only a one-sided item said "already applied". Whatever the status, a destination
        # that already holds the source's content is reported as already applied, as
        # SKILL.md says.
        _write(self.u, "a.txt", "user\n")
        _write(self.w, "a.txt", "work\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan = s.plan()
        plan[0]["direction"] = "user_to_working"
        plan_file = _write(self.tmp, "plan.json", json.dumps(plan))
        with redirect_stdout(io.StringIO()):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", "1"])
        self.assertEqual(rc, 0)
        self.assertEqual((self.w / "a.txt").read_text(encoding="utf-8"), "user\n")
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", "1", "--pulse"])
        self.assertEqual(rc, 1)
        self.assertRegex(out.getvalue(), r"Refused a\.txt: already applied: the working copy holds this content")
        self.assertNotIn("re-plan", out.getvalue())
        self.assertIn("already applied", self._pulse_signals().get("sync_conflict", ""))
        _write(self.w, "a.txt", "edited since\n")
        out = io.StringIO()
        with redirect_stdout(out):
            rc = self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", "1"])
        self.assertEqual(rc, 1)
        self.assertIn("re-plan", out.getvalue())

    def test_any_exception_in_the_backup_phase_refuses_everything_and_leaves_no_archive(self):
        # Break it catches: a MemoryError (anything but an OSError) raised while backing up
        # escaping apply() with ARCHIVE/synk-<stamp>/ left behind without manifest.json and
        # no report returned, so the CLI would have died in a traceback (the seventh v1.3
        # review, injected); the OSError path was right. Any exception in the backup phase
        # refuses every item, leaves no archive folder, and the report is returned; the
        # same for backup() called on its own.
        _write(self.u, "a.txt", "user a\n")
        _write(self.w, "a.txt", "work a\n")
        with redirect_stdout(io.StringIO()):
            s = self.synk()
            s.scan_and_compare()
            plan = s.plan()
        plan[0]["direction"] = "user_to_working"
        real = shutil.copy2

        def copy2(src, dst, *a, **k):
            if "ARCHIVE" in Path(dst).parts:
                raise MemoryError("injected")
            return real(src, dst, *a, **k)
        out = io.StringIO()
        with mock.patch.object(self.mod.shutil, "copy2", copy2), redirect_stdout(out):
            report = s.apply(plan, [1])
            with self.assertRaises(MemoryError):
                s.backup(["a.txt"], side="working")
        self.assertEqual(report["applied"], [])
        self.assertEqual([x["path"] for x in report["refused"]], ["a.txt"])
        self.assertIn("MemoryError", report["refused"][0]["reason"])
        self.assertIsNone(report["archive"])
        self.assertFalse((self.u / "ARCHIVE").exists(), "an archive holds its manifest or does not exist")
        self.assertEqual((self.w / "a.txt").read_text(encoding="utf-8"), "work a\n")
        self.assertIn("nothing written", out.getvalue())

    def test_a_nested_archive_folder_is_named_as_a_folder_not_as_synks_own(self):
        # Break it catches: sub/archive/ at any depth named "Synk's ARCHIVE folder, spelled
        # archive" (the seventh v1.3 review, S4), though Synk's folder lives only at the
        # user copy's root; the skip itself stays, as ARCHIVE is skipped at every depth.
        if not _folds_case(self.u):
            self.skipTest("a case-sensitive file system: archive/ is a project folder there")
        _write(self.u, "archive/root.txt", "x\n")
        _write(self.u, "sub/archive/deep.txt", "x\n")
        _write(self.u, "a.txt", "a\n")
        with redirect_stdout(io.StringIO()):
            r = self.synk().scan_and_compare()
        reasons = {n["path"]: n["reason"] for n in r["not_compared"]}
        self.assertEqual(sorted(reasons), ["archive", "sub/archive"])
        self.assertIn("Synk's ARCHIVE folder", reasons["archive"])
        self.assertTrue(reasons["sub/archive"].startswith("a folder named archive"), reasons["sub/archive"])
        self.assertNotIn("Synk's ARCHIVE folder", reasons["sub/archive"])
        self.assertIn("skipped as ARCHIVE is", reasons["sub/archive"])
        self.assertEqual(sorted(r["files"]), ["a.txt"])

    def test_every_file_the_engines_write_is_lf_on_every_platform(self):
        # Break it catches: on Windows every JSON and Markdown file the pack writes (the
        # plan, manifest.json, rollback.md, apply-report.json, docs/PULSE.json, Solid8's
        # proposal and archive) written CRLF through write_text, so a PULSE that arrived LF
        # was rewritten with every line changed for the other machine's diff (the seventh
        # v1.3 review, T4). Everything the engines write is LF wherever they run.
        _write(self.u, "a.txt", "user\n")
        _write(self.w, "a.txt", "work\n")
        _write(self.u, "new.txt", "new\n")
        _write(self.u, "docs/PULSE.json", data=b'{"project": "X", "cross_skill": {"pending_signals": []}}\n')
        plan_file = Path(self.tmp) / "plan.json"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(self.mod.main([str(self.u), str(self.w), "--plan", str(plan_file), "--pulse"]), 0)
            plan_bytes = plan_file.read_bytes()
            plan = json.loads(plan_bytes.decode("utf-8"))
            for act in plan:
                act["direction"] = "user_to_working"
            plan_file.write_text(json.dumps(plan), encoding="utf-8")
            self.assertEqual(self.mod.main([str(self.u), str(self.w), "--apply", str(plan_file), "--approve", "1,2", "--pulse"]), 0)
        archive = next((self.u / "ARCHIVE").iterdir())
        written = {"plan.json": plan_bytes, "PULSE.json": self.u / "docs" / "PULSE.json",
                   "manifest.json": archive / "manifest.json", "rollback.md": archive / "rollback.md",
                   "apply-report.json": archive / "apply-report.json"}
        solid8 = _load("denser_engine", "solid8/scripts/denser_engine.py")
        target = Path(self.tmp) / "s8"
        _write(target, "a.txt", "same\n")
        _write(target, "a - Copy.txt", "same\n")
        proposal = Path(self.tmp) / "proposal.json"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(solid8.main([str(target), "--json", str(proposal), "--pulse"]), 0)
            e = solid8.DenserEngine(target)
            e.scan()
            dest = e.create_archive(["a.txt"], target / "ARCHIVE", "test")
        written.update({"proposal.json": proposal, "solid8 PULSE.json": target / "docs" / "PULSE.json",
                        "solid8 manifest.json": dest / "manifest.json", "solid8 rollback.md": dest / "rollback.md"})
        for name, path in written.items():
            with self.subTest(file=name):
                data = path if isinstance(path, bytes) else path.read_bytes()
                self.assertTrue(data, name)
                self.assertNotIn(b"\r", data, f"{name} is not LF")

# The seventh v1.3 review's 28 pointer forms, each with its made-up name and the token
# mechanism 1 reports for it, or None where the form is the deny-list's job: a one-word
# name in a code span or a link has no shape (the link's host is red instead). Every
# other form is red through the vocabulary: CamelCase, a dotted name, a bare, dot-folder
# or Windows path to a skill folder, hex letters with one digit, v8, x_y, a date in a
# name, a name in any script, and the hyphenated and digit-bearing names of before.
REVIEW7_FORMS = {
    'Not for notes; use NoteTaker.': ('notetaker', 'notetaker'),
    'Not for notes; use jotBook for those.': ('jotbook', 'jotbook'),
    '| Ask | Skill |\n|---|---|\n| Notes | MemoSweeper |': ('memosweeper', 'memosweeper'),
    'Not for notes; use private.notes.': ('private.notes', 'private.notes'),
    'Not for notes; run org.notes.skill.': ('org.notes', 'org.notes'),
    'Not for notes; the notes.v2 skill does those.': ('notes.v2', 'notes.v2'),
    'Not for notes; see skills/jotbook.': ('jotbook', 'jotbook'),
    'Not for notes; see skills/jotbook for those.': ('jotbook', 'jotbook'),
    'Not for notes; it lives in .agents/skills/jotbook.': ('jotbook', 'jotbook'),
    'Not for notes; it lives in .cursor/skills/jotbook.': ('jotbook', 'jotbook'),
    'Not for notes; see C:\\Users\\me\\.agents\\skills\\jotbook\\SKILL.md.': ('jotbook', 'jotbook'),
    'Not for notes; see %USERPROFILE%\\.agents\\skills\\jotbook.': ('jotbook', 'jotbook'),
    'Not for notes; use face2face.': ('face2face', 'face2face'),
    'Not for notes; use decaf5.': ('decaf5', 'decaf5'),
    'Not for notes; use cab2bed for those.': ('cab2bed', 'cab2bed'),
    'Not for notes; use bad1dea.': ('bad1dea', 'bad1dea'),
    'Not for notes; use v8.': ('v8', 'v8'),
    'Not for notes; use x_y.': ('x_y', 'x_y'),
    'Not for notes; use notes-2026-09-30.': ('notes-2026-09-30', 'notes-2026-09-30'),
    'Not for notes; use 2026-09-30-notes.': ('2026-09-30-notes', '2026-09-30-notes'),
    'Not for notes; use caf\u00e9-notes.': ('caf\u00e9-notes', 'caf\u00e9-notes'),
    'Not for notes; use na\u00efve-notes.': ('na\u00efve-notes', 'na\u00efve-notes'),
    'Not for notes; use `jotbook`.': ('jotbook', None),
    'Not for notes; use [jotbook](https://example.org/x).': ('jotbook', None),
    'Not for release-notes (DevCom5).': ('release-notes', 'release-notes'),
    'Not for notes; use private-notes.': ('private-notes', 'private-notes'),
    'Not for notes; use notes2go.': ('notes2go', 'notes2go'),
    'Not for notes; use 0xdeadbeef1.': ('0xdeadbeef1', '0xdeadbeef1'),
}


# ─────────────────────────────────────────────────────────────── the three folders
class SkillFolders(unittest.TestCase):
    """Each skill folder meets Skillshaper's bar, and its description is what makes it fire."""

    def test_each_skill_validates_strict(self):
        if not VALIDATOR.is_file():
            self.skipTest(f"validator not found at {VALIDATOR}")
        spec = importlib.util.spec_from_file_location("validate_skill", VALIDATOR)
        v = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(v)
        for name in SKILLS:
            with self.subTest(skill=name):
                errors, warnings = v.check(ROOT / name)
                self.assertEqual(errors, [], f"{name}: {errors}")
                self.assertEqual(warnings, [], f"{name}: {warnings}")

    def test_trifecta_protocol_identical_in_all_copies(self):
        texts = {n: (ROOT / n / "references/TRIFECTA_PROTOCOL.md").read_bytes() for n in SKILLS}
        texts["docs"] = (ROOT / "docs/TRIFECTA.md").read_bytes()
        self.assertEqual(len(set(texts.values())), 1, "the protocol must be byte-identical everywhere it is copied")

    def test_protocol_says_what_the_engines_do_with_a_missing_or_broken_pulse(self):
        # Break it catches: the protocol's safety rule still saying "Corrupt/missing
        # PULSE → graceful fallback to standalone" while both engines create
        # docs/PULSE.json holding only cross_skill when none exists (found by the
        # second v1.3 review). The engines' behaviour is driven here, so the rule
        # and the code move together.
        for rel in ("synk182/scripts/synk_engine.py", "solid8/scripts/denser_engine.py"):
            mod = _load(Path(rel).stem, rel)
            tmp = tempfile.mkdtemp()
            try:
                with self.subTest(engine=rel):
                    path = mod.update_pulse(tmp, {"probe_last_run": "2026-09-30T00:00:00-04:00"})
                    self.assertEqual(list(json.loads(Path(path).read_text(encoding="utf-8"))), ["cross_skill"])
                    broken = _write(tmp, "docs/PULSE.json", "{not json")
                    self.assertIsNone(mod.update_pulse(tmp, {"probe_last_run": "x"}))
                    self.assertEqual(broken.read_text(encoding="utf-8"), "{not json")
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
        protocol = (ROOT / "docs/TRIFECTA.md").read_text(encoding="utf-8")
        self.assertFalse("missing PULSE → graceful fallback to standalone" in protocol,
                         "the protocol still says a missing PULSE falls back to standalone")
        rule =[l for l in protocol.splitlines() if l.startswith("4. Missing PULSE")]
        self.assertEqual(len(rule), 1, "Safety rule 4 must say what a missing PULSE leads to")
        self.assertIn("creates `docs/PULSE.json` holding only `cross_skill`", rule[0])
        self.assertIn("leave it untouched, say so and work standalone", rule[0])

    def test_protocol_says_which_signal_timestamps_are_pruned(self):
        # Break it catches: the protocol saying only "ISO-8601" while the engines pruned
        # a Z stamp on some Python versions and never pruned one with no offset (found by
        # the fifth v1.3 review), then a stamp one Python reads and another does not, and
        # a consumed signal whose stamp cannot be read stopping every later --pulse (the
        # sixth). The engines' pruning is driven in each engine's own case; here the
        # lifecycle rule must pin the grammar and say what an unreadable stamp leads to.
        protocol = (ROOT / "docs/TRIFECTA.md").read_text(encoding="utf-8")
        rule = protocol[protocol.index("**Lifecycle:**"):].split("\n\n", 1)[0]
        self.assertIn("with an offset or `Z`", rule)
        self.assertIn("read as local time", rule)
        self.assertIn("`YYYY-MM-DD`, then `T`", rule)
        self.assertIn("then `HH:MM:SS`", rule)
        self.assertIn("a consumed signal whose `timestamp` cannot be read is pruned", rule)
        self.assertIn("only JSON `true` counts as consumed", rule)

    def test_description_reaches_the_host_listing(self):
        # Break it catches: a description a strict host drops from its listing,
        # so the skill never fires (a skill once lost its listing to an unquoted
        # ': ' in a header value).
        for name in SKILLS:
            with self.subTest(skill=name):
                fm = _frontmatter(name)
                self.assertIn(fm["style"], ("block", "line"),
                              f"{name}: description must be one line or a '>-' block")
                self.assertLessEqual(len(fm["description"]), 1024, f"{name}: description over 1024 characters")
                self.assertNotRegex(fm["description"], r"[<>]", f"{name}: angle brackets are rejected at upload")
                for key, raw in fm["metadata"].items():
                    if ": " in raw:
                        self.assertRegex(raw, r"^([\"']).*\1$",
                                         f"{name}: metadata.{key} holds ': ' and must be quoted")

    def test_description_names_the_words_it_is_called_by(self):
        for name, words in CALL_WORDS.items():
            desc = _frontmatter(name)["description"].lower()
            for w in words:
                with self.subTest(skill=name, word=w):
                    self.assertIn(w, desc)

    def test_description_says_what_it_is_not_for(self):
        # Break it catches: a skill that fires on its siblings' work.
        for name in SKILLS:
            with self.subTest(skill=name):
                desc = _frontmatter(name)["description"]
                self.assertIn("not for", desc.lower(), f"{name}: description never says what it is not for")
                named = [s for s in SIBLINGS if s in desc and s.lower() != name]
                self.assertTrue(named, f"{name}: the 'not for' names no sibling skill")

    def test_no_pointer_to_a_skill_that_is_neither_in_the_pack_nor_public(self):
        """Break it catches: "not for X, use Y" where Y is neither in the pack nor public,
        so a reader's agent is sent nowhere (found by the v1.2 review: four private names).

        Mechanism 1 of two (the vocabulary block above): every name-shaped token in every
        tracked .md file must be in VOCABULARY_NAMES or VOCABULARY_WORDS; the failure names
        file:line and the remedy. No grammar is read: a private name is caught by its shape
        (a hyphen, an underscore, a digit, a path) wherever and however it is written. A
        one-word private name has no shape; mechanism 2 (the deny-list test below) catches
        it. Run with TRIAD_ROOT on an export of commit a9f9b3a, this goes red on the three
        hyphenated names that review found; the fourth is a one-word name, so it is the
        deny-list's."""
        unknown = _unknown_tokens(ROOT)
        self.assertEqual(unknown, [], "\n" + "\n".join(unknown) + "\n" + REMEDY)

    def test_vocabulary_holds_only_what_the_pack_uses(self):
        # The ratchet's other edge, by the same tokenizer the check reads with: every entry
        # of the three lists must be produced as a name-shaped token from the pack's
        # Markdown, so an entry that is also an English word (in, path, project, from the
        # one path example) goes stale the moment the text that produced it goes (the
        # seventh v1.3 review measured the whole-word check passing 106 plain uses of
        # "in"); the two plain public names are checked whole-word, since they have no
        # shape. The lists are lowercase and disjoint.
        produced = _produced_tokens(ROOT)
        text = "\n".join(p.read_text(encoding="utf-8") for p in _markdown_files(ROOT)).lower()
        for entry in sorted(VOCABULARY_NAMES | VOCABULARY_KINDS | VOCABULARY_WORDS):
            with self.subTest(entry=entry):
                self.assertEqual(entry, entry.lower().strip())
                self.assertIn(entry, produced, "stale: the pack's text no longer produces it; remove it")
        for entry in PLAIN_NAMES:
            with self.subTest(entry=entry):
                self.assertIsNone(_name_shaped(entry), "it has a shape: list it in VOCABULARY_NAMES")
                self.assertRegex(text, r"(?<![a-z0-9_])" + re.escape(entry) + r"(?![a-z0-9_])", "stale; remove it")
        lists = (VOCABULARY_NAMES, VOCABULARY_KINDS, VOCABULARY_WORDS, frozenset(PLAIN_NAMES))
        self.assertEqual(sum(map(len, lists)), len(frozenset().union(*lists)), "an entry sits in two lists")

    def test_name_shape_is_what_the_vocabulary_block_says(self):
        # Pins the shape rule, one case per clause of the block above, so a change to it is
        # a change here first. The seventh v1.3 review wrote 28 pointer forms before reading
        # the discriminator and 21 passed it: CamelCase folded away, a dotted name read as
        # an extension, any hex letters with a digit read as a commit, v8 as a version, x_y
        # as one-letter parts, a date blanked out of a name, a non-ASCII letter splitting a
        # run, and a bare, dot-folder or Windows path not read as a path (REVIEW7_FORMS).
        for token, name in (("Private-Notes", "private-notes"), ("private_notes", "private_notes"),
                            ("private\u2011notes", "private-notes"), ("private\u2013notes", "private-notes"),
                            ("notes2go", "notes2go"), ("memo7", "memo7"), ("utf-8", "utf-8"), ("3P", "3p"),
                            ("--dry-run", "dry-run"), ("synk_engine.py", "synk_engine"), ("mk1made.us", "mk1made.us"),
                            ("release-notes.", "release-notes"), ("cfg.json.bak.old", None), ("skills.sh", None),
                            ("NoteTaker", "notetaker"), ("jotBook", "jotbook"), ("macOS", "macos"), ("PULSE.corrupt.json", "pulse.corrupt"),
                            ("private.notes", "private.notes"), ("org.notes.skill", "org.notes"), ("notes.v2", "notes.v2"),
                            ("face2face", "face2face"), ("decaf5", "decaf5"), ("cab2bed", "cab2bed"), ("abcdef1", "abcdef1"),
                            ("v8", "v8"), ("v2", "v2"), ("x_y", "x_y"), ("caf\u00e9-notes", "caf\u00e9-notes"),
                            ("notes-2026-09-30", "notes-2026-09-30"), ("0xdeadbeef1", "0xdeadbeef1"),
                            ("v1.3", None), ("v3.3+", None), ("19a8722", None), ("a9f9b3a", None), ("deadbeef", None),
                            ("2026-09-30", None), ("60-99", None), ("A-C", None), ("e.g.", None), ("i.e.", None),
                            ("PULSE.json", None), ("README.md", None), ("notes", None), ("Docker", None),
                            ("private notes", None), ("\u2070", None)):
            with self.subTest(token=token):
                self.assertEqual(_name_shaped(token), name)
        text = ("see /jotbook, jotbook/SKILL.md and `skills/jotbook/`; read/comprehend it at 14:12 on "
                "2026-09-30T14:12:00Z; docs/PULSE.json; https://github.com/someone/x; (D/M/C); 1-2 \u00b6/section; "
                "CI/CD; skills/jotbook; .agents/skills/jotbook; C:\\Users\\me\\.cursor\\skills\\jotbook\\SKILL.md; "
                "notes-2026-09-30 and 2026-09-30-notes, on 2026-09-30 at 13:45:34 -0400; v1.3; v8")
        self.assertEqual([t for _, t in _name_shaped_tokens(text)],
                         ["jotbook", "jotbook", "skill", "skills", "jotbook", "docs", "pulse", "github.com", "someone",
                          "skills", "jotbook", "agents", "skills", "jotbook", "users", "me", "cursor", "skills", "jotbook", "skill",
                          "notes-2026-09-30", "2026-09-30-notes", "v8"])
    def _pack_copy(self):
        """A copy of the pack's Markdown to inject into; README.md's text and line count."""
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        for p in _markdown_files(ROOT):
            _write(tmp, p.relative_to(ROOT).as_posix(), p.read_text(encoding="utf-8"))
        base = (tmp / "README.md").read_text(encoding="utf-8")
        return tmp, base, base.count("\n")

    def test_every_pointer_form_goes_red_on_a_made_up_name(self):
        # Every form the earlier reviews and probes listed, appended to a copy of the
        # pack's README: a made-up name with a mark is reported by the vocabulary check
        # at README.md:line, and every made-up name, one-word ones too, by the deny-list
        # when it is listed. The copy is green before the injection. Closes the sixth
        # review's medium 1 and low 1-2 by construction: no form is parsed.
        tmp, base, n = self._pack_copy()
        listed = sorted({name for names in POINTER_FORMS.values() for name in names})
        self.assertEqual(_unknown_tokens(tmp), [])
        self.assertEqual(_private_name_hits(tmp, listed), [])
        for p in _markdown_files(tmp):  # the injections go into README.md; the rest was read once
            if p != tmp / "README.md":
                p.unlink()
        for text, names in POINTER_FORMS.items():
            with self.subTest(form=text):
                (tmp / "README.md").write_text(base + text + "\n", encoding="utf-8", newline="")
                lowered = text.translate(_DASHES).lower()
                spelled = {_name_shaped(_private_name_pattern(name).search(lowered).group()) for name in names}
                spelled.discard(None)
                found = _unknown_tokens(tmp)
                self.assertTrue(all(f.startswith("README.md:") and int(f.split(":")[1]) > n for f in found), found)
                self.assertTrue(spelled <= {f.split(": ", 1)[1] for f in found}, (spelled, found))
                hits = _private_name_hits(tmp, names)
                self.assertEqual({h.split(": ", 1)[1] for h in hits}, set(names), hits)
                self.assertTrue(all(h.startswith("README.md:") and int(h.split(":")[1]) > n for h in hits), hits)

    def test_a_stale_vocabulary_entry_goes_red(self):
        # The ratchet's other edge: an entry the pack stops using fails, so the lists
        # cannot grow on a guess. Driven on a copy of the pack with one word's every use
        # removed, through the same tokenizer the ratchet test reads with; and an entry
        # that is also an English word (in, path, project: the one path example produces
        # them) goes stale with that example, though the plain words stay everywhere.
        tmp, _, _ = self._pack_copy()
        for p in _markdown_files(tmp):
            p.write_text(p.read_text(encoding="utf-8").replace("re-plan", "plan again").replace("path/in/project.md", "sub/file.md"),
                         encoding="utf-8", newline="")
        produced = _produced_tokens(tmp)
        text = "\n".join(p.read_text(encoding="utf-8") for p in _markdown_files(tmp)).lower()
        for word in ("re-plan", "in", "path", "project"):
            with self.subTest(entry=word):
                self.assertIn(word, VOCABULARY_WORDS)
                self.assertNotIn(word, produced)
        self.assertRegex(text, r"(?<![a-z0-9_])in(?![a-z0-9_])", "the plain word stays; only the token is gone")

    def test_review7_pointer_forms_are_caught_by_the_mechanism_the_table_names(self):
        # Break it catches: the seventh v1.3 review's 28 forms, written before reading the
        # discriminator, 21 of which passed mechanism 1 on 11f65be. Each form is appended
        # to a copy of the pack's README: where REVIEW7_FORMS names a token, mechanism 1
        # reports exactly it at a line past the original; where it names None, the form is
        # the deny-list's job (a one-word name in a code span or a link has no shape), and
        # the deny-list finds the name there. Every listed name is a deny-list hit.
        tmp, base, n = self._pack_copy()
        self.assertEqual(_unknown_tokens(tmp), [])
        for p in _markdown_files(tmp):
            if p != tmp / "README.md":
                p.unlink()
        for text, (name, token) in REVIEW7_FORMS.items():
            with self.subTest(form=text):
                (tmp / "README.md").write_text(base + text + "\n", encoding="utf-8", newline="")
                found = {f.split(": ", 1)[1] for f in _unknown_tokens(tmp) if int(f.split(":")[1]) > n}
                self.assertEqual(found, {f.split(": ", 1)[1] for f in _unknown_tokens(tmp)}, "red only past the original")
                if token:
                    self.assertIn(token, found)
                hits = _private_name_hits(tmp, [name])
                self.assertEqual([h.split(": ", 1)[1] for h in hits], [name], hits)
                self.assertGreater(int(hits[0].split(":")[1]), n)

    def test_deny_list_reads_one_name_per_line_and_finds_every_spelling(self):
        # Mechanism 2 driven on a made-up list: comments and blank lines are skipped; a
        # listed name is found whole-word in any file (Markdown, a script, the licence),
        # in any case, with accents folded, and with its parts joined by a hyphen, an
        # underscore, a dash, one or more spaces, a tab, a no-break space, nothing, or a
        # line break (a soft wrap, reported at its first line); a one-word name split by a
        # hyphen or a space is found too. A longer word that contains it, a name with a
        # digit added, .git and __pycache__ are not hits (the seventh v1.3 review's 27
        # spellings: privatenotes, private--notes, jot-book and the soft wrap were misses).
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        deny = _write(tmp, "names.txt", "# made-up names\n\njotbook\n  Private-Notes\n")
        self.assertEqual(_read_private_names(deny), ["jotbook", "private-notes"])
        pack = tmp / "pack"
        _write(pack, "README.md", "Jotbook keeps those.\nthe jotbooks\njotbook2\nuse private_notes\n"
                                  "PRIVATE NOTES\nprivate‑notes\nprivately noted\n")
        _write(pack, "synk182/scripts/x.py", "# jotbook\n")
        _write(pack, "LICENSE", "Private-Notes\n")
        _write(pack, ".git/config", "jotbook\n")
        _write(pack, "__pycache__/x.pyc", "jotbook\n")
        _write(pack, "docs/MORE.md", "privatenotes\nprivate--notes\nprivate  notes\nprivate\tnotes\nprivate notes\n"
                                     "prívate-notes\njot-book\njot book\nsee private-\nnotes there\nnothing here\nprivate -notes\n")
        self.assertEqual(_private_name_hits(pack, ["jotbook", "private-notes"]),
                         ["LICENSE:1: private-notes", "README.md:1: jotbook", "README.md:4: private-notes",
                          "README.md:5: private-notes", "README.md:6: private-notes",
                          "docs/MORE.md:1: private-notes", "docs/MORE.md:2: private-notes", "docs/MORE.md:3: private-notes",
                          "docs/MORE.md:4: private-notes", "docs/MORE.md:5: private-notes", "docs/MORE.md:6: private-notes",
                          "docs/MORE.md:7: jotbook", "docs/MORE.md:8: jotbook", "docs/MORE.md:9: private-notes",
                          "docs/MORE.md:12: private-notes", "synk182/scripts/x.py:1: jotbook"])
    def test_private_names_from_the_deny_list_never_appear_in_the_pack(self):
        """Mechanism 2 on the pack itself: TRIAD_PRIVATE_NAMES names a file outside the
        repository, one private name per line (# comments); any whole-word occurrence of a
        listed name in any file of the pack fails, named file:line. The list's contents and
        place are never in the repository; without the variable the test is skipped, and
        says so, rather than passing for nothing."""
        path = os.environ.get("TRIAD_PRIVATE_NAMES")
        if not path:
            self.skipTest("TRIAD_PRIVATE_NAMES is not set: the private-name deny-list was not checked")
        names = _read_private_names(path)
        self.assertTrue(names, f"{path} lists no name")
        hits = _private_name_hits(ROOT, names)
        self.assertEqual(hits, [], "a private name in the public pack:\n" + "\n".join(hits))

    def test_devcom5_template_names_the_protocol_version(self):
        # Break it catches: the pulse_version in DevCom5's PULSE template drifting
        # from the protocol's own version (2.0 beside v3.0 at v1.2), which invites
        # an agent to "fix" one of them.
        protocol = re.search(r"<!-- v(\d+\.\d+)", (ROOT / "docs/TRIFECTA.md").read_text(encoding="utf-8")).group(1)
        self.assertIn(f'"pulse_version": "{protocol}"', (ROOT / "devcom5/SKILL.md").read_text(encoding="utf-8"))

    def test_each_skill_declares_freeware(self):
        for name in SKILLS:
            with self.subTest(skill=name):
                lic = _frontmatter(name)["license"] or ""
                self.assertIn("Freeware", lic, f"{name}: frontmatter license must say Freeware")

    def test_skill_bodies_name_no_single_host(self):
        # The skills run in any agent host; a host's name inside a skill is lock-in.
        for name in SKILLS:
            for p in (ROOT / name).rglob("*.md"):
                with self.subTest(file=p.relative_to(ROOT).as_posix()):
                    text = p.read_text(encoding="utf-8")
                    self.assertNotRegex(text, r"Cursor|claude\.ai|Claude Code|Claude Desktop")


# ─────────────────────────────────────────────────────────────── the pack
class Pack(unittest.TestCase):
    """The pack's own face: its name, its audience and its licence."""

    def readme(self):
        return (ROOT / "README.md").read_text(encoding="utf-8")

    def test_pack_is_named_the_triad(self):
        # The pack is named The Triad; its README heading carries the name.
        headings = [l for l in self.readme().splitlines() if l.startswith("# ")]
        self.assertTrue(headings and headings[0].startswith("# The Triad"), headings[:1])

    def test_pack_says_agent_skill_pack_not_two_hosts(self):
        # The pack is for any agent host: the README says "agent skill pack" and
        # never names two hosts as its audience.
        text = self.readme()
        self.assertIn("agent skill pack", text.lower())
        self.assertNotIn("/ Claude **agent skills**", text)

    def test_pack_license_is_freeware_not_mit(self):
        # The pack is freeware, not MIT; the README and LICENSE agree on it.
        text = self.readme()
        self.assertIn("Freeware", text)
        self.assertNotRegex(text, r"^MIT — see", re.M)
        lic = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertFalse(lic.startswith("MIT License"), "LICENSE is still MIT")
        self.assertIn("The Triad", lic)

    def test_readme_links_the_proof_pack_where_it_names_verafox(self):
        # verafox is the one outside skill the pack points at; a reader must be
        # able to reach it from the README.
        text = self.readme()
        self.assertIn("verafox", text)
        self.assertIn(PROOF_PACK, text)

    def test_readme_names_the_current_versions(self):
        # Ties the README to the frontmatter, so a bump in one is a bump in both.
        text = self.readme()
        titles = {"devcom5": "DevCom5", "synk182": "Synk182", "solid8": "Solid8"}
        for name in SKILLS:
            version = _frontmatter(name)["metadata"].get("version", "").strip("\"'")
            with self.subTest(skill=name):
                self.assertTrue(version, f"{name}: no metadata.version")
                self.assertIn(f"{titles[name]} {version}", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
