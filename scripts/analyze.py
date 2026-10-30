"""Analyses behind every table in the write-up.

Each function takes a run name, reads that run's replies and prints a table.
scripts/reproduce.py calls all of them on results/; one can also be run alone:

    python scripts/analyze.py override a_confirm_override
"""

import gzip
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

from clinfail.eval.metrics import discordant_or, holm, mcnemar_exact, paired_diff_ci, wilson_ci

load_dotenv()
# where run directories live: results/ for the bundled runs, outputs/runs for fresh ones
RUNS = Path(
    os.environ.get("RESULTS_DIR") or Path(os.environ.get("OUTPUT_ROOT", "outputs")) / "runs"
)
MODELS = ["medgemma-27b", "gemma3-27b-vllm", "llama33-70b"]
MG, G = "medgemma-27b", "gemma3-27b-vllm"


def read_results(d: Path) -> list[dict] | None:
    if (d / "results.jsonl").exists():
        text = (d / "results.jsonl").read_text(encoding="utf-8")
    elif (d / "results.jsonl.gz").exists():
        text = gzip.decompress((d / "results.jsonl.gz").read_bytes()).decode("utf-8")
    else:
        return None
    return [json.loads(line) for line in text.splitlines()]


def run_dirs(run_name: str) -> dict[str, Path]:
    """The run directory for each model that ran this config."""
    found = {}
    for d in sorted(RUNS.glob(f"{run_name}_*")):
        # directory names are <run name>_<hash>; skip runs whose name only starts the same
        if d.name.rsplit("_", 1)[0] != run_name:
            continue
        for m in sorted({r["model"] for r in read_results(d) or []}):
            found[m] = d
    return found


def load(run_name: str) -> dict[str, dict[str, dict]]:
    """Replies of a run as {model: {case_id: row}}."""
    return {
        m: {r["case_id"]: r for r in read_results(d) if r["model"] == m}
        for m, d in run_dirs(run_name).items()
    }


def rate(k: int, n: int) -> str:
    lo, hi = wilson_ci(k, n)
    return f"{k}/{n} ({k / n:.1%}) [{lo:.1%}, {hi:.1%}]"


def odds_ratio(b: int, c: int) -> str:
    est, lo, hi = discordant_or(b, c)
    return f"{est:.1f} [{lo:.1f}, {hi:.1f}]"


def discordant(x: list[bool], y: list[bool]) -> tuple[int, int]:
    """Pairs where only x failed, and pairs where only y failed."""
    b = sum(p and not q for p, q in zip(x, y, strict=True))
    c = sum(q and not p for p, q in zip(x, y, strict=True))
    return b, c


def baseline_correct(r: dict) -> tuple[list[str], list[str]]:
    """All item ids of an anchoring run, and the ones answered correctly with no line."""
    items = sorted({x["pair_id"] for x in r.values()})
    return items, [i for i in items if not r[f"{i}-baseline"]["failed"]]


def flags_on_target(row: dict) -> str:
    flags = json.loads(re.search(r"\{.*\}", row["output"], re.S).group())["flags"]
    return " ".join(f for f in flags if row["target"] in f.lower())


# ---------------------------------------------------------------- Failure A


def override(run_name: str, primary=("trigger_continued", "neutral_continued")) -> None:
    """MedGemma vs Gemma-3 on the same notes: how often the target drug is dropped."""
    rows = load(run_name)
    mg, g = rows[MG], rows[G]
    conds = sorted({r["condition"] for r in mg.values()})
    print(
        "| condition | MedGemma | Gemma-3 | MG only | G only | diff [95% CI] | OR [95% CI] | p "
        "| silent MG | silent G |\n|---|---|---|---|---|---|---|---|---|---|"
    )
    pvals = {}
    for c in conds:
        # a note counts only if both models' replies parsed
        ids = [
            k
            for k, r in mg.items()
            if r["condition"] == c and r["parse_ok"] and g.get(k, {}).get("parse_ok")
        ]
        b, cc = discordant([mg[i]["failed"] for i in ids], [g[i]["failed"] for i in ids])
        pvals[c] = mcnemar_exact(b, cc)
        sm = sum(mg[i]["silent_override"] for i in ids)
        sg = sum(g[i]["silent_override"] for i in ids)
        d, lo, hi = paired_diff_ci(b, cc, len(ids))
        print(
            f"| {c} | {rate(sum(mg[i]['failed'] for i in ids), len(ids))} "
            f"| {rate(sum(g[i]['failed'] for i in ids), len(ids))} | {b} | {cc} "
            f"| {d:+.1%} [{lo:+.1%}, {hi:+.1%}] | {odds_ratio(b, cc)} | {pvals[c]:.2g} "
            f"| {sm} | {sg} |"
        )
    hits = [c for c in primary if c in pvals]
    for c, p in zip(hits, holm([pvals[c] for c in hits]), strict=True):
        print(f"Holm-adjusted p ({c}): {p:.2g}")


TRIGGER_WORDS = re.compile(
    r"creatinine|inr|potassium|\bck\b|creatine|cpk|glucose|hypoglyc|heart rate|brady|"
    r"blood pressure|hypotens|nosebleed|bleed|epistaxis|myopathy",
    re.I,
)
UNLISTED = re.compile(
    r"not (listed|mentioned|included|specified)|clarify|unclear|no discharge|not documented", re.I
)


def flag_reason(row: dict) -> str:
    """Rough keyword sort of why MedGemma dropped the drug, from its flag text."""
    text = flags_on_target(row)
    if not text:
        return "no flag on the dropped drug"
    if UNLISTED.search(text):
        return "discharge instruction missing, asks to clarify"
    if row["condition"].startswith("trigger") and TRIGGER_WORDS.search(text):
        return "cites the inserted, resolved abnormality"
    return "cites other narrative context"


def override_audit(run_name: str) -> None:
    """Reasons for MedGemma-only drops, and the main test again without notes whose
    narrative mentions a death (where stopping drugs is not a meaningful error)."""
    rows = load(run_name)
    mg, g = rows[MG], rows[G]
    died = set(json.loads((RUNS / "narratives_death.json").read_text(encoding="utf-8")))
    dead = {r["pair_id"] for r in mg.values() if r["course_patient_id"] in died}
    print(f"base notes whose narrative mentions a death: {len(dead)}")
    pvals = []
    for c in ("trigger_continued", "neutral_continued"):
        only = [
            k for k, r in mg.items() if r["condition"] == c and r["failed"] and not g[k]["failed"]
        ]
        reasons = Counter(flag_reason(mg[k]) for k in only)
        print(f"{c}: MedGemma-only drops {len(only)}: {dict(reasons.most_common())}")
        ids = [
            k
            for k, r in mg.items()
            if r["condition"] == c
            and r["parse_ok"]
            and g[k]["parse_ok"]
            and r["pair_id"] not in dead
        ]
        b, cc = discordant([mg[i]["failed"] for i in ids], [g[i]["failed"] for i in ids])
        pvals.append(mcnemar_exact(b, cc))
        print(
            f"  without death notes: MedGemma {rate(sum(mg[i]['failed'] for i in ids), len(ids))}, "
            f"Gemma-3 {rate(sum(g[i]['failed'] for i in ids), len(ids))}, {b} vs {cc}"
        )
    print(f"  Holm-adjusted p without death notes: {', '.join(f'{p:.2g}' for p in holm(pvals))}")


def override_by_drug(run_name: str) -> None:
    """Drops per target drug, and the main test without the drugs a pharmacist might
    reasonably hold (ibuprofen after a creatinine rise, and so on)."""
    rows = load(run_name)
    mg, g = rows[MG], rows[G]
    for c in ("trigger_continued", "neutral_continued"):
        ids = [k for k, r in mg.items() if r["condition"] == c]
        drugs = Counter(mg[k]["target"] for k in ids)
        print(f"{c}, dropped by drug (MedGemma / Gemma-3 / notes):")
        print(
            "  "
            + ", ".join(
                f"{d} {sum(mg[k]['failed'] for k in ids if mg[k]['target'] == d)}/"
                f"{sum(g[k]['failed'] for k in ids if g[k]['target'] == d)}/{n}"
                for d, n in sorted(drugs.items())
            )
        )
        print("  | drug | notes | MedGemma dropped | Gemma-3 dropped | MG only | G only |")
        for d, n in sorted(drugs.items()):
            sel = [k for k in ids if mg[k]["target"] == d]
            b, cc = discordant([mg[k]["failed"] for k in sel], [g[k]["failed"] for k in sel])
            print(
                f"  | {d} | {n} | {sum(mg[k]['failed'] for k in sel)} "
                f"| {sum(g[k]['failed'] for k in sel)} | {b} | {cc} |"
            )
        for label, drop in [
            ("without ibuprofen", {"ibuprofen"}),
            (
                "without ibuprofen, simvastatin, spironolactone",
                {"ibuprofen", "simvastatin", "spironolactone"},
            ),
        ]:
            keep = [k for k in ids if mg[k]["target"] not in drop]
            b, cc = discordant([mg[k]["failed"] for k in keep], [g[k]["failed"] for k in keep])
            print(
                f"  {label}: MedGemma {rate(sum(mg[k]['failed'] for k in keep), len(keep))}, "
                f"Gemma-3 {rate(sum(g[k]['failed'] for k in keep), len(keep))}, "
                f"{b} vs {cc}, p={mcnemar_exact(b, cc):.2g}"
            )


def drug_fate(row: dict) -> str:
    if row["target_in_continue"]:
        where = "kept"
    elif row["target_in_stop"]:
        where = "held"
    else:
        where = "left off"
    return where + (" + flag" if row["target_flagged"] else "")


def drop_kinds(run_name: str) -> None:
    """What each model does with the target drug: keeps it, moves it to stop_or_hold, or
    leaves it off every list, and whether a flag names it."""
    rows = load(run_name)
    kinds = ["kept", "kept + flag", "held", "held + flag", "left off", "left off + flag"]
    print("| condition | model | notes | " + " | ".join(kinds) + " |")
    print("|---|---|---|" + "---|" * len(kinds))
    for c in sorted({r["condition"] for r in rows[MG].values()}):
        for m in (MG, G):
            sel = [r for r in rows[m].values() if r["condition"] == c and r["parse_ok"]]
            n = Counter(drug_fate(r) for r in sel)
            print(f"| {c} | {m} | {len(sel)} | " + " | ".join(str(n[k]) for k in kinds) + " |")
    print("held = in stop_or_hold; left off = in no list; flag = a flag names the drug")


def distractors(run_name: str) -> None:
    """Does MedGemma also drop the five unrelated home drugs? If the failure were
    general list trimming, it would."""
    rows = load(run_name)
    mg, g = rows[MG], rows[G]
    print(
        "| condition | notes with any unrelated drug dropped, MedGemma | Gemma-3 | MG only | G only "
        "| p | unrelated-drug slots dropped, MedGemma | Gemma-3 |\n|---|---|---|---|---|---|---|---|"
    )
    for c in sorted({r["condition"] for r in mg.values()}):
        ids = [
            k for k, r in mg.items() if r["condition"] == c and r["parse_ok"] and g[k]["parse_ok"]
        ]
        am = [mg[k]["distractor_omission_rate"] > 0 for k in ids]
        ag = [g[k]["distractor_omission_rate"] > 0 for k in ids]
        b, cc = discordant(am, ag)
        # omission rate is a share of the 5 unrelated drugs; times 5 gives a count
        sm = round(sum(mg[k]["distractor_omission_rate"] for k in ids) * 5)
        sg = round(sum(g[k]["distractor_omission_rate"] for k in ids) * 5)
        print(
            f"| {c} | {rate(sum(am), len(ids))} | {rate(sum(ag), len(ids))} | {b} | {cc} | "
            f"{mcnemar_exact(b, cc):.2g} | {rate(sm, 5 * len(ids))} | {rate(sg, 5 * len(ids))} |"
        )


ACK_CONTINUED = re.compile(r"continued", re.I)
ACK_RESOLVED = re.compile(
    r"resolved|returned to baseline|normali[sz]ed|back in|no recurrence", re.I
)


def read_and_override(run_name: str) -> None:
    """Does the flag on a dropped drug show that MedGemma read the plan it went against?"""
    mg = load(run_name)[MG]
    for c in ("trigger_continued", "neutral_continued"):
        flags = [flags_on_target(r) for r in mg.values() if r["condition"] == c and r["failed"]]
        cont = sum(bool(ACK_CONTINUED.search(f)) for f in flags)
        res = sum(bool(ACK_RESOLVED.search(f)) for f in flags)
        either = sum(bool(ACK_CONTINUED.search(f) or ACK_RESOLVED.search(f)) for f in flags)
        print(
            f"{c}: MedGemma drops {len(flags)}, flag on the drug says it was continued {cont}, "
            f"says the abnormality resolved {res}, either {either}, "
            f"flag on the drug {sum(bool(f) for f in flags)}, no flag on the drug "
            f"{sum(not f for f in flags)}"
        )


A_RUNS = [
    "p1_med_status_explore_medgemma",
    "p1o_override_explore",
    "p1o_age45",
    "p1o_age85",
    "a_confirm_override",
    "a_mech_noflags",
    "a_mech_mitigation",
    "a_mech_paraphrase_1",
    "a_mech_paraphrase_2",
]


def reasoning_scan(_: str = "") -> None:
    """MedGemma's reasoning block appears on exam questions; check it never appears here."""
    total = blocks = 0
    for run in A_RUNS:
        mg = load(run).get(MG, {})
        n = sum("<unused94>" in r["output"] for r in mg.values())
        total, blocks = total + len(mg), blocks + n
        print(f"{run}: {n}/{len(mg)} MedGemma replies contain <unused94>")
    print(f"all Failure A runs: {blocks}/{total}")


def p1_leakage(run_name: str) -> None:
    """Stopped-drug probe: failures per condition."""
    rows = load(run_name)
    conds = sorted({r["condition"] for v in rows.values() for r in v.values()})
    print("| model | " + " | ".join(conds) + " |\n|---|" + "---|" * len(conds))
    for m, r in sorted(rows.items()):
        cells = []
        for c in conds:
            sel = [x for x in r.values() if x["condition"] == c and x["parse_ok"]]
            cells.append(f"{sum(x['failed'] for x in sel)}/{len(sel)}")
        print(f"| {m} | " + " | ".join(cells) + " |")
    print("failed = target in continue when it was stopped or held, or missing when it was active")


# ---------------------------------------------------------------- Failure B


def anchoring(run_name: str, anchors=("wrong_anchor",)) -> None:
    """Flip rate of each inserted line against the neutral line, on baseline-correct items."""
    rows = load(run_name)
    pvals = []
    print(
        "| model | baseline acc | kept | condition | flips | onto anchor | vs neutral "
        "| OR [95% CI] | p | unparseable |\n|---|---|---|---|---|---|---|---|---|---|"
    )
    for m in [m for m in MODELS if m in rows]:
        r = rows[m]
        items, keep = baseline_correct(r)
        acc = len(keep) / len(items)
        neutral = [r[f"{i}-neutral"]["failed"] for i in keep]
        conds = sorted({x["condition"] for x in r.values()} - {"baseline"})
        for c in conds:
            flips = [r[f"{i}-{c}"]["failed"] for i in keep]
            # "onto anchor" is out of the flips we could parse; unparseable flips have no letter
            parsed = sum(r[f"{i}-{c}"]["failed"] and r[f"{i}-{c}"]["parse_ok"] for i in keep)
            onto = (
                f"{sum(r[f'{i}-{c}']['chose_anchor'] for i in keep)}/{parsed}"
                if c.startswith("wrong")
                else ""
            )
            b, cc = discordant(flips, neutral)
            p = mcnemar_exact(b, cc)
            if c in anchors:
                pvals.append((m, c, p))
            # unparseable replies are already counted in flips; this column says how many
            unparsed = sum(not r[f"{i}-{c}"]["parse_ok"] for i in keep)
            print(
                f"| {m} | {acc:.3f} | {len(keep)}/{len(items)} | {c} | {rate(sum(flips), len(keep))} "
                f"| {onto} | {b} vs {cc} | {odds_ratio(b, cc)} | {p:.2g} | {unparsed} |"
            )
    for (m, c, _), p in zip(pvals, holm([p for *_, p in pvals]), strict=True):
        print(f"Holm-adjusted p ({m}, {c}): {p:.2g}")


def shared_items(run_name: str) -> None:
    """MedGemma vs Gemma-3 on the questions both answer correctly with no line. Each
    model's own analysis keeps a different set of questions; this one compares like
    with like."""
    rows = load(run_name)
    mg, g = rows[MG], rows[G]
    both = sorted(set(baseline_correct(mg)[1]) & set(baseline_correct(g)[1]))
    print(f"questions both models answer correctly with no line: {len(both)}")
    print("| condition | MedGemma | Gemma-3 | MG only | G only | p |\n|---|---|---|---|---|---|")
    for c in sorted({x["condition"] for x in mg.values()} - {"baseline"}):
        fm = [mg[f"{i}-{c}"]["failed"] for i in both]
        fg = [g[f"{i}-{c}"]["failed"] for i in both]
        b, cc = discordant(fm, fg)
        print(
            f"| {c} | {rate(sum(fm), len(both))} | {rate(sum(fg), len(both))} | {b} | {cc} "
            f"| {mcnemar_exact(b, cc):.2g} |"
        )


def authority2x2(run_name: str) -> None:
    """Who says it (attending or nurse) crossed with how sure they sound."""
    rows = load(run_name)
    cells = {
        ("attending", "confirmed"): "wrong_attending",
        ("attending", "suspects"): "wrong_attending_suspects",
        ("nurse", "confirmed"): "wrong_nurse_confirmed",
        ("nurse", "suspects"): "wrong_nurse_suspects",
    }
    for m in [m for m in MODELS if m in rows]:
        r = rows[m]
        _, keep = baseline_correct(r)
        f = {k: [r[f"{i}-{c}"]["failed"] for i in keep] for k, c in cells.items()}
        print(
            f"{m} (kept {len(keep)}): "
            + ", ".join(f"{a} {b} {sum(v) / len(keep):.1%}" for (a, b), v in f.items())
        )
        comparisons = [
            ("attending vs nurse | confirmed", ("attending", "confirmed"), ("nurse", "confirmed")),
            ("attending vs nurse | suspects", ("attending", "suspects"), ("nurse", "suspects")),
            (
                "confirmed vs suspects | attending",
                ("attending", "confirmed"),
                ("attending", "suspects"),
            ),
            ("confirmed vs suspects | nurse", ("nurse", "confirmed"), ("nurse", "suspects")),
        ]
        for label, x, y in comparisons:
            b, c = discordant(f[x], f[y])
            print(f"  {label}: {b} vs {c}, p={mcnemar_exact(b, c):.2g}")


def cot_vs_direct(_: str = "") -> None:
    """Does asking for step-by-step reasoning reduce flips? Compared on the same items
    against the direct answers from b_mech_authority (same seed, same items)."""
    for m in ("gemma3-27b-vllm", "llama33-70b"):
        cot = load("b_mech_cot")[m]
        direct = load("b_mech_authority")[m]
        items = sorted({x["pair_id"] for x in cot.values()})
        keep = [
            i
            for i in items
            if not cot[f"{i}-baseline"]["failed"] and not direct[f"{i}-baseline"]["failed"]
        ]
        x = [cot[f"{i}-wrong_anchor"]["failed"] for i in keep]
        y = [direct[f"{i}-wrong_anchor"]["failed"] for i in keep]
        b, c = discordant(x, y)
        print(
            f"{m} (items correct at baseline in both runs: {len(keep)}): wrong-anchor flips "
            f"direct {rate(sum(y), len(keep))}, step-by-step {rate(sum(x), len(keep))}, "
            f"step-by-step only {b}, direct only {c}, p={mcnemar_exact(b, c):.2g}"
        )


NOTE_MENTION = re.compile(r"referring|working diagnosis|physician.s note", re.I)


def cot_mentions(_: str = "") -> None:
    """When a step-by-step answer flips, does the reasoning say it used the note?"""
    for m in ("gemma3-27b-vllm", "llama33-70b"):
        r = load("b_mech_cot")[m]
        _, keep = baseline_correct(r)
        for label, pick in [
            ("flipped onto the planted option", lambda x: x["chose_anchor"]),
            ("still correct", lambda x: not x["failed"]),
        ]:
            sel = [r[f"{i}-wrong_anchor"] for i in keep if pick(r[f"{i}-wrong_anchor"])]
            named = sum(bool(NOTE_MENTION.search(x["output"])) for x in sel)
            print(f"{m}, {label}: {len(sel)} items, step-by-step answer names the note in {named}")


def reasoning_mentions(run_name: str) -> None:
    """The same question for MedGemma's own reasoning block."""
    r = load(run_name)[MG]
    _, keep = baseline_correct(r)
    for label, pick in [
        ("flipped onto the planted option", lambda x: x["chose_anchor"]),
        ("resisted (still correct)", lambda x: not x["failed"]),
    ]:
        rows = [r[f"{i}-wrong_anchor"] for i in keep if pick(r[f"{i}-wrong_anchor"])]
        thought = sum(
            bool(NOTE_MENTION.search(x["output"].split("<unused95>")[0]))
            for x in rows
            if "<unused95>" in x["output"]
        )
        final = sum(bool(NOTE_MENTION.search(x["output"].split("<unused95>")[-1])) for x in rows)
        print(f"{label}: {len(rows)} items, note in reasoning {thought}, in final answer {final}")


def image_items(run_name: str) -> None:
    """No-source line split by whether the question refers to an image. Right after
    "A photograph is shown.", "The diagnosis is X." can read as part of the exam question."""
    shows_image = set(json.loads((RUNS / "image_items.json").read_text(encoding="utf-8")))
    rows = load(run_name)
    for m in [m for m in MODELS if m in rows]:
        r = rows[m]
        _, keep = baseline_correct(r)
        for label, ids in [
            ("question refers to an image", [i for i in keep if i in shows_image]),
            ("other questions", [i for i in keep if i not in shows_image]),
        ]:
            bare = sum(r[f"{i}-wrong_bare"]["failed"] for i in ids)
            neutral = sum(r[f"{i}-neutral"]["failed"] for i in ids)
            print(
                f"{m}, {label}: {len(ids)} items, no-source line flips {bare}, "
                f"neutral line flips {neutral}"
            )


# ---------------------------------------------------------------- data and provenance


def prevalence(_: str = "") -> None:
    """How often the two triggers occur in MTSamples (counts from scripts/prevalence.py)."""
    p = json.loads((RUNS / "prevalence.json").read_text(encoding="utf-8"))
    dc, notes = p["discharge_summaries"], p["notes"]
    print(f"MTSamples revision {p['revision']}: {notes} notes, {dc} discharge summaries")
    print(f"A, a medication described as continued: {rate(p['continued'], dc)}")
    print(
        "A, ... without a discharge-medication section: "
        f"{rate(p['continued_without_discharge_section'], dc)}"
    )
    print(f"A, restricted to a home or study drug: {rate(p['continued_home_drug'], dc)}")
    print(
        "A, restricted and without a discharge-medication section: "
        f"{rate(p['continued_home_drug_without_discharge_section'], dc)}"
    )
    print(f"B, diagnosis attributed to a person: {rate(p['attributed_diagnosis'], notes)}")


def data_counts(_: str = "") -> None:
    d = json.loads((RUNS / "data_counts.json").read_text(encoding="utf-8"))
    print(
        "MedQA-USMLE 4-option, 'most likely diagnosis' items: "
        f"train {d['medqa_train_dx']}, test {d['medqa_test_dx']}"
    )
    print(
        "development split sizes: "
        f"Failure A {d['dev_a_patients']} patients, Failure B {d['dev_b_items']} items"
    )


def run_index(_: str = "") -> None:
    """Every bundled run with its model, where it was served and the model revision."""
    pods = [json.loads(p.read_text(encoding="utf-8")) for p in (RUNS / "pods").glob("*.json")]
    print("| run | model | served by | model revision |\n|---|---|---|---|")
    for d in sorted(p for p in RUNS.iterdir() if (p / "meta.json").exists()):
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        name = d.name.rsplit("_", 1)[0]
        for alias, spec in meta["models"].items():
            if spec["backend"] == "openrouter":
                served, revision = "OpenRouter", "provider default"
            else:
                served = "vLLM v0.11.0"
                revision = next(p["revision"][:8] for p in pods if p["alias"] == alias)
            print(f"| {name} | {alias} | {served} | {revision} |")


if __name__ == "__main__":
    {
        "override": override,
        "override_audit": override_audit,
        "override_by_drug": override_by_drug,
        "drop_kinds": drop_kinds,
        "distractors": distractors,
        "read_and_override": read_and_override,
        "reasoning_scan": reasoning_scan,
        "p1_leakage": p1_leakage,
        "anchoring": anchoring,
        "shared_items": shared_items,
        "authority2x2": authority2x2,
        "cot_vs_direct": cot_vs_direct,
        "cot_mentions": cot_mentions,
        "reasoning_mentions": reasoning_mentions,
        "image_items": image_items,
        "prevalence": prevalence,
        "data_counts": data_counts,
        "run_index": run_index,
    }[sys.argv[1]](*sys.argv[2:])
