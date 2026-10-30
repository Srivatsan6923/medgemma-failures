# Two clinical failure modes of MedGemma-27B

Code and data for a study of two ways MedGemma-27B fails on clinical tasks. Each test
shows a model the same note or exam question twice, with one sentence changed, and compares
the answers. MedGemma is compared with its base model, Gemma-3-27B, and with Llama-3.3-70B.
Both failures were pre-registered (`prereg/`) and confirmed on fresh data.

**Failure A.** When a discharge summary says a home drug "was continued at the home dose
throughout the admission" but gives no discharge instruction, MedGemma takes it off the
discharge list in 15% of notes (29% when a resolved lab problem is also mentioned). Gemma-3
does this in 4% and 9% of the same notes.

**Failure B.** One line saying the referring physician thinks the diagnosis is a wrong option
flips 7.7% of the diagnoses MedGemma otherwise gets right (2.6% for a neutral line). If the
line says the attending "has confirmed" it, 33.8% flip.

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

This reads the saved model replies in `results/`, writes one Markdown table per analysis
to `results/tables/` and redraws the figures in `figures/`. The two main tables are
`a_confirm.md` and `b_confirm.md`, the pre-registered confirmation runs; the rest are the
mechanism tests and checks described in the write-up.

## How the code works

A run goes through five steps.

1. A probe in `src/clinfail/probes/` builds the cases. Each note or question becomes a few
   versions that differ by one sentence and share a `pair_id`. `med_override.py` builds
   Failure A and `anchoring.py` builds Failure B.
2. `runner.py` reads a YAML config, builds the cases and sends each prompt through
   `models/llm.py`, an OpenAI-compatible client. Every reply is cached under a hash of the
   model, prompt and settings, so rerunning a config replays the same replies.
3. The probe's `score` method parses each reply with fixed rules (JSON for A, the answer
   letter for B) and sets `failed`. An unparseable reply is never scored as correct: in B
   it counts as a flip, and in A the note leaves the comparison (every A reply parsed).
4. `scripts/analyze.py` loads the run folders and compares versions of the same item with
   the functions in `eval/metrics.py`: Wilson intervals, the exact McNemar test and Holm's
   correction.
5. `scripts/reproduce.py` runs every analysis on the saved replies in `results/` and
   writes the tables and figures.

## Tests

```bash
pytest
```

`test_reproduce.py` checks that `reproduce.py` regenerates the committed tables exactly.
`test_bundled_runs.py` rebuilds every saved prompt from the datasets and re-scores every
saved reply; run `python scripts/get_data.py` first or it is skipped. The other tests cover
the case builders, scorers, cache and statistics.

## Fresh runs

Copy `.env.example` to `.env` and fill in the keys you need.

MedGemma is not on OpenRouter, so MedGemma and Gemma-3 run on a vLLM server
(bf16, greedy decoding). This starts one on
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

Each run writes `outputs/runs/<run name>_<config hash>/` with the config, every prompt
(`cases.jsonl`), every reply and its scores (`results.jsonl`), a summary and `meta.json`
(hashes and model endpoints). `python scripts/bundle.py` copies finished runs into
`results/`. A fresh run asks the model again, so its replies can differ slightly from the
saved ones; the saved replies are what every table is built from.

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
  data/             Asclepius and MedQA loaders
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

| Dataset | Licence | Used for |
|---|---|---|
| Asclepius synthetic clinical notes (`starmpcc/Asclepius-Synthetic-Clinical-Notes`), written from published case reports | CC-BY-NC-SA-4.0 | Hospital-course narratives in the Failure A notes |
| MedQA-USMLE 4-option (`GBaker/MedQA-USMLE-4-options`), board-exam questions | CC-BY-4.0 | "Most likely diagnosis" questions for Failure B |
| MTSamples (`harishnair04/mtsamples`), medical transcription samples | Apache-2.0 | How often each trigger occurs (`scripts/prevalence.py`) |
