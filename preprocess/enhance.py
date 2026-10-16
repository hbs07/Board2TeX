# -*- coding: utf-8 -*-
"""preprocess/enhance.py —— 图像增强四步(主责: B 郭佳欣;骨架: A 提供)

验证命令(填完函数后运行):
    python -m preprocess.enhance assets/test_text.png data/enhance_check
期望结果:
    data/enhance_check/ 下生成 gray.png / norm.png / binary.png / crop.png
    其中 crop.png 四边贴合内容,没有大片空白边;肉眼核对即可。

AI 辅助范围(课程要求):
    本骨架由 AI 依据《Board2TeX_分工_B_版面分析.md》§3 生成文件结构、
    函数签名、类型注解、文档字符串与验证脚本;四个函数体均为占位实现,
    由 B 独立实现并替换。A 只在评审 PR 时检查接口与边界情况。

数据流(接口已冻结,只填函数体,不改签名):
    load_image(A) -> to_gray -> normalize -> binarize -> crop_content
    输入 bgr    : np.ndarray, 形状 (H, W, 3), uint8, BGR, 长边 <= 1600
    最终输出    : np.ndarray, 形状 (H, W),   uint8, 取值 0/255

极性约定(重要,联调时与 A 确认):
    本模块输出的二值图极性不保证(板书照片通常是"黑字白底");
    layout 入口会先 ensure_foreground_white() 统一成"字=白(255)"再切行。
    因此这里不需要你自己翻转极性,也不要改动 crop_content 的前景判断。
"""

from __future__ import annotations

import cv2
import numpy as np


def to_gray(bgr: np.ndarray) -> np.ndarray:
    """第一步: BGR 彩色图 -> 单通道灰度图。

    单行实现,用 cv2.cvtColor。验证:
        python -c "import cv2; from preprocess.enhance import to_gray; \
g = to_gray(cv2.imread('assets/test_text.png')); print(g.shape, g.dtype)"
    期望: (H, W) uint8 —— 比输入少一维。
    """
    # TODO(B): 参考《分工_B_版面分析.md》§3.1 实现(一行)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)



def normalize(gray: np.ndarray) -> np.ndarray:
    """第二步: 光照归一化(CLAHE),把板书照片上的明暗拉均匀。

    用 cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)) 再 .apply。
    验证: 对同一张图,角落发暗的区域在 norm.png 里字迹应更清晰均匀。
    """
    # TODO(B): 参考《分工_B_版面分析.md》§3.2 实现(两行)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def binarize(gray: np.ndarray) -> np.ndarray:
    """第三步: Otsu 自动阈值二值化,输出只有 0 和 255 两种值。

    用 cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU),
    阈值参数填 0 表示让 Otsu 自己找,不要手调数字。
    验证: binary.png 里整张图只有黑白两色,没有中间灰。
    """
    # TODO(B): 参考《分工_B_版面分析.md》§3.3 实现(两行)
    return gray  # 占位: 原样返回


def crop_content(bin_img: np.ndarray) -> np.ndarray:
    """第四步: 用行列投影裁掉四周空白边。

    前景判断: 本步骤按"暗像素是字"统计(与 Otsu 输出极性一致),
    即 fg = (bin_img < 128)。不需要翻转极性,layout 入口会统一。

    算法步骤(参考《分工_B_版面分析.md》§3.4):
      1. fg = (bin_img < 128)              # True 表示是字
      2. rows = np.where(fg.any(axis=1))[0]  # 有字的行号
      3. cols = np.where(fg.any(axis=0))[0]  # 有字的列号
      4. 空图(len(rows)==0 或 len(cols)==0)原样返回,不要崩溃
      5. 用切片 bin_img[rows[0]:rows[-1]+1, cols[0]:cols[-1]+1] 裁剪

    验证: crop.png 四边贴合内容,无大片空白边。
    """
    # TODO(B): 参考《分工_B_版面分析.md》§3.4 实现(约 6 行)
    return bin_img  # 占位: 原样返回


# ---------------------------------------------------------------------------
# 以下自测脚本与四个函数的实现无关,B 不需要修改。
# 作用: 把一张样例图走完四步并存图,让你用眼睛检查每一步结果。
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import sys

    from config import MAX_SIDE

    if len(sys.argv) != 3:
        print("用法: python -m preprocess.enhance <图片路径> <输出目录>")
        raise SystemExit(1)

    src, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    # 与 A 的 load_image 等价的缩放逻辑(正式版以 preprocess/pipeline.py 为准)
    bgr = cv2.imread(src)
    if bgr is None:
        raise FileNotFoundError(src)
    h, w = bgr.shape[:2]
    scale = MAX_SIDE / max(h, w)
    if scale < 1:
        bgr = cv2.resize(bgr, (int(w * scale), int(h * scale)))

    gray = to_gray(bgr)
    norm = normalize(gray)
    bin_img = binarize(norm)
    crop = crop_content(bin_img)

    cv2.imwrite(os.path.join(out_dir, "gray.png"), gray)
    cv2.imwrite(os.path.join(out_dir, "norm.png"), norm)
    cv2.imwrite(os.path.join(out_dir, "binary.png"), bin_img)
    cv2.imwrite(os.path.join(out_dir, "crop.png"), crop)
    print(f"已输出 4 张图到 {out_dir}/ ,请肉眼核对 crop.png 是否贴合内容")
