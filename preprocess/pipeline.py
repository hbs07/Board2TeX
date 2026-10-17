# -*- coding: utf-8 -*-
"""preprocess/pipeline.py —— 图像入口(主责: A 胡秉善)

验证命令:
    python -m preprocess.pipeline assets/test_text.png data/preprocess_check
期望结果:
    终端打印 bgr / binary 的尺寸;data/preprocess_check/ 下生成
    bgr.png(缩放后原图)和 binary.png(二值图)。
    B 填完 enhance 后,binary.png 应为"整页裁剪过的二值图";
    骨架阶段 enhance 是占位实现,binary 与原图相同,属预期。

AI 辅助说明: 见 README「诚信声明」。

冻结接口(Week 6 起不改,下游 layout/compose 依赖):
    load_image(path) -> np.ndarray        # BGR, 长边 <= MAX_SIDE(1600)
    preprocess(path) -> {"binary": 二值图, "bgr": 缩放后 BGR 图}

数据流:
    path -> load_image -> [B 的 enhance 四步] -> {"binary", "bgr"}

极性说明(与 enhance.py / segment.py 文件头呼应):
    本模块不保证 binary 的前景极性(通常"黑字白底");
    layout 入口的 ensure_foreground_white 负责统一成"字=白(255)"。
"""

from __future__ import annotations

import cv2
import numpy as np

from config import MAX_SIDE
from preprocess.enhance import binarize, crop_content, normalize, to_gray


def load_image(path: str, max_side: int = MAX_SIDE) -> np.ndarray:
    """读入图片并缩放,返回 BGR ndarray(长边 <= max_side)。

    - 读不到/非图片时抛 FileNotFoundError(不要返回 None,让错误尽早暴露);
    - 只在图太大时缩小,从不放大(放大只会糊)。
    """
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    h, w = img.shape[:2]
    scale = max_side / max(h, w)
    if scale < 1:
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
    return img


def preprocess(path: str) -> dict:
    """完整预处理:原始路径 -> {"binary": 二值图, "bgr": 缩放后 BGR 图}。

    四步增强全部来自 B 的 preprocess/enhance.py:
        to_gray -> normalize -> binarize -> crop_content
    A 只负责读图、缩放和按序调用,不做任何像素级处理。
    """
    bgr = load_image(path)
    gray = to_gray(bgr)              # B
    gray = normalize(gray)           # B
    bin_img = binarize(gray)         # B
    bin_img = crop_content(bin_img)  # B
    return {"binary": bin_img, "bgr": bgr}


if __name__ == "__main__":
    import os
    import sys

    if len(sys.argv) != 3:
        print("用法: python -m preprocess.pipeline <图片路径> <输出目录>")
        raise SystemExit(1)

    src, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    result = preprocess(src)
    cv2.imwrite(os.path.join(out_dir, "bgr.png"), result["bgr"])
    cv2.imwrite(os.path.join(out_dir, "binary.png"), result["binary"])

    print(f"bgr   : {result['bgr'].shape} {result['bgr'].dtype}")
    print(f"binary: {result['binary'].shape} {result['binary'].dtype}")
    print(f"已输出 2 张图到 {out_dir}/")
