# -*- coding: utf-8 -*-
"""eval/metrics.py —— 评估指标(主责: D 李若宸)

两种口径,别混:
    自动指标(CER / 分类准确率 / 公式匹配): 跑合成板书,衡量算法链路;
    人工可用率(usable_rate):            真实照片试跑后统计"改几处能用",
                                          由 eval/run_eval.py --mode manual 读取。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

import re


# ----------------------------------------------------------------- 文本指标


def normalize_text(s: str) -> str:
    """比较前的归一化: 合并空白、去首尾空格(保留大小写,大小写也是识别质量)。"""
    return re.sub(r"\s+", " ", s or "").strip()


def levenshtein(a: str, b: str) -> int:
    """编辑距离(插入/删除/替换各算 1),经典 DP,O(len(a)*len(b))。"""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur.append(min(prev[j] + 1,        # 删除
                           cur[j - 1] + 1,     # 插入
                           prev[j - 1] + cost))  # 替换
        prev = cur
    return prev[-1]


def cer(ref: str, hyp: str) -> float:
    """字符错误率 = 编辑距离 / 参考长度;参考为空时: 输出也为空算 0,否则 1。"""
    r = normalize_text(ref)
    h = normalize_text(hyp)
    if not r:
        return 0.0 if not h else 1.0
    return levenshtein(r, h) / len(r)


def normalize_latex(s: str) -> str:
    """公式比较前的归一化: 去尺寸命令/细空格/别名,再统一去掉花括号。

    去花括号是刻意的: `x^{2}` 与 `x^2`、`\frac{1}{3}` 与 `\frac13`
    在 LaTeX 里语义相同,比较时应视为相同;这不是放松标准,而是去掉"排版写法"差异。
    """
    s = s or ""
    for token in (r"\left", r"\right", r"\textstyle", r"\displaystyle",
                  r"\,", r"\;", r"\!", r"\ "):
        s = s.replace(token, "")

    # 别名归一: \operatorname*{lim} / \mathrm{d} / \prime
    s = re.sub(r"\\operatorname\*?\{\s*(lim|max|min|sin|cos|tan|log|exp)\s*\}",
               r"\\\1", s)
    s = re.sub(r"\\mathrm\{([A-Za-z])\}", r"\1", s)
    s = s.replace(r"\prime", "'")

    s = re.sub(r"\s+", "", s)
    s = s.replace("{", "").replace("}", "")
    return s.replace("^'", "'")       # f^{\prime} 与 f' 是同一个东西


def formula_exact(ref: str, hyp: str) -> bool:
    return normalize_latex(ref) == normalize_latex(hyp)


def formula_similarity(ref: str, hyp: str) -> float:
    """1 - CER,给"差一点但方向对"的识别一个分数。"""
    r, h = normalize_latex(ref), normalize_latex(hyp)
    if not r:
        return 0.0 if h else 1.0
    return max(0.0, 1.0 - levenshtein(r, h) / len(r))


# ----------------------------------------------------------------- 人工可用率


def usable_rate(rows, max_edits: int = 3) -> float:
    """rows: [(image, edits), ...];改动 <= max_edits 处算"可用"。"""
    rows = list(rows)
    if not rows:
        return 0.0
    ok = sum(1 for _, e in rows if e <= max_edits)
    return ok / len(rows)
