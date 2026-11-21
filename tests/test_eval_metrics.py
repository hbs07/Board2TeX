# -*- coding: utf-8 -*-
"""tests/test_eval_metrics.py —— 评估指标的单元测试(维护: A 胡秉善)

跑法:
    python -m pytest -q tests/test_eval_metrics.py

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

from eval.metrics import (cer, formula_exact, formula_similarity, levenshtein,
                          normalize_text, usable_rate)


def test_levenshtein_known_pairs() -> None:
    assert levenshtein("kitten", "sitting") == 3
    assert levenshtein("", "abc") == 3
    assert levenshtein("abc", "abc") == 0


def test_cer_basic() -> None:
    assert cer("abcd", "abcd") == 0.0
    assert cer("abcd", "abxd") == 0.25
    assert cer("abcd", "") == 1.0
    assert cer("", "") == 0.0
    assert cer("", "x") == 1.0


def test_cer_ignores_extra_spaces() -> None:
    assert normalize_text("  a   b ") == "a b"
    assert cer("a b", "a   b") == 0.0


def test_formula_exact_ignores_sizing_commands() -> None:
    assert formula_exact(r"\left(\frac{1}{2}\right)", r"(\frac{1}{2})")
    assert formula_exact(r"x^{2} = 2 x", r"x^{2}=2x")
    assert formula_exact(r"x^{2}", r"x^2")
    assert not formula_exact(r"x^{2}", r"x^{3}")


def test_normalize_latex_aliases() -> None:
    from eval.metrics import normalize_latex

    assert normalize_latex(r"\operatorname*{lim}_{x\to 0}") == r"\lim_x\to0"
    assert normalize_latex(r"f^{\prime}(x)") == "f'(x)"
    assert normalize_latex(r"\mathrm{d}x") == "dx"


def test_formula_similarity_range() -> None:
    assert formula_similarity(r"x^{2}", r"x^{2}") == 1.0
    assert 0.0 <= formula_similarity(r"x^{2}", r"y") <= 1.0
    assert formula_similarity("", "") == 1.0


def test_usable_rate() -> None:
    rows = [("a.jpg", 1), ("b.jpg", 5), ("c.jpg", 3)]
    assert usable_rate(rows, max_edits=3) == 2 / 3
    assert usable_rate([], max_edits=3) == 0.0
