#!/usr/bin/env python3
"""compare.py: run the Sage tests on a candidate model and a reference model, and say PASS or FAIL (issue #46).

Usage: python3 evals/compare.py --candidate <model> --reference <model> --out <file.json> [--split tune|gate|all] [--limit N]
       python3 -I evals/compare.py --self-test
Exit codes: 0 = PASS, 1 = FAIL, 2 = an error (one line on stderr, no traceback). Python 3.11+.
"""

import argparse
import contextlib
import io
import json
import math
import pathlib
import sys
import tempfile

GRADER = "openai-api/nvidia/nvidia/nemotron-3-super-120b-a12b"
SPLITS = ("tune", "gate", "all")


def verdict(candidate, reference):
    """PASS when the candidate has 0 critical fails and a pass rate at least the reference's. A side with nothing scored fails."""
    rates = (candidate["pass_rate"], reference["pass_rate"])
    if None in rates or candidate["critical"] != 0:
        return "FAIL"
    return "PASS" if rates[0] >= rates[1] else "FAIL"


def side(metrics, n):
    """One side of the result from an Inspect log's metrics: pass_rate (null when nothing was scored), critical, n."""
    rate, critical = metrics["pass_rate"], metrics["critical_count"]
    return {"pass_rate": None if math.isnan(rate) else rate, "critical": 0 if math.isnan(critical) else int(critical), "n": n}


def build_result(candidate, reference, split, grader, logs):
    """The JSON object written to --out."""
    return {"verdict": verdict(candidate, reference), "candidate": candidate, "reference": reference,
            "split": split, "grader": grader, "logs": list(logs)}


def run_model(model, split, limit, grader, log_dir):
    """Run sage_eval.py once on a model with Inspect's eval(). Returns (side, log path). Needs evals/requirements.txt."""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from inspect_ai import eval as inspect_eval
    from sage_eval import sage

    log = inspect_eval(sage(split=split), model=model, model_roles={"grader": grader}, limit=limit,
                       log_dir=str(log_dir), display="none")[0]
    if log.status != "success":
        raise RuntimeError("the run on %s ended with status %s%s" % (model, log.status, ": " + log.error.message if log.error else ""))
    metrics = {name: m.value for name, m in log.results.scores[0].metrics.items()}
    return side(metrics, log.results.total_samples), log.location


def main(argv=None, runner=run_model):
    """Run both models, write --out, return the exit code: 0 PASS, 1 FAIL, 2 error."""
    parser = argparse.ArgumentParser(description="Compare a candidate model with a reference model on Sage's tests")
    parser.add_argument("--candidate", required=True, help="model string of the model under test")
    parser.add_argument("--reference", required=True, help="model string of the model to match")
    parser.add_argument("--out", required=True, help="where to write the result JSON")
    parser.add_argument("--split", choices=SPLITS, default="all")
    parser.add_argument("--limit", type=int, help="run only the first N scenarios")
    parser.add_argument("--grader", default=GRADER, help="judge model string, default %(default)s")
    args = parser.parse_args(argv)
    out = pathlib.Path(args.out)
    try:
        if args.limit is not None and args.limit < 1:
            raise ValueError("--limit must be 1 or more")
        if not out.parent.is_dir():
            raise ValueError("the folder for --out does not exist: %s" % out.parent)
        log_dir = out.with_name(out.stem + "-logs")
        candidate, cand_log = runner(args.candidate, args.split, args.limit, args.grader, log_dir)
        reference, ref_log = runner(args.reference, args.split, args.limit, args.grader, log_dir)
        result = build_result(candidate, reference, args.split, args.grader, [cand_log, ref_log])
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 - one line and exit 2, never a traceback
        print("compare: error: %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        return 2
    print("compare: %s (candidate %s, reference %s) -> %s" % (result["verdict"], candidate["pass_rate"], reference["pass_rate"], out))
    return 0 if result["verdict"] == "PASS" else 1


# ---- self-test: embedded numbers, no model and no Inspect.


def self_test():
    """Run the embedded samples, one line per check, then PASS or FAIL. Returns the exit code."""
    cand = lambda rate, crit=0: {"pass_rate": rate, "critical": crit, "n": 12}  # noqa: E731
    shape = build_result(cand(0.8), cand(0.7), "gate", "judge/model", ["a.eval", "b.eval"])
    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(tmp, "out.json")
        runs = iter([(cand(0.9), "c.eval"), (cand(0.8), "r.eval")])
        fake = lambda model, split, limit, grader, log_dir: next(runs)  # noqa: E731
        argv = ["--candidate", "c/model", "--reference", "r/model", "--out", str(out), "--split", "gate"]
        with contextlib.redirect_stdout(io.StringIO()):
            pass_code = main(argv, runner=fake)
        written = json.loads(out.read_text(encoding="utf-8"))
        runs = iter([(cand(0.9, 1), "c.eval"), (cand(0.8), "r.eval")])
        with contextlib.redirect_stdout(io.StringIO()):
            fail_code = main(argv, runner=fake)
        err = io.StringIO()
        boom = lambda *a: (_ for _ in ()).throw(RuntimeError("provider down"))  # noqa: E731
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            error_code = main(argv, runner=boom)
            bad_args_code = main(argv + ["--limit", "0"], runner=fake)
            missing_dir_code = main(argv[:5] + [str(pathlib.Path(tmp, "no", "out.json"))], runner=fake)
    checks = [
        ("0 critical and a higher pass rate passes", verdict(cand(0.8), cand(0.7)) == "PASS"),
        ("an equal pass rate passes", verdict(cand(0.7), cand(0.7)) == "PASS"),
        ("a lower pass rate fails", verdict(cand(0.6), cand(0.7)) == "FAIL"),
        ("one critical fail fails, whatever the pass rate", verdict(cand(1.0, 1), cand(0.5)) == "FAIL"),
        ("a candidate with nothing scored fails", verdict(cand(None), cand(0.5)) == "FAIL"),
        ("a reference with nothing scored fails", verdict(cand(0.9), cand(None)) == "FAIL"),
        ("the result has exactly the agreed keys", sorted(shape) == ["candidate", "grader", "logs", "reference", "split", "verdict"]),
        ("each side has pass_rate, critical and n", sorted(shape["candidate"]) == ["critical", "n", "pass_rate"]),
        ("the result carries split, grader and logs", (shape["split"], shape["grader"], shape["logs"]) == ("gate", "judge/model", ["a.eval", "b.eval"])),
        ("the result is valid JSON", json.loads(json.dumps(shape)) == shape),
        ("a NaN pass rate becomes null", side({"pass_rate": float("nan"), "critical_count": 0.0}, 12)["pass_rate"] is None),
        ("a critical count becomes an int", side({"pass_rate": 0.5, "critical_count": 2.0}, 12)["critical"] == 2),
        ("nothing scored gives 0 critical, not a crash", side({"pass_rate": float("nan"), "critical_count": float("nan")}, 2) == {"pass_rate": None, "critical": 0, "n": 2}),
        ("n is the number of scenarios", side({"pass_rate": 0.5, "critical_count": 0.0}, 12)["n"] == 12),
        ("PASS exits 0 and writes the file", pass_code == 0 and written["verdict"] == "PASS" and written["logs"] == ["c.eval", "r.eval"]),
        ("FAIL exits 1", fail_code == 1),
        ("a run that raises exits 2 with one line and no traceback", error_code == 2 and "provider down" in err.getvalue() and "Traceback" not in err.getvalue()),
        ("a limit of 0 exits 2", bad_args_code == 2),
        ("an out file in a missing folder exits 2", missing_dir_code == 2),
    ]
    for label, passed in checks:
        print("self-test: %s: %s" % (label, "OK" if passed else "FAIL"))
    ok = all(passed for _, passed in checks)
    print("self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__" and "--self-test" in sys.argv[1:]:
    sys.exit(self_test())


if __name__ == "__main__":
    sys.exit(main())
