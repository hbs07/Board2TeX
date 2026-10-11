# -*- coding: utf-8 -*-
"""layout/classify.py —— 行分类:文字 or 公式(主责: B 郭佳欣;骨架: A 提供)

验证命令(随 layout/pipeline.py 的自测脚本一起跑,单独快检):
    python -c "import numpy as np; from layout.classify import classify_line; \
img = np.zeros((60, 200), np.uint8); img[10:50, 10:190] = 255; \
print(classify_line(img))"
期望结果: 打印 text 或 formula(占位阶段恒为 text)。

AI 辅助范围(课程要求):
    本骨架由 AI 依据《Board2TeX_分工_B_版面分析.md》§5 生成函数签名、
    类型注解与文档字符串;函数体为占位实现,由 B 独立实现并替换。

调参纪律(文档 §5 加粗强调,组长评审时按此检查):
    先人工标注 10~20 行真值(文字/公式),再改阈值看准确率;
    不许拍脑袋定阈值。规则简单即可,猜错由 D 的界面人工纠正。
"""

from __future__ import annotations

import numpy as np


def classify_line(line_img: np.ndarray) -> str:
    """输入一行二值图(字=白),返回 "text" 或 "formula"。

    记分规则(参考《分工_B_版面分析.md》§5,共 3 分,>=2 分判公式):
      1. 连通域宽度差异大: np.std(widths) > 0.5 * np.mean(widths)   -> +1
      2. 存在超大符号:   areas.max() > 3 * np.median(areas)         -> +1
      3. 整行偏高:       h / max(w, 1) > 0.35                       -> +1
    连通域用 cv2.connectedComponentsWithStats(line_img, 8);
    注意取 stats[1:] —— 第 0 个是背景,要丢掉;没有任何前景时返回 "text"。

    验证: 纯文字行 -> "text";带分式/根号的行 -> 倾向 "formula"。
    """
    # TODO(B): 参考《分工_B_版面分析.md》§5 实现(约 10 行,含 import cv2)
    return "text"  # 占位: 恒判文字,保证流水线能跑;调参阶段再改阈值
