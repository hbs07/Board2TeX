# -*- coding: utf-8 -*-
"""layout/visualize.py —— 标注可视化(主责: B 郭佳欣;骨架: A 提供)

验证命令(随 layout/pipeline.py 的自测脚本一起跑):
    python -m layout.pipeline assets/test_text.png data/layout_check
期望结果: data/layout_check/annotated.png 生成,绿框=text,红框=formula,
          框左上角标 "序号:类型"。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

import numpy as np


def draw_regions(bin_img: np.ndarray, regions: list[dict], out_path: str) -> np.ndarray:
    """在二值图上画 Region 框并存盘,返回标注图(BGR)。

    算法步骤(参考《分工_B_版面分析.md》§6,文档里有完整参考代码):
      1. vis = cv2.cvtColor(bin_img, cv2.COLOR_GRAY2BGR)   # 转三通道才能上彩色
      2. 遍历 regions: 红色(0,0,255) 画 formula,绿色(0,255,0) 画 text
         cv2.rectangle(vis, (x, y), (x+w, y+h), color, 2)
      3. 框左上角写文字: cv2.putText(vis, f'{order}:{type}', (x, max(y-5, 12)),
         cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
      4. cv2.imwrite(out_path, vis)

    验证: 打开生成的图,框应贴合每行内容,编号从上到下递增。
    """
    import cv2

    vis = cv2.cvtColor(bin_img, cv2.COLOR_GRAY2BGR) if bin_img.ndim == 2 else bin_img.copy()
    for r in regions:
        x, y, w, h = r["bbox"]
        color = (0, 0, 255) if r["type"] == "formula" else (0, 255, 0)
        cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)
        cv2.putText(vis, f'{r["order"]}:{r["type"]}', (x, max(y - 5, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.imwrite(out_path, vis)
    return vis
