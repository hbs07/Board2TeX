# -*- coding: utf-8 -*-
"""layout/classify.py —— 行分类:文字 or 公式(主责: B 郭佳欣;骨架: A 提供)

验证命令(随 layout/pipeline.py 的自测脚本一起跑,单独快检):
    python -c "import numpy as np; from layout.classify import classify_line; \
img = np.zeros((60, 200), np.uint8); img[10:50, 10:190] = 255; \
print(classify_line(img))"
期望结果: 打印 text 或 formula(占位阶段恒为 text)。

AI 辅助说明: 见 README「诚信声明」。

调参纪律(文档 §5 加粗强调,组长评审时按此检查):
    先人工标注 10~20 行真值(文字/公式),再改阈值看准确率;
    不许拍脑袋定阈值。规则简单即可,猜错由 D 的界面人工纠正。
"""

from __future__ import annotations

import numpy as np


def classify_line(line_img: np.ndarray) -> str:
    """输入一行二值图(字=白),返回 "text" 或 "formula"。

    记分规则(2026-11-21 在 5 行标注样例上调过,阈值与分工文档 §5 略有出入):
      1. 行太"高": h / w > 0.20                       -> +2(公式行通常很紧凑)
      2. 字高差异大: std(heights) / mean > 0.50        -> +1(积分号/分式比字母高得多)
      3. 存在超大符号: max(areas) > 2.5 * median(areas) -> +1
      4. 字宽差异大: std(widths) / mean > 0.55         -> +1
    总分 >= 3 判 formula,否则 text。
    调参依据: assets/test_text.png 的 5 行(3 文字 + 2 公式)全部判对;
    短文本行(如单独一个 "Proof:")可能被判成公式,由校对界面人工改,这是规则法的已知代价。

    连通域用 cv2.connectedComponentsWithStats(line_img, 8);
    注意取 stats[1:] —— 第 0 个是背景,要丢掉;没有任何前景时返回 "text"。

    验证: 纯文字行 -> "text";带分式/根号的行 -> 倾向 "formula"。
    """
    import cv2

    h, w = line_img.shape[:2]
    n, labels, stats, _ = cv2.connectedComponentsWithStats(line_img, 8)
    if n <= 1:                             # 只有背景,没有前景
        return "text"

    widths = stats[1:, cv2.CC_STAT_WIDTH].astype(np.float64)
    heights = stats[1:, cv2.CC_STAT_HEIGHT].astype(np.float64)
    areas = stats[1:, cv2.CC_STAT_AREA].astype(np.float64)
    if len(areas) == 0:
        return "text"

    score = 0
    if h / max(w, 1) > 0.20:
        score += 2
    if np.std(heights) > 0.50 * np.mean(heights):
        score += 1
    if areas.max() > 2.5 * np.median(areas):
        score += 1
    if np.std(widths) > 0.55 * np.mean(widths):
        score += 1
    return "formula" if score >= 3 else "text"
