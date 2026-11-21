# -*- coding: utf-8 -*-
"""recog/engine.py —— 识别统一入口(主责: C 陶谱州)

验证命令(需要模型,首次会下载):
    python -m recog.engine assets/test_text.png
期望结果:
    打印每行的 order/type/识别内容/置信度,以及整篇 .tex 的前 300 字符。

AI 辅助说明: 见 README「诚信声明」。

分工:
    layout 的 Region -> recognize(region) -> Block
      type == "formula" -> recog.formula.recognize_formula  (pix2tex)
      type == "text"    -> recog.ocr_engine.recognize_text  (PaddleOCR)

两个必须记住的细节:
    1. layout 的图是"字=白、背景=黑";PaddleOCR 与 pix2tex 都要"白底黑字",
       所以进引擎前要统一取反(见 _to_engine_image)。
    2. 太窄的行(宽 < 20px)识别没有意义,直接返回空 Block,省掉一次推理。
"""

from __future__ import annotations

import numpy as np

from recog.formula import recognize_formula
from recog.ocr_engine import recognize_text
from recog.postprocess import clean_latex, escape_latex

MIN_WIDTH = 20          # 窄于此宽度的行不做识别
FORMULA_CONF = 0.8      # pix2tex 不输出置信度,用经验值


def _to_engine_image(img: np.ndarray) -> np.ndarray:
    """layout 的"字=白"行图 -> 引擎要的"白底黑字"三通道图。"""
    import cv2

    out = img
    if out.ndim == 2:
        out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
    if float(np.mean(out)) < 127:      # 整体偏黑 = 当前是白字黑底
        out = cv2.bitwise_not(out)
    return out


def _empty_block(region: dict) -> dict:
    """识别不出内容时的占位 Block(字段必须齐全,下游要用)。"""
    return {
        "order": region["order"],
        "type": region["type"],
        "content": "",
        "latex": "",
        "confidence": 0.0,
        "bbox": region["bbox"],
    }


def recognize(region: dict) -> dict:
    """一个 Region -> 一个 Block。"""
    img = region.get("image")
    kind = region.get("type", "text")

    if img is None or img.size == 0 or img.shape[1] < MIN_WIDTH:
        return _empty_block(region)

    engine_img = _to_engine_image(img)

    if kind == "formula":
        content, conf = recognize_formula(engine_img)
        latex = clean_latex(content)
    else:
        content, conf = recognize_text(engine_img)
        latex = escape_latex(content)

    return {
        "order": region["order"],
        "type": kind,
        "content": content,
        "latex": latex,
        "confidence": float(conf),
        "bbox": region["bbox"],
    }


if __name__ == "__main__":
    import sys

    from compose.builder import build_body, compose_document
    from layout.pipeline import analyze_layout
    from preprocess.pipeline import preprocess

    path = sys.argv[1] if len(sys.argv) > 1 else "assets/test_text.png"
    pre = preprocess(path)
    regions = analyze_layout(pre["binary"])

    print(f"共 {len(regions)} 个 Region,开始识别(首次会加载两个模型)...")
    doc = compose_document(regions)

    for b in doc["blocks"]:
        print(f'[{b["order"]}] {b["type"]:<7} conf={b["confidence"]:.2f} '
              f'content={b["content"][:60]!r}')

    print("\n--- 正文预览 ---")
    print(build_body(doc["blocks"])[:300])
