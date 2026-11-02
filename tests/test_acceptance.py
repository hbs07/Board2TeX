# -*- coding: utf-8 -*-
"""tests/test_acceptance.py —— 验收标准看板(维护: A 胡秉善)

每个测试对应某位组员的一条验收标准。跑 `python -m pytest -q`,看结果就知道进度:

    passed  = 已实现且达标
    xfailed = 负责人还没做(**正常状态,不是 bug**,原因写在 reason 里)
    xpassed = 已经做完了 -> 提醒 A 删掉这条测试的 xfail 标记
    failed  = 做了但没达标(真问题,去找负责人)

所以这个文件同时也是周会的进度依据:xfail 数量减少 = 进度在走。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

import os

import numpy as np
import pytest

from compose.builder import build_body
from gui.exporter import compile_pdf, has_xelatex
from layout.pipeline import analyze_layout
from preprocess.pipeline import preprocess

SAMPLE = os.path.join("assets", "test_text.png")


# ---------------------------------------------------------------- B: 图像增强


@pytest.mark.xfail(reason="B 尚未实现:preprocess/enhance.py 的 to_gray 仍是占位(BGR 原样返回)",
                   strict=False)
def test_binary_is_single_channel() -> None:
    """B 的验收(第一个小目标):preprocess 的 binary 必须是单通道二值图。

    这一条一旦变成 xpassed,说明 to_gray/normalize/binarize 已经接上,
    下游 layout 的 `(bin_img > 0).sum(axis=1)` 才有意义。
    """
    pre = preprocess(SAMPLE)
    assert pre["binary"].ndim == 2, f"binary 应为 (H, W),实际 {pre['binary'].shape}"
    assert set(np.unique(pre["binary"])) <= {0, 255}, "二值图只能有 0 和 255"


# ---------------------------------------------------------------- B: 版面分析


@pytest.mark.xfail(reason="B 尚未实现:layout/segment.py 的 split_lines/analyze_layout 仍是占位",
                   strict=False)
def test_layout_splits_sample_into_ordered_lines() -> None:
    """B 的验收:工整板书能被切成多行,按阅读顺序编号。"""
    pre = preprocess(SAMPLE)
    regions = analyze_layout(pre["binary"])

    assert len(regions) >= 2, f"示例图至少应切出 2 行,实际 {len(regions)}"
    assert [r["order"] for r in regions] == list(range(len(regions)))
    ys = [r["bbox"][1] for r in regions]
    assert ys == sorted(ys), "必须按从上到下排序"
    assert all(r["image"].size > 0 for r in regions), "每行必须带裁剪图"


# ---------------------------------------------------------------- C: 识别与合成


@pytest.mark.xfail(reason="C 尚未实现:compose/builder.py 的 build_body 仍是占位",
                   strict=False)
def test_build_body_merges_text_and_wraps_formula() -> None:
    """C 的验收:连续文字并成一段,公式单独包 $$...$$。"""
    blocks = [
        {"order": 0, "type": "text", "content": "Given", "latex": "Given",
         "confidence": 0.9, "bbox": (0, 0, 10, 10)},
        {"order": 1, "type": "text", "content": " f(x)", "latex": " f(x)",
         "confidence": 0.9, "bbox": (0, 0, 10, 10)},
        {"order": 2, "type": "formula", "content": r"\int x", "latex": r"\int x",
         "confidence": 0.8, "bbox": (0, 0, 10, 10)},
    ]
    body = build_body(blocks)

    assert "Given f(x)" in body, "连续文字行应合并,不能一行一段"
    assert "$$ \\int x $$" in body, "公式必须被 $$ 包住"


@pytest.mark.xfail(reason="C 尚未接入:recog/engine.py 还不存在",
                   strict=False)
def test_recognize_returns_block_for_region() -> None:
    """C 的验收:任意 Region 进 recognize,出来一个完整 Block。"""
    import numpy as np

    from recog.engine import recognize

    region = {"bbox": (0, 0, 100, 30), "type": "text", "order": 0,
              "image": np.full((30, 100), 255, np.uint8), "confidence": 0.9}
    block = recognize(region)

    assert block["order"] == 0
    assert block["latex"], "识别结果不能为空"


# ---------------------------------------------------------------- D: 错题本


@pytest.mark.xfail(reason="D 尚未实现:vault/db.py 全是 NotImplementedError",
                   strict=False)
def test_vault_add_and_list(tmp_path) -> None:
    """D 的验收:存一条错题,能查回来。"""
    from vault.db import add_problem, init_db, list_problems

    con = init_db(str(tmp_path / "board2tex.db"))
    try:
        add_problem(con, course="Calculus", tags=["limit", "ch1"],
                    tex=r"$\lim_{x\to 0} x$", image_path="")
        rows = list_problems(con)
        assert len(rows) == 1
        assert rows[0][1] == "Calculus", "course 字段应按列序返回"
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


# ---------------------------------------------------------------- 通用:GUI 可构造


def test_main_window_constructs_offscreen(monkeypatch) -> None:
    """GUI 框架能在无显示器环境构造出来(替代人工开窗冒烟)。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    try:
        from PyQt5.QtWidgets import QApplication
    except ImportError:
        pytest.skip("未安装 PyQt5")

    from gui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        assert window.image_path is None
        assert window.doc is None
        assert window.image_label is not None
        assert window.editor_layout is not None
    finally:
        window.close()
