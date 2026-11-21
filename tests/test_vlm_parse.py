# -*- coding: utf-8 -*-
"""tests/test_vlm_parse.py —— 视觉模型输出解析的单元测试(不联网)

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

import pytest

from recog.vlm import parse_blocks


def test_parse_object_with_lines() -> None:
    content = """
    {
      "lines": [
        {"type": "text", "latex": "5.5 Taylor's formula"},
        {"type": "formula", "latex": "R_n(f,a,x)=f(x)-f(a)"}
      ]
    }
    """
    blocks = parse_blocks(content)
    assert [b["type"] for b in blocks] == ["text", "formula"]
    assert blocks[0]["latex"] == "5.5 Taylor's formula"
    assert blocks[0]["content"] == "5.5 Taylor's formula"
    assert blocks[1]["latex"] == "R_n(f,a,x)=f(x)-f(a)"
    assert [b["order"] for b in blocks] == [0, 1]


def test_parse_text_is_escaped_and_formula_delimiters_stripped() -> None:
    content = '{"lines": [{"type": "text", "latex": "50% & _x_"}, ' \
              '{"type": "formula", "latex": "$$x^{2}$$"}]}'
    blocks = parse_blocks(content)
    assert blocks[0]["latex"] == r"50\% \& \_x\_"      # 普通文本要转义
    assert blocks[1]["latex"] == "x^{2}"               # 公式去掉 $ 定界符


def test_parse_code_fence_and_unknown_type() -> None:
    content = '```json\n{"lines": [{"latex": "\\\\frac{1}{2}"}]}\n```'
    blocks = parse_blocks(content)
    assert blocks[0]["type"] == "formula"              # 没写 type 时按内容猜
    assert blocks[0]["latex"] == r"\frac{1}{2}"


def test_parse_invalid_raises() -> None:
    with pytest.raises(ValueError):
        parse_blocks("sorry, I cannot read this image")
