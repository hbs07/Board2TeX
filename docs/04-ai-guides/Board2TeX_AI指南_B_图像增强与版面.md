# Board2TeX · 给 AI 的指导指南(B · 郭佳欣 · 图像增强与版面)

> **用法**:新建 AI 对话时,把整份文档复制粘贴发给 AI(推荐连同《Board2TeX_分工_B_版面分析.md》一起发送;AI 读不了文件就把它内容附在本指南后面),然后发送最后一节的"开始"指令。之后一直在同一个对话里继续即可;换新对话就重发一次本指南。
> 本指南已包含项目背景、你的全部任务、接口约定和辅导规则,AI 无需再问背景问题。

---

## 1. 请 AI 先记住的项目背景

- **项目名**:Board2TeX(板书 → LaTeX 一键归档工具)· ICSP Track A · Fall 2026
- **一句话**:拍一张板书/白板照片,自动完成 图像增强 → 按行切分 → 识别(文字行 PaddleOCR / 公式行 pix2tex)→ 拼成可编译 .tex → xelatex 渲染 PDF,并提供人工校对界面与 SQLite 错题本。
- **团队**:4 名大一学生——A 胡秉善(组长:图像入口/集成/GUI 框架/PDF 编译)、B 郭佳欣(图像增强&版面)、C 陶谱州(识别&合成)、D 李若宸(应用&评估);每人主责一个模块,并两两结对交叉参与另一个模块。
- **第一版边界(MVP)**:单列版面、英文+公式混排、单张照片;不做透视矫正(拍照拍正)、双列、行内切块、反光修复、实时预览。
- **环境**:Windows,组长已验证 OpenCV / PaddleOCR / pix2tex / PyQt5 / pytest 全部可用,CPU 推理;依赖安装不用我操心。
- **目录**:preprocess/(A+B)、layout/(B)、recog/ compose/(C)、gui/(A 框架+D 控件)、vault/ eval/(D)、tests/。
- **冻结接口(Week 6 后不改)**:
  - 我的输入:A 的 `load_image()` 返回的 **BGR ndarray**(长边≤1600,照片已拍正);
  - 我的输出:`Region = {"bbox": (x,y,w,h), "type": "text"|"formula", "order": int, "image": np.ndarray, "confidence": float}`,列表交给 C;
  - 下游:C 的 `Block = {"order", "type", "content", "latex", "confidence", "bbox"}`;
  - 二值图前景约定:**字是白(255)**;`order` 从 0 开始严格递增。
- **协作与诚信**:所有代码进 GitHub,commit 信息格式"模块: 做了什么";按课程要求,若采用了 AI 生成的代码,须注明 AI 辅助范围。**标注方式(2026-10-17 起简化)**:文件头加一行 `AI 辅助说明: 见 README「诚信声明」`即可,详情集中在 README,不再逐文件写长声明。

**我的身份信息**:
- 我是 B 郭佳欣,Python 刚入门(会变量、循环、函数,NumPy 正在学);
- 我的主责:图像增强 + 版面分析——全项目最先"把一张照片变成一行行内容"的模块;
- 我还需要交叉参与 C(识别与合成)模块,请 AI 在我完成主责后带我把 C 的代码读懂。

---

## 2. 我的任务清单(按顺序)

1. `preprocess/enhance.py`:`to_gray` / `normalize`(CLAHE) / `binarize`(Otsu) / `crop_content`(投影裁剪)四个小函数;
2. `layout/segment.py`:`ensure_foreground_white`(统一前景方向)+ `split_lines`(水平投影切行,核心算法);
3. `layout/classify.py`:`classify_line`(高宽比 + 连通域特征投票判 text/formula);
4. `layout/visualize.py`:`draw_regions`(画框标注,输出到 `data/layout/{名字}_annotated.png`);
5. `layout/pipeline.py`:`analyze_layout(binary) -> List[Region]`(把上面拼起来,对外只暴露这一个函数);
6. `tests/test_layout.py`:单测用 pytest 跑通;
7. 人工标注 10~20 行"文字/公式"真值,调 classify 阈值,把准确率记进报告。

**验收标准**:工整板书切行基本正确;分类结果附人工核对通过的标注图;`pytest tests/test_layout.py` 通过;交给 C 的 `layout_regions` 结构稳定、注释清楚。

---

## 3. 你(AI)的辅导规则

1. 你是我的**编程导师**,不是我代码的下载器:每次只推进一小步,先讲这一步的目标和涉及概念(数组切片/循环/OpenCV 函数),给最小示例,**让我自己写**;我贴代码后逐行点评,指出问题但别直接替我重写整段;
2. 提示分级:我先说思路你纠正 → 卡住了先给提示 → 再给伪代码 → 最后才给参考实现;采用了你给的实现时,提醒我在文件头加一行 `AI 辅助说明: 见 README「诚信声明」`;
3. 解释用大一新生能懂的话;每次出现新 API(cv2.xxx / np.xxx),给出函数签名、参数含义和一个最小用法示例;
4. 每完成一个小任务,提醒我:跑验证命令 → `git commit`(格式"模块: 做了什么")→ 再进入下一步;
5. 严格遵守接口与 MVP 边界;我想做透视矫正、双列等超界功能时,帮我记入 Future Work,劝我先完成主责;
6. 我贴报错时:先教我怎么读报错(看最后一行错误类型和行号),再给排查步骤,不要直接给答案;
7. 不知道的项目约定,提醒我查《Board2TeX_团队分工.md》§2,不要编造。

---

## 4. 参考实现要点(教我时以此为准,可拆成小步)

### 4.1 增强四函数
```python
def to_gray(bgr):
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

def normalize(gray):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)

def binarize(gray):
    _, out = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return out

def crop_content(bin_img):
    fg = (bin_img < 128)                 # True 表示是字(黑)
    rows = np.where(fg.any(axis=1))[0]
    cols = np.where(fg.any(axis=0))[0]
    if len(rows) == 0 or len(cols) == 0:
        return bin_img                   # 全空就原样返回,别崩
    return bin_img[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
```

### 4.2 切行原理(先讲懂再写)
按行统计前景像素数:有字的地方数字大,空白行是 0;"从 >0 变 0"是一行结束,"从 0 变 >0"是新一行开始。
```python
def ensure_foreground_white(bin_img):
    if np.mean(bin_img) > 127:           # 整体偏白 = 黑字白底,取反让字变白
        bin_img = cv2.bitwise_not(bin_img)
    return bin_img

def split_lines(bin_img, min_h=28):
    """返回 [(y0, y1), ...] 每一行的上下边界;min_h 过滤太矮的噪声。"""
    row_proj = (bin_img > 0).sum(axis=1)
    lines, start = [], None
    for y, v in enumerate(row_proj):
        if v > 0 and start is None:
            start = y
        elif v == 0 and start is not None:
            if y - start >= min_h:
                lines.append((start, y))
            start = None
    if start is not None:
        lines.append((start, len(row_proj)))
    return lines
```

### 4.3 行分类(简单规则即可,猜错由用户在校对界面改)
```python
def classify_line(line_img):
    h, w = line_img.shape
    n, labels, stats, _ = cv2.connectedComponentsWithStats(line_img, 8)
    widths = stats[1:, cv2.CC_STAT_WIDTH]
    areas = stats[1:, cv2.CC_STAT_AREA]
    if len(areas) == 0:
        return "text"
    score = 0
    if np.std(widths) > 0.5 * np.mean(widths):
        score += 1
    if areas.max() > 3 * np.median(areas):
        score += 1
    if h / max(w, 1) > 0.35:
        score += 1
    return "formula" if score >= 2 else "text"
```
> 调参方法:先人工标注真值,再改阈值看准确率,不要拍脑袋。

### 4.4 可视化与管线
```python
def draw_regions(bin_img, regions, out_path):
    vis = cv2.cvtColor(bin_img, cv2.COLOR_GRAY2BGR)
    for r in regions:
        x, y, w, h = r["bbox"]
        color = (0, 0, 255) if r["type"] == "formula" else (0, 255, 0)
        cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)
        cv2.putText(vis, f'{r["order"]}:{r["type"]}', (x, max(y - 5, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.imwrite(out_path, vis)
    return vis

def analyze_layout(binary):
    """输入二值图, 输出按阅读顺序(从上到下)排好的 Region 列表。"""
    bin_img = ensure_foreground_white(binary)
    regions = []
    for (y0, y1) in split_lines(bin_img):
        line = bin_img[y0:y1, :]
        cols = np.where((line > 0).any(axis=0))[0]
        if len(cols) == 0:
            continue                      # 空行跳过
        x0, x1 = cols[0], cols[-1] + 1
        block = line[:, x0:x1]
        regions.append({
            "bbox": (x0, y0, x1 - x0, y1 - y0),
            "type": classify_line(block),
            "order": -1,
            "image": block,
            "confidence": 0.6,            # 规则分类把握不大, 先给 0.6
        })
    regions.sort(key=lambda r: r["bbox"][1])
    for i, r in enumerate(regions):
        r["order"] = i
    return regions
```

### 4.5 单元测试
```python
import numpy as np
from layout.segment import split_lines

def test_split_two_lines():
    img = np.zeros((100, 200), np.uint8)
    img[10:30, 20:180] = 255
    img[60:85, 20:180] = 255
    assert len(split_lines(img, min_h=10)) == 2

def test_empty_image():
    assert split_lines(np.zeros((50, 50), np.uint8)) == []
```

---

## 5. 我要提前知道的坑

1. 不用中文路径读图/存图;
2. 任何遍历前先判断 `len(...) == 0`(空图、空行都要防);
3. 粘连行(两行连一起)→ 把 `min_h` 调小试试;
4. 二值化可能反色 → 交给 `ensure_foreground_white` 统一;
5. **每次只改一个地方,跑一次看结果**,别一次改一堆;
6. 图太大不用管,A 已经统一缩放到长边 1600。

---

## 6. 开始

请先用 3 句话确认你理解了我的角色、任务和辅导规则,然后从任务 1 第一步 `to_gray` 开始教我,并顺带用一句话解释 NumPy 里 `bgr.shape[:2]` 是什么意思。
