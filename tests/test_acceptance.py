# -*- coding: utf-8 -*-
"""tests/test_acceptance.py —— 验收标准看板(维护: A 胡秉善)

跑法:
    python -m pytest -q            # 快速版:不加载识别模型,几秒钟
    python -m pytest -q -m slow    # 完整版:真跑 PaddleOCR + pix2tex,约 1 分钟

每个测试对应一位组员的一条验收标准。看结果就知道状态:
    passed  = 已实现且达标
    xfailed = 负责人还没做(**正常状态,不是 bug**,原因写在 reason 里)
    xpassed = 已经做完了 -> 提醒 A 删掉这条测试的 xfail 标记
    failed  = 做了但没达标(真问题,去找负责人)

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

import os
import shutil

import numpy as np
import pytest

from compose.builder import build_body
from gui.exporter import compile_pdf, has_xelatex
from layout.pipeline import analyze_layout
from main import pipeline
from preprocess.pipeline import preprocess

SAMPLE = os.path.join("assets", "test_text.png")


# ---------------------------------------------------------------- B: 图像增强


def test_binary_is_single_channel() -> None:
    """B 的验收:binary 是单通道(下游 layout 的列投影才有意义)。"""
    pre = preprocess(SAMPLE)
    assert pre["binary"].ndim == 2, f"binary 应为 (H, W),实际 {pre['binary'].shape}"


def test_binary_is_binarized() -> None:
    """B 的验收:Otsu 之后只有 0/255,且裁掉了四周空白。"""
    pre = preprocess(SAMPLE)
    values = set(np.unique(pre["binary"]))
    assert values <= {0, 255}, f"二值图只能有 0 和 255,实际 {len(values)} 种取值"


# ---------------------------------------------------------------- B: 版面分析


def test_layout_splits_sample_into_ordered_lines() -> None:
    """B 的验收:示例板书有 5 行(英文 3 行 + 公式 2 行),至少要切出 3 行。"""
    pre = preprocess(SAMPLE)
    regions = analyze_layout(pre["binary"])

    assert len(regions) >= 3, f"5 行板书至少应切出 3 行,实际 {len(regions)}"
    assert [r["order"] for r in regions] == list(range(len(regions)))
    ys = [r["bbox"][1] for r in regions]
    assert ys == sorted(ys), "必须按从上到下排序"
    assert all(r["image"].size > 0 for r in regions), "每行必须带裁剪图"


def test_layout_classifies_formula_lines() -> None:
    """B 的验收:2 行公式要判成 formula,3 行英文判成 text。"""
    pre = preprocess(SAMPLE)
    types = [r["type"] for r in analyze_layout(pre["binary"])]
    assert types == ["text", "text", "formula", "formula", "text"], types


# ---------------------------------------------------------------- C: 识别与合成


def test_build_body_merges_text_and_wraps_formula() -> None:
    """C 的验收:连续文字并成一段,公式单独包 $$...$$。"""
    blocks = [
        {"order": 0, "type": "text", "content": "Given", "latex": "Given",
         "confidence": 0.9, "bbox": (0, 0, 10, 10)},
        {"order": 1, "type": "text", "content": " f(x)", "latex": "f(x)",
         "confidence": 0.9, "bbox": (0, 0, 10, 10)},
        {"order": 2, "type": "formula", "content": r"\int x", "latex": r"\int x",
         "confidence": 0.8, "bbox": (0, 0, 10, 10)},
    ]
    body = build_body(blocks)

    assert "Given f(x)" in body, "续行(小写开头)应合并"
    assert "$$ \\int x $$" in body, "公式必须被 $$ 包住"


def test_build_body_breaks_before_new_sentence() -> None:
    """C 的验收:标题/句号结尾后的新行必须另起一段,不能糊成一段。"""
    blocks = [
        {"order": 0, "type": "text", "content": "Derivative Rules",
         "latex": "Derivative Rules", "confidence": 0.9, "bbox": (0, 0, 10, 10)},
        {"order": 1, "type": "text", "content": "Given ...", "latex": "Given ...",
         "confidence": 0.9, "bbox": (0, 0, 10, 10)},
    ]
    body = build_body(blocks)
    assert "Derivative Rules\n\nGiven" in body, body


def test_recognize_returns_block_for_region(monkeypatch) -> None:
    """C 的验收:任意 Region 进 recognize,出来一个完整 Block(用假引擎,不加载模型)。"""
    import recog.engine as engine

    monkeypatch.setattr(engine, "recognize_text", lambda img: ("Given f(x)", 0.93))
    monkeypatch.setattr(engine, "recognize_formula", lambda img: (r"\int_0^1 x", 0.8))

    text_region = {"bbox": (0, 0, 100, 30), "type": "text", "order": 0,
                   "image": np.full((30, 100), 255, np.uint8), "confidence": 0.9}
    block = engine.recognize(text_region)
    assert block["type"] == "text"
    assert block["latex"] == "Given f(x)"
    assert block["confidence"] == pytest.approx(0.93)

    formula_region = dict(text_region, type="formula", order=1)
    fblock = engine.recognize(formula_region)
    assert fblock["latex"] == r"\int_0^1 x"


def test_escape_latex_handles_ocr_symbols() -> None:
    """C 的验收:OCR 常见的 % & ′ ² 必须变成能编译的 LaTeX。"""
    from recog.postprocess import clean_latex, escape_latex

    assert escape_latex("50% & 3′") == r"50\% \& 3'"
    assert escape_latex("x²") == r"x\textsuperscript{2}"
    assert clean_latex(r"\left( x \right)") == "( x )"


# ---------------------------------------------------------------- D: 错题本


def test_vault_add_and_list(tmp_path) -> None:
    """D 的验收:存一条错题,能查回来、能按课程筛选、能删。"""
    from vault.db import add_problem, delete_problem, init_db, list_problems, search

    con = init_db(str(tmp_path / "board2tex.db"))
    try:
        add_problem(con, course="Calculus", tags=["limit", "ch1"],
                    tex=r"$\lim_{x\to 0} x$", image_path="")
        rows = list_problems(con)
        assert len(rows) == 1
        assert rows[0][1] == "Calculus"
        assert rows[0][2] == "limit,ch1"
        assert len(search(con, "Calculus")) == 1
        assert len(search(con, "Other")) == 0
        delete_problem(con, rows[0][0])
        assert list_problems(con) == []
    finally:
        con.close()


# ---------------------------------------------------------------- 通用:PDF 编译


@pytest.mark.skipif(not has_xelatex(), reason="本机未安装 xelatex")
def test_compile_pdf_end_to_end(tmp_path) -> None:
    """A 的验收:一条龙产出的 tex 能被 xelatex 编译成 PDF。"""
    from compose.builder import compose_document
    from gui.exporter import export_tex

    doc = compose_document([])
    tex_path = tmp_path / "smoke.tex"
    export_tex(doc, str(tex_path))

    pdf_path = compile_pdf(str(tex_path), str(tmp_path))
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 1000, "PDF 太小,可能是空文档"


@pytest.mark.skipif(
    not has_xelatex() or shutil.which("pdftoppm") is None,
    reason="预览需要 xelatex + pdftoppm",
)
def test_preview_renders_pdf_pages(tmp_path) -> None:
    """预览链路: tex -> PDF -> 逐页 PNG(截图显示的就是编译后的样子)。"""
    from compose.builder import compose_document
    from gui.preview import export_preview_pdf, render_pdf_pages

    doc = compose_document([])
    pdf_path = export_preview_pdf(doc, str(tmp_path))
    pages = render_pdf_pages(pdf_path, str(tmp_path))

    assert pages, "至少应渲染出 1 页"
    assert os.path.getsize(pages[0]) > 1000, "页面图太小,可能是空白页"


# ---------------------------------------------------------------- 通用:GUI 可构造


def test_main_window_constructs_offscreen(monkeypatch) -> None:
    """GUI 框架能在无显示器环境构造出来(替代人工开窗冒烟)。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    try:
        # 先导 gui.main_window(内部先 import torch 再 import PyQt5),
        # 顺序反了会在 Windows 上触发 torch 的 c10.dll 初始化失败。
        from gui.main_window import MainWindow
        from PyQt5.QtWidgets import QApplication
    except ImportError:
        pytest.skip("未安装 PyQt5")

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        assert window.image_paths == []
        assert window.doc is None
        assert window._image_pixmaps == []
        assert window.editor_layout is not None
        assert window.preview_pane is not None
    finally:
        window.close()


# ---------------------------------------------------------------- 端到端(慢)


@pytest.mark.slow
def test_end_to_end_real_models() -> None:
    """真跑 PaddleOCR + pix2tex:照片 -> 5 个 Block -> 可编译 tex。"""
    pre, regions, doc = pipeline(SAMPLE)
    assert len(regions) == 5
    assert len(doc["blocks"]) == 5

    text_contents = " ".join(b["content"] for b in doc["blocks"] if b["type"] == "text")
    assert "Derivative" in text_contents, text_contents
    assert any(b["latex"] for b in doc["blocks"]), "至少要有一行识别出内容"
    assert "\\begin{document}" in doc["tex_source"]
