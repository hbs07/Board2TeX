# Board2TeX 分工详解 · B(图像增强 & 版面分析)

> 配套:《Board2TeX_Proposal_大纲.md》《Board2TeX_团队分工.md》
> 你的角色:**图像增强 + 行切分 + 行分类 + 可视化**
> 预估代码量:180+ 行 · 关键交付:增强函数、`layout/` 模块 + 可视化标注图
>
> **写给刚学 Python 的你**:本模块刻意选成了最简单的算法(数数、切片、循环),不涉及复杂数学。组长已经给你骨架,你只需要填小函数。**每一步都先让程序跑起来,再想对不对。** 卡住超过半天,把报错截图发群里找组长。

---

## 0. 你要产出的东西

1. `preprocess/enhance.py`:灰度、光照归一化、二值化、裁剪(4 个小函数);
2. `layout/segment.py`:把整页按**行**切开(核心,也是最容易上手的部分);
3. `layout/classify.py`:判断每一行是"文字"还是"公式";
4. `layout/visualize.py`:在图上画框标注,用于报告和调试;
5. 单元测试 `tests/test_layout.py`。

---

## 1. 输入 / 输出约定(先看懂,不要改)

**输入**(来自 A 的 `load_image()`):
```python
bgr  # 已缩放的 BGR 图(np.ndarray,长边 ≤ 1600;第一版不做矫正,拍照时拍正)
```

**输出**(交给 C/D):
```python
Region = {
    "bbox": (x, y, w, h),           # 区域外接矩形(左上角 x,y + 宽高)
    "type": "text" | "formula",      # 你分类的结果
    "order": int,                    # 阅读顺序,从 0 开始,严格递增
    "image": np.ndarray,             # 该行裁剪出来的图,供 C 识别
    "confidence": float,             # 分类把握(0~1),先给个固定值也行
}
layout_regions: List[Region]
```

> 本版**只处理单列**版面,所以没有 `col` 字段。双列列为 Future Work。

---

## 2. 目录结构

```
preprocess/
├── enhance.py           # 你:to_gray / normalize / binarize / crop_content
layout/
├── __init__.py
├── segment.py           # 你:split_lines / analyze_layout
├── classify.py          # 你:classify_line
├── visualize.py         # 你:draw_regions
└── pipeline.py          # 你:把上面拼起来, 对外只暴露 analyze_layout()
```

---

## 3. 第一部分:图像增强 `enhance.py`(4 个小函数)

### 3.1 灰度

```python
def to_gray(bgr):
    import cv2
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
```

### 3.2 光照归一化(替代原版复杂去反光)

原版用 inpaint 修复反光,太难且易出错。**本版只做 CLAHE**——一行代码,先把明暗拉均匀。

```python
def normalize(gray):
    import cv2
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)
```

### 3.3 Otsu 二值化(自动找阈值,不用手调)

```python
def binarize(gray):
    import cv2
    _, out = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return out
```

### 3.4 裁剪空白边(用投影,你第一个"算法")

思路:找"有内容"的行和列,把它们围起来的区域切出来。步骤:
1. 把二值图里"有字"的像素记为前景(这里约定白色 255 是背景,黑色 0 是字);
2. 逐行统计前景数量 → 找到非零的最高行 `top` 和最低行 `bottom`;
3. 逐列同理 → `left` / `right`;
4. 用切片 `img[top:bottom, left:right]` 裁出来。

```python
def crop_content(bin_img):
    import numpy as np
    fg = (bin_img < 128)                 # True 表示是字
    rows = np.where(fg.any(axis=1))[0]   # 有字的行号
    cols = np.where(fg.any(axis=0))[0]   # 有字的列号
    if len(rows) == 0 or len(cols) == 0:
        return bin_img                   # 全空就原样返回,别崩
    return bin_img[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
```

**验证**:拿一张缩放后的板书照片走完四步,保存裁剪结果,用眼睛看边框是不是贴着内容。

---

## 4. 第二部分:行切分 `segment.py`(核心)

### 4.1 原理(理解这个就够写代码了)

板书有很多行字,行与行之间是空白。如果**按行统计有多少个黑点**,有字的地方数字大,空白行数字是 0。于是"从数字>0 变成 0"就是一行结束,"从 0 变成 >0"就是新一行开始。

```
行号:  0   1   2   3   4   5   6   7  ...
黑点数: 0  40  52  48   0   0  30  55 ...   -> 第 1~3 行是一行字, 第 6~7 行是一行字
```

### 4.2 统一前景约定

二值化后可能有"白字黑底"或"黑字白底"两种。先统一成"**字是前景(>0)**":

```python
def ensure_foreground_white(bin_img):
    import numpy as np
    if np.mean(bin_img) > 127:     # 整体偏白, 说明是黑字白底
        import cv2
        bin_img = cv2.bitwise_not(bin_img)   # 取反, 让字变白
    return bin_img
```

### 4.3 切行

```python
def split_lines(bin_img, min_h=28):
    """返回 [(y0, y1), ...] 每一行的上下边界。min_h 过滤太矮的噪声。"""
    row_proj = (bin_img > 0).sum(axis=1)     # 每行的前景像素数
    lines, start = [], None
    for y, v in enumerate(row_proj):
        if v > 0 and start is None:
            start = y                        # 进入一行
        elif v == 0 and start is not None:
            if y - start >= min_h:           # 够高才算一行
                lines.append((start, y))
            start = None
    if start is not None:
        lines.append((start, len(row_proj))) # 收尾: 最后一行贴着底边
    return lines
```

### 4.4 合并成 Region + 排序

```python
def analyze_layout(binary):
    from layout.classify import classify_line
    from layout.segment import ensure_foreground_white, split_lines
    bin_img = ensure_foreground_white(binary)
    regions = []
    for (y0, y1) in split_lines(bin_img):
        line = bin_img[y0:y1, :]
        # 去掉行左右空白, 得到更紧凑的 bbox
        import numpy as np
        cols = np.where((line > 0).any(axis=0))[0]
        if len(cols) == 0:
            continue                          # 空行跳过
        x0, x1 = cols[0], cols[-1] + 1
        block = line[:, x0:x1]
        regions.append({
            "bbox": (x0, y0, x1 - x0, y1 - y0),
            "type": classify_line(block),
            "order": -1,
            "image": block,
            "confidence": 0.6,               # 规则分类把握不大, 先给 0.6
        })
    # 阅读顺序: 从上到下
    regions.sort(key=lambda r: r["bbox"][1])
    for i, r in enumerate(regions):
        r["order"] = i
    return regions
```

---

## 5. 第三部分:行分类 `classify.py`(简单规则)

目标:猜这一行是文字还是公式。**规则简单即可,猜错也没关系**——D 的编辑器里可以人工改。

可用特征(先易后难):
1. **高宽比**:公式常含分式/根号,整行偏高或上下结构明显;
2. **连通域**:公式里符号大小悬殊,文字比较均匀。

```python
def classify_line(line_img):
    import cv2, numpy as np
    h, w = line_img.shape
    n, labels, stats, _ = cv2.connectedComponentsWithStats(line_img, 8)
    widths = stats[1:, cv2.CC_STAT_WIDTH]
    areas = stats[1:, cv2.CC_STAT_AREA]
    if len(areas) == 0:
        return "text"
    score = 0
    if np.std(widths) > 0.5 * np.mean(widths):   # 宽窄变化大 -> 可能公式
        score += 1
    if areas.max() > 3 * np.median(areas):       # 有特别大的符号 -> 可能公式
        score += 1
    if h / max(w, 1) > 0.35:                     # 整行偏高 -> 可能公式
        score += 1
    return "formula" if score >= 2 else "text"
```

> **调参方法(重要)**:先把 10~20 行样例人工标好"文字/公式"真值,再改上面的阈值,看准确率。**不要拍脑袋定阈值。**

---

## 6. 第四部分:可视化 `visualize.py`

```python
def draw_regions(bin_img, regions, out_path):
    import cv2
    vis = cv2.cvtColor(bin_img, cv2.COLOR_GRAY2BGR)
    for r in regions:
        x, y, w, h = r["bbox"]
        color = (0, 0, 255) if r["type"] == "formula" else (0, 255, 0)
        cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)
        cv2.putText(vis, f'{r["order"]}:{r["type"]}', (x, max(y - 5, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.imwrite(out_path, vis)
    return vis
```

输出到 `data/layout/{名字}_annotated.png`,发到群里给大家看。

---

## 7. 测试 `tests/test_layout.py`(必须写)

```python
import numpy as np
from layout.segment import split_lines

def test_split_two_lines():
    img = np.zeros((100, 200), np.uint8)
    img[10:30, 20:180] = 255      # 第一行
    img[60:85, 20:180] = 255      # 第二行
    lines = split_lines(img, min_h=10)
    assert len(lines) == 2

def test_empty_image():
    assert split_lines(np.zeros((50, 50), np.uint8)) == []
```

运行:
```bash
pytest tests/test_layout.py -v
```

再拿 10~20 张真实照片,人工核对标注图,在报告里记录:行切分正确率、分类准确率。

---

## 8. 你的周计划

| 周次 | 你要做的事 |
|---|---|
| W4 | 装好环境;学 NumPy 数组切片(`arr[a:b]`);读懂 `split_lines` |
| W5 | 期中汇报;读组长发的骨架 |
| W6 | 完成 `enhance.py` 四个函数,保存一张裁剪结果给组长看 |
| W7~8 | 完成 `segment.py` 切行,在一张真实图上跑出几行 |
| W9~10 | 完成 `classify.py` + `visualize.py`;人工标注 20 行调阈值 |
| W11~12 | 与 C 联调:确认裁剪出的行图能识别;修 bug |
| W13~14 | 补边界样例;协助整体联调 |
| W15 | 协助评估与打包 |
| W16 | 写报告里"图像增强 + 版面分析"章节与指标 |

---

## 9. 常见坑清单

1. **不要用中文路径**读图/存图,会报错;
2. **图太大**先让组长帮你缩放,或自己 `cv2.resize`;
3. **空行导致崩溃**:任何遍历前先判断 `len(...) == 0`,像上面 `analyze_layout` 那样 `continue`;
4. **粘连行**:两行挨太近连一起 → 把 `min_h` 调小一点试试;
5. **断笔被切成多行**:行内有大片空白但 `row_proj>0` 一般不会断,若断可把二值图做个轻微闭运算(问组长);
6. **分类全判成一种**:先人工标注,再调阈值,别急;
7. **每次只改一个地方,跑一次看结果**,别一次改一堆。

---

## 10. 你的 DoD(Definition of Done)

- [ ] `enhance.py` 四个函数正确,裁剪结果肉眼可见贴合内容;
- [ ] `analyze_layout()` 在工整板书上切行基本正确;
- [ ] 分类结果附人工核对通过的标注图;
- [ ] `pytest tests/test_layout.py` 通过;
- [ ] 向 C 交付的 `layout_regions` 结构稳定、注释清楚。
