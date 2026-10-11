# Board2TeX 四人小组工作分工方案(简化版)

> 配套文档:《Board2TeX_Proposal_大纲.md》及四份《分工详解》。
> 设计前提:全组均为大一学生,**共同参与、模块主责、交叉互补**:每人主责一个模块,并结对交叉参与另一模块的开发与评审;组长额外承担集成、编译与项目管理。
> 目标:把约 740 行工程拆成 4 条可并行、接口清晰、能独立验收的工作流,**大部分工作是写代码**。

---

## 0. 总体原则

- **共同参与,模块主责,交叉互补**:需求、方案与进度四人共同确定;开发阶段每人主责一个模块,同时两两结对参与另一模块的开发与代码评审,保证每人理解整条流程。
- **组长先给骨架**:每个模块组长先提交一个"能跑但结果可能是错"的骨架 + 一张测试图 + 一条验证命令。这是协作机制,不是代写。
- **接口先行**:Week 6 冻结模块间数据结构(见 §2),之后不改。
- **小步交付**:每人每周至少提交一个可运行的 commit;卡住超过半天就在群里贴报错 + 截图。
- **分工证据**:所有代码进 GitHub,commit / PR 记录即分工证据,报告逐模块写明个人贡献。

---

## 1. 成员与主责模块

| 成员 | 角色 | 主责模块 | 核心交付物 |
|---|---|---|---|
| A | 组长 / 集成 & GUI 框架 & 编译 | 图像入口、pix2tex 模板、`main.py`、GUI 主窗口、PDF 编译、项目管理 | 图像入口 + 集成主程序 + 可运行 GUI |
| B | 图像增强 & 版面 | CLAHE/Otsu 二值化、裁剪、水平投影切行、行分类、可视化 | `enhance.py`、`layout/` 模块 + 标注图 |
| C | 识别 & 合成 | PaddleOCR/pix2tex 封装、LaTeX 转义、`.tex` 生成 | 识别合成模块、`.tex` 生成器 |
| D | 应用 & 评估 | GUI 控件填充、导出 .tex/PDF、SQLite 错题本、评估脚本 | 应用控件、错题本、评估报告 |

> 每份《分工详解》里都写清了"**你要实现的函数清单**"和"**可以照抄的骨架**",照做即可;卡住先问结对伙伴,再找组长。

---

## 2. 模块接口约定(冻结于 Week 6)

各成员严格按下列数据结构交接。

| 接口 | 生产者 → 消费者 | 数据结构 |
|---|---|---|
| `raw_image` | 输入 | `np.ndarray` (BGR, uint8) |
| `load_image()` | A → 全组 | `np.ndarray`(已缩放 BGR,长边 ≤ 1600) |
| `enhance.py` 四函数 | B 实现,A 的 `preprocess()` 调用 | 二值图(**前景为白 255**) |
| `layout_regions` | B → C/D | `List[Region]` |
| `Region` | B 定义 | `{"bbox": (x,y,w,h), "type": "text"\|"formula", "order": int, "image": np.ndarray, "confidence": float}` |
| `Block` | C 定义 | `{"order": int, "type": str, "content": str, "latex": str, "confidence": float, "bbox": (x,y,w,h)}` |
| `Document` | C → D | `{"blocks": List[Block], "tex_source": str}` |
| 错题本记录 | D 内部 | SQLite 表 `problems(id, course, tags, tex, image_path, created_at)` |

> **单列假设**:不处理双列,`Region` 不需要 `col` 字段。`order` 严格递增,从 0 开始。
> **拍正假设**:第一版不做透视矫正,拍照时尽量拍正;矫正列 Future Work。

---

## 3. 详细任务拆解

### A(组长 · 集成 & GUI 框架 & 编译)—— 约 200 行

**主责**
- [ ] 维护 `check_env.py`(已通过);维护 `requirements.txt` 与 README 安装说明。
- [ ] **为 B/C/D 提供每个模块的骨架文件**(函数名、参数、返回值、`# TODO` 注释、一张测试图、一条验证命令)。
- [ ] 图像入口 `preprocess/pipeline.py`:`load_image()` 读图 + 缩放,并调用 B 的 enhance 四函数。
- [ ] `recog/formula.py`:pix2tex 封装模板(**已验证可用**),并完成首次运行暖机(提前下载模型)。
- [ ] GUI 主窗口框架 `gui/main_window.py`:布局、按钮、文件对话框、结果列表、信号槽(先同步执行,不强制子线程)。
- [ ] 集成主流程 `main.py` 的 `pipeline()`;PDF 编译 `gui/exporter.py` 里的 `xelatex` 调用部分。
- [ ] 项目管理:例会、看板、PR 审核、最终报告汇总。

**验收标准**:`main.py` 一条龙可跑;GUI 能打开并跑通;每位组员的骨架都能独立运行。

---

### B(图像增强 & 版面)—— 约 180 行

**你要实现的东西(组长给了骨架)**
- [ ] `preprocess/enhance.py`:
  - `to_gray(bgr)` → 灰度(1 行);
  - `normalize(gray)` → CLAHE 光照归一化(2 行,替代原版复杂去反光);
  - `binarize(gray)` → Otsu 二值化(1 行);
  - `crop_content(bin_img)` → 用投影裁掉四周空白(约 20 行,组长给框架)。
- [ ] `layout/segment.py`:**水平投影切行** —— 统计每行前景像素数,空白处切行(约 25 行,最容易上手的算法)。
- [ ] `layout/classify.py`:`classify_line(line_img)` → 用"高宽比 + 连通域特征"简单投票判 `text`/`formula`(约 20 行,组长给骨架)。
- [ ] `layout/visualize.py`:在原图上画框并标注类型(约 15 行,纯画图)。
- [ ] 单元测试 `tests/test_layout.py`。

**验收标准**:工整板书行切分基本正确;分类结果附人工核对通过的标注图。

---

### C(识别 & 合成)—— 约 180 行

**你要实现的东西**
- [ ] `recog/ocr_engine.py`:封装 `PaddleOCR`,写一个 `recognize_text(img) -> (文字, 置信度)`(组长给模板,约 20 行)。
- [ ] `recog/formula.py`:与 A 共同验证 `recognize_formula(img) -> (latex, 置信度)`(A 提供已验证可用的模板,约 15 行)。
- [ ] `recog/postprocess.py`:
  - `escape_latex(s)`:用字典把 `& % _ # $ ^ ~ { } \` 转义(约 10 行,最简单);
  - `clean_latex(s)`:去掉多余 `\left \right`、压缩空白(约 8 行)。
- [ ] `recog/engine.py`:`recognize(region) -> Block` 统一入口(约 20 行,按 `type` 二选一)。
- [ ] `compose/builder.py`:
  - `.tex` 模板(article + amsmath,组长给);
  - `build_body(blocks)`:按 `order` 排序,文字合并成段、公式包进 `$$...$$`(约 25 行);
  - `compose_document(regions) -> Document`(约 10 行)。
- [ ] 单元测试 `tests/test_recog.py`。

**验收标准**:能生成可被 `xelatex` 编译的 `.tex`;转义单测通过。

---

### D(应用 & 评估)—— 约 180 行

**你要实现的东西**
- [ ] `vault/db.py`:SQLite 错题本
  - `init_db()` 建表(约 8 行);
  - `add_problem(...)` 插入(约 6 行);
  - `list_problems()` 列出全部(约 5 行);
  - `search(course)` 按课程筛选(约 8 行)。
- [ ] `gui/exporter.py`:`export_tex(doc, path)` 写 UTF-8 文件(约 5 行);`export_pdf(tex_path)` 调用 A 已写好的 xelatex 函数。
- [ ] `gui/` 简单控件(在 A 的框架上填):结果编辑行、"存入错题本"对话框、错题本列表页(约 40 行)。
- [ ] `eval/dataset.py` + `eval/metrics.py` + `eval/run_eval.py`:
  - 与 A/B 协作采集并整理 **20~30 张**板书照片;
  - `usable_rate(pairs)`:人工改动不超过 N 处即算可用(约 20 行);
  - 输出一个简单统计到 `eval/report.txt`。
- [ ] 单元测试 `tests/test_vault.py`。

**验收标准**:一条龙 demo 可现场跑通;错题本能存能列;评估脚本能出可用率。

---

## 4. 里程碑与负责人对照(对齐大纲 §8)

| 周次 | 里程碑 | 主责人 | 协作者 |
|---|---|---|---|
| Week 4 | 组队、环境搭建 | A | 全组 |
| Week 5 | **期中汇报**(提案大纲 + 环境验证) | A | 全组 |
| Week 6 | 冻结接口、A 发放骨架、各人跑通最小例子 | A / 全组 | — |
| Week 7~8 | 图像增强 + 版面 + 识别合成核心模块 | B / C | A 支援 |
| Week 9~10 | 识别与 `.tex` 合成;与版面联调整版识别 | A / B / C | — |
| Week 11~12 | 导出、错题本、GUI 控件 | D | A |
| Week 13~14 | GUI 组装、一条龙联调 | D + A | 全组 |
| Week 15 | 评估、整体联调打包、demo | D + A | 全组 |
| Week 16 末 | **提交项目报告**(量化评估 / 贡献 / AI 声明) | A | 全组 |
| Week 17 | **决赛展示 + Demo 视频** | A | 全组 |

---

## 5. 每周例会机制

- **时间**:每周固定一次,由 A 主持并记录纪要(存 `docs/meetings/weekN.md`);
- **产出**:每人汇报 ① 本周完成 ② 下周计划 ③ 阻塞点(卡住多久);
- **看板**:GitHub Issues / Projects 列 `Todo / Doing / Done`,卡片标注负责人;
- **协作规则**:跨模块改动先更新 §2 接口约定,再提 PR,由 A 审核合并;
- **互助规则**:任何人卡住超过半天,直接在群里贴报错 + 截图,先由结对伙伴协助,再由组长远程解决。

---

## 6. 工作量汇总(对齐大纲 §5)

| 模块 | 预估代码量 | 负责人 |
|---|---|---|
| 图像入口 + 集成 + GUI 框架 + 编译 + pix2tex 模板 | 200+ 行 | A |
| 图像增强 + 行切分 + 分类 + 可视化 | 180+ 行 | B |
| 识别封装 + 转义 + `.tex` 合成 | 180+ 行 | C |
| 导出 + 错题本 + 评估 + 数据集 | 180+ 行 | D |
| **合计** | **约 740 行** | 全员 |

> 说明:四个模块工程量相近、全是写代码任务;集成与调试经验要求上 A 略高,由组长承担。答辩时说明"主责 + 交叉互补"的安排保证每人都有完整模块贡献。

---

## 7. 验收清单(定义每个成员的 "Done")

- [ ] A:图像入口 + `main.py` + GUI 框架可运行,并为每人提供过骨架;
- [ ] B:`enhance.py` 与 `layout/` 输出 `layout_regions` 并附可视化标注图;
- [ ] C:识别合成模块生成可编译 `.tex`;
- [ ] D:导出 + 错题本 + 评估脚本,一条龙 demo 跑通,可用率 ≥ 70%;
- [ ] 全员:代码入 GitHub、commit 记录清晰、报告贡献说明与 AI 声明齐全。
