# -*- coding: utf-8 -*-
"""recog/formula.py —— pix2tex 公式识别封装(主责: C 陶谱州;A 提供已验证模板)

验证命令(第一次运行同时就是"暖机",会下载模型,可能很慢,属正常):
    python -m recog.formula assets/test_formula.png
期望结果:
    第一次: 先下载模型(看终端进度),然后打印识别出的 LaTeX 与耗时;
    第二次起: 模型走本地缓存,几秒~几十秒出结果。
    **Week 6 前必须完成一次成功运行,demo 现场绝不第一次跑。**

AI 辅助说明: 见 README「诚信声明」。

数据流(冻结接口):
    B 的 Region["image"](一行图) -> recognize_formula(img) -> (LaTeX, 置信度)

极性说明(联调关键,别删这段逻辑):
    layout 约定"字=白(255)"(黑底白字);pix2tex 训练数据是"白底黑字"。
    _ensure_dark_text 在识别前自动检测并取反,两边约定互不干扰。
"""

from __future__ import annotations

import time

# 模块级单例: 模型加载要几秒~几十秒,整个进程只加载一次
_tex = None


def get_tex():
    """返回 pix2tex 的 LatexOCR 单例(第一次调用会触发模型下载/加载)。"""
    global _tex
    if _tex is None:
        from pix2tex.cli import LatexOCR
        _tex = LatexOCR()
    return _tex


def _ensure_dark_text(img):
    """把行图统一成 pix2tex 期望的"白底黑字"。

    判断: 灰度均值 < 127 说明整体偏黑(黑底白字,即 layout 的"字=白"),
    整体取反;否则已经是白底黑字,原样返回。
    """
    import cv2
    import numpy as np

    arr = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    if np.mean(arr) < 127:
        return cv2.bitwise_not(img)
    return img


def to_pil(bin_img):
    """numpy 数组 -> PIL RGB 图(pix2tex 的输入类型)。"""
    import cv2
    from PIL import Image

    if bin_img.ndim == 2:
        return Image.fromarray(bin_img).convert("RGB")
    return Image.fromarray(cv2.cvtColor(bin_img, cv2.COLOR_BGR2RGB))


def recognize_formula(img):
    """输入一行图, 返回 (LaTeX 字符串, 置信度)。

    极窄的行(宽 < 20px)识别没有意义,由调用方(engine.py)过滤。
    pix2tex 不输出置信度,按指南给经验值 0.8;真正的质量兜底
    靠花括号配对检查(postprocess/engine 层)。
    """
    try:
        latex = get_tex()(to_pil(_ensure_dark_text(img)))
    except Exception:
        return "", 0.0
    return str(latex).strip(), 0.8


def warm_up() -> float:
    """加载模型并用一张极小图跑一次完整识别,返回耗时(秒)。

    用途: 开发机提前把模型下载/加载完,demo 现场只吃缓存。
    """
    import numpy as np

    t0 = time.time()
    get_tex()
    t_load = time.time() - t0
    dummy = np.full((32, 128), 255, dtype=np.uint8)  # 一张全白小图
    recognize_formula(dummy)
    return time.time() - t0


if __name__ == "__main__":
    import sys

    import cv2

    path = sys.argv[1] if len(sys.argv) > 1 else "assets/test_formula.png"
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)

    print("正在加载 pix2tex 模型(第一次会下载,请耐心)...")
    t0 = time.time()
    get_tex()
    print(f"模型就绪,加载耗时 {time.time() - t0:.1f}s")

    t0 = time.time()
    latex, conf = recognize_formula(img)
    print(f"识别耗时 {time.time() - t0:.1f}s")
    print(f"LaTeX: {latex}")
    print(f"置信度(经验值): {conf}")
