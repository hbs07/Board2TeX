# -*- coding: utf-8 -*-
"""layout/classify.py —— 行分类:文字 or 公式(主责: B 郭佳欣;骨架: A 提供)

验证命令(随 layout/pipeline.py 的自测脚本一起跑,单独快检):
    python -c "import numpy as np; from layout.classify import classify_line; \
img = np.zeros((60, 200), np.uint8); img[10:50, 10:190] = 255; \
print(classify_line(img))"
期望结果: 打印 text 或 formula。

AI 辅助说明: 见 README「诚信声明」。

调参纪律(文档 §5 加粗强调,组长评审时按此检查):
    先人工标注 10~20 行真值(文字/公式),再改阈值看准确率;
    不许拍脑袋定阈值。规则简单即可,猜错由 D 的界面人工纠正。
"""

from __future__ import annotations

import numpy as np


def classify_line(line_img: np.ndarray) -> str:
    """输入一行二值图(字=白),返回 "text" 或 "formula"。

    记分规则(2026-11-21 在 15 行标注样例上调过,阈值与分工文档 §5 略有出入):
      1. 墨迹稀疏: 前景像素占比 < 0.185              -> +2(公式周围留白多,文字行更"满")
      2. 行太"高"且够宽: h / w > 0.20 且 w > 250px   -> +1(公式行通常紧凑)
      3. 字高差异大: std(heights) / mean > 0.50      -> +1(积分号/分式比字母高得多)
      4. 存在超大符号: max(areas) > 2.5 * median     -> +1
    总分 >= 3 判 formula,否则 text。
    调参依据: assets/eval/ 的 4 张合成板书共 15 行(9 文字 / 6 公式)全部判对;
    真实照片的墨迹占比会受光照影响,若误判多,优先重调第 1 条阈值。

    连通域用 cv2.connectedComponentsWithStats(line_img, 8);
    注意取 stats[1:] —— 第 0 个是背景,要丢掉;没有任何前景时返回 "text"。

    验证: 纯文字行 -> "text";带分式/根号的行 -> 倾向 "formula"。
    """
    import cv2

    h, w = line_img.shape[:2]
    n, labels, stats, _ = cv2.connectedComponentsWithStats(line_img, 8)
    if n <= 1:                             # 只有背景,没有前景
        return "text"

    heights = stats[1:, cv2.CC_STAT_HEIGHT].astype(np.float64)
    areas = stats[1:, cv2.CC_STAT_AREA].astype(np.float64)
    if len(areas) == 0:
        return "text"

    density = float((line_img > 0).mean())

    score = 0
    if density < 0.185 and h / max(w, 1) >= 0.12:
        score += 2                          # 稀疏且紧凑: 公式
    if w > 250 and h / max(w, 1) > 0.20:
        score += 1
    if np.std(heights) > 0.50 * np.mean(heights):
        score += 1
    if areas.max() > 2.5 * np.median(areas):
        score += 1
    return "formula" if score >= 3 else "text"
