"""The write-up figure, drawn from the run outputs."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager

from analyze import load
from clinfail.eval.metrics import wilson_ci

OUT = Path("figures")
FONTS = Path("assets/fonts")
INK, MUTED, RULE = "#111111", "#444444", "#BBBBBB"
COLORS = {"medgemma-27b": "#1F3A5F", "gemma3-27b-vllm": "#D9822B", "llama33-70b": "#3A8F5C"}
MARKERS = {"medgemma-27b": "o", "gemma3-27b-vllm": "s", "llama33-70b": "^"}
SHORT = {
    "medgemma-27b": "MedGemma",
    "gemma3-27b-vllm": "Gemma-3 (base)",
    "llama33-70b": "Llama-3.3",
}


def style(size: float = 9) -> None:
    for f in ("SourceSans3-Regular.ttf", "SourceSans3-Semibold.ttf", "SourceSans3-It.ttf"):
        font_manager.fontManager.addfont(str(FONTS / f))
    plt.rcParams.update(
        {
            "font.family": "Source Sans 3",
            "font.size": size,
            "axes.edgecolor": RULE,
            "axes.labelcolor": MUTED,
            "xtick.color": MUTED,
            "ytick.color": INK,
            "text.color": INK,
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "axes.spines.top": False,
            "axes.spines.right": False,
            # fixed ids so the SVGs come out byte-identical on every run
            "svg.fonttype": "path",
            "svg.hashsalt": "clinfail",
        }
    )


def rate(rows: list[dict], key: str = "failed") -> tuple[float, float, float]:
    """Percentage of rows that failed, with its Wilson 95% interval."""
    k, n = sum(bool(r[key]) for r in rows), len(rows)
    lo, hi = wilson_ci(k, n)
    return 100 * k / n, 100 * lo, 100 * hi


def flips(r: dict, cond: str) -> tuple[float, float, float]:
    """Flip rate under a condition, among items the model answers correctly with no line."""
    items = sorted({x["pair_id"] for x in r.values()})
    keep = [i for i in items if not r[f"{i}-baseline"]["failed"]]
    return rate([r[f"{i}-{cond}"] for i in keep])


def dot(ax, y: float, est: tuple[float, float, float], model: str, label=None, ms: float = 5):
    m, lo, hi = est
    ax.errorbar(
        m,
        y,
        xerr=[[max(0.0, m - lo)], [max(0.0, hi - m)]],
        fmt=MARKERS[model],
        color=COLORS[model],
        ms=ms,
        mec="white",
        mew=0.8,
        elinewidth=0.9,
        capsize=2,
        capthick=0.9,
        label=label,
    )


def tag(ax, est: tuple[float, float, float], y: float, left: bool = False) -> None:
    """Write the rate next to its error bar."""
    x, ha = (est[1] - 1, "right") if left else (est[2] + 1, "left")
    ax.text(x, y, f"{est[0]:.0f}%", va="center", ha=ha, fontsize=plt.rcParams["font.size"] - 0.5)


def save(fig, name: str) -> None:
    fig.savefig(OUT / f"{name}.svg", metadata={"Date": None})
    fig.savefig(OUT / f"{name}.png", dpi=300)


def figure_b() -> None:
    """Flip rate for the same wrong option stated by different sources and with
    different certainty, on the confirmation items."""
    style(8.5)
    rows = load("b_posthoc_certainty")
    lines = [
        ("neutral", "neutral line"),
        ("wrong_anchor", "referral note *"),
        ("wrong_nurse_suspects", "nurse suspects"),
        ("wrong_attending_suspects", "attending suspects"),
        ("wrong_nurse_confirmed", "nurse has confirmed"),
        ("wrong_attending", "attending has confirmed"),
        ("wrong_bare", "no source"),
    ][::-1]
    # sized to sit beside the example in the write-up
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    for y in range(0, len(lines), 2):
        ax.axhspan(y - 0.5, y + 0.5, color="#F2F4F7", lw=0, zorder=0)
    models = [(0.26, "medgemma-27b"), (0.0, "gemma3-27b-vllm"), (-0.26, "llama33-70b")]
    for y, (c, _) in enumerate(lines):
        for off, m in models:
            est = flips(rows[m], c)
            dot(ax, y + off, est, m, SHORT[m] if y == 0 else None, ms=4)
            if m == "medgemma-27b":
                tag(ax, est, y + off)
    ax.set_yticks(range(len(lines)), [label for _, label in lines])
    ax.tick_params(axis="y", length=0)
    ax.xaxis.grid(True, color="#E3E6EA", lw=0.6)
    ax.set_axisbelow(True)
    ax.set_xlim(0, 50)
    ax.set_ylim(-0.5, len(lines) - 0.5)
    ax.set_xlabel("Correct diagnoses flipped (%)")
    handles, labels = ax.get_legend_handles_labels()
    # centred on the whole figure, since the long row labels push the axes right
    fig.legend(
        handles,
        labels,
        frameon=False,
        loc="upper center",
        ncol=3,
        handletextpad=0.2,
        columnspacing=1.0,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    save(fig, "fig_b_deference")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    figure_b()
    print(f"wrote figures to {OUT}")
