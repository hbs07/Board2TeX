# -*- coding: utf-8 -*-
"""recog/ocr_engine.py —— PaddleOCR 文字识别封装(主责: C 陶谱州)

验证命令(第一次运行同时就是"暖机",会下载模型,可能很慢,属正常):
    python -m recog.ocr_engine assets/test_text.png
期望结果:
    第一次: 先下载 PaddleOCR 模型(看终端进度),然后打印识别出的文字与置信度;
    第二次起: 模型走本地缓存,几秒~十几秒出结果。
    **demo 现场绝不第一次跑。**

AI 辅助说明: 见 README「诚信声明」。

数据流(冻结接口):
    B 的 Region["image"](一行图) -> recognize_text(img) -> (文字, 置信度)

版本兼容(联调关键,别删这段逻辑):
    PaddleOCR 3.x: ocr.predict(img) -> [ {rec_texts:[...], rec_scores:[...], ...} ]
    PaddleOCR 2.x: ocr.ocr(img, cls=False) -> [ [ [box, (text, score)], ... ] ]
    本模块先试 3.x 的 predict,失败再回退 2.x,两种返回结构都能解析。
"""

from __future__ import annotations

import time

# 模块级单例: 模型加载要几秒~几十秒,整个进程只加载一次
_ocr = None


def get_ocr():
    """返回 PaddleOCR 单例(第一次调用会触发模型下载/加载)。"""
    global _ocr
    if _ocr is None:
        import os
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
        from paddleocr import PaddleOCR

        try:
            # PaddleOCR 3.x 新参数
            _ocr = PaddleOCR(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                enable_mkldnn=False,
                lang="ch",
            )
        except TypeError:
            # 回退:PaddleOCR 2.x 参数
            _ocr = PaddleOCR(lang="ch", use_angle_cls=False)
    return _ocr


def _parse_3x(out):
    """解析 PaddleOCR 3.x 的 predict 结果 -> (texts, scores)。"""
    texts, scores = [], []
    for item in (out or []):
        rt = None
        rs = None
        try:                       # Result 支持下标访问
            rt, rs = item["rec_texts"], item["rec_scores"]
        except Exception:
            rt = getattr(item, "rec_texts", None)
            rs = getattr(item, "rec_scores", None)
        if rt is None:
            continue
        texts.extend(str(t) for t in rt)
        if rs is not None:
            scores.extend(float(s) for s in rs)
    return texts, scores


def _parse_2x(out):
    """解析 PaddleOCR 2.x 的 ocr 结果 -> (texts, scores)。"""
    texts, scores = [], []
    for line in (out or []):
        for seg in (line or []):
            try:
                texts.append(str(seg[1][0]))
                scores.append(float(seg[1][1]))
            except Exception:
                continue
    return texts, scores


def _run_ocr(ocr, img):
    """统一调用: 先试 3.x 的 predict,再回退 2.x 的 ocr。"""
    if hasattr(ocr, "predict"):
        try:
            texts, scores = _parse_3x(ocr.predict(img))
            if texts:
                return texts, scores
        except Exception:
            pass
    return _parse_2x(ocr.ocr(img, cls=False))


def recognize_text(img):
    """输入一行图, 返回 (文字, 置信度)。

    img 为 numpy 数组(BGR 或灰度) 或图片路径;PaddleOCR 两种都接受。
    没有识别到任何文字时返回 ("", 0.0),调用方据此判空。
    """
    ocr = get_ocr()
    texts, scores = _run_ocr(ocr, img)
    if not texts:
        return "", 0.0
    text = "".join(texts)
    conf = sum(scores) / len(scores) if scores else 0.0
    return text, conf


def warm_up() -> float:
    """加载模型并用一张极小图跑一次完整识别,返回耗时(秒)。

    用途: 开发机提前把模型下载/加载完,demo 现场只吃缓存。
    """
    import numpy as np

    t0 = time.time()
    get_ocr()
    dummy = np.full((32, 128, 3), 255, dtype=np.uint8)  # 全白小图
    recognize_text(dummy)
    return time.time() - t0


if __name__ == "__main__":
    import sys

    import cv2

    path = sys.argv[1] if len(sys.argv) > 1 else "assets/test_text.png"
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)

    print("正在加载 PaddleOCR 模型(第一次会下载,请耐心)...")
    t0 = time.time()
    get_ocr()
    print(f"模型就绪,加载耗时 {time.time() - t0:.1f}s")

    t0 = time.time()
    text, conf = recognize_text(img)
    print(f"识别耗时 {time.time() - t0:.1f}s")
    print(f"文字: {text}")
    print(f"置信度: {conf:.3f}")
