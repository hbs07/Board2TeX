# Board2TeX 分工详解 · A(组长 / 集成 & GUI 框架 & 编译)

> 配套:《Board2TeX_Proposal_大纲.md》《Board2TeX_团队分工.md》
> 你的角色:**组长 + 图像入口 + 集成负责人 + GUI 框架 + PDF 编译 + 项目管理**
> 预估代码量:200+ 行 · 关键交付:图像入口与增强管线、`main.py`、可运行 GUI、给组员的骨架
>
> **本版前提**:组员刚学 Python,全组"共同参与、模块主责、交叉互补"。你的核心任务不只是写自己的代码,更是**把项目切成新手能上手的小块**,并提前给出骨架、测试图、验证命令。第一版**不做透视矫正**(拍照拍正替代),识别主线(PaddleOCR + pix2tex + xelatex)环境已验证通过。

---

## 0. 你要产出的东西(先记住目标)

1. `check_env.py` / `requirements.txt` / README(已存在,维护即可);
2. `preprocess/pipeline.py`:读图 + 缩放入口,并调用 B 的增强函数;
3. `recog/formula.py` pix2tex 封装模板(已验证可用)+ 首次运行暖机;
4. GUI 主窗口框架 `gui/main_window.py`(布局 + 按钮 + 文件对话框 + 结果列表);
5. `main.py` 的 `pipeline()` 集成;
6. PDF 编译部分(`gui/exporter.py` 的 `xelatex` 调用,D 负责文件写入);
7. **给 B/C/D 的骨架文件 + 测试图 + 验证命令**;
8. 项目管理:例会纪要、里程碑表、PR 审核、报告汇总。

---

## 1. 项目目录(英文路径)

```
Board2TeX/
├── check_env.py          # 已完成
├── requirements.txt
├── main.py               # A: pipeline()
├── config.py             # A: 阈值、路径等常量集中放这里
├── data/
│   ├── raw/              # 原始照片
│   └── samples/          # 精选 demo 样例
├── preprocess/           # A + B
│   ├── __init__.py
│   ├── enhance.py        # B
│   └── pipeline.py       # A
├── layout/               # B
├── recog/                # C
├── compose/              # C
├── gui/                  # A 框架 + D 控件
├── vault/                # D
├── eval/                 # D
├── docs/meetings/        # A
└── tests/
```

---

## 2. 第一件事:给组员发骨架(Week 5 末~6,最重要)

**原则:组员拿到手的文件应该"已经能运行,只是结果可能是错的"。**

对每个组员负责的模块,你创建一个 `.py` 骨架,包含:
- 完整的函数签名(参数、返回值、类型注释);
- 函数体里写清 `# TODO: 在这里实现,输入是...输出要满足...`;
- 先 `return` 一个占位值(比如全 0 数组、空字符串),保证导入不报错;
- 文件顶部注释里写"**验证命令**"和"**期望结果**"。

示例(给 B 的 `enhance.py` 骨架):

```python
# verify: python -c "from preprocess.enhance import binarize; import cv2,numpy as np;
#                     print(binarize(np.zeros((10,10),np.uint8)).shape)"  -> (10, 10)
import cv2
import numpy as np

def to_gray(bgr):
    """BGR 图 -> 单通道灰度图。"""
    # TODO: 用 cv2.cvtColor(...)
    return np.zeros(bgr.shape[:2], np.uint8)

def normalize(gray):
    """光照归一化(CLAHE),返回同尺寸灰度图。"""
    # TODO: cv2.createCLAHE(...).apply(gray)
    return gray

def binarize(gray):
    """Otsu 二值化,返回同尺寸图,前景为 0/255。"""
    # TODO: cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return gray

def crop_content(bin_img):
    """用投影裁掉四周空白,返回裁剪后的图。"""
    # TODO: 找前景行列范围后再切片
    return bin_img
```

同样给 C(`recog/ocr_engine.py` 模板)、D(`vault/db.py` 骨架)各发一份。

---

## 3. 图像入口 `preprocess/pipeline.py`

第一版不做透视矫正:你负责把照片**读进来、缩放到统一大小**,再按顺序调用 B 的四个增强函数,输出标准二值图。

```python
import cv2
from config import MAX_SIDE
from preprocess.enhance import to_gray, normalize, binarize, crop_content

def load_image(path, max_side=MAX_SIDE):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    h, w = img.shape[:2]
    scale = max_side / max(h, w)
    if scale < 1:
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
    return img

def preprocess(path):
    """A 的对外接口:原始路径 -> {"binary": 二值图, "bgr": 缩放后的 BGR 图}"""
    bgr = load_image(path)
    gray = to_gray(bgr)              # B
    gray = normalize(gray)           # B
    bin_img = binarize(gray)         # B
    bin_img = crop_content(bin_img)  # B
    return {"binary": bin_img, "bgr": bgr}
```

> 注意:`enhance.py` 是 B 的。联调前你可以先用第 2 节的占位骨架跑通,A 的代码不阻塞。
> **拍照要求**:第一版不做矫正,采集样例时尽量把板书拍正;自动矫正列入 Future Work。

---

## 4. pix2tex 模板与暖机 `recog/formula.py`

模板已由 `tools/smoke_test.py` 验证可用,直接给 C:

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

**暖机(重要)**:pix2tex 首次运行要下载模型,很慢。Week 6 前你在自己机器上跑通一次,并让 C 也跑通一次;demo 现场绝不第一次调用。

---

## 5. GUI 主窗口框架(Week 13 前先做骨架)

**先做同步版,不强制子线程**(小图 CPU 推理通常几秒,够 demo)。线程作为加分项。

### 5.1 界面布局

```
┌─────────────────────────────────────────────┐
│ [导入图片] [运行识别] [预览] [导出 .tex][导出 PDF] │
├───────────────┬─────────────────────────────┤
│  左:图像显示   │  右:识别结果 + 校对编辑区    │
│ (增强/原图)    │  (每块一行,可编辑,低置信标红) │
├───────────────┴─────────────────────────────┤
│ [存入错题本]  课程:[___] 标签:[___]          │
└─────────────────────────────────────────────┘
```

### 5.2 主窗口骨架(你搭, D 填控件)

```python
# gui/main_window.py
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QScrollArea)
from PyQt5.QtGui import QImage, QPixmap

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.doc = None            # C 的 Document
        self.pre = None
        self._build_ui()

    def _build_ui(self):
        root = QWidget(); self.setCentralWidget(root)
        top = QHBoxLayout()
        for name in ["导入图片", "运行识别", "预览", "导出 .tex", "导出 PDF"]:
            btn = QPushButton(name)
            top.addWidget(btn)
            # TODO(D): btn.clicked.connect(self.on_<...>)
        self.image_label = QLabel("图像区")     # TODO(D): 显示增强/原图
        self.editor_area = QWidget()            # TODO(D): 放逐行编辑框
        left = QVBoxLayout(); left.addWidget(self.image_label)
        right = QVBoxLayout(); right.addWidget(QScrollArea())
        body = QHBoxLayout(); body.addLayout(left); body.addLayout(right)
        lay = QVBoxLayout(root); lay.addLayout(top); lay.addLayout(body)

    def on_run(self):
        from main import pipeline
        self.pre, regions, self.doc = pipeline(self.image_path)
        # 同步执行;若卡顿再改成 QThread
```

> **给 D 的约定**:`on_run` 后 `self.doc["blocks"]` 是 `Block` 列表,D 负责把它们渲染成可编辑行,并把改动写回 `self.doc`。

### 5.3 图像显示(D 用)

```python
def ndarray_to_qpixmap(img):
    if img.ndim == 2:
        h, w = img.shape
        qimg = QImage(img.data, w, h, w, QImage.Format_Grayscale8)
    else:
        h, w, ch = img.shape
        qimg = QImage(img.data, w, h, ch * w, QImage.Format_RGB888).rgbSwapped()
    return QPixmap.fromImage(qimg.copy())   # .copy() 防花屏
```

---

## 6. 集成与 PDF 编译

### 6.1 `main.py`

```python
from preprocess.pipeline import preprocess
from layout.pipeline import analyze_layout
from compose.builder import compose_document

def pipeline(image_path):
    pre = preprocess(image_path)                    # A + B
    regions = analyze_layout(pre["binary"])         # B
    doc = compose_document(regions)                 # C
    return pre, regions, doc
```

### 6.2 PDF 编译(`gui/exporter.py` 里你写函数,D 调用)

```python
import subprocess, shutil

def has_xelatex():
    return shutil.which("xelatex") is not None

def compile_pdf(tex_path, out_dir):
    if not has_xelatex():
        raise RuntimeError("未安装 xelatex, 请先安装 TeX Live 或 MiKTeX")
    subprocess.run(["xelatex", "-interaction=nonstopmode",
                    "-output-directory", out_dir, tex_path], check=True)
```

---

## 7. 项目管理职责(全程)

- [ ] 建 GitHub 仓库,分支策略:`main` 保护 + 每人 feature 分支;
- [ ] 建 Issues/Projects 看板:Todo / Doing / Done,卡片写负责人与周次;
- [ ] **Week 6 发放全部骨架**,并组织一次 30 分钟"如何跑通骨架"的讲解;
- [ ] 每周例会:定时间、写纪要(`docs/meetings/weekN.md`),记录 完成/计划/阻塞;
- [ ] 审核 PR:重点看是否遵守 §接口约定、是否突破 MVP 边界;
- [ ] 互助规则:组员卡住时,先让结对伙伴看,再给最小可运行示例,而非直接代写;
- [ ] Week 16 汇总报告:量化评估(找 D 要)+ 每人贡献说明 + AI 使用声明。

---

## 8. 周计划(A 视角)

| 周次 | 你要做的事 |
|---|---|
| W4 | 建目录/环境;写 `requirements.txt`、README |
| W5 | 期中汇报;**准备 B/C/D 的骨架 + 测试图** |
| W6 | **发放骨架 + 30 分钟讲解**;pix2tex 模板整理 + 暖机;采集照片 |
| W7~8 | `preprocess/pipeline.py` 完成,用骨架跑通;检查 B/C/D 进度 |
| W9~10 | 冻结接口;帮 C 解决 pix2tex 问题;帮 D 跑通 SQLite;与 B/C 联调 |
| W11~12 | 输出识别对比图;写好 PDF 编译函数 |
| W13~14 | 搭 GUI 框架 + 与 D 一起填控件;集成 `main.py` |
| W15 | 打包 demo 样例;支持 D 的评估 |
| W16 | 汇总评估与报告 |
| W17 | 决赛展示 + Demo 视频 |

---

## 9. 常见坑清单

1. **中文路径**:OpenCV/Paddle 对中文路径可能报错,统一英文路径或先 `np.fromfile` 读;
2. **pix2tex 首次下载模型慢**:提前暖机,别在 demo 现场第一次跑;
3. **CPU 太慢**:限制图像长边、及时 `del` 大数组;
4. **照片拍歪**:第一版不做矫正,采集样例时拍正;demo 样例提前筛一遍;
5. **二值化反色**:交给 B,但你要在联调时确认前景约定统一;
6. **GUI 花屏**:`QPixmap.fromImage(qimg.copy())` 必须 `.copy()`;
7. **commit 粒度**:每人一个模块一次提交,信息写清 `模块: 做了什么`;
8. **不要替组员写完**:给骨架、给示例,让他们自己填——这是他们的分工证据。

---

## 10. 你的 DoD(Definition of Done)

- [ ] `check_env.py` 新机 30 分钟全 OK(已达成);
- [ ] **每位组员都收到过你发的骨架文件,并能独立跑通**;
- [ ] `preprocess/pipeline.py` + 识别一条龙可跑,并附识别对比图;
- [ ] GUI 框架 + `main.py` 一条龙可跑;pix2tex 模板已暖机;
- [ ] GitHub 看板、例会纪要、报告汇总齐全。
