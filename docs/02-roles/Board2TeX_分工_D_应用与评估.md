# Board2TeX 分工详解 · D(应用 / 校对 / 错题本 / 评估)

> 配套:《Board2TeX_Proposal_大纲.md》《Board2TeX_团队分工.md》
> 你的角色:**GUI 控件填充 + 校对编辑 + 导出 + SQLite 错题本 + 数据集与评估**
> 预估代码量:180+ 行 · 关键交付:应用控件、错题本、评估报告
>
> **写给刚学 Python 的你**:GUI 框架组长已经搭好(窗口、布局、按钮都在),你只需要往按钮上挂函数、把结果列表显示出来;错题本和评估都是普通的文件/SQLite 操作,很适合练手。**先让窗口能打开,再一步步加功能。** 卡住找组长。

---

## 0. 你要产出的东西

1. `vault/db.py`:SQLite 错题本(建表、增、查);
2. GUI 控件(在 A 的 `gui/main_window.py` 上填):显示增强后的图像、逐行可编辑列表、"存入错题本"对话框、错题本列表页;
3. `gui/exporter.py`:`export_tex` 写文件、调用 A 的 `compile_pdf`;
4. `eval/`:数据集整理 + 可用率脚本 + 报告;
5. 单元测试 `tests/test_vault.py`。

---

## 1. 输入约定(先看懂)

**消费 C 的输出**:
```python
Block = {"order": int, "type": "text"|"formula", "content": str,
         "latex": str, "confidence": float, "bbox": (x,y,w,h)}
Document = {"blocks": List[Block], "tex_source": str}
```
**消费 A 的输出**:`{"binary": ndarray, "bgr": ndarray}`(`bgr` 用于界面显示)

> **本版简化**:不要求"实时逐键重渲染",改成**点一次"预览"按钮**才更新预览;不要求子线程,先同步执行。

---

## 2. 目录结构

```
gui/
├── main_window.py     # A 搭框架, 你填控件
├── exporter.py        # 你:export_tex / 调 A 的 compile_pdf
└── widgets.py         # 你:可复用小部件(编辑行、错题本页)
vault/
├── __init__.py
└── db.py              # 你:SQLite
eval/
├── dataset.py         # 你:数据集整理
├── metrics.py         # 你:可用率
└── run_eval.py        # 你:评估入口
```

---

## 3. 第一部分:错题本 `vault/db.py`(最好上手,先做)

### 3.1 建表

```python
import sqlite3

def init_db(path="vault/board2tex.db"):
    con = sqlite3.connect(path)
    con.execute("""CREATE TABLE IF NOT EXISTS problems(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course TEXT, tags TEXT, tex TEXT,
        image_path TEXT, created_at TEXT)""")
    con.commit()
    return con
```

### 3.2 增 / 查

```python
def add_problem(con, course, tags, tex, image_path):
    con.execute("INSERT INTO problems(course,tags,tex,image_path,created_at)"
                " VALUES(?,?,?,?,datetime('now'))",
                (course, ",".join(tags), tex, image_path))
    con.commit()

def list_problems(con):
    return con.execute("SELECT * FROM problems ORDER BY id DESC").fetchall()

def search(con, course=None):
    if course:
        return con.execute("SELECT * FROM problems WHERE course=?",
                            (course,)).fetchall()
    return list_problems(con)

def delete_problem(con, pid):
    con.execute("DELETE FROM problems WHERE id=?", (pid,))
    con.commit()
```

### 3.3 测试 `tests/test_vault.py`

```python
from vault.db import init_db, add_problem, list_problems, search

def test_vault_roundtrip(tmp_path):
    con = init_db(str(tmp_path / "t.db"))
    add_problem(con, "高数", ["极限"], "$$x^2$$", "a.png")
    assert len(list_problems(con)) == 1
    assert len(search(con, "高数")) == 1
    assert len(search(con, "线代")) == 0
```

```bash
pytest tests/test_vault.py -v
```

---

## 4. 第二部分:GUI 控件(在 A 的框架上填)

A 已经给你:
- `self.image_label`(显示图像)、`self.editor_area`(放编辑行)、`self.doc`(识别结果);
- 顶部按钮:`导入图片 / 运行识别 / 预览 / 导出 .tex / 导出 PDF`。

**你负责**:给按钮挂函数 + 把 `self.doc["blocks"]` 渲染成可编辑行 + 更新 `self.doc`。

### 4.1 一个可编辑行的小部件 `gui/widgets.py`

```python
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit

class BlockEditor(QWidget):
    def __init__(self, block, on_change):
        super().__init__()
        self.block = block
        self.edit = QLineEdit(block["latex"])
        if block["confidence"] < 0.85:                 # 低置信度标红
            self.edit.setStyleSheet("background:#ffd6d6;")
        self.edit.textChanged.connect(lambda t: on_change(block["order"], t))
        lay = QHBoxLayout(self)
        lay.addWidget(QLabel(f'{block["order"]} [{block["type"]}]'))
        lay.addWidget(self.edit)
```

在 `main_window.py` 里:

```python
def show_blocks(self):
    # 清空旧控件后, 为每个 block 建一个 BlockEditor
    ...
    self.editors = [BlockEditor(b, self.on_edit) for b in self.doc["blocks"]]

def on_edit(self, order, new_latex):
    for b in self.doc["blocks"]:
        if b["order"] == order:
            b["latex"] = new_latex        # 改回内存里的 block
```

### 4.2 预览(点按钮才刷新,最简单)

```python
def on_preview(self):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from compose.builder import build_body          # 复用 C 的函数
    body = build_body(self.doc["blocks"])
    fig = plt.figure(figsize=(5, 2))
    fig.text(0.02, 0.98, body[:300], va="top", family="SimHei")  # 简单文字预览
    fig.savefig("preview.png", dpi=120); plt.close(fig)
    # TODO: 把 preview.png 显示到界面
```

> 更真实的预览可以让 A 的 `compile_pdf` 生成 PDF 再转图,但那慢,**作为加分项**,MVP 用上面的简单预览即可。

### 4.3 显示图像

```python
from PyQt5.QtGui import QImage, QPixmap

def ndarray_to_qpixmap(img):
    if img.ndim == 2:
        h, w = img.shape
        qimg = QImage(img.data, w, h, w, QImage.Format_Grayscale8)
    else:
        h, w, ch = img.shape
        qimg = QImage(img.data, w, h, ch * w, QImage.Format_RGB888).rgbSwapped()
    return QPixmap.fromImage(qimg.copy())   # .copy() 防花屏
```

### 4.4 错题本按钮

"存入错题本"弹出小对话框填课程/标签;错题本列表页用 `QTableWidget` 显示 `list_problems()` 结果,顶部加课程输入框做 `search`。

---

## 5. 第三部分:导出 `gui/exporter.py`

### 5.1 导出 `.tex`

```python
def export_tex(doc, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc["tex_source"])
```

> 注意:编辑校对后要**先用 `self.doc["blocks"]` 重新生成 `tex_source`**(调 C 的 `build_body` + 模板),再导出,否则导出的是改动前的内容。

### 5.2 导出 PDF

```python
from gui.exporter import compile_pdf      # A 已写好的 xelatex 调用
import os

def export_pdf(doc, tex_path):
    export_tex(doc, tex_path)
    out_dir = os.path.dirname(os.path.abspath(tex_path))
    compile_pdf(tex_path, out_dir)         # 需要系统装了 xelatex
```

界面上先判断有没有 `xelatex`,没有就提示"请安装 TeX Live/MiKTeX",只导 `.tex`。

---

## 6. 第四部分:数据集与评估 `eval/`(简化版)

### 6.1 数据集
- 与 A/B 协作采集 **20~30 张**板书照片,存 `data/raw/`,命名 `{课程}_{编号}.jpg`;
- 建 `eval/labels.csv`,每行 `image`(文件名)、`usable_after_edits`(人工试跑后填改动次数)。

### 6.2 可用率(最简单的指标)

```python
def usable_rate(rows, max_edits=3):
    """rows: [(image, edits), ...]; 改动 <= max_edits 处算可用。"""
    if not rows:
        return 0.0
    ok = sum(1 for _, e in rows if e <= max_edits)
    return ok / len(rows)
```

### 6.3 入口

```python
import csv
from eval.metrics import usable_rate

def main(csv_path="eval/labels.csv"):
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append((r["image"], int(r["usable_after_edits"])))
    rate = usable_rate(rows)
    with open("eval/report.txt", "w", encoding="utf-8") as f:
        f.write(f"样本数: {len(rows)}\n端到端可用率: {rate:.1%}\n")
    print(f"可用率 {rate:.1%}")
```

```bash
python eval/run_eval.py
```

> 若时间紧,评估可退化为"人工试跑 10~20 张,手动记改动次数"。

---

## 7. 与队友的接口动作清单

- [ ] 找 A 要 GUI 框架和 `pipeline()` 稳定入口,别自己拼接;
- [ ] 找 C 确认 `Block` 字段、标红阈值、`build_body` 可复用;
- [ ] 确认 `tex_source` 是否已含模板(决定导出是否再包一层);
- [ ] 校对后重渲染前,记得把编辑写回 `blocks` 再调 `build_body`。

---

## 8. 你的周计划

| 周次 | 你要做的事 |
|---|---|
| W4 | 学 PyQt5 基础;跟 A 一起采集照片 |
| W5 | 期中汇报;先把 `vault/db.py` + 测试做完 |
| W6 | 在 A 给的窗口骨架上让"导入图片"能显示图 |
| W7~8 | "运行识别"能跑通(A/C 用假数据也行),结果列表显示出来 |
| W9~10 | 可编辑行 + 标红 + 写回;导出 `.tex` 跑通 |
| W11~12 | 错题本按钮 + 列表页;导出 PDF 联调 |
| W13~14 | 预览功能;整体联调;补 bug |
| W15 | 数据集标注完成,跑评估,出报告图表 |
| W16 | 整理报告图表与贡献说明 |
| W17 | 演示 Demo 视频、错题本现场展示 |

---

## 9. 常见坑清单

1. **窗口打不开/Qt 报错**:先跑一个最小 PyQt5 窗口确认环境;有问题找 A;
2. **QPixmap 花屏**:`QImage` 引用的 numpy 内存被回收导致,必须 `.copy()`;
3. **xelatex 不存在**:先检测再提示,PDF 测试加 `pytest.mark.skipif`;
4. **导出的是旧内容**:校对后先更新 `blocks` 再重新生成 `tex_source`;
5. **SQLite 连接**:桌面单进程没问题,用完 `con.close()`;
6. **中文文件名**:导出路径尽量避免中文;
7. **标红阈值**:与 C 对齐,避免全红或全不红;
8. **评估别造假**:改动次数如实记录,报告写明样本量小这一局限。

---

## 10. 你的 DoD(Definition of Done)

- [ ] 桌面应用跑通:导入 → 识别 → 校对改一行 → 导出 `.tex`;
- [ ] 错题本可增 / 查 / 删,并按课程筛选,`pytest` 通过;
- [ ] 20~30 张数据集 + 标注表 + 评估脚本;
- [ ] 端到端可用率 ≥ 70%(或如实记录实际值)并写入报告;
- [ ] Demo 视频中"一条龙"可现场复现。
