"""Version 1.1 | Deps: stdlib; Skillshaper's validate_skill.py when present | Parent: The Triad (DevCom5 1.3, Synk182 3.3, Solid8 1.3) | Path: tests | Filename: test_triad.py | Created: 2026-09-30 01:12 ET - kept tests for the pack: the two engines, the three skill folders, and the pack's own ratchets. | Updated: 2026-09-30 04:05 ET - v1.3: red-first cases from the v1.2 review (bounded plan paths, stale plans, wrong-typed PULSE fields, CLI messages, copy numbers, sprawl across folders, pointer and version ratchets); comments read for a public reader; both engines checked for personal paths.

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
from pathlib import Path

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
RETIRED_POINTERS = ("knowledge-query", "archify", "mk-repo-rules", "consolidate-memory")
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
        for p in sorted(ROOT.rglob("*.md")):
            if ".git" in p.parts:
                continue
            with self.subTest(file=p.relative_to(ROOT).as_posix()):
                text = p.read_text(encoding="utf-8")
                for name in RETIRED_POINTERS:
                    self.assertNotIn(name, text, f"{name} is not public; describe the work instead")

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
