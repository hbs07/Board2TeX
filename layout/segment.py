# -*- coding: utf-8 -*-
"""layout/segment.py —— 行切分(主责: B 郭佳欣;骨架: A 提供)

验证命令(填完后运行,由 layout/pipeline.py 的自测脚本代跑):
    python -m layout.pipeline assets/test_text.png data/layout_check
期望结果:
    data/layout_check/annotated.png 里每个句子被绿/红框单独框住,
    框的数量 = 板书行数,从上到下编号 0,1,2,...

AI 辅助说明: 见 README「诚信声明」。

数据流(接口已冻结,只填函数体,不改签名):
    enhance 的二值图 -> ensure_foreground_white -> split_lines
    -> (每行) classify_line -> 组装 Region 列表(analyze_layout)

Region 冻结结构(交给 C 识别,字段名和类型不许改):
    {"bbox": (x, y, w, h), "type": "text"|"formula",
     "order": int, "image": np.ndarray, "confidence": float}

极性约定(与 preprocess/enhance.py 文件头呼应):
    enhance 输出的二值图极性不保证(通常黑字白底),
    本模块的 ensure_foreground_white 负责统一成"字=白(255)"。
    统一之后,全 layout 模块一律按 >0 为前景来判断。
"""

from __future__ import annotations

import numpy as np


def ensure_foreground_white(bin_img: np.ndarray) -> np.ndarray:
    """把二值图统一成"字=白(255)"。

    判断方法: np.mean(bin_img) > 127 说明整体偏白(黑字白底),取反即可。
    取反用 cv2.bitwise_not(bin_img)。注意: 已经是白字白底黑(整体偏黑)时不要动。
    验证: 黑字白底图输入后,np.mean(输出) < 127 且 cv2.countNonZero 明显增多。
    """
    import cv2

    if np.mean(bin_img) > 127:            # 整体偏白 = 黑字白底
        return cv2.bitwise_not(bin_img)
    return bin_img


def split_lines(bin_img: np.ndarray, min_h: int = 28) -> list[tuple[int, int]]:
    """按行投影切行,返回每行的 (y0, y1) 上下边界(左闭右开)。

    算法(参考《分工_B_版面分析.md》§4.1 与 §4.3):
      1. row_proj = (bin_img > 0).sum(axis=1)   # 每行白像素数(字=白)
      2. 从左到右扫: 投影从 0 变 >0 是一行开始,从 >0 变 0 是一行结束
      3. 连续段高度 >= min_h 才算一行(过滤噪点);不够高就丢弃
      4. 扫到结尾还没闭合的段,收尾为 (start, 图高)

    验证: test_empty_image 应返回 [];有两行字、中间空 5 行的图应返回 2 个区间。
    """
    row_proj = (bin_img > 0).sum(axis=1)   # 每行的前景像素数(字=白)
    lines: list[tuple[int, int]] = []
    start = None

    for y, v in enumerate(row_proj):
        if v > 0 and start is None:        # 空白 -> 有字: 一行开始
            start = y
        elif v == 0 and start is not None:  # 有字 -> 空白: 一行结束
            if y - start >= min_h:
                lines.append((start, y))
            start = None

    if start is not None:                  # 图像底部还有一行没收尾
        if len(row_proj) - start >= min_h:
            lines.append((start, len(row_proj)))
    return lines


def analyze_layout(binary: np.ndarray) -> list[dict]:
    """把二值图切成 Region 列表(layout 模块对外唯一入口)。

    算法步骤(参考《分工_B_版面分析.md》§4.4,文档里有完整参考代码):
      1. bin_img = ensure_foreground_white(binary)
      2. for (y0, y1) in split_lines(bin_img):
           取行图 line = bin_img[y0:y1, :]
           用列投影去掉左右空白: cols = np.where((line > 0).any(axis=0))[0]
           空行(cols 为空)跳过;切出 block = line[:, x0:x1]
           组装 Region: bbox=(x0, y0, x1-x0, y1-y0),
                       type=classify_line(block)  # 从 layout.classify 导入
                       order=-1, image=block, confidence=0.6
      3. 按 bbox 的 y 从小到大排序,重新编号 order = 0,1,2,...

    验证: 返回的每个 Region 都满足文件头注释里的冻结结构。
    """
    from layout.classify import classify_line

    bin_img = ensure_foreground_white(binary)
    regions: list[dict] = []

    for y0, y1 in split_lines(bin_img):
        line = bin_img[y0:y1, :]
        cols = np.where((line > 0).any(axis=0))[0]
        if len(cols) == 0:
            continue                       # 空行: 跳过
        x0, x1 = int(cols[0]), int(cols[-1]) + 1
        block = line[:, x0:x1]
        regions.append({
            "bbox": (x0, int(y0), x1 - x0, int(y1 - y0)),
            "type": classify_line(block),
            "order": -1,
            "image": block,
            "confidence": 0.6,             # 规则分类把握不大, 先给 0.6
        })

    regions.sort(key=lambda r: r["bbox"][1])
    for i, r in enumerate(regions):
        r["order"] = i
    return regions
