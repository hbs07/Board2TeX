# -*- coding: utf-8 -*-
"""tests/test_contracts.py —— 冻结接口的契约测试(维护: A 胡秉善)

跑法:
    python -m pytest -q

这些测试只回答一个问题:**改实现时,有没有把冻结接口改坏?**
所以只查字段名、类型、取值边界,不查算法效果(效果由各人的单测和
tests/test_acceptance.py 管)。

红了怎么办:
    1. 看断言信息里是哪个接口;
    2. 对照《分工_X_….md》的"冻结接口"一节;
    3. 确实需要改接口时,由 A 统一改「生产代码 + 分工文档 + 本文件」三处,
       并在群里通知全组,不允许单人直接改。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

import os

import numpy as np
import pytest

from compose.builder import build_body, compose_document
from config import MAX_SIDE
from layout.pipeline import analyze_layout
from main import pipeline
from preprocess.pipeline import load_image, preprocess

SAMPLE = os.path.join("assets", "test_text.png")

REGION_KEYS = {"bbox", "type", "order", "image", "confidence"}
BLOCK_KEYS = {"order", "type", "content", "latex", "confidence", "bbox"}


# ---------------------------------------------------------------- 公共断言


def _assert_region(r: dict) -> None:
    """校验一个 Region 是否满足冻结结构。"""
    assert isinstance(r, dict), "Region 必须是 dict"
    assert set(r) == REGION_KEYS, f"Region 字段不对: {sorted(r)}"
    x, y, w, h = r["bbox"]
    assert all(isinstance(v, (int, np.integer)) for v in (x, y, w, h)), "bbox 必须是 4 个整数"
    assert w > 0 and h > 0, f"bbox 宽高必须为正: {r['bbox']}"
    assert r["type"] in ("text", "formula"), f"type 只能是 text/formula: {r['type']}"
    assert isinstance(r["order"], (int, np.integer)), "order 必须是整数"
    assert isinstance(r["image"], np.ndarray), "image 必须是 ndarray"
    assert 0.0 <= float(r["confidence"]) <= 1.0, "confidence 必须在 0~1"


def _assert_block(b: dict) -> None:
    """校验一个 Block 是否满足冻结结构。"""
    assert isinstance(b, dict), "Block 必须是 dict"
    assert set(b) == BLOCK_KEYS, f"Block 字段不对: {sorted(b)}"
    assert b["type"] in ("text", "formula"), f"type 只能是 text/formula: {b['type']}"
    assert isinstance(b["order"], (int, np.integer)), "order 必须是整数"
    assert isinstance(b["content"], str), "content 必须是 str"
    assert isinstance(b["latex"], str), "latex 必须是 str"
    assert 0.0 <= float(b["confidence"]) <= 1.0, "confidence 必须在 0~1"
    x, y, w, h = b["bbox"]
    assert all(isinstance(v, (int, np.integer)) for v in (x, y, w, h)), "bbox 必须是 4 个整数"


def _two_line_binary() -> np.ndarray:
    """人造二值图:两条白色横带(字=白),不依赖任何模型。"""
    img = np.zeros((120, 300), np.uint8)
    img[20:50, 30:270] = 255
    img[80:110, 30:270] = 255
    return img


def _fake_regions() -> list[dict]:
    """人造 Region 列表,用来单独测 compose,不经过 B。"""
    return [
        {"bbox": (10, 10, 100, 30), "type": "text", "order": 0,
         "image": np.zeros((30, 100), np.uint8), "confidence": 0.9},
        {"bbox": (10, 50, 100, 40), "type": "formula", "order": 1,
         "image": np.zeros((40, 100), np.uint8), "confidence": 0.8},
    ]


# ---------------------------------------------------------------- 图像入口(A)


def test_load_image_returns_bgr_and_respects_max_side() -> None:
    img = load_image(SAMPLE)
    assert isinstance(img, np.ndarray)
    assert img.dtype == np.uint8
    assert img.ndim == 3 and img.shape[2] == 3, "必须是 BGR 三通道"
    assert max(img.shape[:2]) <= MAX_SIDE, f"长边超过 MAX_SIDE={MAX_SIDE}"


def test_load_image_raises_on_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_image(os.path.join("assets", "__不存在__.png"))


def test_preprocess_returns_binary_and_bgr() -> None:
    pre = preprocess(SAMPLE)
    assert set(pre) == {"binary", "bgr"}, f"pre 字段不对: {sorted(pre)}"
    # 最终契约是 (H, W) 单通道;占位期 B 的 to_gray 原样返回三通道,
    # 因此这里只查"维度合法",单通道的验收在 test_acceptance.test_binary_is_single_channel。
    assert pre["binary"].ndim in (2, 3), "binary 必须是单通道或三通道图像"
    assert pre["binary"].dtype == np.uint8
    assert pre["bgr"].ndim == 3 and pre["bgr"].shape[2] == 3


# ---------------------------------------------------------------- 版面(B)


def test_analyze_layout_returns_valid_regions() -> None:
    regions = analyze_layout(_two_line_binary())
    assert isinstance(regions, list), "analyze_layout 必须返回 list"
    for r in regions:
        _assert_region(r)
    assert [r["order"] for r in regions] == list(range(len(regions))), \
        "order 必须是从 0 开始连续递增"


# ---------------------------------------------------------------- 合成(C)


def test_compose_document_returns_blocks_and_tex_source() -> None:
    doc = compose_document(_fake_regions())
    assert set(doc) == {"blocks", "tex_source"}, f"Document 字段不对: {sorted(doc)}"
    assert len(doc["blocks"]) == 2, "一个 Region 必须对应一个 Block"
    for b in doc["blocks"]:
        _assert_block(b)
    assert [b["order"] for b in doc["blocks"]] == [0, 1], "blocks 必须保持 Region 的顺序"

    tex = doc["tex_source"]
    assert r"\documentclass" in tex, "tex_source 必须包含完整模板头"
    assert r"\begin{document}" in tex and r"\end{document}" in tex
    assert "% BODY" not in tex, "模板占位符 % BODY 必须被替换掉"


def test_build_body_returns_string() -> None:
    assert isinstance(build_body([]), str)


# ---------------------------------------------------------------- 导出(A)


def test_export_tex_writes_utf8(tmp_path) -> None:
    from gui.exporter import export_tex

    doc = compose_document([])
    doc["tex_source"] += "\n% 中文注释: 编码测试\n"
    path = tmp_path / "out.tex"
    export_tex(doc, str(path))

    text = path.read_text(encoding="utf-8")
    assert text.startswith("\\documentclass")
    assert "中文注释" in text, "必须用 UTF-8 写入,否则中文/公式会乱码"


def test_compile_pdf_fails_fast_without_xelatex(monkeypatch) -> None:
    from gui import exporter

    monkeypatch.setattr(exporter, "has_xelatex", lambda: False)
    with pytest.raises(RuntimeError, match="xelatex"):
        exporter.compile_pdf("whatever.tex", ".")


def test_exporter_does_not_import_pyqt() -> None:
    """exporter 必须能被纯命令行环境 import(设计约束,见文件头)。"""
    import subprocess
    import sys

    code = "import sys, gui.exporter; assert 'PyQt5' not in sys.modules"
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    proc = subprocess.run([sys.executable, "-c", code],
                          capture_output=True, text=True, cwd=root)
    assert proc.returncode == 0, proc.stderr


# ---------------------------------------------------------------- 一条龙(A)


def test_pipeline_end_to_end_types() -> None:
    pre, regions, doc = pipeline(SAMPLE)
    assert set(pre) == {"binary", "bgr"}
    assert isinstance(regions, list)
    assert set(doc) == {"blocks", "tex_source"}
    assert len(doc["blocks"]) == len(regions), "blocks 与 regions 必须一一对应"
