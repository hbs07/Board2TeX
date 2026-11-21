# -*- coding: utf-8 -*-
"""tools/make_eval_assets.py —— 生成评估用板书图与真值(维护: A 胡秉善)

用法:
    python tools/make_eval_assets.py

产物:
    assets/eval/board_01.png ... board_04.png   4 张合成板书
    assets/eval/labels.json                     每张图的逐行真值

说明(写报告时必须一起交代):
    这是**合成**板书(纯白底、无透视、无阴影、印刷体),
    只用来验证"算法链路是否正确",不代表手机拍的真实板书;
    真实照片的可用率用 eval/run_eval.py --mode manual 另算(见 D 的分工文档 §6)。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = os.path.join("assets", "eval")

# 每块板书: [(类型, 内容), ...];text 用纯英文(避免行内公式干扰 CER),
# formula 用 LaTeX(matplotlib mathtext 能渲染的子集)
BOARDS = {
    "board_01.png": [
        ("text", "Derivative Rules"),
        ("text", "Given two functions f and g, we have:"),
        ("formula", r"\frac{d}{dx}x^{2}=2x"),
        ("formula", r"\int_{0}^{1}x^{2}\,dx=\frac{1}{3}"),
        ("text", "The chain rule composes the two derivatives"),
    ],
    "board_02.png": [
        ("text", "Matrix Multiplication"),
        ("text", "The product of two matrices is defined as:"),
        ("formula", r"(AB)_{ij}=\sum_{k}A_{ik}B_{kj}"),
        ("text", "The identity matrix leaves every vector unchanged"),
    ],
    "board_03.png": [
        ("text", "Limits"),
        ("formula", r"\lim_{x\to 0}\frac{\sin x}{x}=1"),
        ("text", "A function is continuous when the limit equals the value"),
        ("formula", r"f'(x)=\lim_{h\to 0}\frac{f(x+h)-f(x)}{h}"),
    ],
    "board_04.png": [
        ("text", "Euler Identity"),
        ("formula", r"e^{i\pi}+1=0"),
    ],
}


def render_board(lines: list[tuple[str, str]], out_path: str) -> None:
    """把一块板书画成 1600x960 的白底黑字图。"""
    fig = plt.figure(figsize=(10, 6), dpi=160)
    fig.patch.set_facecolor("white")

    n = len(lines)
    step = 0.74 / max(n - 1, 1)
    for i, (kind, content) in enumerate(lines):
        y = 0.88 - i * step
        if kind == "formula":
            text = f"${content}$"
            size = 28
        else:
            text = content
            size = 30 if i == 0 else 23
        fig.text(0.06, y, text, fontsize=size, color="black",
                 ha="left", va="center")

    fig.savefig(out_path, facecolor="white")
    plt.close(fig)


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    labels: dict[str, list[dict]] = {}

    for name, lines in BOARDS.items():
        render_board(lines, os.path.join(OUT_DIR, name))
        labels[name] = [
            {"order": i, "type": kind,
             **({"text": content} if kind == "text" else {"latex": content})}
            for i, (kind, content) in enumerate(lines)
        ]
        print(f"{name}: {len(lines)} 行")

    with open(os.path.join(OUT_DIR, "labels.json"), "w", encoding="utf-8") as f:
        json.dump(labels, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in labels.values())
    print(f"共 {len(labels)} 张图 / {total} 行;真值写入 {OUT_DIR}/labels.json")


if __name__ == "__main__":
    main()
