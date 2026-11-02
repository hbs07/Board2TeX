# Board2TeX · 板书 → LaTeX 一键归档工具

> ICSP Track A · Fall 2026 · 团队项目
> 拍一张板书/白板照片,自动完成 **图像增强 → 按行切分 → 识别 → 合成 .tex → 渲染 PDF**,并提供人工校对界面与 SQLite 错题本。

## 流程

```
板书照片
   │
   ▼
preprocess/   图像入口:读图、缩放、灰度、光照归一化、二值化、裁剪   (A + B)
   │
   ▼
layout/       版面分析:按行切分,判断每行是文字还是公式             (B)
   │
   ▼
recog/        识别:文字行 → PaddleOCR,公式行 → pix2tex             (C)
   │
   ▼
compose/      合成:拼接为可编译的 .tex                              (C)
   │
   ▼
gui/          校对界面 + 导出 PDF;xelatex 编译                      (A + D)
vault/        SQLite 错题本                                          (D)
eval/         数据集与端到端可用率评估                               (D)
```

一条龙入口:

```python
from main import pipeline
pre, regions, doc = pipeline("board_photo.jpg")   # doc["tex_source"] 可直接编译
```

## 快速开始

环境安装(Windows + uv + Python 3.12)见 **[docs/05-setup/环境安装指南.md](docs/05-setup/环境安装指南.md)**,装好后:

```powershell
.venv_b2t\Scripts\Activate.ps1        # 激活虚拟环境

python main.py assets/test_text.png data/exports   # 命令行:照片 → .tex → PDF
python -m gui.main_window                          # 图形界面
python -m pytest -q                                # 契约测试 + 验收看板
```

## 团队

| 成员 | 职责 |
|---|---|
| 胡秉善(A,组长) | 图像入口、集成、GUI 框架、PDF 编译、项目管理 |
| 郭佳欣(B) | 图像增强、版面分析(切行/分类/可视化) |
| 陶谱州(C) | 识别引擎接入(PaddleOCR / pix2tex)、LaTeX 合成 |
| 李若宸(D) | GUI 控件、校对编辑、导出、错题本、评估 |

协作方式:`main` 分支受保护,每人开 `feature/xxx` 分支开发,PR 由组长评审合并;commit 信息格式 `模块: 做了什么`。

### 从哪开始

每个人接手时按这个顺序:读自己的**分工文档** → 把**AI 辅导指南**整份复制给 AI(它已包含项目背景和你的任务)→ 跑通自己模块的验证命令。

| 成员 | 分工文档 | AI 辅导指南 | 自己模块的验证命令 |
|---|---|---|---|
| A 胡秉善 | [图像与集成](docs/02-roles/Board2TeX_分工_A_图像与集成.md) | [AI 指南 A](docs/04-ai-guides/Board2TeX_AI指南_A_组长.md) | `python main.py assets/test_text.png data/exports` |
| B 郭佳欣 | [版面分析](docs/02-roles/Board2TeX_分工_B_版面分析.md) | [AI 指南 B](docs/04-ai-guides/Board2TeX_AI指南_B_图像增强与版面.md) | `python -m layout.pipeline assets/test_text.png data/layout_check` |
| C 陶谱州 | [识别与合成](docs/02-roles/Board2TeX_分工_C_识别与合成.md) | [AI 指南 C](docs/04-ai-guides/Board2TeX_AI指南_C_识别与合成.md) | `python -m compose.builder` |
| D 李若宸 | [应用与评估](docs/02-roles/Board2TeX_分工_D_应用与评估.md) | [AI 指南 D](docs/04-ai-guides/Board2TeX_AI指南_D_应用与评估.md) | `python -m gui.main_window` |

## 测试

```powershell
python -m pytest -q
```

- `tests/test_contracts.py`:冻结接口的结构守卫。**红了说明有人改坏了接口**,先找组长。
- `tests/test_acceptance.py`:验收看板,每个测试对应一位组员的一条验收标准。
  - `passed` = 已达标;`xfailed` = 负责人还没做(正常,不是 bug);`xpassed` = 做完了,提醒组长删掉 xfail 标记;`failed` = 做了但没达标。

## MVP 边界(第一版)

- ✅ 单列版面、英文 + 公式混排、单张照片、CPU 推理
- ❌ 透视矫正(拍照拍正替代)、双列、行内切块、反光修复、实时预览 → Future Work

## 文档导航

- 提案与分工:`docs/01-proposal/`、`docs/02-roles/`
- 期中汇报:`docs/03-report/`
- AI 辅导指南(A/B/C/D 各一份,配合 AI 使用):`docs/04-ai-guides/`
- 环境安装:`docs/05-setup/环境安装指南.md`
- 协作规范:`.github/pull_request_template.md`(提 PR 时自动带出)

## 诚信声明(AI 辅助与开源组件)

本项目按课程要求声明 AI 辅助范围:

- **AI 辅助的部分**:项目骨架代码(函数签名、类型注解、文档字符串与占位实现)由 AI 生成,经组长审查后发放;集成代码(`preprocess/pipeline.py`、`gui/main_window.py`、`main.py` 等)由 AI 依据组长确认的设计起草、经组长逐行验证;文档、演示文稿与讲稿由 AI 协助起草。
- **成员独立完成的部分**:各模块算法实现(图像增强、切行、分类、识别封装、LaTeX 拼接、GUI 控件、错题本、评估)、联调调试、测试用例与全部技术决策。
- **开源组件**:文字识别使用 PaddleOCR,公式识别使用 pix2tex;均为开源模型,将在项目报告中注明。

各代码文件头部的 `AI 辅助说明` 行均指向本声明;细节以项目报告中的 AI 辅助说明章节为准。
