# -*- coding: utf-8 -*-
"""recog/postprocess.py —— 识别结果的转义与清洗(主责: C 陶谱州)

验证命令:
    python -m recog.postprocess
期望结果:
    打印 3 组"输入 -> 输出",与注释里的期望完全一致。

AI 辅助说明: 见 README「诚信声明」。

两条路线,别混用:
    文字行: PaddleOCR 出的是"普通文本",进 .tex 前必须 escape_latex,
            否则 50% 会被 LaTeX 当成注释、& 直接编译报错;
    公式行: pix2tex 出的是"LaTeX 源码",不能转义!只需 clean_latex
            去掉 \\left/\\right(它们常导致括号尺寸报错)并压缩空白。
"""

from __future__ import annotations

import re

# 普通文本 -> LaTeX 文本 的转义表(逐字符查表,不会二次转义)
SPECIAL = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

# OCR 常吐出的 Unicode 字符 -> LaTeX 能排的东西
# (不处理的话 xelatex 只报 Missing character,PDF 里直接丢字,很难发现)
UNICODE_FIXES = {
    "′": "'", "″": "''",
    "−": "-", "–": "--", "—": "---",
    "“": "``", "”": "''", "‘": "`", "’": "'",
    "×": r"$\times$", "÷": r"$\div$",
    "≤": r"$\le$", "≥": r"$\ge$", "≠": r"$\ne$",
    "→": r"$\to$", "∞": r"$\infty$",
    "²": r"\textsuperscript{2}", "³": r"\textsuperscript{3}",
}


def escape_latex(s: str) -> str:
    """把 OCR 出的普通文本转义成可安全放进 .tex 的文本。

    两步: 先逐字符转义 LaTeX 特殊符号,再把 OCR 常见的 Unicode 字符
    换成 LaTeX 写法(顺序不能反——否则后插入的 $...$ 会被当成普通 $ 转义掉)。

    例: "50%_rate & $x$" -> r"50\%\_rate \& \$x\$"
    """
    out = "".join(SPECIAL.get(ch, ch) for ch in s)
    for src, dst in UNICODE_FIXES.items():
        out = out.replace(src, dst)
    return out


def clean_latex(s: str) -> str:
    """清洗 pix2tex 的 LaTeX 输出(不做转义)。

    - 去掉 \\left / \\right: pix2tex 常给不配套的尺寸命令,去掉后更稳;
    - 连续空白压成一个空格,首尾去空。
    """
    s = s.replace("\\left", "").replace("\\right", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def braces_balanced(s: str) -> bool:
    """花括号是否配对(不配对 = 该公式大概率编译失败,交给界面标红)。"""
    return s.count("{") == s.count("}")


if __name__ == "__main__":
    demos = [
        ("escape", r"50%_rate & $x$", r"50\%\_rate \& \$x\$"),
        ("clean", r"\left x \right", "x"),
        ("clean", r"a  +   b", "a + b"),
    ]
    for kind, src, want in demos:
        got = escape_latex(src) if kind == "escape" else clean_latex(src)
        flag = "OK" if got == want else "FAIL"
        print(f"[{flag}] {kind}: {src!r} -> {got!r} (期望 {want!r})")
    print("括号配对检查:", braces_balanced(r"\frac{1}{3}"), braces_balanced(r"\frac{1}{3"))
