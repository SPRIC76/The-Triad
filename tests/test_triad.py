"""Version 1.1 | Deps: stdlib; Skillshaper's validate_skill.py when present | Parent: The Triad (DevCom5 1.3, Synk182 3.3, Solid8 1.3) | Path: tests | Filename: test_triad.py | Created: 2026-09-30 01:12 ET - kept tests for the pack: the two engines, the three skill folders, and the pack's own ratchets. | Updated: 2026-09-30 04:05 ET - v1.3: red-first cases from the v1.2 review (bounded plan paths, stale plans, wrong-typed PULSE fields, CLI messages, copy numbers, sprawl across folders, pointer and version ratchets); comments read for a public reader; both engines checked for personal paths. | Updated: 2026-09-30 04:53 ET - red-first cases from the second v1.3 review: folder targets and rollback, backups read as the file they back up, unknown --approve ids, one folder given twice, an unparseable PULSE reported, signals only when true, protocol safety rule 4; the pointer check is an allow-list, so the test names no private skill. | Updated: 2026-09-30 05:37 ET - red-first cases from the third v1.3 review: --pulse when docs is a file, a PULSE holding no object, an approved item with no direction, an item with only an id named by its id, --plan beside --apply and --diff beside another action, a backup of a binary, backups with two markers; the pointer check reads what a pointer names, in any of its forms, rather than its first word. | Updated: 2026-09-30 06:09 ET - red-first cases from the fourth v1.3 review: a --plan or --json file that cannot be written, an item with no path in the --approve new listing; the pointer check reads the "X tool/helper/plugin" form, verbs beyond "use", possessives and subjects, loose names, Task/Need/Tool tables, wrapped clauses and a bare arrow's name, leaves slot words, counts and the pack's flows alone, and every allowed kind must be read from the pack. | Updated: 2026-09-30 07:28 ET - red-first cases from the fifth v1.3 review: the pointer check tells a skill name from English's own hyphenated words by form, with a short ratcheted list of lexicalized compounds, keeps a realistic-prose corpus green and reads a one-word name after a verb again; an empty --plan, --apply, --diff or --json name, a file named ARCHIVE, hand-edited plan ids and hashes, junctions and links, a folder that cannot be listed, and signals stamped with Z.

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
# The words a pointer may name: the siblings, git, and the kinds of work the pack
# describes ("a diagramming skill"). A new kind is added here on purpose; any other
# skill-shaped word in a pointer names a skill the reader cannot reach.
POINTER_NAMES = {s.lower() for s in SIBLINGS} | {"git"}
POINTER_KINDS = {"knowledge-search", "diagramming", "repo-rules", "memory-consolidation"}
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


# An Agent Skills name is lowercase letters, digits and hyphens, so a capitalised word
# (GitHub, Verafox) is never one; where a pointer is certain, a hyphenated or underscored
# name written loosely (Private-Notes, private_notes) is read as the name it spells.
_SKILL_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_LOOSE_NAME = re.compile(r"[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)+")
_HYPHENATED = r"[a-z0-9]+(?:-[a-z0-9]+)+"

# A skill name is a kebab-case identifier: it hyphenates where English writes a space
# ("private notes" is private-notes). English hyphenates its own words by a few forms,
# so a hyphenated word is English when one of them explains it: a prefix, particle or
# number first (re-plan, co-maintainer, on-call, back-end, third-party); a particle last
# (follow-up, sign-off, check-ins); a linker inside (end-to-end, point-in-time); a
# participle last (self-contained, spell-checking); a modifier head last (read-only,
# high-level, domain-specific, long-term); a one-letter or all-digit part (e-mail,
# utf-8). The forms are closed classes of English, so a compound nobody listed is still
# known by its form. What no form marks is kept as data in _ENGLISH_COMPOUNDS, which a
# test keeps free of anything a form marks and of every allowed name.
_PARTICLES = frozenset("up off in out on over back down by away through about around along apart ahead".split())
_LEADS = _PARTICLES | frozenset(
    "re co sub self non pre post anti multi cross semi de un ex mid under inter intra meta auto bi tri mono "
    "poly pseudo quasi super ultra well ill half all counter micro macro mini mega hyper per zero one two "
    "three four five six seven eight nine ten hundred first second third fourth fifth last single double "
    "triple many few".split())
_LINKERS = frozenset("to and or of the a an in on for at as by n".split())
_HEADS = frozenset(
    "only level specific based aware free safe wide side time term party purpose platform source way like "
    "friendly proof ready facing bound driven oriented centric agnostic compatible dependent independent "
    "sensitive insensitive native first worthy style scale grade class alone".split())
_PARTICIPLE = re.compile(r"[a-z]{3,}(?:ed|ing)|known|written|built|made|driven|grown|drawn|given|taken"
                         r"|broken|hidden|proven|shown|done|held|kept")
_ENGLISH_COMPOUNDS = frozenset("""
    ad-hoc best-effort brute-force camel-case check-box cherry-pick code-base code-review command-line
    copy-paste data-set dead-end dead-lock dry-run end-point end-user fact-check file-name file-system
    front-end front-matter go-to hard-link hot-fix how-to kebab-case key-value life-cycle load-test man-page
    merge-request must-have no-op peer-review plain-text pull-request real-world rich-text round-trip
    run-book sanity-check side-effect snake-case spell-check time-stamp to-do tool-chain
    unit-test web-hook what-if wild-card work-flow work-tree""".split())


def _english_by_form(word):
    """True when one of English's own hyphenating forms explains a hyphenated word."""
    parts = word.split("-")
    return (parts[0] in _LEADS or parts[-1] in _PARTICLES or parts[-1] in _HEADS
            or bool(_PARTICIPLE.fullmatch(parts[-1])) or any(p in _LINKERS for p in parts[1:-1])
            or any(len(p) == 1 or p.isdigit() for p in parts))


def _english(word):
    """True when a hyphenated word is English's own, as it stands or as a plural."""
    forms = {word, word[:-1] if word.endswith("s") else word, word[:-2] if word.endswith("es") else word}
    return any(_english_by_form(w) or w in _ENGLISH_COMPOUNDS for w in forms if "-" in w)


# One word is a name by its slot and its shape. Where the slot is certain (an arrow
# group, a Skill cell) a word is read unless its ending marks ordinary English (manual,
# optional); in prose, where "use caution" and "use notetaker" share a slot, a word is
# read only with a name's mark: a digit inside it (notes2go), or an agent's or a
# coiner's ending (notetaker, jotify), a count noun English never uses bare.
_ORDINARY = re.compile(r"[a-z]+(?:ly|al|ive|ous|able|ible|ful|less|tion|sion|ment|ness|ity|ance|ence|wise|wards?)")
_NAME_MARK = re.compile(r"[a-z]{2,}\d+[a-z][a-z0-9]*|[a-z]{3,}(?:er|or|ify)")
# English's closed classes (pronouns, determiners, quantifiers, a few adverbs) fill a
# pointer's slot ('use yours instead') but name nothing; nor do counts and versions.
_CLOSED = frozenset("""
    it its this that them they these those one ones both each either neither any some none all another other
    others such same yours mine ours theirs his hers whichever whatever whoever however whenever wherever
    something anything nothing everything someone anyone nobody everyone somebody anybody everybody here there
    now later soon again instead elsewhere nowhere anywhere everywhere somewhere above below never ever rather
    further together whether""".split())
_NUMBERED = re.compile(r"[a-z]?\d+")
# A name takes no article: "the follow-up" is a common noun, except before the noun a
# kind is described by ("the X skill"). A word after "git" is git's own (git filter-repo).
_NOT_BEFORE_A_NAME = frozenset("a an the this that these those each every any some no your our their its his her my "
                               "git".split())

_NOUN = r"(?:skills?|tools?|helpers?|plugins?)"
_SUBJECT_VERB = (r"(?:is|are|was|does|do|can|will|should|may|must|handles?|covers?|owns?|takes?|keeps?|exists?"
                 r"|holds?|manages?|writes?|runs?|tracks?|stores?|deals?|works?|lives?|belongs?)")
# A name ends its phrase: punctuation, a version, a function word, a skill noun ("the X
# skill"), or the verb it is the subject of; a word a noun follows is describing it
# ("read-only mode", "zip-file backups"), and a dot before a letter is a file's extension.
_ENDS = (r"(?![\w-])(?=\s*(?:$|[,;:!?)(`'\"*_|+—–]|\.(?!\w)|→|->)"
         r"|\s+(?:instead|for|to|when|if|here|there|first|or|and|which|but|then|v?\d[\w.]*|"
         + _NOUN + "|" + _SUBJECT_VERB + r")\b)")
_EDGE = r"(?<![\w\-./\\])"
_ENDING = re.compile(_EDGE + "(" + _HYPHENATED + ")" + _ENDS)
_KIND = re.compile(r"\b(?:a|an|the|your)\s+([a-z0-9][a-z0-9-]*)\s+(" + _NOUN + r")\b")
_VERB = r"(?:[Uu]se|[Ss]ee|[Tt]ry|[Ll]oad|[Rr]un|[Aa]sk|[Cc]all|[Ii]nvoke|[Oo]pen|[Pp]refer|[Ii]nstall)"
_VERB_OBJECT = re.compile(r"\b" + _VERB + r"\s+([a-z][a-z0-9]*)" + _ENDS)
_BACKTICKED = re.compile(r"\b" + _VERB + r"\s+(?:(?:the|a|an|your)\s+)?`([a-z0-9][a-z0-9-]*)`")
_BARE_OWNER = re.compile(_EDGE + r"([a-z][a-z0-9]*)(?='s\b|\s+" + _SUBJECT_VERB + r"\b)")
_SENTENCE_CASE = re.compile(r"(?:^|(?<=[.!?;:]\s))([A-Z][a-z0-9]*(?:-[a-z0-9]+)+)(?![\w-])")
_ARROW = re.compile(r"\((?:→|->)\s*((?:[^()]|\([^()]*\))*)\)")
# A bare arrow is the pack's flow notation ('backup → copy → verify'); it points at a
# skill only when a hyphenated name follows it and ends the line or the clause.
_BARE_ARROW = re.compile(r"(?<!\()(?:→|->)[ \t]*(" + _HYPHENATED + r")(?=[ \t]*(?:$|[.,;)]))", re.M)
_PAREN = re.compile(r"\((?:→|->)?\s*((?:[^()]|\([^()]*\))*)\)")
_PARTS = re.compile(r",|\s+(?:or|and)\s+")
_VERSION = re.compile(r"\s+v?\d+(?:\.\d+)*\+?$")
_NOT_FOR = re.compile(r"(?i)\bnot (?:(?:meant|intended|designed|built|made|used|suited) )?for\b|\bout of scope\b"
                      r"|\*\*not [^*\n]+:\*\*")
_NOT_FOR_LABEL = re.compile(r"(?i)^\s*(?:#{1,6}\s+)?[*_]*(?:[a-z' ]*\s)?(?:not (?:\w+ )?for|out of scope)[*_:\s]*$")


def _free(text, start):
    """True when the word before start is neither an article nor git (_NOT_BEFORE_A_NAME)."""
    before = re.search(r"([A-Za-z]+)[ \t]+$", text[max(0, start - 40):start])
    return not before or before.group(1).lower() not in _NOT_BEFORE_A_NAME


def _opens(text, start):
    """True when a lone word at start opens its phrase: after the clause's start or its
    punctuation, or after 'is', so 'a schema-aware editor does' names nothing."""
    return bool(re.search(r"(?:^|[.,;:(—–→]|\b(?:is|are|was|were))\s*$", text[max(0, start - 40):start]))


def _kinds(text, one_word):
    """'a/an/the/your X skill|tool|helper|plugin': X when it is hyphenated, or when one_word
    and the noun is skill ('a diagramming skill'); 'a diff tool' describes, never names."""
    return [x for x, noun in _KIND.findall(text) if "-" in x or (one_word and noun.startswith("skill"))]


def _part_names(part, certain):
    """The names one part of a pointer names: its whole text, bare of parentheses, a
    version and markup, when that is a skill name (a lone word by its slot, above), and
    a kind. certain: the part is surely a pointer (an arrow group or a Skill cell), so a
    loosely written name and a hyphenated word ending its phrase anywhere in it count."""
    part = _VERSION.sub("", re.sub(r"\([^()]*\)", "", part).strip()).strip("`*_ ")
    names = []
    if _SKILL_NAME.fullmatch(part):
        if "-" in part or (not _ORDINARY.fullmatch(part) if certain else _NAME_MARK.fullmatch(part)):
            names.append(part)
    elif certain and _LOOSE_NAME.fullmatch(part):
        names.append(part.lower().replace("_", "-"))
    if certain:
        names += [m.group(1) for m in _ENDING.finditer(part) if _free(part, m.start())]
    return names + _kinds(part, one_word=True)


def _prose_names(text):
    """Names in the prose of a pointer clause: a hyphenated word that ends its phrase with
    no article or git before it (a sentence's capital aside); a lone word after a verb, or
    opening its phrase to own or do something ("notetaker's job", "notetaker handles
    those"), when it bears a name's mark; a backticked word after a verb; and "a/the/your
    X-Y skill"."""
    text = _SENTENCE_CASE.sub(lambda m: m.group(1).lower(), text)
    names = [m.group(1) for m in _ENDING.finditer(text) if _free(text, m.start())]
    names += [m.group(1) for m in _VERB_OBJECT.finditer(text) if _NAME_MARK.fullmatch(m.group(1))]
    names += [m.group(1) for m in _BARE_OWNER.finditer(text)
              if _NAME_MARK.fullmatch(m.group(1)) and _opens(text, m.start())]
    return names + _BACKTICKED.findall(text) + _kinds(text, one_word=False)


def _clause_names(line):
    """The names a pointer clause names: its parentheses up to '. ' or ';', each part read
    by _part_names, and the prose of its sentence and the next."""
    clause = re.split(r"\.\s|;", line, maxsplit=1)[0]
    names = [n for group in _PAREN.findall(clause) for part in group.split(",")
             for n in _part_names(part, certain=False)]
    return names + _prose_names(" ".join(re.split(r"(?<=\.)\s+", line, maxsplit=2)[:2]))


def _skill_column(headers):
    """The column of a table that names skills: one whose header says skill (Skill, Skill to
    use, Which skill), or a Use, Tool or Handled by column beside a request (Ask, Need,
    When); -1 when there is none. Beside a Task or a Version, a Tool column lists programs
    ('| Lint | ruff |'), and 'How to use' is not a Use column."""
    for i, h in enumerate(headers):
        if re.search(r"\bskills?\b", h):
            return i
    if {"ask", "need", "when", "request"} & set(headers):
        for i, h in enumerate(headers):
            if h in ("use", "tool", "tools", "handled by", "handler", "owner"):
                return i
    return -1


def _pointers_read(text):
    """Every skill-shaped name a Markdown text's pointers name, once each, in order.

    The pointers read are:
      - '(→ ...)' and '(-> ...)' groups, anywhere, and a bare arrow's name (_BARE_ARROW);
      - a table's skill column (_skill_column);
      - a clause after 'not for', 'not meant/intended/designed/built/made/used/suited for',
        'out of scope' or '**Not X:**', up to the line's end, and each line of the list
        under a heading or label that says one of them ('## Not for', '**Not for:**').
    A paragraph wrapped mid-sentence reads as one line, a link as its text, CRLF as LF and
    a curly apostrophe as a straight one. Arrow groups and table cells are split on ',',
    'or' and 'and', a clause's parentheses on ',' only, and each part is read by
    _part_names; a clause's prose by _prose_names. A word read is dropped when English
    writes it itself (_english, _CLOSED) or it is a count or a version.
    Not read, by design, each with a kept green case or a reason:
      - a hyphenated word after an article ('see the release-train'), or describing a noun
        ('zip-file backups'): a name takes no article and heads its phrase;
      - a word right after 'git' ('git filter-repo'): git's own;
      - any other word after a bare arrow: the pack's flows ('backup → copy → verify');
      - a lone word in prose without a name's mark ('use rebase.', 'use jotbook.'): English
        cannot tell a mass noun from a one-word name by shape;
      - a lone word opening a sentence ('Jotbook keeps those.'): a sentence's capital and
        a product's own (Docker) look the same;
      - a Tool column beside a Task or a Version: it lists programs, not skills.
    Read, by design: a lone lowercase word alone in an arrow group or a Skill cell, unless
    its ending marks it ordinary ('(→ upstream)' reads as a name: write '(→ the upstream
    project)'); and a public tool in a pointer's slot ('use docker.', 'run `pytest`'),
    which is added to POINTER_NAMES on purpose, as git is. A review that finds a private
    name passing adds its form here with a kept red case.
    """
    text = text.replace("\r\n", "\n").replace("’", "'")
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # a Markdown link reads as its text
    text = re.sub(r"\n[ \t]+", " ", text)  # a folded frontmatter description reads as one line
    text = re.sub(r"(?<=[^\s|])\n(?=[a-z(])", " ", text)  # so does a paragraph wrapped mid-sentence
    named = [n for group in _ARROW.findall(text) for part in _PARTS.split(group)
             for n in _part_names(part, certain=True)]
    named += _BARE_ARROW.findall(text)
    lines = text.splitlines()
    col, in_table = -1, False
    for line in lines:
        if not line.lstrip().startswith("|"):
            in_table = False
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not in_table:  # a table's first row is its header
            in_table, col = True, _skill_column([c.strip("*_: ").lower() for c in cells])
        elif 0 <= col < len(cells) and cells[col].strip("-: "):
            named += [n for part in _PARTS.split(cells[col]) for n in _part_names(part, certain=True)]
    for m in _NOT_FOR.finditer(text):
        named += _clause_names(text[m.end():].split("\n", 1)[0])
    for i, line in enumerate(lines):
        if _NOT_FOR_LABEL.match(line):  # the list under it, after any blank lines, to a blank line or heading
            rest = lines[i + 1:]
            while rest and not rest[0].strip():
                rest = rest[1:]
            for item in rest:
                if not item.strip() or item.lstrip().startswith("#"):
                    break
                named += _clause_names(item)
    return list(dict.fromkeys(n for n in named if n not in _CLOSED and not _NUMBERED.fullmatch(n)
                              and not ("-" in n and _english(n))))


def _unlisted_pointers(text):
    """The names _pointers_read finds that are neither a sibling, git nor an allowed kind."""
    allowed = POINTER_NAMES | POINTER_KINDS
    return [n for n in _pointers_read(text) if n not in allowed]


# Realistic skill prose that points at no skill outside the pack: the fifth v1.3
# review's paragraphs (all but its '(→ upstream)', a limit named in _pointers_read),
# then fresh ones naming public tools and ordinary hyphenated words. Each must read
# nothing; a grammar change that reads one of them is a false red.
REALISTIC_PROSE = (
    # the fifth v1.3 review
    "description: >-\n  Synk182 compares two copies of a project and applies what you approve.\n"
    "  Not for merging branches (use git). A command-line tool that never writes\n  until you approve a plan.",
    "Not for secrets or credentials; use a third-party tool for those.",
    "Not for licence checks. Use an open-source tool such as licensee.",
    "Not for three-way merges; git's built-in tool does those.",
    "Not for CI pipelines. Each engine is a stand-alone tool.",
    "Not for scripting; it is not a general-purpose helper.",
    "Not for IDE integration (that is a first-party plugin's job).",
    "**Not Solid8:** archiving to tape. It is a cross-platform tool, nothing more.",
    "Not for legal review; use a domain-specific skill.",
    "Not for the back-end or the front-end; only the docs.",
    "Not for the command-line. Use the engine from a script.",
    "Not for live copies; use a dry-run first.",
    "Not for history rewrites; use a cherry-pick or a rebase.",
    "Not for one-off edits via copy-paste.",
    "Not for onboarding; see the write-up in docs/.",
    "Not for scheduling; see the follow-up.",
    "Not for the day-to-day, only releases.",
    "Not for the pull-request; see git.",
    "Not for the post-mortem; DevCom5 writes those.",
    "The engine is not for the faint-hearted.",
    "Not for the end-user's machine; that copy is theirs.",
    "Not for hot-fixes; on-call handles those.",
    "Not for cleanup; a follow-up covers that.",
    "Not for merges in a work-tree.",
    "| x | merges (→ git cherry-pick) |",
    "| x | later (→ a follow-up) |",
    "| x | notes (→ by hand, copy-paste) |",
    "changed since the plan → re-plan.",
    "verify fails → roll-back; verify holds → log",
    "review → sign-off.",
    "scan → compare → plan → back-up → apply → verify.",
    "| Tool | Version |\n|---|---|\n| python | 3.10+ |\n| git | any |",
    "| Tools | Purpose |\n|---|---|\n| ruff | lint |\n| pytest | tests |",
    "| Task | Tool |\n|---|---|\n| Lint | ruff |\n| Diff | git |\n| Merge | by hand |",
    "Not for a shared copy; use yours instead.",
    "Not for both copies; use either for the plan.",
    "Not for writes; it is a read-only tool.",
    "Not for a first run; run the dry-run first.",
    "Not for releases; ask a co-maintainer.",
    "Not for edits in the sub-folder.",
    "Not for parsing; that is a lower-level tool's job.",
    "Not for the high-level; see the low-level.",
    "Not for bundles. Each skill is a self-contained tool.",
    "Not for frameworks (a drop-in helper).",
    "Not for the long-term; use git.",
    "Not for repeats; use a one-off.",
    "Not for the well-known cases.",
    "Not for the end-to-end; only unit checks.",
    "write → read-back.",
    # fresh, for the fix of that review
    "description: >-\n  Tidies a docs folder before a release. Not for code formatting (Prettier and Black\n"
    "  already own that) or for spell-checking, which codespell does well.",
    "Not for secrets. Keep tokens in a password manager such as Bitwarden or KeePassXC, never in a plan file.",
    "Not for real-time sync; this is a point-in-time comparison that runs on demand.",
    "Not for large binaries (use Git LFS or an object store).",
    "Not for notebooks: nbdime understands .ipynb diffs and merges far better than a line-based tool.",
    "| Tool | Minimum | Why |\n|---|---|---|\n| python | 3.10 | the engines |\n| git | 2.30 | history checks |\n"
    "| gh | 2.40 | optional, for release notes |",
    "Flow: scan → dry-run → sign-off → apply → read-back → log.",
    "Not for merge conflicts → resolve them in your editor or with git mergetool.",
    "Not for cross-repo refactors; see the follow-up in docs/ROADMAP.md.",
    "Not for pre-commit hooks. Wire the engine into pre-commit yourself if you want it on every commit.",
    "Not for editing YAML by hand; yq and a schema-aware editor do that job.",
    "Not for Markdown lint (markdownlint and Vale are the usual picks).",
    "Not for the day-to-day churn of a work-in-progress branch, only for release copies.",
    "Not for one-way mirrors; rsync or robocopy /MIR is simpler for that.",
    "Not for anything user-facing: the engine writes plain-text reports for a human to read.",
    "Not for a hand-off between two people; write a short hand-over note instead.",
    "Not for CI. The engines are stand-alone scripts a workflow can call, but nothing here sets one up.",
    "Not for copy-paste edits. Retype the change, or apply a proper patch with git apply.",
    "Not for long-running jobs; each run is a single pass that exits when it is done.",
    "Not for multi-root workspaces yet (one root per run).",
    "Not for sub-modules; run the engine inside each sub-module on its own.",
    "Not for lock files (package-lock.json, poetry.lock); regenerate them with the package manager.",
    "Not for time-stamped backups (the engine keeps its own under ARCHIVE/).",
    "Not for code review. A pull-request template and a second pair of eyes do more than any engine.",
    "Not for rewriting history; git rebase and git filter-repo exist for that.",
    "Not for images; oxipng and svgo shrink those without touching the docs.",
    "Not for anything outside the two folders you name: no network calls, no auto-updates, no telemetry.",
    "Not for non-UTF-8 files; the engine reads UTF-8 and skips the rest with a note.",
    "Not for a shared drive without asking: check with the copy's co-owner first.",
    "**Not Synk182:** a one-off rename (do it by hand), or a follow-up merge (→ git).",
    "Not for scripted runs in a read-only container; --apply needs write access.",
    "Not for large monorepos: scan time grows with file count, so point it at a sub-folder.",
    "If the premise changed since the plan → re-plan. If a verify fails → roll-back.",
    "Not for notes → use your own note-taking app.",
    "Not for tests; pytest and coverage.py already cover that.",
    "Not for Docker images or other build artefacts (see the Dockerfile's own docs).",
    "| When | Use |\n|---|---|\n| Two copies drifted | Synk182 |\n| A branch merge | git |\n| A decision to log | DevCom5 |",
    "Not for built-in help; run the engine with --help for that.",
    "Not for check-ins to main: the engine never commits, pushes or tags.",
    "Not for high-stakes copies without a backup; take a snapshot first.",
    "| Ask | Skill |\n|---|---|\n| Two copies drifted | Synk182 |\n| Anything else | none |\n| Retyping a list | by hand |",
    "Not for lint (ruff does that), nor for type checks, which mypy or pyright handle.",
    "Not suited for huge repos: a full re-scan of 100k files takes a while.",
    "Out of scope: GitHub issues, pull-request reviews and release tagging (the gh CLI does those).",
    "Not for side-by-side diffs; a GUI such as Meld or Beyond Compare shows those better.",
    "Not for the first run on a new machine (do a dry-run, then a read-back).",
    "Not for opt-in telemetry or crash reports; the engines send nothing anywhere.",
    "Not for key-value stores or SQLite files: those are binary, and the engine skips them.",
    "Not for a to-do list. Keep one in your issue tracker (GitHub Issues, Jira, Linear).",
    "Not for formatting; use black.",
    "Not for side-by-side merges; use meld or kdiff3 instead.",
    "Not for containers; run podman.",
    "## Out of scope\n\n- Branch merges (git)\n- Anything on a network drive (copy it local first)\n- A follow-up release",
    "Not for notes; use care. Not for merges; use rebase, with judgement, and sparingly.",
    # each listed English compound where a pointer is read, so every entry earns its place
    "Not for fixes that are ad-hoc, best-effort or brute-force.",
    "Out of scope: renaming between camel-case, snake-case and kebab-case.",
    "Not for review work (code-review, peer-review, fact-check, spell-check); ask a person.",
    "Not for everyday lists (check-box, to-do, how-to, must-have); keep those in your issue tracker.",
    "Not for git plumbing (cherry-pick, merge-request, pull-request, work-tree); git and your host cover it.",
    "Not for the repository's layout (code-base, file-system, file-name, hard-link).",
    "Not for data questions (data-set, key-value, plain-text, rich-text); ask whoever owns the data.",
    "Out of scope: release plumbing (tool-chain, web-hook, end-point, front-end, command-line).",
    "Not for tests (unit-test, load-test, sanity-check, dry-run): run the project's own suite.",
    "Not for writing docs (man-page, run-book, front-matter, life-cycle).",
    "Not for chasing bugs (dead-lock, dead-end, side-effect, round-trip, hot-fix).",
    "Not for scenario planning (what-if, real-world, work-flow); bring those to the team.",
    "Not for spelling questions (end-user, go-to, wild-card, no-op, time-stamp, copy-paste); follow the house style guide.",
)


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
        # the fifth v1.3 review). The engines' pruning is driven in each engine's own
        # case; here the lifecycle rule must name both forms.
        protocol = (ROOT / "docs/TRIFECTA.md").read_text(encoding="utf-8")
        rule = protocol[protocol.index("**Lifecycle:**"):].split("\n\n", 1)[0]
        self.assertIn("with an offset or `Z`", rule)
        self.assertIn("read as local time", rule)

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
        # Break it catches: "not for X, use Y" where Y is neither in the pack nor
        # public, so a reader's agent is sent nowhere (found by the v1.2 review).
        # An allow-list, so the test itself names no skill it keeps out; run with
        # TRIAD_ROOT on commit a9f9b3a it goes red on all four pointers that
        # review found.
        for p in sorted(ROOT.rglob("*.md")):
            if ".git" in p.parts:
                continue
            with self.subTest(file=p.relative_to(ROOT).as_posix()):
                self.assertEqual(_unlisted_pointers(p.read_text(encoding="utf-8")), [],
                                 "not in the pack and not public; describe the work instead")

    def test_pointer_check_goes_red_on_every_form_it_reads(self):
        # The probe for the case above, in made-up names: each pointer form goes
        # red on a skill outside the pack, and stays green on the pack's names,
        # git, verafox behind a link, a described kind of work, and parentheses
        # that name nothing. The third v1.3 review found a first-word check passed
        # "(→ the private-notes skill)", "use X", "->" and a lowercase table
        # header, and flagged "(→ GitHub)", "(see above)" and a 3-column table.
        red = {"Not for diagrams (private-helper).": ["private-helper"],
               "| x | redundancy (→ internal-notes) |": ["internal-notes"],
               "**Not Synk:** repo rules (git, house-rules), the rest": ["house-rules"],
               "| Ask | Skill |\n|-----|-------|\n| Tidy notes | memo-sweeper |": ["memo-sweeper"],
               "description: >-\n  Does things. Not for proofs\n  (github-helper).": ["github-helper"],
               "| x | notes (→ the private-notes skill) |": ["private-notes"],
               "| x | notes (→ a private-notes skill) |": ["private-notes"],
               "| x | notes (→ in private-notes) |": ["private-notes"],
               "| x | notes (→ your private-notes skill) |": ["private-notes"],
               "| x | notes (→ `private-notes`) |": ["private-notes"],
               "| x | notes (→ Solid8 or private-notes) |": ["private-notes"],
               "| x | notes (-> private-notes) |": ["private-notes"],
               "| x | notes (→ notetaker) |": ["notetaker"],
               "Not for notes (the private-notes skill).": ["private-notes"],
               "Not for notes (see private-notes).": ["private-notes"],
               "Not for notes (private-notes (v2)).": ["private-notes"],
               "Not for notes; use private-notes instead.": ["private-notes"],
               "Not for notes. Use notetaker for those.": ["notetaker"],
               "**Not Synk:** notes, use private-notes for those": ["private-notes"],
               "| ask | skill |\n|---|---|\n| Notes | private-notes |": ["private-notes"],
               "| Ask | Skill | Why |\n|---|---|---|\n| Notes | notetaker | because |": ["notetaker"],
               "| Ask | Skill |\n|---|---|\n| Notes | [private-notes](https://example.org) |": ["private-notes"],
               # the fourth v1.3 review: the pack's own "X tool" form, verbs beyond "use",
               # a possessive or a subject, names written loosely, other table headers,
               # and a clause wrapped onto the next line
               "| x | notes (→ your private-notes tool) |": ["private-notes"],
               "| x | notes (→ the private-notes plugin) |": ["private-notes"],
               "Not for notes (a private-notes helper).": ["private-notes"],
               "Not for notes; see private-notes.": ["private-notes"],
               "Not for notes; load private-notes first.": ["private-notes"],
               "Not for notes: private-notes handles those.": ["private-notes"],
               "Not for notes (that is private-notes's job).": ["private-notes"],
               "| x | notes (→ Private-Notes), memos (→ memo_sweeper) |": ["private-notes", "memo-sweeper"],
               "| Task | Skill |\n|---|---|\n| Notes | private-notes |": ["private-notes"],
               "| Need | Use |\n|---|---|\n| Notes | private-notes |": ["private-notes"],
               "| Ask | Tool |\n|---|---|\n| Notes | private-notes |": ["private-notes"],
               "Not for notes\n(private-notes).": ["private-notes"],
               "Not for notes → private-notes\n- memos -> memo-sweeper.": ["private-notes", "memo-sweeper"]}
        for text, names in red.items():
            with self.subTest(red=text):
                self.assertEqual(_unlisted_pointers(text), names)
        green = ("Not for proofs ([verafox](https://example.org), in The Proof Pack), or diagrams "
                 "(a diagramming skill). Other text (not a pointer).",
                 "| x | redundancy (→ Solid8), merges (→ git), rules (→ your repository's own rules) |",
                 "| x | memory (→ your memory-consolidation tool), proofs (→ verafox Mutate, in The Proof Pack) |",
                 "| x | issues (→ GitHub), CI (→ GitHub Actions), merges (→ git's own merge) |",
                 "| x | proofs (→ The Proof Pack), comms (→ DevCom5 Scribe), copies (→ Synk182's engine) |",
                 "| Ask | Skill | Why |\n|---|---|---|\n| Two copies | Synk182 | because |\n"
                 "| Prove it | verafox (The Proof Pack) | it is public |",
                 "**Not Synk:** repo rules (git, a repo-rules skill); use git for merges.",
                 "Not for merges (e.g., branch merges).", "Not for merges (see above).",
                 "Not for merges (that is Synk182's job).", "Not for merges (v2 and later).",
                 "Not for notes (or diagrams).", "Not for notes (and diagrams).", "Not for big files (over 10 MB).",
                 "Not for merging (one copy wins).", "Not for notes (\"memory\").", "Not for proofs (Verafox).",
                 "Not for notes (which stay).", "Not for notes (this one); use it elsewhere.",
                 "Byte-comparing docs (use section-aware diff).",
                 "| x | merges (→ git's own three-way merge) |", "Not for merges (in read-only mode).",
                 "Not for merges; use section-aware diff instead.", "Not for merges; use a diff tool.",
                 "Formerly: v1.2 (it is not for beside Solid8; freeware) → v1.3 (2026-09-30: fixes).",
                 # the fourth v1.3 review: words that fill a pointer's slot but name no skill,
                 # a "How to use" column, and the pack's flows written with bare arrows
                 "Not for merges; use caution.", "Not for merges. Use discretion.", "**Not yet:** use caution.",
                 "Not for writes (read-only).", "Not for merges (one-off).", "Not for merges (optional).",
                 "Not for builds (x64).", "**Not Solid8:** two copies (2).", "Not for notes (via drag-and-drop).",
                 "| x | mail (→ e-mail), files (→ your file-system), merges (→ a three-way merge) |",
                 "| Ask | Skill |\n|---|---|\n| Plain edits | none |\n| Retyping | manual |",
                 "| Host | Works? | How to use |\n|---|---|---|\n| Any | yes | drop-in |",
                 "Low confidence → suggest skip-to-action; both → user-unique + working-unique → merged.",
                 "backup → copy or merged write → verify (six layers) → roll back failures → log\n"
                 "Config-first → Doc-reality cross-check → the new docs are doc-worthy.")
        for text in green:
            with self.subTest(green=text):
                self.assertEqual(_unlisted_pointers(text), [])

    def test_every_allowed_kind_is_read_from_the_pack(self):
        # Break it catches: a kind in POINTER_KINDS that the check never reads, so a
        # private name in its slot passes unseen: "(→ your memory-consolidation
        # tool)", the pack's own form, was read as nothing (found by the fourth
        # v1.3 review). Each allowed kind must be read from the pack's own files.
        read = {n for p in ROOT.rglob("*.md") if ".git" not in p.parts
                for n in _pointers_read(p.read_text(encoding="utf-8"))}
        for kind in sorted(POINTER_KINDS):
            with self.subTest(kind=kind):
                self.assertIn(kind, read)

    def test_pointer_check_reads_the_fifth_reviews_forms(self):
        # Break it catches: a pointer the check passed at 1ce715f (the fifth v1.3
        # review): an em dash or a colon, verbs and prepositions beyond the first eight,
        # a "Not for" heading, "Out of scope:", more table headers, a version or italics
        # around a name, a name opening a sentence or owning with a curly apostrophe, and
        # a one-word name after a verb, as a possessive or as a subject.
        red = {"Not for notes — private-notes.": ["private-notes"],
               "Not for notes: private-notes.": ["private-notes"],
               "Not for notes; leave those to private-notes.": ["private-notes"],
               "Not for notes; those belong to private-notes.": ["private-notes"],
               "Not for notes; open private-notes.": ["private-notes"],
               "Not for notes; prefer private-notes.": ["private-notes"],
               "Not for notes; install private-notes first.": ["private-notes"],
               "Not for notes; switch to private-notes.": ["private-notes"],
               "Not for notes; reach for private-notes.": ["private-notes"],
               "Not for notes; that is what private-notes is for.": ["private-notes"],
               "Not for notes; private-notes exists for that.": ["private-notes"],
               "Not for notes; do those with private-notes.": ["private-notes"],
               "Not for notes; go through private-notes.": ["private-notes"],
               "Not for notes; take those from private-notes.": ["private-notes"],
               "Not for notes; those are done by private-notes.": ["private-notes"],
               "Not for notes; hand those off to private-notes.": ["private-notes"],
               "Not for notes; delegate to private-notes.": ["private-notes"],
               "Not for notes; defer to private-notes.": ["private-notes"],
               "Not for notes → use private-notes.": ["private-notes"],
               "Not for notes: `private-notes`.": ["private-notes"],
               "Not for notes. Private-notes keeps those.": ["private-notes"],
               "Not for notes (that is private-notes’s job).": ["private-notes"],
               "Not meant for notes (private-notes).": ["private-notes"],
               "## Not for\n\n- Notes (private-notes)\n- Merges (git)": ["private-notes"],
               "**Not for:**\n- memos (memo-sweeper)": ["memo-sweeper"],
               "Out of scope: notes (private-notes).": ["private-notes"],
               "| Ask | Handled by |\n|---|---|\n| Notes | private-notes |": ["private-notes"],
               "| Need | Skill to use |\n|---|---|\n| Notes | private-notes |": ["private-notes"],
               "| Ask | Which skill |\n|---|---|\n| Notes | private-notes |": ["private-notes"],
               "| When | Use |\n|---|---|\n| Notes | private-notes |": ["private-notes"],
               "| Ask | Skill: |\n|---|---|\n| Notes | private-notes |": ["private-notes"],
               "| Ask | Skill |\n|---|---|\n| Notes | private-notes v2 |": ["private-notes"],
               "| Ask | Skill |\n|---|---|\n| Notes | _private-notes_ |": ["private-notes"],
               "| x | notes (→ private-notes v2) |": ["private-notes"],
               "| Ask | Skill |\n|---|---|\n| Notes | jotbook v2 |": ["jotbook"],
               "| x | notes (→ jotbook 2.1) |": ["jotbook"],
               "Not for notes; use notetaker.": ["notetaker"],
               "Not for notes; use notes2go.": ["notes2go"],
               "Not for notes; that is notetaker's job.": ["notetaker"],
               "Not for notes; notetaker handles those.": ["notetaker"]}
        for text, names in red.items():
            with self.subTest(red=text):
                self.assertEqual(_unlisted_pointers(text), names)
        for text in ("Not for merges; use caution.", "Not for merges. Use discretion.", "Not for notes; use care.",
                     "Not for merges; use rebase.", "Not for merges; use judgement.", "Not for merges; use sparingly."):
            with self.subTest(green=text):
                self.assertEqual(_unlisted_pointers(text), [])

    def test_pointer_check_reads_nothing_in_realistic_prose(self):
        # Break it catches: ordinary English read as a skill name. At 1ce715f, 43 of the
        # fifth review's 50 realistic paragraphs went red (third-party, dry-run,
        # follow-up, a '| Tool | Version |' table, 'use yours instead').
        for text in REALISTIC_PROSE:
            with self.subTest(text=text):
                self.assertEqual(_unlisted_pointers(text), [])

    def test_english_forms_are_known_without_being_listed(self):
        # Break it catches: an English compound read as a name because nobody listed it.
        # None of these is in _ENGLISH_COMPOUNDS or in the realistic prose, and each sits
        # alone in an arrow group, the slot that reads any hyphenated word, so each is
        # known by its form: a prefix, particle or number first, a particle last, a
        # linker inside, a participle or a modifier head last, a one-letter or digit part.
        held_out = ("re-run", "co-author", "sub-agent", "self-hosted", "non-blocking", "pre-release",
                    "post-merge", "multi-agent", "cross-reference", "sign-up", "log-in", "add-ons", "hand-offs",
                    "two-pass", "one-shot", "peer-to-peer", "up-to-date", "hand-written", "hard-coded",
                    "long-lived", "thread-safe", "context-aware", "platform-agnostic", "user-friendly",
                    "server-side", "compile-time", "sha-256", "x-ray", "record-keeping", "mobile-first")
        for word in held_out:
            with self.subTest(word=word):
                self.assertNotIn(word, _ENGLISH_COMPOUNDS)
                self.assertFalse(any(word in text for text in REALISTIC_PROSE))
                self.assertEqual(_unlisted_pointers(f"| x | y (→ {word}) |"), [])

    def test_english_compounds_list_holds_only_what_no_form_marks(self):
        # Keeps _ENGLISH_COMPOUNDS the one place for English's unmarked compounds: an
        # entry a form already marks is dead weight, and an entry that is an allowed
        # name or kind would hide a pointer.
        for word in sorted(_ENGLISH_COMPOUNDS):
            with self.subTest(word=word):
                self.assertRegex(word, r"^[a-z]+(?:-[a-z]+)+$")
                self.assertFalse(_english_by_form(word), "a form already marks it")
                self.assertNotIn(word, POINTER_NAMES | POINTER_KINDS)

    def test_english_compounds_list_holds_only_what_the_corpus_needs(self):
        # Keeps _ENGLISH_COMPOUNDS from growing on a guess: every entry must be needed by
        # a paragraph of REALISTIC_PROSE, which reads a name without it. An entry is
        # added with the realistic paragraph that needs it, and removing one is caught.
        global _ENGLISH_COMPOUNDS
        full = _ENGLISH_COMPOUNDS
        try:
            for word in sorted(full):
                with self.subTest(word=word):
                    _ENGLISH_COMPOUNDS = full - {word}
                    self.assertTrue(any(word in _unlisted_pointers(p) for p in REALISTIC_PROSE),
                                    "no realistic paragraph needs it")
        finally:
            _ENGLISH_COMPOUNDS = full

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
