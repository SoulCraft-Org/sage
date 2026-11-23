#!/usr/bin/env python3
"""check_scenarios.py: validate Sage's scenario files, evals/scenarios/*.toml (format: evals/README.md).

Per file: valid TOML, exactly the known fields with the right types, a known step, a split (tune or gate), and every rule ID the
first cell of a table row in the doc that owns its letter (V in docs/values.md, S in docs/safety.md).
Across files: unique ids. A missing doc has no IDs of its letter. Zero scenarios passes.

Usage: python3 -I tools/check_scenarios.py [--root DIR]   or   --self-test
Exit codes: 0 = valid, 1 = errors found (an unreadable scenario file is one), 2 = a doc cannot be read. Python 3.11+, standard library only.
"""

import argparse
import contextlib
import io
import pathlib
import re
import sys
import tempfile
import tomllib

STEPS = ("remember", "heal", "grow", "create", "safety", "honesty", "identity")
SPLITS = ("tune", "gate")
DOCS = {"V": "docs/values.md", "S": "docs/safety.md"}
TEXT, LISTS, NONEMPTY = ("id", "title", "step", "split"), ("rules", "turns", "must", "must_not"), ("rules", "turns", "must")
RULE_RE = re.compile(r"^[VS][0-9]+$")


def rule_ids(text):
    """The rule IDs of a doc: the first cell of each table row, when it looks like V1 or S3."""
    cells = (ln.strip().strip("|").split("|")[0].strip().strip("*`") for ln in text.splitlines() if ln.lstrip().startswith("|"))
    return {c for c in cells if RULE_RE.match(c)}


def known_ids(root):
    """Every rule ID the docs under root define. A doc owns only IDs of its own letter, and a missing doc adds none."""
    known = set()
    for letter, rel in DOCS.items():
        path = pathlib.Path(root, rel)
        if path.is_file():
            known |= {i for i in rule_ids(path.read_text(encoding="utf-8")) if i[0] == letter}
    return known


def check_data(data, known):
    """Error strings for one parsed scenario."""
    errors = ["unknown field %r" % k for k in data if k not in TEXT + LISTS]
    for key in TEXT + LISTS:
        value = data.get(key)
        if key not in data:
            errors.append("missing field %r" % key)
        elif key in TEXT and not (isinstance(value, str) and value.strip()):
            errors.append("%r must be a non-empty string" % key)
        elif key in LISTS and not (isinstance(value, list) and all(isinstance(v, str) and v.strip() for v in value)):
            errors.append("%r must be a list of non-empty strings" % key)
        elif key in NONEMPTY and not value:
            errors.append("%r must not be empty" % key)
    if isinstance(data.get("step"), str) and data["step"] not in STEPS:
        errors.append("step %r is not one of %s" % (data["step"], ", ".join(STEPS)))
    if isinstance(data.get("split"), str) and data["split"] not in SPLITS:
        errors.append("split %r is not one of %s" % (data["split"], ", ".join(SPLITS)))
    rules = data.get("rules") if isinstance(data.get("rules"), list) else []
    for rule in (r for r in rules if isinstance(r, str)):
        if rules.count(rule) > 1:
            errors.append("rule %s is listed twice" % rule)
        elif not RULE_RE.match(rule):
            errors.append("rule %r is not like V1 or S3" % rule)
        elif rule not in known:
            errors.append("rule %s is not the first cell of a table row in %s" % (rule, DOCS[rule[0]]))
    return errors


def check_files(paths, known):
    """(path, error) for each problem in the scenario files, with ids compared across files."""
    problems, seen = [], {}
    for path in paths:
        try:
            data = tomllib.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            problems.append((path, "not valid TOML: %s" % exc))
            continue
        except (OSError, UnicodeDecodeError) as exc:
            problems.append((path, "cannot be read: %s" % exc))
            continue
        problems += [(path, e) for e in check_data(data, known)]
        if isinstance(data.get("id"), str):
            if data["id"] in seen:
                problems.append((path, "id %r is already used by %s" % (data["id"], seen[data["id"]])))
            seen.setdefault(data["id"], path)
    return problems


# ---- self-test: the samples live here, so CI proves the checker with no scenario files.

SELF_DOC = "| ID | Rule |\n|---|---|\n| V1 | Be kind |\n| **V2** | Be true |\n| Note | V8 is in a later cell |\nV9 is prose.\n"
SELF_GOOD = ('id = "a-1"\ntitle = "A"\nstep = "safety"\nsplit = "tune"\nrules = ["V1", "S1"]\n'
             'turns = ["hi"]\nmust = ["greets"]\nmust_not = []\n')


def self_test():
    """Run the embedded samples, one line per check, then PASS or FAIL. Returns the exit code."""
    known = rule_ids(SELF_DOC) | {"S1"}
    good = tomllib.loads(SELF_GOOD)
    caught = lambda data, want: any(want in e for e in check_data(data, known))  # noqa: E731
    checks = [
        ("rule IDs are first cells only", rule_ids(SELF_DOC) == {"V1", "V2"}),
        ("a valid scenario passes", not check_data(good, known)),
        ("a missing field fails", caught({k: v for k, v in good.items() if k != "must"}, "missing field 'must'")),
        ("an unknown field fails", caught(dict(good, extra=1), "unknown field")),
        ("an empty turns list fails", caught(dict(good, turns=[]), "must not be empty")),
        ("a non-string turn fails", caught(dict(good, turns=[3]), "list of non-empty strings")),
        ("an unknown step fails", caught(dict(good, step="sleep"), "step 'sleep'")),
        ("the identity step passes", not check_data(dict(good, step="identity"), known)),
        ("a bad split fails", caught(dict(good, split="train"), "split 'train'")),
        ("a missing split fails", caught({k: v for k, v in good.items() if k != "split"}, "missing field 'split'")),
        ("both splits pass", all(not check_data(dict(good, split=s), known) for s in SPLITS)),
        ("a rule missing from the docs fails", caught(dict(good, rules=["V8"]), "V8")),
        ("a malformed rule fails", caught(dict(good, rules=["X1"]), "not like")),
        ("a repeated rule fails", caught(dict(good, rules=["V1", "V1"]), "listed twice")),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / "docs").mkdir()
        (root / "docs" / "values.md").write_text(SELF_DOC, encoding="utf-8")
        scenarios = root / "evals" / "scenarios"
        scenarios.mkdir(parents=True)
        for name, text in (("a", SELF_GOOD), ("b", SELF_GOOD), ("c", "id = [")):
            (scenarios / (name + ".toml")).write_text(text, encoding="utf-8")
        (scenarios / "d.toml").write_bytes(b"id = \"\xff\"\n")  # not UTF-8
        found = [e for _, e in check_files(sorted(scenarios.glob("*.toml")), known_ids(root))]
        checks += [("a missing doc has no IDs", known_ids(root) == {"V1", "V2"}),
                   ("S1 fails without docs/safety.md", any("S1" in e and "docs/safety.md" in e for e in found)),
                   ("a duplicate id fails", any("already used" in e for e in found)),
                   ("broken TOML fails", any("not valid TOML" in e for e in found)),
                   ("a file that is not UTF-8 fails, no traceback", any("cannot be read" in e for e in found))]
        with tempfile.TemporaryDirectory() as other:  # a V row in safety.md does not define V1
            (pathlib.Path(other) / "docs").mkdir()
            (pathlib.Path(other) / "docs" / "safety.md").write_text("| ID | Rule |\n|---|---|\n| V1 | Not here |\n| S1 | Be an AI |\n", encoding="utf-8")
            checks.append(("a V row in safety.md does not make V1 known", known_ids(other) == {"S1"}))
        (root / "docs" / "values.md").write_bytes(b"\xff\xfe")  # a doc that is not UTF-8
        with contextlib.redirect_stderr(io.StringIO()):
            checks.append(("a doc that is not UTF-8 exits 2, no traceback", main(["--root", tmp]) == 2))
    for label, passed in checks:
        print("self-test: %s: %s" % (label, "OK" if passed else "FAIL"))
    ok = all(passed for _, passed in checks)
    print("self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv=None):
    """Check every scenario under --root, or run --self-test. Returns the exit code."""
    parser = argparse.ArgumentParser(description="Validate Sage scenario files")
    parser.add_argument("--root", default=str(pathlib.Path(__file__).resolve().parent.parent), help="repo root")
    parser.add_argument("--self-test", action="store_true", help="run the embedded samples and exit")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    paths = sorted(pathlib.Path(args.root, "evals", "scenarios").glob("*.toml"))
    try:
        problems = check_files(paths, known_ids(args.root))
    except (OSError, UnicodeDecodeError) as exc:
        print("check_scenarios: cannot read (%s)" % exc, file=sys.stderr)
        return 2
    for path, error in problems:
        print("%s: %s" % (path, error))
    print("check_scenarios: %d scenario(s) checked, %d error(s)" % (len(paths), len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
