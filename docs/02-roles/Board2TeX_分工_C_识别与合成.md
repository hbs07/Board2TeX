# Board2TeX 分工详解 · C(识别引擎 & LaTeX 合成)

> 配套:《Board2TeX_Proposal_大纲.md》《Board2TeX_团队分工.md》
> 你的角色:**识别引擎接入 + LaTeX 合成**
> 预估代码量:180+ 行 · 关键交付:识别合成模块、`.tex` 生成器
>
> **写给刚学 Python 的你**:识别引擎本身是现成的(PaddleOCR / pix2tex),你主要做"调用 + 拼接字符串",是最容易的部分。组长会给你**已验证可用的函数模板**,你照着改参数即可。转义和拼字符串就是普通的字典和循环。卡住找组长。

---

## 0. 你要产出的东西

1. `recog/ocr_engine.py`:封装 PaddleOCR,识别英文文字;
2. `recog/formula.py`:封装 pix2tex,识别公式(组长给模板);
3. `recog/postprocess.py`:`escape_latex` / `clean_latex`;
4. `recog/engine.py`:`recognize(region) -> Block` 统一入口;
5. `compose/builder.py`:把 `Block` 拼成可编译 `.tex`;
6. 单元测试 `tests/test_recog.py`。

---

## 1. 输入 / 输出约定(先看懂,不要改)

**输入**(来自 B):
```python
Region = {"bbox": (x,y,w,h), "type": "text" | "formula",
          "order": int, "image": np.ndarray, "confidence": float}
```

**输出**(交给 D):
```python
Block = {
    "order": int,              # 直接抄输入 region["order"]
    "type": "text" | "formula",
    "content": str,            # 原始识别结果(文字原文 / LaTeX 片段)
    "latex": str,              # 处理后可直接放进 .tex 的内容
    "confidence": float,       # 0~1, 低于阈值 D 会标红
    "bbox": (x, y, w, h),
}
Document = {"blocks": List[Block], "tex_source": str}
```

---

## 2. 目录结构

```
recog/
├── __init__.py
├── ocr_engine.py     # 你:PaddleOCR 封装
├── formula.py        # 你:pix2tex 封装(模板)
├── engine.py         # 你:recognize(region) -> Block
└── postprocess.py    # 你:文本清洗、公式后处理
compose/
├── __init__.py
├── template.py       # 组长给好的 .tex 模板字符串
└── builder.py        # 你:compose_document()
```

---

## 3. 第一部分:文字识别 `ocr_engine.py`

### 3.1 引擎只初始化一次(第一次会下载模型,提前暖机!)

```python
_ocr = None

def get_ocr():
    global _ocr
    if _ocr is None:
        from paddleocr import PaddleOCR
        _ocr = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)
    return _ocr
```

> **重要**:第一次运行会下载模型,很慢。**开发时先自己跑一次**,别到 demo 现场才第一次调用。

### 3.2 识别一行文字

```python
def recognize_text(img):
    """输入一行图, 返回 (文字, 置信度)。"""
    ocr = get_ocr()
    result = ocr.ocr(img, cls=False)
    if not result or not result[0]:
        return "", 0.0
    texts, scores = [], []
    for line in result[0]:
        texts.append(line[1][0])      # 第 1 个元素是 (文本, 置信度)
        scores.append(line[1][1])
    return "".join(texts), sum(scores) / len(scores)
```

> PaddleOCR 不同版本返回结构可能不同。**先 `print(result)` 看一眼**再决定怎么取。

---

## 4. 第二部分:公式识别 `formula.py`(组长给模板)

```python
_tex = None

def get_tex():
    global _tex
    if _tex is None:
        from pix2tex.cli import LatexOCR
        _tex = LatexOCR()
    return _tex

def to_pil(bin_img):
    import cv2
    from PIL import Image
    if bin_img.ndim == 2:
        return Image.fromarray(bin_img).convert("RGB")
    return Image.fromarray(cv2.cvtColor(bin_img, cv2.COLOR_BGR2RGB))

def recognize_formula(img):
    """输入一行图, 返回 (LaTeX 字符串, 置信度)。"""
    try:
        latex = get_tex()(to_pil(img))
    except Exception:
        return "", 0.0
    return str(latex).strip(), 0.8       # pix2tex 不给置信度, 给经验值
```

> 公式行太窄(宽 < 20px)识别没意义,可在 `engine.py` 里过滤。

---

## 5. 第三部分:文本后处理 `postprocess.py`(最简单,先做这个)

### 5.1 转义(不做会导致 `.tex` 编译失败!)

LaTeX 里 `& % _ # $ ^ ~ { } \` 是特殊字符,普通文字里出现必须转义。

```python
SPECIAL = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%",
    "$": r"\$", "#": r"\#", "_": r"\_",
    "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

def escape_latex(s):
    return "".join(SPECIAL.get(c, c) for c in s)
```

### 5.2 公式清洗

```python
import re

def clean_latex(s):
    s = s.replace("\\left", "").replace("\\right", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s
```

### 5.3 低置信度判定
- 文字:`confidence < 0.85` → 让 D 标红;
- 公式:花括号不配对(`count("{") != count("}")`)→ 让 D 标红。

---

## 6. 第四部分:统一入口 `engine.py`

```python
from recog.ocr_engine import recognize_text
from recog.formula import recognize_formula
from recog.postprocess import escape_latex, clean_latex

def recognize(region):
    img, t = region["image"], region["type"]
    if t == "formula":
        content, conf = recognize_formula(img)
        latex = clean_latex(content)
    else:
        content, conf = recognize_text(img)
        latex = escape_latex(content)
    return {
        "order": region["order"],
        "type": t,
        "content": content,
        "latex": latex,
        "confidence": conf,
        "bbox": region["bbox"],
    }
```

---

## 7. 第五部分:LaTeX 合成 `compose/builder.py`(拼字符串)

### 7.1 模板 `compose/template.py`(组长给,直接用)

```python
TEMPLATE = r"""\documentclass[12pt]{article}
\usepackage{amsmath, amssymb}
\usepackage[margin=2.5cm]{geometry}
\begin{document}
\section*{Board2TeX Export}
% BODY
\end{document}
"""
```

> 英文文档用 `article` 即可,`pdflatex` 或 `xelatex` 均可编译;若日后需要中文,再换成 `ctexart` + `xelatex`。

### 7.2 拼接逻辑

规则:按 `order` 排序;连续的文字行合并成一个段落;公式行单独包在 `$$...$$` 里,前后空行隔开。

```python
from compose.template import TEMPLATE
from recog.engine import recognize

def build_body(blocks):
    blocks = sorted(blocks, key=lambda b: b["order"])
    parts, buf = [], []
    for b in blocks:
        if b["type"] == "formula":
            if buf:                       # 先把攒着的文字段落收掉
                parts.append("".join(buf)); buf = []
            parts.append(f"$$ {b['latex']} $$")
        else:
            buf.append(b["latex"])
    if buf:
        parts.append("".join(buf))
    return "\n\n".join(parts)

def compose_document(regions):
    blocks = [recognize(r) for r in regions]
    body = build_body(blocks)
    return {"blocks": blocks, "tex_source": TEMPLATE.replace("% BODY", body)}
```

要点:
- **一定要按 `order` 排序**,不要依赖列表原顺序;
- 英文换行交给 LaTeX,不要手动加 `\\`。

### 7.3 编译验证(组长已装 `xelatex`)

```bash
# 把生成的 tex 存成 out.tex, 然后:
xelatex -interaction=nonstopmode out.tex
```

编译失败时,先看是不是某个块没转义;可以临时只放一个块,逐个排查。

---

## 8. 测试 `tests/test_recog.py`

```python
from recog.postprocess import escape_latex, clean_latex

def test_escape():
    assert escape_latex("50%_rate & $x$") == r"50\%\_rate \& \$x\$"

def test_clean():
    assert clean_latex(r"\left x \right") == "x"
```

再写一个集成测试:自己用 matplotlib 生成一张 `x^2+1` 公式图,调 `recognize_formula`,断言结果里含 `x`。
```bash
pytest tests/test_recog.py -v
```

指标(与 D 一起统计):整页导出后公式行正确率、文字准确率。

---

## 9. 你的周计划

| 周次 | 你要做的事 |
|---|---|
| W4 | 装好环境;让组长帮你各跑一个 PaddleOCR / pix2tex 最小例子 |
| W5 | 期中汇报;读组长发的骨架 |
| W6 | 封装两个引擎;测试单张文字图与公式图 |
| W7~8 | 完成 `postprocess.py`(转义 + 清洗) |
| W9~10 | 完成 `engine.py` 与 `compose/builder.py`;跑通"一行 -> 一段 .tex -> xelatex 编译" |
| W11~12 | 与 B 联调:整版识别一条板书 |
| W13~14 | 与 D 联调:校对后可重新合成;修识别 bug |
| W15 | 协助评估与打包 |
| W16 | 输出识别指标,写报告识别/合成章节 |

---

## 10. 常见坑清单

1. **PaddleOCR 首次下载慢**:提前暖机,别在 demo 现场第一次跑;
2. **返回结构版本差异**:先 `print(result)` 再解析;
3. **pix2tex 无置信度**:用经验值 + 花括号配对做兜底;
4. **编译失败**:确认特殊字符已转义、公式环境配平;
5. **转义遗漏导致编译崩**:`& % _ # $ ^ ~ { } \` 全部转义,写单测覆盖;
6. **公式 `$$` 里混进正文文字**:说明 B 分类错了,回给 B 调整;
7. **空块**:B 已过滤,但你在 `recognize` 里仍要防御性判空;
8. **顺序错**:始终以 `order` 排序。

---

## 11. 你的 DoD(Definition of Done)

- [ ] 两个引擎封装完成,单张图可识别;
- [ ] `compose_document` 输出 `.tex` 且 `xelatex` 编译通过;
- [ ] 低置信度信息正确传给 D;
- [ ] 转义单测通过,识别指标记录在案。
