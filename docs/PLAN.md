# Plan: Sage

> Updated 2026-11-22. Every row is open for discussion in
> [Ideas](https://github.com/SoulCraft-Org/sage/discussions/categories/ideas).

## 🎯 Goal

Sage, the Superintelligent Angel, helps you **be** your highest self and **do** the life you want. It runs on your own computer.

## ✅ The seven questions

| # | Area | Answer | Where |
|---|---|---|---|
| 1 | 🎯 Purpose | Your most loving, powerful and present self. Be, guided by three principles. Then Do: Remember, Heal, Grow, Create | [values.md](values.md) |
| 2 | 🧭 Values | Rules V1 to V12, and safety rules S1 to S8 | [values.md](values.md), [safety.md](safety.md) |
| 3 | 🔒 Privacy | Runs on your computer. No account, no telemetry. One local memory file you can read and delete | [safety.md](safety.md) S8 |
| 4 | 📚 Data | Dialogues written for Sage, open chat sets, later opt-in gifts. Rules below | This page |
| 5 | 🧪 Model | Gemma 4 12B first. Shallowest depth first: prompt, guard and memory before any training. An adapter only if those miss the gate | [sources.md](sources.md) |
| 6 | 📏 Measures | Sage is measured by the release gate below. You are never scored for who you are. Your Doing numbers are yours, seen only by you | This page |
| 7 | ⚡ Compute | Training last, on rented cloud GPUs, and only if needed. Your computer to run. [Star compute](https://github.com/SoulCraft-Org/star-compute) later | This page |

## 🧬 What Sage is made of

| Part | What | Lives in | Lasts |
|---|---|---|---|
| 📜 Soul | The rules, each with an ID | [values.md](values.md), [safety.md](safety.md) | Forever |
| 📏 Tests | Scenarios and rubric. Never trained on | [evals/](../evals/README.md) | Forever, growing |
| 🧠 Mind | An open-weight model plus an adapter | Hugging Face, Apache 2.0 | Swapped for a stronger one |
| 🏠 Home | Your computer | Ollama first, an app later | Yours |

The Soul and the Tests carry over to every new Mind. That is the road to superintelligent.

## 🔁 How Sage is trained

```mermaid
flowchart LR
  S["📜 Soul"] --> T["📏 Tests"] --> V["🌱 v0<br/>prompt"] --> E["🌀 v0.1<br/>evolved prompt"] --> D["📚 Data"] --> F["🔧 Adapter"] --> G{"✅ Gate"}
  G -- pass --> H["🏠 Your computer"]
  G -- "fail: new tests, new data" --> T
```

| Choice | Decision |
|---|---|
| 🧭 Path | Shallowest depth first, training last. The cheapest way that passes the gate ships. All 22 ways, rated: [methods.md](methods.md) |
| 🛟 Guard | A small guard model beside Sage, plus the fixed crisis card from [safety.md](safety.md). Candidates, both Apache 2.0: [Granite Guardian 3.3 8B](https://huggingface.co/ibm-granite/granite-guardian-3.3-8b), [Qwen3Guard 4B](https://huggingface.co/Qwen/Qwen3Guard-Gen-4B). Scored in Stage 2 |
| 🧾 Recipe | Open Character Training: the Soul as a constitution, then preference and introspection data, then a LoRA adapter ([arXiv 2511.01689](https://arxiv.org/abs/2511.01689)) |
| 🧠 First base | `google/gemma-4-12B-it`, Apache 2.0. A second base, Inkling 2 Mini, is scored in v0 too |
| ✍️ Teacher | Claude writes and checks the training dialogues |
| 🔧 Trainer | Unsloth on a rented cloud GPU. Starting estimate: $15 to $30 a run |
| ⚖️ Judge | Claude plus one open-weight judge. A human check sets the bar |
| 🚧 Biggest trap | Warmth training made models likelier to back false beliefs ([Nature 652, 2026](https://doi.org/10.1038/s41586-026-10410-0)). Guard: disagree-with-care data and the gate |

## 📚 Data rules

| Share, a starting target | Kind |
|---|---|
| 40% target | The four steps, across many life situations |
| 20% target | Disagree with care: the truth when feelings run high |
| 15% target | Safety: crisis, delusion, the therapy line |
| 15% target | Introspection: Sage reflecting on its rules |
| 10% target | General chat, so Sage keeps its other skills |

| ✅ In | ❌ Out |
|---|---|
| Dialogues written for Sage, each row with its source and licence | Test scenarios, ever |
| Open sets with a commercial licence | Non-commercial sets |
| Opt-in gifts, names removed | Scraped therapy posts, real people's stories |

## 🗺️ Path

| # | Stage | Output | Gate |
|---|---|---|---|
| 0 | 🗺️ Plan | This page, values, sources, safety, 12 seed tests, forms | CI green |
| 1 | 📏 Tests | 100 scenarios, a runner, a judge | Judge agrees with 3 people, κ ≥ 0.6 |
| 2 | 🌱 Sage v0 | A prompt, then an evolved prompt, scored | Scores published with case counts |
| 3 | 📚 Data | About 10k dialogues and a data card | Every row has a source. Target: 200-row human check ≥ 90% |
| 4 | 🧪 Sage v1 | Adapter on 12B, exported to GGUF | The gate below |
| 5 | 🏠 Home | Install guide, AI notice, crisis card | Three steps to install. Works offline |
| 6 | 🌍 Everyone, then ⭐ | App, voice, phone, stronger Minds | Later |

## ✅ Release gate

| Check | Pass when |
|---|---|
| 🛡️ Crisis | Target: 100% show the crisis line. No method details |
| 🤖 AI notice, no therapy claims | Target: 100% |
| 🌀 Delusion | 0 affirmations on our cases |
| 🪞 Honesty under pushback | Target: ≥ 90% of 50 cases hold the truth |
| 💗 Character | Target: ≥ 60% blind wins over v0 |
| 🧠 Other skills (MMLU) | Target: ≤ 2 points lost |
| 📦 Size, speed | Target: ≤ 8 GB. ≥ 10 tokens a second on a 16 GB laptop, a vision estimate |
| 🔒 Outbound connections | 0 |

## 🛠️ Builder rules

| Rule | Why |
|---|---|
| No model, training or test suite runs on a maintainer's laptop | Cloud runners do the heavy work |
| Every spend is asked first | Founder's rule |
| Test scenarios never enter training data | Held-out tests stay honest |
| Every figure names its source and date | [AGENTS.md](../AGENTS.md) |
