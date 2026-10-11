# -*- coding: utf-8 -*-
"""layout/visualize.py —— 标注可视化(主责: B 郭佳欣;骨架: A 提供)

验证命令(随 layout/pipeline.py 的自测脚本一起跑):
    python -m layout.pipeline assets/test_text.png data/layout_check
期望结果: data/layout_check/annotated.png 生成,绿框=text,红框=formula,
          框左上角标 "序号:类型"。

AI 辅助范围(课程要求):
    本骨架由 AI 依据《Board2TeX_分工_B_版面分析.md》§6 生成函数签名、
    类型注解与文档字符串;函数体为占位实现,由 B 独立实现并替换。
    本函数是给报告和联调看的"眼睛",不参与识别,写错不影响主流程。
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
    # TODO(B): 参考《分工_B_版面分析.md》§6 实现(约 8 行,含 import cv2)
    # 占位: 只保证能存图不崩;已是三通道就原样用,否则复制成三通道
    vis = bin_img if bin_img.ndim == 3 else np.stack([bin_img] * 3, axis=-1)
    return vis
