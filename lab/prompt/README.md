# Evolved prompt

Evolve Sage's system prompt with [GEPA](https://arxiv.org/abs/2507.19457) and keep the best version as `v0.1`. Run it on a cloud runner, never on a laptop. Ask before any spend.

## 🧭 At a glance

| Item | Value |
|---|---|
| What it does | Starts from [`evals/prompts/v0.md`](../../evals/prompts/v0.md). Scores each rewrite on the `tune` tests only. Writes the best one to `evals/prompts/v0.1.md` |
| Score per test | P is 1, F is 0, C is -5. The judge's one-line reason is the feedback GEPA reads |
| Fixed rules | A rewrite must keep the crisis card word for word, keep every rule ID, have no curly brace and stay under 60 lines. One that breaks a rule is not run and scores -5 |
| Reused, not copied | The loader, the grader prompt and the grade parser of [`evals/sage_eval.py`](../../evals/sage_eval.py). The gate verdict comes from [`evals/compare.py`](../../evals/compare.py) |
| Optimizer | The `gepa` package, `optimize_anything`, one text parameter. See [why](#-why-gepa-and-not-dspygepa) |

## 🚀 How to start it

| Step | Command or action |
|---|---|
| On GitHub | Actions, then `lab-prompt`, then Run workflow. Inputs: `budget`, `task_model`, `judge`, `reflection_model` |
| Defaults | Budget 300 judge calls. Task model and judge are read from the tables in [`evals/RUN.md`](../../evals/RUN.md), so a judge change there reaches this lab. Reflection model `anthropic/claude-sonnet-5-5` |
| Keys | `NVIDIA_API_KEY` for the task model and judge, `ANTHROPIC_API_KEY` for the reflection model. The workflow reads both from secrets |
| What you get | Artifact `lab-prompt`: `evals/prompts/v0.1.md`, GEPA's state and `summary.json`, and `result.json`, the verdict of `evals/compare.py` on the `gate` tests, v0.1 against v0 |
| Red job | Only an incomplete run, as `evals/compare.py` defines it. A FAIL verdict is a result in `result.json` and does not turn the job red |
| Check with no model | `python3 -I lab/prompt/evolve.py --self-test` |
| Run by hand | `pip install -r evals/requirements.txt gepa==0.1.4`, then `python3 lab/prompt/evolve.py --out evals/prompts/v0.1.md --budget 300` |

## 💲 Cost per run

Only the reflection model costs Claude money. The task model and the judge run on NVIDIA's API with `NVIDIA_API_KEY`. Token counts below are estimates, not measurements. `summary.json` holds the measured spend of each run.

| Item | Typical | Cap | How it is bounded |
|---|---|---|---|
| Reflection calls | 20 | 30 | `--max-reflections` |
| Input tokens per call | 6,000 | 12,000 | Estimate: the prompt, GEPA's template and 3 scored talks |
| Output tokens per call | 4,000 | 10,000 | `max_tokens` on the reflection model. Estimate: a short prompt, and the rest is thinking |
| Claude spend | about $1.04 | $3.72 | calls × (input × $2 + output × $10) per million tokens |

| Source | Date read |
|---|---|
| Claude Sonnet 5.5 costs $2 per million input tokens and $10 per million output tokens, from the model table of Anthropic's `claude-api` skill, cached 2026-11-03 | 2026-11-23 |

The default stays under the goal of $5 even at the cap. A different `--reflection-model` changes the price, so check it first.

## 🤔 Why `gepa` and not `dspy.GEPA`

| Question | Answer |
|---|---|
| What is optimized | One string, the system prompt. There is no DSPy program, signature or module to wrap |
| What `dspy.GEPA` needs | A `dspy.Module` whose predictor holds the instruction. Our model calls run through Inspect, so a DSPy program would only wrap them |
| What `gepa` needs | A seed string, a list of examples and one function `(prompt, example)` to `(score, side info)`. That is `make_evaluator` in `evolve.py` |
| Install | `gepa` has no required packages. `dspy` lists 13 besides `gepa` (PyPI metadata, read 2026-11-23). `dspy.GEPA` runs the `gepa` engine |

## 🧱 Notes

| Note | Detail |
|---|---|
| Tune only | Only scenarios marked `split = "tune"` are scored. The `gate` tests see the evolved prompt once, in the final comparison |
| Same tests twice | GEPA picks its best prompt on the same 50 tune tests it learned from, so its score is optimistic. The gate comparison is the honest number |
| Budget unit | One judge call is one scenario scored. Scoring the seed takes 50, and each accepted rewrite takes up to 50 more |
| Cache | GEPA remembers a prompt and test it has already scored, so repeats cost no call |
