"""Statistics for paired comparisons.

Every comparison in this project is paired: the same note or exam item is shown
under two conditions (or to two models). Only the discordant pairs carry
information, so b = pairs where only the first side failed and c = pairs where
only the second side failed.
"""

import math

from scipy import stats


def wilson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson score interval for a proportion k/n."""
    z = stats.norm.ppf(1 - alpha / 2)
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar test: a binomial test of b against b + c at p = 0.5."""
    if b + c == 0:
        return 1.0
    return float(min(1.0, 2 * stats.binom.cdf(min(b, c), b + c, 0.5)))


def paired_diff_ci(b: int, c: int, n: int, alpha: float = 0.05) -> tuple[float, float, float]:
    """Difference of two paired proportions, (b - c) / n, with a Wald interval."""
    z = stats.norm.ppf(1 - alpha / 2)
    d = (b - c) / n
    se = math.sqrt(b + c - (b - c) ** 2 / n) / n
    return d, d - z * se, d + z * se


def holm(pvalues: list[float]) -> list[float]:
    """Holm step-down adjustment, returned in the input order."""
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    adjusted, running = [0.0] * len(pvalues), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[i]))
        adjusted[i] = running
    return adjusted
