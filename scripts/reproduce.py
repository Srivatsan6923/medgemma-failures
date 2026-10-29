"""Rebuild every table and figure from the bundled run outputs in results/.

    python scripts/reproduce.py

Needs no API keys, GPU or network. Each table is printed and written to
results/tables/<name>.md; the figures go to figures/.
"""

import contextlib
import io
from pathlib import Path

import analyze
import figures

TABLES = Path("results/tables")

# (table file, title, analysis function, run it reads)
STEPS = [
    (
        "a_confirm",
        "Failure A, confirmation (pre-registered)",
        analyze.override,
        "a_confirm_override",
    ),
    (
        "a_audit",
        "Failure A, reasons for MedGemma-only drops and the test without death narratives",
        analyze.override_audit,
        "a_confirm_override",
    ),
    (
        "a_by_drug",
        "Failure A, drops by target drug",
        analyze.override_by_drug,
        "a_confirm_override",
    ),
    (
        "a_distractors",
        "Failure A, unrelated home drugs dropped",
        analyze.distractors,
        "a_confirm_override",
    ),
    (
        "a_read_and_override",
        "Failure A, flags that acknowledge the documented plan",
        analyze.read_and_override,
        "a_confirm_override",
    ),
    (
        "a_reasoning_scan",
        "MedGemma reasoning blocks in Failure A replies",
        analyze.reasoning_scan,
        "",
    ),
    (
        "a_noflags",
        "Failure A, list-only output (no flags field)",
        analyze.override,
        "a_mech_noflags",
    ),
    (
        "a_mitigation",
        'Failure A, system prompt adds "reproduce the documented plan"',
        analyze.override,
        "a_mech_mitigation",
    ),
    (
        "a_paraphrase_1",
        "Failure A, system prompt reworded (1)",
        analyze.override,
        "a_mech_paraphrase_1",
    ),
    (
        "a_paraphrase_2",
        "Failure A, system prompt reworded (2)",
        analyze.override,
        "a_mech_paraphrase_2",
    ),
    ("a_dev", "Failure A, development run", analyze.override, "p1o_override_explore"),
    ("a_age45", "Failure A, patient aged 45", analyze.override, "p1o_age45"),
    ("a_age85", "Failure A, patient aged 85", analyze.override, "p1o_age85"),
    (
        "b_confirm",
        "Failure B, confirmation (pre-registered)",
        analyze.anchoring,
        "b_confirm_anchoring",
    ),
    (
        "b_posthoc",
        "Failure B, certainty, source and no-source lines on the confirmation items (post-hoc)",
        analyze.anchoring,
        "b_posthoc_certainty",
    ),
    (
        "b_posthoc_2x2",
        "Failure B, source x certainty on the confirmation items (post-hoc)",
        analyze.authority2x2,
        "b_posthoc_certainty",
    ),
    (
        "b_image_items",
        "Failure B, no-source line on questions that refer to an image (exploratory)",
        analyze.image_items,
        "b_posthoc_certainty",
    ),
    (
        "b_dev",
        "Failure B, development run (the MedGemma row is a discarded run whose replies were "
        "cut off at 32 tokens; see the next table)",
        analyze.anchoring,
        "p3_anchoring_explore",
    ),
    (
        "b_dev_medgemma",
        "Failure B, development run, MedGemma",
        analyze.anchoring,
        "p3_anchoring_explore_medgemma",
    ),
    (
        "b_authority",
        "Failure B, source of the wrong diagnosis",
        analyze.anchoring,
        "b_mech_authority",
    ),
    ("b_2x2", "Failure B, source x certainty", analyze.authority2x2, "b_mech_authority2x2"),
    ("b_cot", "Failure B, step-by-step reasoning", analyze.anchoring, "b_mech_cot"),
    ("b_cot_vs_direct", "Failure B, step-by-step vs direct answers", analyze.cot_vs_direct, ""),
    (
        "b_cot_mentions",
        "Failure B, step-by-step answers that name the note",
        analyze.cot_mentions,
        "",
    ),
    (
        "b_reasoning_mentions",
        "Failure B, MedGemma's reasoning block names the note",
        analyze.reasoning_mentions,
        "p3_anchoring_explore_medgemma",
    ),
    ("prevalence", "Trigger prevalence in MTSamples", analyze.prevalence, ""),
    ("data_counts", "Dataset and split sizes", analyze.data_counts, ""),
    (
        "p1_leakage",
        "Stopped-drug probe (development)",
        analyze.p1_leakage,
        "p1_med_status_explore",
    ),
    (
        "p1_leakage_medgemma",
        "Stopped-drug probe, MedGemma (development)",
        analyze.p1_leakage,
        "p1_med_status_explore_medgemma",
    ),
    ("run_index", "Run index", analyze.run_index, ""),
]

if __name__ == "__main__":
    analyze.RUNS = Path("results")
    TABLES.mkdir(parents=True, exist_ok=True)
    for slug, title, fn, run in STEPS:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            fn(run)
        text = f"## {title}{f' ({run})' if run else ''}\n{buf.getvalue()}"
        (TABLES / f"{slug}.md").write_text(text, encoding="utf-8", newline="\n")
        print(f"\n{text}", end="")
    figures.OUT.mkdir(parents=True, exist_ok=True)
    figures.figure_a()
    figures.figure_b()
    print(f"\ntables written to {TABLES}, figures to {figures.OUT}")
