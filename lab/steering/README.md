# Flattery gauge

> Issue #38. A trait's direction is the difference of mean activations between two contrasting personas ([persona vectors](https://arxiv.org/abs/2507.21509), [repeng](https://github.com/vgel/repeng)). The gauge reads how far a reply sits along the flattery direction. Nothing here steers a model. Status: **built, trial not yet run** (see Result).

| Question | Answer |
|---|---|
| What it shows | One number per reply: its position along the flattery vector of `google/gemma-4-E2B-it`, from the midpoint of the flattery persona and the plain-spoken persona. Higher means more flattering. Vectors for honesty and warmth are built the same way |
| The trial | Sage v0's replies on the honesty `tune` tests, the gauge reading beside the judge's grade (P 1, F 0, C -1), then Pearson, Spearman and AUC. The layer is fixed before grades are seen, at three fifths of the depth. The sweep over all layers is a side table. It is not the headline |
| Result | **Not run.** Two blockers, below |
| Does the gauge track the judge? | **Not known yet.** The held-out check (6 flattering and 6 honest replies written for it) runs in the same Space call and comes first: if it fails, the gauge is not worth correlating |
| Free compute only | A private ZeroGPU Space on the PRO account `Soul-Craft`, `Soul-Craft/sage-flattery-gauge` (the token could not create one under `SoulCraft-Org`). No paid hardware. Each GPU call asks for 120 seconds or less of the 40 minutes a day |

## Why there is no result yet

| Blocker | State | What unblocks it |
|---|---|---|
| Sage v0's replies and the judge's grades | The `evals` runs of 2026-11-23 were cancelled or too slow. NVIDIA retired the default judge. Gemma 4 31B took minutes a reply. Dispatches on `main` cancel each other, because they share one concurrency group. A fix is on branch `evals/judge-ultra` | Merge of that branch, then `gh workflow run evals.yml -R SoulCraft-Org/sage --ref <your branch> -f split=tune -f limit=100`. Dispatch from your own branch so another dispatch cannot cancel yours |
| Starting the GPU run | ZeroGPU bills the signed-in visitor who triggers the call, and the Space is private. This session had no token and its browser showed the embedded app blank | Open <https://huggingface.co/spaces/Soul-Craft/sage-flattery-gauge> signed in as `Soul-Craft`. The run starts on load, and the Logs tab (Container) prints `RESULT` lines |

## Rerun

| Step | Command or action |
|---|---|
| 1. Check the model-free parts | `python3 -I lab/steering/make_vectors.py --self-test` |
| 2. Get replies and grades | Download the `evals-logs` artifact of the run, then `python3 -I lab/steering/make_vectors.py extract --log <file>.eval --replies lab/steering/replies.jsonl --grades lab/steering/grades.jsonl --step honesty`. Check the log's `status` and its unscored count first: `inspect` can exit 0 on an error log |
| 3. Push both files | The Space fetches `make_vectors.py`, `replies.jsonl` and `grades.jsonl` from this branch when it starts (`REF` in `space_app.py`). Restart the Space by saving its `app.py` again |
| 4. Run on the Space | Upload `space_app.py` as `app.py`, with `requirements.txt` (`transformers>=5.0`, `accelerate`) and this front matter in its `README.md`: `sdk: gradio`, `python_version: "3.12"`, `app_file: app.py`. Hardware `zero-a10g`. Open the Space as a signed-in visitor and read the `RESULT` lines in the Container log |
| 5. Chart and numbers on this Mac, no model | Save the per-scenario gauge lines as `gauge.jsonl`, then `python3 -I lab/steering/make_vectors.py trial --gauge gauge.jsonl --grades lab/steering/grades.jsonl --layer <n> --svg lab/steering/chart.svg` |

## Files

| File | What |
|---|---|
| `make_vectors.py` | `make`, `gauge`, `extract`, `trial` and `--self-test`. The self-test needs only the standard library. The model code imports torch and transformers when called, and must run on a free GPU, never on a laptop |
| `space_app.py` | The ZeroGPU Space app. Builds the three vectors, runs the held-out check, gauges the replies, and prints the sweep |
