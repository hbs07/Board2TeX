# -*- coding: utf-8 -*-
"""tools/make_test_assets.py —— 生成测试用"板书"图(维护: A 胡秉善)

用法:
    python tools/make_test_assets.py

产物:
    assets/test_text.png —— 5 行英文 + 公式混排的"板书",供 B/C/D 与 pytest 共用

为什么用脚本生成而不是随手截图:
    1. 可复现、可版本化:改行数/字号/间距就能造出新的难度样例;
    2. 全组共用同一张图,联调时"你那边也是这张"才有意义;
    3. MVP 边界是**英文 + 公式**,样例图也必须是英文,否则验收标准和素材对不上。

注意:
    这张图是"理想板书"(纯白底、无透视、无阴影),用来测算法正确性;
    真实照片样例放 assets/photos/,不要混用。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# (纵坐标, 文本, 字号, 是否粗体) —— y 用 0~1 的相对坐标,从上往下排
LINES = [
    (0.86, "Derivative Rules", 30, True),
    (0.70, r"Given $f(x)=x^{2}$ and $g(x)=\sin x$:", 24, False),
    (0.54, r"$\frac{d}{dx}\,x^{2}=2x$", 30, False),
    (0.38, r"$\int_{0}^{1}x^{2}\,dx=\frac{1}{3}$", 30, False),
    (0.20, r"Chain rule: $(f(g(x)))' = f'(g(x))\,g'(x)$", 24, False),
]


def make_board(out_path: str = os.path.join("assets", "test_text.png")) -> str:
    """画一张 1600px 宽的英文板书图并保存,返回路径。"""
    fig = plt.figure(figsize=(10, 5.6), dpi=160)   # 1600 x 896
    fig.patch.set_facecolor("white")

    for y, text, size, bold in LINES:
        fig.text(
            0.06, y, text,
            fontsize=size,
            color="black",
            fontweight="bold" if bold else "normal",
            ha="left", va="center",
        )

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig.savefig(out_path, facecolor="white")
    plt.close(fig)
    return out_path


if __name__ == "__main__":
    path = make_board()
    from PIL import Image

    with Image.open(path) as im:
        print(f"已生成 {path}: {im.size[0]}x{im.size[1]}, {len(LINES)} 行内容")
