# Run the tests

> The runner is [sage_eval.py](sage_eval.py), an [Inspect AI](https://inspect.aisi.org.uk/) task. It sends each scenario's turns to the model under test, then a judge gives one grade per scenario ([rubric.md](rubric.md)). Run it on a cloud runner, never on a laptop. Ask before any spend.

## 🚀 Commands

| Step | Command |
|---|---|
| Install | `pip install -r evals/requirements.txt` |
| Check the loader and grade parser, with no model | `python3 -I evals/sage_eval.py --self-test` |
| Run, gate split, gate judge | `inspect eval evals/sage_eval.py --model openai-api/nvidia/google/gemma-4-31b-it --model-role grader=openai-api/nvidia/nvidia/nemotron-3-super-120b-a12b -T split=gate` |
| Second opinion on the same log | `inspect score <log> --model-role grader=anthropic/claude-sonnet-5-5 --action overwrite --output-file <new log>` |
| Read a log | `inspect view` |

## 🔑 Models and keys

| Role | Model string | Key |
|---|---|---|
| Answers, the model under test | `openai-api/nvidia/google/gemma-4-31b-it` | `NVIDIA_API_KEY`, `NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1` |
| Gate judge, role `grader` | `openai-api/nvidia/nvidia/nemotron-3-super-120b-a12b` | the same two |
| Second judge, role `grader` | `anthropic/claude-sonnet-5-5` | `ANTHROPIC_API_KEY` |

The gate judge is an open-weight model. Claude is a second opinion. Never print or commit a key.

## ⚙️ Task arguments

Pass them with `-T name=value`.

| Argument | Values | Default |
|---|---|---|
| `split` | `tune`, `gate` or `all`. A scenario file with no `split` field counts as `all`, so every split keeps it | `all` |
| `step` | One step: `remember`, `heal`, `grow`, `create`, `safety`, `honesty` | every step |
| `prompt` | A file in [prompts/](prompts/), without `.md`. The system prompt Sage gets | `v0` |

## 🧮 What a log holds

| Item | Value |
|---|---|
| Score value | P is 1, F is 0, C is -1. The letter is in `answer`, the judge's one-line reason in `explanation` |
| Unparseable judge output | Unscored (NaN). Left out of both metrics, and the raw text is kept |
| `pass_rate` | Passes over scored scenarios |
| `critical_count` | Scenarios graded C. The goal is zero |

Keep one epoch. The default reducer averages scores across epochs, which blurs a C.

## 🧪 Test the runner with no real model

Inspect ships a mock provider, `mockllm/model`. It answers every call with the fixed text `Default output from mockllm/model`, so a judge on it is always unscored.

| Goal | How |
|---|---|
| Smoke test the CLI | `inspect eval evals/sage_eval.py --model mockllm/model --model-role grader=mockllm/model` |
| Canned replies | In Python, `get_model("mockllm/model", custom_outputs=[...])` takes a list of `ModelOutput`, a generator, or a function of `(input, tools, tool_choice, config)` that returns one. Pass it to `inspect_ai.eval(sage(), model=..., model_roles={"grader": ...})` |
| Canned judge grades | The same `custom_outputs`, with replies such as `GRADE: P` and `REASON: every must met` |

The command line cannot give `custom_outputs`, because it needs `ModelOutput` objects.
