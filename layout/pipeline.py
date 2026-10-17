# -*- coding: utf-8 -*-
"""layout/pipeline.py —— layout 模块对外唯一出口(A 维护,B 不要修改)

为什么有这个文件:
    main.py 的冻结接口写的是 `from layout.pipeline import analyze_layout`。
    本文件只做转口 + 自测脚本;真正的实现在 segment/classify 里,由 B 维护。

验证命令(给 B 的整体自测,也是 A 评审时第一步跑的):
    python -m layout.pipeline assets/test_text.png data/layout_check
期望结果:
    data/layout_check/annotated.png 生成;
    B 填完全部函数后,图中每行板书被单独框住,编号从上到下递增。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

from layout.segment import analyze_layout

__all__ = ["analyze_layout"]


if __name__ == "__main__":
    import os
    import sys

    import cv2

    from config import MAX_SIDE
    from layout.visualize import draw_regions
    from preprocess.enhance import binarize, crop_content, normalize, to_gray

    if len(sys.argv) != 3:
        print("用法: python -m layout.pipeline <图片路径> <输出目录>")
        raise SystemExit(1)

    src, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    # 复现 A 的 load_image 缩放逻辑(正式版以 preprocess/pipeline.py 为准)
    bgr = cv2.imread(src)
    if bgr is None:
        raise FileNotFoundError(src)
    h, w = bgr.shape[:2]
    scale = MAX_SIDE / max(h, w)
    if scale < 1:
        bgr = cv2.resize(bgr, (int(w * scale), int(h * scale)))

    # 走一遍 enhance(B 填完后这里是真实二值图;占位阶段仍是彩色图,仅供跑通)
    gray = to_gray(bgr)
    gray = normalize(gray)
    bin_img = crop_content(binarize(gray))

    regions = analyze_layout(bin_img)
    print(f"切出 {len(regions)} 个 Region")  # 占位阶段为 0 属正常

    vis = draw_regions(bin_img, regions, os.path.join(out_dir, "annotated.png"))
    cv2.imwrite(os.path.join(out_dir, "annotated.png"), vis)
    print(f"标注图已存到 {out_dir}/annotated.png")
