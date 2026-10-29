# Two clinical failure modes of MedGemma-27B

Code and data for my Alterra Labs take-home. I tested Google's MedGemma-27B-text on two
tasks a clinician does from the chart, and compared it with its own base model
(Gemma-3-27B, served with the same vLLM version and settings) and with Llama-3.3-70B.
Every test shows the same note or exam question twice, with one sentence changed, so each
model is compared with itself. Both failures were pre-registered (`prereg/`) and then
confirmed on notes and questions I had not looked at.

**Failure A: MedGemma overrides the documented medication plan.** When a discharge summary
says a home drug "was continued at the home dose throughout the admission" but gives no
discharge instruction, MedGemma drops it from the discharge list in 15.0% of notes (29.0%
when a lab abnormality that has already resolved is also mentioned), against 4.3% and 8.7%
for Gemma-3 on the same 300 notes.

**Failure B: MedGemma defers to an asserted wrong diagnosis.** One line saying the referring
physician's working diagnosis is a wrong option flips 7.7% of the diagnoses MedGemma
otherwise gets right (2.6% for a neutral line, 379 questions). On the same questions,
"The attending physician has confirmed a diagnosis of X" flips 33.8% (post-hoc).

## Setup

Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Reproduce every table and figure

No GPU, API key or network needed. Takes about a minute.

```bash
python scripts/reproduce.py
```

This reads the saved model replies in `results/`, prints every analysis, writes one
Markdown table per analysis to `results/tables/` and redraws the two figures in
`figures/`. The main tables:

| Table | What it shows |
|---|---|
| `a_confirm.md` | Failure A, pre-registered confirmation: drop rate per condition, both models |
| `a_audit.md`, `a_by_drug.md` | Failure A without drugs a pharmacist might reasonably hold, and without narratives that end in a death |
| `a_distractors.md` | MedGemma does not drop the unrelated home drugs more often |
| `a_noflags.md`, `a_mitigation.md` | Failure A with a list-only output, and with an instruction to copy the plan |
| `a_age45.md`, `a_age85.md` | The same notes with only the patient's age changed |
| `b_confirm.md` | Failure B, pre-registered confirmation, three models |
| `b_posthoc.md`, `b_posthoc_2x2.md` | Who states the wrong diagnosis and how certain the wording is |
| `b_cot_vs_direct.md`, `b_cot_mentions.md` | Asking for step-by-step reasoning |
| `p1_leakage.md` | The stopped-drug probe, which did not turn up a failure |
| `prevalence.md` | How often each trigger appears in MTSamples |
| `run_index.md` | Every run with its model, server and model revision |

## Tests

```bash
pytest
```

`tests/test_reproduce.py` checks that `reproduce.py` regenerates the committed tables and
figures exactly. `tests/test_bundled_runs.py` rebuilds the prompts of every bundled run from
the pinned datasets and checks them against the sha256 recorded at run time, then re-scores
every stored reply and checks that each verdict is unchanged. It needs the datasets, so run
`python scripts/get_data.py` first (it is skipped otherwise).

## Fresh runs

Copy `.env.example` to `.env` and fill in the keys you need.

MedGemma is not on OpenRouter, so MedGemma and Gemma-3 run on a vLLM server
(`vllm/vllm-openai:v0.11.0`, bf16, pinned revisions, greedy decoding). This starts one on
RunPod, runs the configs and always shuts the server down:

```bash
python deploy/runpod.py medgemma-27b configs/experiments/a_confirm_override.yaml
python deploy/runpod.py gemma3-27b-vllm configs/experiments/a_confirm_override.yaml
```

Llama-3.3-70B runs through OpenRouter:

```bash
python -m clinfail.cli configs/experiments/b_confirm_anchoring.yaml --use llama33-70b
```

With your own vLLM server, set `VLLM_URL_MEDGEMMA_27B` (or `VLLM_URL_GEMMA3_27B`) and
`VLLM_API_KEY`, then use `python -m clinfail.cli <config> --use medgemma-27b`. Add
`--n-cases 10` for a quick check.

Each run writes `outputs/runs/<time>_<run name>_<config hash>/` with the config, every
prompt (`cases.jsonl`), every reply and its scores (`results.jsonl`), a summary and
`meta.json` (git commit, hashes, model endpoints). Replies are cached under
`outputs/cache/`, so rerunning a config replays them. `python scripts/bundle.py` copies
finished runs into `results/`.

## Experiments

| Config | What it tests |
|---|---|
| `p1_med_status_explore`, `p1_med_status_explore_medgemma` | Stopped-drug probe: is a drug the note says was stopped or held kept on the list? (No failure; this is where Failure A first showed up) |
| `p1o_override_explore` | Failure A development run, 120 notes, six versions each |
| `p1o_age45`, `p1o_age85` | Failure A with only the patient's age changed (tests an age-based rule) |
| `a_confirm_override` | Failure A confirmation, 300 new notes (pre-registered) |
| `a_mech_noflags` | Failure A with no field for concerns in the output |
| `a_mech_mitigation` | Failure A with "reproduce the documented plan" in the system prompt |
| `a_mech_paraphrase_1`, `_2` | Failure A with the system prompt reworded |
| `p3_anchoring_explore`, `p3_anchoring_explore_medgemma` | Failure B development run, 300 questions |
| `b_confirm_anchoring` | Failure B confirmation, 400 new questions (pre-registered) |
| `b_mech_authority` | The same wrong diagnosis credited to five different sources |
| `b_mech_authority2x2` | Attending or nurse, crossed with "suspects" or "has confirmed" |
| `b_mech_cot` | Failure B when the model is asked to reason step by step |
| `b_posthoc_certainty` | Source, certainty and no-source lines on the confirmation questions (post-hoc) |

Development and confirmation data never overlap: the confirmation configs exclude the ids
in `configs/splits/`.

## Layout

```
configs/            experiment configs, model registry, development splits
prereg/             the two pre-registrations, written before the confirmation runs
src/clinfail/
  data/             Asclepius and MedQA loaders (pinned revisions)
  probes/           notes.py (discharge-summary template), med_override.py (Failure A),
                    anchoring.py (Failure B), med_status.py (stopped-drug probe)
  models/llm.py     OpenAI-compatible client with the reply cache
  eval/metrics.py   Wilson interval, exact McNemar test, paired difference, odds ratio, Holm
  runner.py, cli.py run a config and write the run directory
scripts/            reproduce.py, analyze.py, figures.py, bundle.py, prevalence.py, get_data.py
deploy/runpod.py    vLLM server on RunPod
results/            one directory per run (config, meta, every reply), tables, derived files
figures/            the two figures
tests/
```

## Data

No patient records are used.

| Dataset | Licence | Revision | Used for |
|---|---|---|---|
| Asclepius synthetic clinical notes (`starmpcc/Asclepius-Synthetic-Clinical-Notes`), written from published case reports | CC-BY-NC-SA-4.0 | `52af6897` | Hospital-course narratives in the Failure A notes |
| MedQA-USMLE 4-option (`GBaker/MedQA-USMLE-4-options`), board-exam questions | CC-BY-4.0 | `0fb93dd2` | "Most likely diagnosis" questions for Failure B |
| MTSamples (`harishnair04/mtsamples`), medical transcription samples | Apache-2.0 | `139c3fb2` | How often each trigger occurs (`scripts/prevalence.py`) |

The runs were made from an earlier working copy of this code, so the commit in each
`meta.json` points to that history. `tests/test_bundled_runs.py` is the check that this code
produces exactly the prompts and scores of those runs.
