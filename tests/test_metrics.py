import pytest

from clinfail.eval.metrics import discordant_or, holm, mcnemar_exact, paired_diff_ci, wilson_ci


def test_wilson():
    lo, hi = wilson_ci(10, 100)
    assert lo == pytest.approx(0.05523, abs=1e-4)
    assert hi == pytest.approx(0.17437, abs=1e-4)
    assert wilson_ci(0, 20)[0] == 0.0
    assert wilson_ci(20, 20)[1] == 1.0


def test_mcnemar():
    assert mcnemar_exact(0, 6) == pytest.approx(0.03125)  # 2 * 0.5**6
    assert mcnemar_exact(0, 0) == 1.0
    assert mcnemar_exact(5, 5) == 1.0


def test_holm():
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert holm([0.5]) == [0.5]


def test_paired_diff_ci():
    d, lo, hi = paired_diff_ci(62, 1, 300)
    assert d == pytest.approx(61 / 300)
    assert lo < d < hi
    assert paired_diff_ci(5, 5, 100)[0] == 0


def test_discordant_or():
    est, lo, hi = discordant_or(62, 1)
    assert est == 62
    assert 1 < lo < 62 < hi
    assert discordant_or(5, 0)[0] == float("inf")
    assert discordant_or(0, 5)[1] == 0
