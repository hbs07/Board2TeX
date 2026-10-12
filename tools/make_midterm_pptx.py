# -*- coding: utf-8 -*-
"""生成《Board2TeX 期中汇报》PPTX(中文版 + 英文版)。

用法:  python tools/make_midterm_pptx.py
输出:  docs/03-report/Board2TeX_期中汇报.pptx        (中文)
        docs/03-report/Board2TeX_Midterm_Report.pptx  (English)
说明:  7 张 Slide,与 docs/03-report/ 下两份讲稿逐页一致;
        每页右上角标注讲者,备注栏内嵌对应讲稿原文(接力汇报用)。
"""
import os

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

NAVY = RGBColor(0x1F, 0x38, 0x64)
ACCENT = RGBColor(0xE8, 0x8D, 0x2E)
GRAY = RGBColor(0x59, 0x59, 0x59)
LIGHT = RGBColor(0xEA, 0xF1, 0xFB)
LIGHTER = RGBColor(0xF2, 0xF6, 0xFC)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARKBG = RGBColor(0x16, 0x22, 0x3A)
SOFTBLUE = RGBColor(0x8F, 0xA3, 0xC8)
GREEN = RGBColor(0x2E, 0x7D, 0x32)
GREENBG = RGBColor(0xE8, 0xF5, 0xE9)
WARMBG = RGBColor(0xFF, 0xF3, 0xDE)

OUT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..",
                                        "docs", "03-report"))

# 仅作默认占位;build() 按语言显式传入字体(中文=微软雅黑,英文=Calibri)
FONT = "Calibri"

TEXTS = {
    "cn": dict(
        file="Board2TeX_期中汇报.pptx",
        font="微软雅黑",
        cover_title="Board2TeX",
        cover_sub="板书 → LaTeX 一键归档工具",
        cover_meta="ICSP (Track A) 期中汇报 · Fall 2026",
        cover_team="小组成员:胡秉善(组长)· 郭佳欣 · 陶谱州 · 李若宸",
        cover_repo="github.com/hbs07/Board2TeX",
        cover_foot="四人接力汇报 · 约 3 分钟 · 讲者:郭佳欣",
        s2_title="问题与目标", s2_sp="讲者 · 郭佳欣",
        pain_label="痛点",
        pain=["手机拍板书快,复习时逐条敲进 LaTeX/Word,慢且易错",
              "Mathpix 等按次收费,只支持单条公式截图",
              "整版板书、英文与公式混排,现有工具无法处理"],
        goal_label="我们的目标",
        goal=["免费工具,支持整版板书 + 英文与公式混排",
              "用户:归档板书复习的同学;整理讲义的助教与老师"],
        diff_title="我们的不同",
        diff=["整版板书 → 可编译文档,完整端到端",
              "支持英文与公式混排",
              "错题本归档,服务复习闭环"],
        diff_foot="—— 现有工具均不具备",
        s3_title="系统架构", s3_sp="讲者 · 胡秉善",
        input_line="输入:一张板书照片(第一版拍照拍正)",
        stages=[("① 图像预处理", "缩放 · 灰度", "CLAHE · Otsu · 裁剪"),
                ("② 版面分析", "水平投影切行", "文字/公式分类"),
                ("③ 识别", "文字→PaddleOCR", "公式→pix2tex"),
                ("④ LaTeX 合成", "特殊字符转义", "拼接可编译 .tex"),
                ("⑤ 应用", "PyQt5 校对编辑", "导出 PDF · 错题本")],
        output_line="输出:可编译 .tex → PDF,可存入错题本",
        stack1="技术栈:Python · OpenCV · PaddleOCR · pix2tex(LaTeX-OCR)· "
               "PyQt5 · SQLite",
        stack2="环境已由 check_env.py 验证:15 OK / 0 FAIL,CPU 推理,模型已暖机",
        s4_title="关键技术点", s4_sp="讲者 · 胡秉善",
        cards=[("① 光照增强", "CLAHE 拉匀明暗 + Otsu 自动阈值;现成函数组合,"
                             "简单稳定"),
               ("② 按行切分", "统计每行前景像素,空白处即行分界;第一版只做"
                             "单列"),
               ("③ 文字 / 公式区分", "高宽比 + 连通域几何特征粗判;拿不准在"
                                   "界面人工改判"),
               ("④ 拼接 LaTeX", "& % _ # 等特殊字符统一转义;xelatex 实际编译"
                               "验证")],
        scope="有意缩小范围:透视矫正 · 双列 · 行内切块 · 反光修复 · 实时预览"
              " → 列入后续版本;第一版拍照拍正即可",
        s5_title="团队分工", s5_sp="讲者 · 陶谱州",
        headline="共同参与 · 模块主责 · 交叉互补",
        table=[("成员", "主责模块", "核心交付物"),
               ("胡秉善(组长)", "图像入口 · 主程序集成 · GUI 框架 · PDF 编译",
                "可运行主程序 + 集成管线"),
               ("郭佳欣", "图像增强 · 按行切分 · 行分类",
                "enhance.py + layout/ + 标注图"),
               ("陶谱州", "识别封装 · LaTeX 转义与合成",
                "识别合成模块 + 可编译 .tex"),
               ("李若宸", "界面 · 导出 · 错题本 · 评估",
                "桌面应用 + 错题本 + 评估报告")],
        s5_bullets=["两两结对,交叉参与另一个模块的开发与代码评审",
                    "Week 6 冻结接口后,每人用统一骨架先跑通自己模块的最小示例",
                    "代码全部进 GitHub,commit 记录就是每个人的参与凭证"],
        s6_title="进度安排", s6_sp="讲者 · 陶谱州",
        chevrons=[("W4", "组队 · 环境"), ("W5", "期中汇报 · 本周"),
                  ("W6", "冻结接口 · 发骨架"), ("W7~10", "主体模块"),
                  ("W11~15", "界面 · 联调 · 评估"), ("W16", "项目报告"),
                  ("W17", "决赛展示")],
        risk2="Week 6 专门冻结接口 + 跑通最小示例,不急着联调,给开发留足 buffer",
        s6_bullets=[
            "Week 7~8:图像增强/切行/分类 + 识别封装;Week 9~10:识别合成,"
            "与版面联调",
            "Week 11~12:导出、错题本与 GUI 控件;Week 13~14:界面组装,"
            "打通完整流程",
            "Week 15:评估、联调打包与 demo 准备;Week 16:项目报告;"
            "Week 17:决赛展示"],
        s7_title="预期成果", s7_sp="讲者 · 李若宸",
        s7_bullets=[
            "交付:Windows 桌面程序,照片 → PDF 完整流程,支持错题本归档",
            "交付物:GitHub 仓库 · check_env 一键环境验证 · demo 视频 · "
            "项目报告"],
        metrics=[("行切分正确率 ≥ 90%", "自采 20~30 张工整板书,人工核对标注图"),
                 ("端到端可用率 ≥ 70%", "仅需少量人工修改即可导出正确 .tex"),
                 ("全流程 demo", "拍照 → 识别 → 校对 → PDF → 错题本")],
        ai="AI 使用声明:识别使用开源模型 PaddleOCR / pix2tex(报告中注明);"
           "其余代码由四名成员自行编写。",
        thanks="我们的汇报就到这里,谢谢大家!",
        qa="[停] 下面是提问环节",
        doc_title="Board2TeX 期中汇报",
        doc_comments="ICSP Track A 期中汇报,7 张 Slide,四人接力;备注栏含讲稿。",
        notes=[
            "【郭佳欣 · 10 秒】\n各位老师、同学好,我是第 __ 组的郭佳欣。"
            "我们的项目叫 **Board2TeX:拍一张板书照片,自动变成能编译的 "
            "LaTeX 文档**。下面由我们四个人接力汇报。",
            "【郭佳欣 · 25 秒】\n为什么做这个:拍板书很快,但复习时把公式一条"
            "条敲进 LaTeX,**又慢又容易错**;市面上的工具按次收费,而且只认单"
            "条公式,整版板书、混排就不行。所以我们想做**免费、整版处理的一条"
            "龙工具**。和现有工具的具体差异,大家看屏幕上这张对比表。\n"
            "(交接)接下来请胡秉善同学介绍系统方案。",
            "【胡秉善 · 30 秒】\n谢谢郭佳欣。整个流程五步,大家跟着屏幕上的图"
            "走:预处理把**字迹和背景**分清楚;版面分析**按行切开**,判断文字"
            "还是公式;识别环节文字行走 PaddleOCR、公式行走 pix2tex;然后拼成"
            "可编译的 LaTeX;最后在桌面程序里**校对、导出 PDF、存错题本**。\n"
            "(衔接)这套流程里有几个关键技术点,我接着讲。",
            "【胡秉善 · 35 秒】\n四个技术点,细节屏幕上都有,我各用一句话点一"
            "下。一是**光照增强**:CLAHE 拉均匀明暗,自动阈值二值化,简单稳定。"
            "二是**按行切分**:按投影找行间空隙,第一版只做单列。三是**文字公"
            "式粗分**:先按几何特征判断,拿不准的留给界面人工改。四是 **LaTeX "
            "转义**:特殊字符统一转义,并用 xelatex 真实编译验证。\n(交接)团"
            "队怎么分工、进度怎么排,请陶谱州同学介绍。",
            "【陶谱州 · 25 秒】\n谢谢胡秉善。分工原则一句话:**立项方案大家一"
            "起定;开发每人主责一个模块,两两结对、交叉评审**。具体谁负责哪一"
            "块,大家看屏幕上的分工表。所有代码提交 GitHub,**commit 记录就是"
            "我们每个人参与的凭证**。\n(衔接)接下来的进度安排,我继续讲。",
            "【陶谱州 · 15 秒】\n进度大家看屏幕上的时间轴:现在 Week 5 期中汇"
            "报,之后主体模块、界面联调评估、报告、决赛展示依次推进。\n"
            "(交接)最后请李若宸同学介绍预期成果。",
            "【李若宸 · 25 秒】\n谢谢陶谱州。最终交付一个 **Windows 桌面程序**"
            ",走通从照片到 PDF 的完整流程,带错题本;指标是**行切分正确率 90% "
            "以上、端到端可用率 70% 以上**(见屏幕)。识别用的开源模型会在报告"
            "里注明,其余代码由我们四个人自己完成。\n我们的汇报就到这里,谢谢"
            "大家。\n[停] 下面是提问环节。",
        ],
    ),
    "en": dict(
        file="Board2TeX_Midterm_Report.pptx",
        font="Calibri",
        cover_title="Board2TeX",
        cover_sub="Board → LaTeX One-Click Archiving Tool",
        cover_meta="ICSP (Track A) Midterm Report · Fall 2026",
        cover_team="Team: Hu Bingshan (Leader) · Guo Jiaxin · Tao Puzhou · "
                   "Li Ruochen",
        cover_repo="github.com/hbs07/Board2TeX",
        cover_foot="Four-speaker relay · about 5 minutes · Speaker: "
                   "Guo Jiaxin",
        s2_title="Problem & Goal", s2_sp="Speaker · Guo Jiaxin",
        pain_label="Pain points",
        pain=["Snapping a photo is easy — retyping every formula into "
              "LaTeX is slow and error-prone",
              "Mathpix charges per use and only recognizes single-formula "
              "screenshots",
              "Full boards, and English mixed with formulas, are not "
              "supported by existing tools"],
        goal_label="Our goal",
        goal=["A free tool that works on a whole board",
              "Users: students archiving board notes; TAs and instructors "
              "turning derivations into handouts"],
        diff_title="What sets us apart",
        diff=["Full board → compilable document, end to end",
              "English text mixed with formulas",
              "Error notebook for archiving and review"],
        diff_foot="— none of this exists in current tools",
        s3_title="System Design", s3_sp="Speaker · Hu Bingshan",
        input_line="Input: one board photo (shot as straight as possible "
                   "in v1)",
        stages=[("① Preprocessing", "resize · grayscale",
                 "CLAHE · Otsu · crop"),
                ("② Layout analysis", "projection line split",
                 "text vs. formula"),
                ("③ Recognition", "text → PaddleOCR", "formula → pix2tex"),
                ("④ LaTeX composition", "character escaping",
                 "compilable .tex"),
                ("⑤ Application", "PyQt5 proofreading",
                 "PDF export · notebook")],
        output_line="Output: compilable .tex → PDF, saved to the error "
                    "notebook",
        stack1="Stack: Python · OpenCV · PaddleOCR · pix2tex (LaTeX-OCR) · "
               "PyQt5 · SQLite",
        stack2="Verified by check_env.py: 15 OK / 0 FAIL · CPU inference · "
               "models warmed up",
        s4_title="Key Technical Problems", s4_sp="Speaker · Hu Bingshan",
        cards=[("① Illumination enhancement",
                "CLAHE evens out lighting + Otsu auto threshold; ready-made "
                "and stable"),
               ("② Line segmentation",
                "count foreground pixels per row; blank rows are boundaries; "
                "single column in v1"),
               ("③ Text vs. formula",
                "geometric features cast the first vote; uncertain lines are "
                "fixed in the UI"),
               ("④ Compilable LaTeX",
                "escape & % _ # uniformly; verify by compiling with "
                "xelatex")],
        scope="Deliberate scope cut: perspective correction · double columns "
              "· in-line splitting · glare removal · live preview → later; "
              "shooting straight is enough for v1",
        s5_title="Team Division", s5_sp="Speaker · Tao Puzhou",
        headline="Full participation · Module ownership · Cross-coverage",
        table=[("Member", "Module ownership", "Key deliverables"),
               ("Hu Bingshan (Leader)",
                "Image entry · integration · UI framework · PDF compilation",
                "Runnable pipeline + integration"),
               ("Guo Jiaxin",
                "Image enhancement · line segmentation · classification",
                "enhance.py + layout/ + annotated images"),
               ("Tao Puzhou",
                "Recognition wrappers · LaTeX escaping & composition",
                "Recognition module + compilable .tex"),
               ("Li Ruochen",
                "UI · export · error notebook · evaluation",
                "Desktop app + notebook + evaluation report")],
        s5_bullets=[
            "Pair up and cross-join another module for development and code "
            "review",
            "After interfaces freeze in Week 6, everyone first runs a minimal "
            "example on the shared skeletons",
            "All code goes to GitHub — commit history is each person's record "
            "of contribution"],
        s6_title="Schedule", s6_sp="Speaker · Tao Puzhou",
        chevrons=[("W4", "Team & env"), ("W5", "Midterm · now"),
                  ("W6", "Freeze + skeletons"), ("W7–10", "Core modules"),
                  ("W11–15", "UI & integration"), ("W16", "Report"),
                  ("W17", "Finals")],
        risk2="Week 6 is for freezing interfaces and running minimal examples "
              "— no rush to integrate, buffer built in",
        s6_bullets=[
            "Week 7–8: enhancement / segmentation / classification + "
            "recognition wrappers; Week 9–10: composition, integrated with "
            "layout",
            "Week 11–12: export, error notebook and UI controls; Week 13–14: "
            "assemble the full pipeline",
            "Week 15: evaluation, packaging and demo; Week 16: report; "
            "Week 17: finals"],
        s7_title="Expected Outcomes", s7_sp="Speaker · Li Ruochen",
        s7_bullets=[
            "Deliverable: a Windows desktop app — the full pipeline from "
            "photo to PDF, with the error notebook",
            "Deliverables: GitHub repo · check_env one-click verification · "
            "demo video · project report"],
        metrics=[("Line-segmentation accuracy ≥ 90%",
                  "20–30 neat board photos, manually checked"),
                 ("End-to-end usability ≥ 70%",
                  "usable with only minor manual edits"),
                 ("Full-pipeline demo",
                  "photo → recognition → proofread → PDF → notebook")],
        ai="AI statement: recognition uses open-source models — PaddleOCR / "
           "pix2tex (stated in the report); the rest of the code is written "
           "by the four of us.",
        thanks="That is our report. Thank you!",
        qa="[pause] Now we are happy to take questions.",
        doc_title="Board2TeX Midterm Report",
        doc_comments="ICSP Track A midterm report, 7 slides, four-speaker "
                     "relay; speech text in the notes pane.",
        notes=[
            "【Guo Jiaxin · 15 sec】\nHello everyone. I'm Guo Jiaxin from "
            "Group __. Our project is called Board2TeX. In "
            "short, it turns a photo of a blackboard into a compilable LaTeX "
            "document. All four of us built this project together, and today "
            "each of us will present one continuous part of it. Let me first "
            "explain the problem and our goal.\n(Handover) After Slide 2, "
            "Hu Bingshan steps up.",
            "【Guo Jiaxin · 45 sec】\nLet me start with why we are doing "
            "this.\nTaking photos of the board with a phone is easy, but when "
            "we review, we have to type every formula into LaTeX by hand — "
            "slow, and easy to get wrong. Existing tools like Mathpix charge "
            "per use, and they only recognize a screenshot of a single "
            "formula. They cannot handle a full board, and they do not "
            "support English text mixed with formulas.\nSo we want to build a "
            "free tool that works on a whole board. Our target users are "
            "students who want to archive board notes, and teaching "
            "assistants and instructors who need to turn derivations into "
            "handouts.\nWhat sets our project apart is the complete "
            "end-to-end flow — from a full board all the way to a compilable "
            "document — with English text mixed with formulas, and an error "
            "notebook for archiving. Existing tools offer none of these.\n"
            "(Handover) Next, Hu Bingshan will walk you through the system "
            "design.",
            "【Hu Bingshan · 50 sec】\nThank you, Jiaxin. Our pipeline has five "
            "stages.\nFirst, preprocessing: we resize the photo, then convert "
            "to grayscale, normalize the lighting, and binarize, so the "
            "writing stands out clearly from the background. Second, layout "
            "analysis: we split the board into lines, and judge whether each "
            "line is text or a formula. Third, recognition: text lines go to "
            "PaddleOCR, formula lines go to pix2tex. Fourth, composition: "
            "everything is assembled into a compilable LaTeX file in reading "
            "order. Fifth, the application: in a desktop program, the user "
            "proofreads, exports a PDF, and saves the result to an error "
            "notebook.\nOur stack is Python, OpenCV, PaddleOCR, pix2tex, "
            "PyQt5, and SQLite.\n(Continue) Now let me zoom into the key "
            "technical problems.",
            "【Hu Bingshan · 60 sec】\nFirst, illumination enhancement. Phone "
            "photos of a board are often half bright, half dark. We equalize "
            "the lighting with CLAHE, then binarize with Otsu's automatic "
            "threshold — both are ready-made OpenCV functions, and the "
            "combination is simple and stable.\nSecond, line segmentation. We "
            "count foreground pixels per row and treat the blank rows as the "
            "boundaries between lines. It is simple and stable, and the first "
            "version handles single columns only.\nThird, telling text and "
            "formulas apart. They need different engines, so we first judge "
            "by geometric features, and let the user correct uncertain cases "
            "in the interface.\nFourth, producing compilable LaTeX. "
            "Characters like percent, ampersand, and underscore break "
            "compilation if not escaped, so we escape them uniformly and "
            "verify by compiling with xelatex.\nTo be safe on time, the first "
            "version skips perspective correction, double columns, in-line "
            "block splitting, glare removal, and live preview — we have left "
            "those for later, and shooting the board straight is enough for "
            "now. This is a deliberate scope cut.\n(Handover) Now Tao Puzhou "
            "will explain how we divide the work and stay on schedule.",
            "【Tao Puzhou · 45 sec】\nThanks, Bingshan. Our division of work is "
            "built on full participation by all four of us: the proposal, the "
            "design, and the schedule were all decided together. During "
            "development, each of us owns one core module and also pairs up "
            "to join another module for development and code review, so every "
            "one of us understands the whole pipeline.\nSpecifically, Hu "
            "Bingshan owns the image entry, main integration, and the UI "
            "framework; Guo Jiaxin owns image enhancement and line "
            "segmentation; I own recognition integration and LaTeX "
            "composition; Li Ruochen owns the interface, export, and the "
            "error notebook. After the interfaces freeze in Week 6, each of "
            "us first runs a minimal example of our own module using the "
            "shared skeletons, test images, and verification commands. All "
            "code goes to GitHub, and the commit history is the record of "
            "each person's contribution.\n(Continue) Next, the schedule.",
            "【Tao Puzhou · 30 sec】\nIn terms of timing, we formed the team "
            "in Week 4, and this midterm report is in Week 5. Weeks 6 to 10 "
            "will finish the core modules, Weeks 11 to 15 the interface, "
            "integration, and evaluation, Week 16 the report, and Week 17 the "
            "final presentation.\n(Handover) Finally, Li Ruochen will present "
            "the expected outcomes.",
            "【Li Ruochen · 30 sec】\nThanks, Puzhou. We plan to deliver a "
            "Windows desktop program that runs the whole pipeline, from photo "
            "to PDF, and can save to the error notebook. On metrics, we are "
            "aiming for line-segmentation accuracy above 90%, and an "
            "end-to-end usability rate above 70%.\nRecognition uses "
            "open-source models, which we will state clearly in the report; "
            "the rest of the code is written by the four of us ourselves.\n"
            "That is our report. Thank you — from all four of us.\n> [pause] "
            "Now we are happy to take questions.",
        ],
    ),
}


def _set_run_font(run, size, bold=False, color=NAVY, name=FONT):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = name
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", name)


def _fill_text(tf, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
               font=FONT):
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    first = True
    for text, size, bold, color in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        run = p.add_run()
        run.text = text
        _set_run_font(run, size, bold, color, font)


def add_textbox(slide, l, t, w, h, lines, align=PP_ALIGN.LEFT,
                anchor=MSO_ANCHOR.TOP, font=FONT):
    box = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    _fill_text(box.text_frame, lines, align, anchor, font)
    return box


def add_shape(slide, l, t, w, h, fill, lines=None, shape=MSO_SHAPE.RECTANGLE,
              line_color=None, align=PP_ALIGN.CENTER,
              anchor=MSO_ANCHOR.MIDDLE, font=FONT):
    sp = slide.shapes.add_shape(shape, Inches(l), Inches(t), Inches(w),
                                Inches(h))
    sp.fill.solid()
    sp.fill.fore_color.rgb = fill
    if line_color is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line_color
        sp.line.width = Pt(1)
    sp.shadow.inherit = False
    if lines:
        _fill_text(sp.text_frame, lines, align, anchor, font)
    return sp


def add_bullets(slide, l, t, w, h, items, size=17, color=NAVY, gap=6,
                font=FONT):
    box = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    first = True
    for item in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.space_after = Pt(gap)
        run = p.add_run()
        run.text = "• " + item
        _set_run_font(run, size, False, color, font)
    return box


def set_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def build(T):
    font = T["font"]
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    def new_slide(title=None, presenter=None, page=None):
        s = prs.slides.add_slide(blank)
        if title:
            add_textbox(s, 0.55, 0.3, 9.6, 0.85, [(title, 30, True, NAVY)],
                        font=font)
            add_shape(s, 0.6, 1.12, 1.6, 0.05, ACCENT)
        if presenter:
            add_textbox(s, 9.7, 0.42, 3.1, 0.4, [(presenter, 12, False, GRAY)],
                        align=PP_ALIGN.RIGHT, font=font)
        if page:
            add_textbox(s, 12.5, 7.02, 0.7, 0.35, [(page, 11, False, GRAY)],
                        align=PP_ALIGN.RIGHT, font=font)
        return s

    # ---------- Slide 1 · cover ----------
    s = prs.slides.add_slide(blank)
    add_shape(s, 0, 0, 13.333, 7.5, DARKBG)
    add_shape(s, 5.87, 1.62, 1.6, 0.05, ACCENT)
    add_textbox(s, 1.5, 1.95, 10.33, 1.1, [(T["cover_title"], 54, True, WHITE)],
                align=PP_ALIGN.CENTER, font=font)
    add_textbox(s, 1.5, 3.05, 10.33, 0.7, [(T["cover_sub"], 26, False, WHITE)],
                align=PP_ALIGN.CENTER, font=font)
    add_textbox(s, 1.5, 3.95, 10.33, 0.45, [(T["cover_meta"], 16, False,
                                             SOFTBLUE)],
                align=PP_ALIGN.CENTER, font=font)
    add_textbox(s, 1.5, 4.6, 10.33, 0.5, [(T["cover_team"], 16, False, WHITE)],
                align=PP_ALIGN.CENTER, font=font)
    add_textbox(s, 1.5, 5.15, 10.33, 0.4, [(T["cover_repo"], 13, False,
                                            SOFTBLUE)],
                align=PP_ALIGN.CENTER, font=font)
    add_textbox(s, 1.5, 6.6, 10.33, 0.4, [(T["cover_foot"], 13, False,
                                           SOFTBLUE)],
                align=PP_ALIGN.CENTER, font=font)
    set_notes(s, T["notes"][0])

    # ---------- Slide 2 · problem & goal ----------
    s = new_slide(T["s2_title"], T["s2_sp"], "2 / 7")
    add_textbox(s, 0.6, 1.45, 6.0, 0.4, [(T["pain_label"], 15, True, GRAY)],
                font=font)
    add_bullets(s, 0.6, 1.9, 6.1, 2.2, T["pain"], size=17, font=font)
    add_textbox(s, 0.6, 4.1, 6.0, 0.4, [(T["goal_label"], 15, True, GRAY)],
                font=font)
    add_bullets(s, 0.6, 4.55, 6.1, 2.2, T["goal"], size=17, font=font)
    card = add_shape(s, 7.1, 1.45, 5.65, 4.9, LIGHT,
                     lines=[(T["diff_title"], 18, True, NAVY),
                            ("", 8, False, NAVY)]
                           + [(d, 17, False, NAVY) for d in T["diff"]]
                           + [("", 8, False, NAVY),
                              (T["diff_foot"], 14, True, ACCENT)],
                     align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE, font=font)
    card.text_frame.margin_left = Inches(0.35)
    card.text_frame.margin_right = Inches(0.25)
    set_notes(s, T["notes"][1])

    # ---------- Slide 3 · system design ----------
    s = new_slide(T["s3_title"], T["s3_sp"], "3 / 7")
    add_textbox(s, 0.6, 1.42, 12.0, 0.4, [(T["input_line"], 14, False, GRAY)],
                font=font)
    box_w, gap, y0, box_h = 2.24, 0.28, 1.95, 1.75
    for i, (t, l1, l2) in enumerate(T["stages"]):
        x = 0.5 + i * (box_w + gap)
        add_shape(s, x, y0, box_w, box_h, LIGHT,
                  lines=[(t, 15, True, NAVY), (l1, 12, False, NAVY),
                         (l2, 12, False, NAVY)],
                  shape=MSO_SHAPE.ROUNDED_RECTANGLE, line_color=NAVY,
                  font=font)
        if i < len(T["stages"]) - 1:
            add_shape(s, x + box_w + 0.01, y0 + 0.68, 0.26, 0.38, ACCENT,
                      shape=MSO_SHAPE.RIGHT_ARROW)
    add_textbox(s, 0.6, 3.95, 12.0, 0.4, [(T["output_line"], 14, False, GRAY)],
                font=font)
    add_shape(s, 0.6, 4.7, 12.13, 1.3, LIGHTER, line_color=NAVY,
              lines=[(T["stack1"], 15, True, NAVY),
                     (T["stack2"], 14, False, GRAY)], font=font)
    set_notes(s, T["notes"][2])

    # ---------- Slide 4 · key technical problems ----------
    s = new_slide(T["s4_title"], T["s4_sp"], "4 / 7")
    pos = [(0.6, 1.5), (6.78, 1.5), (0.6, 3.4), (6.78, 3.4)]
    for (t, d), (x, y) in zip(T["cards"], pos):
        card = add_shape(s, x, y, 5.95, 1.7, LIGHTER, line_color=NAVY,
                         lines=[(t, 17, True, NAVY), (d, 14, False, GRAY)],
                         align=PP_ALIGN.LEFT, font=font)
        card.text_frame.margin_left = Inches(0.3)
        card.text_frame.margin_right = Inches(0.25)
    add_shape(s, 0.6, 5.45, 12.13, 0.95, WARMBG, line_color=ACCENT,
              lines=[(T["scope"], 14, True, NAVY)], font=font)
    set_notes(s, T["notes"][3])

    # ---------- Slide 5 · team division ----------
    s = new_slide(T["s5_title"], T["s5_sp"], "5 / 7")
    add_textbox(s, 0.6, 1.42, 12.0, 0.45, [(T["headline"], 17, True, ACCENT)],
                font=font)
    rows = T["table"]
    gf = s.shapes.add_table(5, 3, Inches(0.6), Inches(2.0), Inches(12.13),
                            Inches(2.9))
    tbl = gf.table
    tbl.columns[0].width = Inches(2.3)
    tbl.columns[1].width = Inches(5.63)
    tbl.columns[2].width = Inches(4.2)
    for r in range(5):
        tbl.rows[r].height = Inches(0.5 if r == 0 else 0.62)
        for c in range(3):
            cell = tbl.cell(r, c)
            cell.margin_left = Inches(0.12)
            cell.margin_right = Inches(0.08)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = NAVY
                text, size, bold, color = rows[r][c], 15, True, WHITE
            else:
                cell.fill.fore_color.rgb = (WHITE if r % 2 else LIGHTER)
                text = rows[r][c]
                size, bold = 14, (c == 0)
                color = NAVY
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            run = p.add_run()
            run.text = text
            _set_run_font(run, size, bold, color, font)
    add_bullets(s, 0.6, 5.25, 12.1, 1.8, T["s5_bullets"], size=15, gap=4,
                font=font)
    set_notes(s, T["notes"][4])

    # ---------- Slide 6 · schedule ----------
    s = new_slide(T["s6_title"], T["s6_sp"], "6 / 7")
    for i, (w, label) in enumerate(T["chevrons"]):
        if i == 0:
            fill, tc = GREEN, WHITE
        elif i == 1:
            fill, tc = ACCENT, WHITE
        else:
            fill, tc = LIGHT, NAVY
        add_shape(s, 0.5 + i * 1.76, 1.9, 1.98, 1.0, fill,
                  lines=[(w, 14, True, tc), (label, 11, False, tc)],
                  shape=MSO_SHAPE.CHEVRON, font=font)
    add_shape(s, 0.6, 3.35, 12.13, 1.15, GREENBG, line_color=GREEN,
              lines=[(T["risk2"], 15, True, GREEN)], font=font)
    add_bullets(s, 0.6, 4.85, 12.1, 2.1, T["s6_bullets"], size=15, gap=5,
                font=font)
    set_notes(s, T["notes"][5])

    # ---------- Slide 7 · expected outcomes ----------
    s = new_slide(T["s7_title"], T["s7_sp"], "7 / 7")
    add_bullets(s, 0.6, 1.5, 12.1, 1.4, T["s7_bullets"], size=17, font=font)
    for i, (m, d) in enumerate(T["metrics"]):
        add_shape(s, 0.6 + i * 4.12, 3.15, 3.9, 1.35, LIGHT, line_color=NAVY,
                  lines=[(m, 17, True, NAVY), (d, 12, False, GRAY)],
                  font=font)
    add_textbox(s, 0.6, 4.85, 12.1, 0.5, [(T["ai"], 13, False, GRAY)],
                font=font)
    add_textbox(s, 0.6, 5.7, 12.1, 0.7, [(T["thanks"], 24, True, NAVY)],
                font=font)
    add_textbox(s, 0.6, 6.5, 12.1, 0.4, [(T["qa"], 14, False, GRAY)],
                font=font)
    set_notes(s, T["notes"][6])

    prs.core_properties.title = T["doc_title"]
    prs.core_properties.author = "Board2TeX Team"
    prs.core_properties.comments = T["doc_comments"]

    out = os.path.join(OUT_DIR, T["file"])
    prs.save(out)
    print("saved:", out, "| slides:", len(prs.slides._sldIdLst))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    build(TEXTS["cn"])
    build(TEXTS["en"])


if __name__ == "__main__":
    main()
