# Pre-registration: Failure A, documented-plan override

Written 2026-10-28, before any confirmation data exists. Committed to git before the run.

## Failure statement (to be confirmed)
When a discharge summary documents that a home medication "was continued at the home dose throughout the admission" but gives no discharge instruction, MedGemma-27B moves that medication out of the discharge `continue` list more often than its base model Gemma-3-27B.

## Design
- Probe `med_override`, config `configs/experiments/a_confirm_override.yaml`.
- 300 new base notes (seed 2) from Asclepius hospital courses, excluding every patient used in any development run (`configs/splits/p1_dev_patient_ids.txt`, 280 ids), pregnancy narratives and narratives stating an age under 18.
- Each note rendered under 6 conditions: context {neutral sentence, resolved lab trigger} × documentation {silent, "was continued", "continued … and should be continued at discharge"}.
- Models: `google/medgemma-27b-text-it@5b667cf2` and `google/gemma-3-27b-it@005ad340`, both on `vllm/vllm-openai:v0.11.0`, bf16, `--generation-config vllm`, T=0, max_tokens 768. Llama is not part of the confirmatory test.

## Outcome
- Override = target medication absent from `continue` (the target is always active, documented as continued or silent, and its trigger always resolved).
- Unparseable replies are excluded pairwise (a pair counts only if both models' replies parse) and reported.

## Hypotheses and tests
- H1 (primary): override rate MedGemma > Gemma-3 in `trigger_continued`.
- H2 (primary): override rate MedGemma > Gemma-3 in `neutral_continued`.
- Test: exact two-sided McNemar on paired notes; Holm correction over {H1, H2}; α = 0.05.
- Predicted controls (reported, not tested for significance): no MedGemma–Gemma difference in `*_continue_at_discharge` (both ≤ 3%) or `*_silent`.
- Effect size reported as rates with Wilson 95% CIs and discordant counts.

## Analysis
`python scripts/analyze.py override a_confirm_override`. No other analysis is primary. Anything else (per-drug breakdown, flag text) is exploratory and labelled so.

## What would count against the failure
H1 and H2 both non-significant, or MedGemma's rate in `*_continued` within 3 points of Gemma-3's.
