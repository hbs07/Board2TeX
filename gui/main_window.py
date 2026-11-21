# -*- coding: utf-8 -*-
"""gui/main_window.py —— 主窗口框架(主责: A 胡秉善;控件逻辑: D 李若宸)

验证命令(会弹出窗口,人工确认):
    python -m gui.main_window
期望结果:
    标题 Board2TeX 的窗口打开:左侧图像区 + 右侧编辑区 + 顶部 5 个按钮;
    「导入图片」能选图并显示;其余按钮在未识别时给出提示,不崩溃。

AI 辅助说明: 见 README「诚信声明」。

A 已就绪(D 可以直接用):
    - self.image_label : 显示图像的 QLabel(左);
    - self.editor_area : 右侧滚动区,里面 self.editor_layout 可加控件;
    - self.doc / self.pre / self.regions : 识别结果(数据结构见冻结接口);
    - 7 个按钮已接线:导入图片 / 运行识别 / 预览 / 导出 .tex / 导出 PDF /
      存入错题本 / 错题本;

编辑区实现(2026-11-21 接入):
    1. show_blocks(): 把 self.doc["blocks"] 渲染成一行一个输入框,低置信度标红;
    2. _on_block_edited(): 输入框改动实时写回 block["latex"];
    3. on_preview(): 预览当前 blocks 拼出的正文;
    4. 导出前统一 _rebuild_tex(),保证导出的是改过的版本;
    5. 错题本: 存入/查看/按编号删除,数据库在 vault/board2tex.db。
"""

from __future__ import annotations

import os

import numpy as np

# 必须先于 PyQt5 导入(原因见 gui/torch_preload.py 的说明与实测记录)
from gui import torch_preload  # noqa: F401

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QDialog, QFileDialog, QFrame, QHBoxLayout, QInputDialog,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QSplitter, QTextEdit, QVBoxLayout, QWidget,
)

from config import TEXT_CONF_THRESHOLD
from gui.exporter import compile_pdf, has_xelatex
from gui.preview_pane import PreviewPane
from main import pipeline
from preprocess.pipeline import load_image


def ndarray_to_qpixmap(img):
    """numpy 图(2D 灰度或 3D BGR) -> QPixmap。

    注意 .copy():QImage 只引用 numpy 内存,数组被回收就会花屏,
    必须 copy() 拷贝一份——这是分工文档反复强调的坑,别删。
    """
    if img.ndim == 2:
        h, w = img.shape
        qimg = QImage(img.data, w, h, w, QImage.Format_Grayscale8)
    else:
        rgb = np.ascontiguousarray(img[:, :, ::-1])  # BGR -> RGB 且保证内存连续
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg.copy())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Board2TeX · 板书转 LaTeX")
        self.resize(1440, 860)
        self.setMinimumSize(1200, 680)

        # ---- 识别结果状态(冻结接口的数据在这里流转) ----
        self.image_path: str | None = None
        self.pre: dict | None = None       # {"binary", "bgr"}
        self.regions: list[dict] = []      # layout 输出
        self.doc: dict | None = None       # {"blocks", "tex_source"}
        self.block_edits: dict[int, QLineEdit] = {}   # order -> 编辑框
        self._db = None                    # 错题本连接(懒加载)
        self._image_pixmap = None          # 原图 QPixmap(窗口缩放时重新适配)

        self._build_ui()

    # ------------------------------------------------------------------
    # 界面搭建(A)
    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        central.setObjectName("root")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(22, 16, 22, 10)
        root.setSpacing(14)

        # ---- 顶部标题区 ----
        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("Board2TeX")
        title.setObjectName("appTitle")
        badge = QLabel("MVP")
        badge.setObjectName("badge")
        subtitle = QLabel("板书照片 → 可编译 LaTeX")
        subtitle.setObjectName("appSubtitle")

        header.addWidget(title)
        header.addWidget(badge)
        header.addSpacing(10)
        header.addWidget(subtitle)
        header.addStretch()
        root.addLayout(header)

        # ---- 按钮行 ----
        # 每种按钮的"角色": primary=主操作, accent=次强调, 空=普通
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        for text, slot, role, tip in [
            ("导入图片", self.on_import, "", "选择一张板书照片(png / jpg / bmp)"),
            ("运行识别", self.on_run, "primary", "预处理 → 切行 → 识别 → 合成;首次会加载模型"),
            ("预览", self.on_preview, "", "查看当前编辑后的正文"),
            ("导出 .tex", self.on_export_tex, "", "导出 LaTeX 源文件"),
            ("导出 PDF", self.on_export_pdf, "accent", "导出 .tex 并用 xelatex 编译成 PDF"),
            ("存入错题本", self.on_save_problem, "", "把当前整篇 LaTeX 存入 SQLite 错题本"),
            ("错题本", self.on_show_vault, "", "查看 / 删除已保存的错题"),
        ]:
            btn = QPushButton(text)
            if role:
                btn.setProperty("class", role)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

        # ---- 左卡片: 图像显示区 ----
        left_card = QFrame()
        left_card.setObjectName("card")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(14, 12, 14, 14)
        left_layout.setSpacing(8)

        left_title = QLabel("板书预览")
        left_title.setObjectName("cardTitle")
        self.left_title = left_title
        left_layout.addWidget(left_title)

        self.image_label = QLabel("先点「导入图片」,再「运行识别」")
        self.image_label.setObjectName("imageCanvas")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(520, 400)
        left_layout.addWidget(self.image_label, 1)

        # ---- 右卡片: 编辑区 ----
        right_card = QFrame()
        right_card.setObjectName("card")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(14, 12, 14, 14)
        right_layout.setSpacing(8)

        right_title = QLabel("识别结果 · 可直接编辑")
        right_title.setObjectName("cardTitle")
        self.right_title = right_title
        right_layout.addWidget(right_title)

        self.editor_area = QScrollArea()
        self.editor_area.setObjectName("editorScroll")
        self.editor_area.setWidgetResizable(True)
        self.editor_area.setFrameShape(QFrame.NoFrame)

        editor_host = QWidget()
        editor_host.setObjectName("editorHost")
        self.editor_layout = QVBoxLayout(editor_host)
        self.editor_layout.setContentsMargins(0, 0, 6, 0)
        self.editor_layout.setSpacing(8)
        self.editor_layout.setAlignment(Qt.AlignTop)

        self._editor_hint = QLabel(
            "识别结果会显示在这里,一行一个输入框。\n改完直接「预览」或「导出」。"
        )
        self._editor_hint.setObjectName("legend")
        self._editor_hint.setWordWrap(True)
        self.editor_layout.addWidget(self._editor_hint)
        self.editor_area.setWidget(editor_host)
        right_layout.addWidget(self.editor_area, 1)

        # 第三栏: 实时编译预览(可拖动分隔条调整宽度)
        self.preview_pane = PreviewPane(self, on_open=self.on_preview)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(10)
        splitter.addWidget(left_card)
        splitter.addWidget(right_card)
        splitter.addWidget(self.preview_pane)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 4)
        splitter.setSizes([280, 460, 620])
        root.addWidget(splitter, 1)

        self._add_card_shadow(left_card)
        self._add_card_shadow(right_card)

        self.statusBar().showMessage("就绪")

        # 状态栏右侧常驻: 本机能不能编 PDF,一眼就能看到
        tex_ok = has_xelatex()
        tex_status = QLabel("xelatex 已就绪" if tex_ok else "未检测到 xelatex(只能导出 .tex)")
        tex_status.setObjectName("statusBadge")
        self.statusBar().addPermanentWidget(tex_status)

        # 主题必须在控件建好之后、显示之前应用(属性选择器依赖 setProperty)
        from gui.style import apply_theme

        app = QApplication.instance()
        if app is not None:
            apply_theme(app)

    @staticmethod
    def _add_card_shadow(card: QFrame) -> None:
        """给卡片加一层很淡的投影,让白色卡片从背景里"浮"起来。"""
        from PyQt5.QtGui import QColor
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect

        effect = QGraphicsDropShadowEffect(card)
        effect.setBlurRadius(26)
        effect.setOffset(0, 5)
        effect.setColor(QColor(15, 23, 42, 26))
        card.setGraphicsEffect(effect)

    # ------------------------------------------------------------------
    # 图像上屏(A)
    # ------------------------------------------------------------------
    def _show_image(self, img, note: str = ""):
        self._image_pixmap = ndarray_to_qpixmap(img)
        self._fit_image()
        # 有图之后去掉虚线占位框(样式见 gui/style.py 的 [filled="true"])
        if self.image_label.property("filled") != "true":
            self.image_label.setProperty("filled", "true")
            self.image_label.style().unpolish(self.image_label)
            self.image_label.style().polish(self.image_label)
        if note:
            self.statusBar().showMessage(note)

    def _fit_image(self):
        """按当前 label 尺寸等比缩放原图(窗口/分隔条变化时也保持完整可见)。"""
        if self._image_pixmap is None:
            return
        scaled = self._image_pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_image()

    # ------------------------------------------------------------------
    # 右侧编辑区(D 的接入点)
    # ------------------------------------------------------------------
    def show_blocks(self):
        """把 doc["blocks"] 渲染成"一行一个输入框",改哪个就写回哪个 Block。"""
        self._clear_editor()

        if not self.doc:
            hint = QLabel(
                "识别结果会显示在这里,一行一个输入框。\n改完直接「预览」或「导出」。"
            )
            hint.setObjectName("legend")
            hint.setWordWrap(True)
            self.editor_layout.addWidget(hint)
            return

        for b in self.doc["blocks"]:
            order = b["order"]
            conf = float(b["confidence"])

            # 红色 = "建议人工核对",但两种行的判据不同:
            #   文字行: 看置信度(< TEXT_CONF_THRESHOLD);
            #   公式行: pix2tex 不给真实置信度(固定 0.8),拿 0.8 当低置信度
            #           会让每条公式都变红,所以改看"花括号是否配对 / 是否为空"。
            if b["type"] == "formula":
                from recog.postprocess import braces_balanced

                risky = (not b["latex"].strip()) or (not braces_balanced(b["latex"]))
                tip = "公式: 空结果或花括号不配对,建议核对"
            else:
                risky = 0.0 < conf < TEXT_CONF_THRESHOLD
                tip = f"文字: 置信度 {conf:.2f} < {TEXT_CONF_THRESHOLD},建议核对"

            row = QFrame()
            row.setObjectName("blockRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 9, 10, 9)
            row_layout.setSpacing(8)

            order_label = QLabel(f"#{order}")
            order_label.setObjectName("orderLabel")
            order_label.setFixedWidth(30)

            chip = QLabel("FORMULA" if b["type"] == "formula" else "TEXT")
            chip.setObjectName(
                "chipFormula" if b["type"] == "formula" else "chipText"
            )
            chip.setAlignment(Qt.AlignCenter)
            chip.setFixedWidth(66)

            conf_label = QLabel(f"{conf:.2f}")
            conf_label.setObjectName("confLabel")
            conf_label.setProperty("risky", "true" if risky else "false")
            conf_label.setFixedWidth(40)
            conf_label.setToolTip(tip if risky else "置信度")

            edit = QLineEdit(b["latex"])
            edit.setObjectName("blockEdit")
            edit.setPlaceholderText("(空)")
            edit.setCursorPosition(0)          # 默认滚到末尾会看不到行首,拉回开头
            edit.setProperty("risky", "true" if risky else "false")
            edit.setToolTip(tip if risky else f"完整内容:\n{b['latex']}")
            edit.textChanged.connect(
                lambda text, o=order: self._on_block_edited(o, text)
            )

            row_layout.addWidget(order_label)
            row_layout.addWidget(chip)
            row_layout.addWidget(conf_label)
            row_layout.addWidget(edit, 1)
            self.editor_layout.addWidget(row)
            self.block_edits[order] = edit

        legend = QLabel("红框 = 建议人工核对:文字看置信度(<0.85),公式看括号是否配对")
        legend.setObjectName("legend")
        legend.setWordWrap(True)
        self.editor_layout.addWidget(legend)

    def _clear_editor(self):
        """清空右侧所有编辑行(换图/重新识别/无结果时用)。"""
        while self.editor_layout.count():
            item = self.editor_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.block_edits.clear()

    def _on_block_edited(self, order: int, text: str):
        """编辑框一改: 写回 block,重建 tex,并触发实时预览(防抖)。"""
        if not self.doc:
            return
        for b in self.doc["blocks"]:
            if b["order"] == order:
                b["latex"] = text
                break
        self._rebuild_tex()
        self.preview_pane.schedule(self.doc["tex_source"])

    def _rebuild_tex(self):
        """用当前(可能已被人工修改的)blocks 重建 tex_source。"""
        if not self.doc:
            return
        from compose.builder import build_body
        from compose.template import TEMPLATE

        body = build_body(self.doc["blocks"])
        self.doc["tex_source"] = TEMPLATE.replace("% BODY", body)

    def _get_db(self):
        """懒加载错题本连接(第一次用时才建库)。"""
        if self._db is None:
            from vault.db import init_db

            os.makedirs("vault", exist_ok=True)
            self._db = init_db(os.path.join("vault", "board2tex.db"))
        return self._db

    def closeEvent(self, event):
        if self._db is not None:
            self._db.close()
            self._db = None
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # 按钮槽函数
    # ------------------------------------------------------------------
    def on_import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择板书照片", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not path:
            return
        self.image_path = path
        self.left_title.setText(f"板书预览 · {os.path.basename(path)}")

        # 换图后旧结果全部作废,避免"图是新的、编辑区还是上一张"的错位
        self.pre = None
        self.regions = []
        self.doc = None
        self.show_blocks()
        self.preview_pane.clear()
        self.right_title.setText("识别结果 · 可直接编辑")

        self._show_image(load_image(path), f"已导入: {os.path.basename(path)}")

    def on_run(self):
        if not self.image_path:
            QMessageBox.information(self, "提示", "请先导入图片")
            return
        self.setEnabled(False)  # 同步版:识别期间界面禁点,CPU 推理需几秒~几十秒
        QApplication.processEvents()
        try:
            self.pre, self.regions, self.doc = pipeline(self.image_path)
        finally:
            self.setEnabled(True)
        self._show_image(
            self.pre["bgr"],
            f"识别完成: {len(self.regions)} 个区域, {len(self.doc['blocks'])} 个块",
        )
        self.show_blocks()
        n_formula = sum(1 for b in self.doc["blocks"] if b["type"] == "formula")
        self.right_title.setText(
            f"识别结果 · {len(self.doc['blocks'])} 行(公式 {n_formula})"
        )
        self.statusBar().showMessage(
            f"识别完成: {len(self.doc['blocks'])} 块,右侧可直接修改"
        )
        self.preview_pane.compile_now(self.doc["tex_source"])

    def on_preview(self):
        if not self.doc:
            QMessageBox.information(self, "提示", "请先运行识别")
            return
        self._rebuild_tex()

        # 预览的是"编译后的样子": xelatex 编译 -> PDF 逐页转图 -> 弹窗显示
        from gui.preview import show_compiled_preview

        show_compiled_preview(self, self.doc)

    def on_export_tex(self):
        if not self.doc:
            QMessageBox.information(self, "提示", "请先运行识别")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 .tex", "result.tex", "LaTeX (*.tex)"
        )
        if not path:
            return
        self._rebuild_tex()          # 先写回人工修改,再导出
        from gui.exporter import export_tex
        export_tex(self.doc, path)
        self.statusBar().showMessage(f"已导出: {path}")

    def on_export_pdf(self):
        if not self.doc:
            QMessageBox.information(self, "提示", "请先运行识别")
            return
        if not has_xelatex():
            QMessageBox.warning(
                self, "无法导出 PDF",
                "本机未安装 xelatex。\n请安装 TeX Live 或 MiKTeX,"
                "或先只导出 .tex 文件。"
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 PDF(会同时保存 .tex)", "result.tex", "LaTeX (*.tex)"
        )
        if not path:
            return
        self._rebuild_tex()          # 先写回人工修改,再导出
        from gui.exporter import export_tex
        export_tex(self.doc, path)
        out_dir = os.path.dirname(os.path.abspath(path)) or "."
        try:
            pdf = compile_pdf(path, out_dir)
        except RuntimeError as e:
            QMessageBox.critical(self, "编译失败", str(e))
            return
        self.statusBar().showMessage(f"已导出: {pdf}")

    # ------------------------------------------------------------------
    # 错题本(D)
    # ------------------------------------------------------------------
    def on_save_problem(self):
        if not self.doc:
            QMessageBox.information(self, "提示", "请先运行识别")
            return
        self._rebuild_tex()

        course, ok = QInputDialog.getText(self, "存入错题本", "课程名(如 Calculus):")
        if not ok or not course.strip():
            return
        tags_text, ok = QInputDialog.getText(
            self, "存入错题本", "标签(逗号分隔,可留空):"
        )
        if not ok:
            return
        tags = [t.strip() for t in tags_text.replace("，", ",").split(",") if t.strip()]

        try:
            from vault.db import add_problem

            add_problem(self._get_db(), course.strip(), tags,
                        self.doc["tex_source"], self.image_path or "")
        except Exception as exc:                    # 数据库异常不能弄崩界面
            QMessageBox.critical(self, "保存失败", str(exc))
            return
        self.statusBar().showMessage(f"已存入错题本: {course.strip()}")

    def on_show_vault(self):
        try:
            from vault.db import delete_problem, list_problems

            rows = list_problems(self._get_db())
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", str(exc))
            return

        if not rows:
            QMessageBox.information(self, "错题本", "还没有记录,先识别一道题再「存入错题本」")
            return

        text = "\n".join(
            f"#{r[0]}  [{r[1]}]  {r[2] or '(无标签)'}  {r[5]}" for r in rows
        )
        dialog = QDialog(self)
        dialog.setWindowTitle(f"错题本({len(rows)} 条)")
        dialog.resize(720, 480)
        layout = QVBoxLayout(dialog)
        view = QTextEdit()
        view.setReadOnly(True)
        view.setPlainText(text)
        layout.addWidget(view)
        dialog.exec_()

        pid, ok = QInputDialog.getInt(
            self, "删除记录", "要删除的编号(点 Cancel 跳过):", 0, 0, 10 ** 9
        )
        if ok and pid > 0:
            try:
                delete_problem(self._get_db(), pid)
            except Exception as exc:
                QMessageBox.critical(self, "删除失败", str(exc))
                return
            self.statusBar().showMessage(f"已删除记录 #{pid}")


if __name__ == "__main__":
    # 高 DPI 缩放: 笔记本 125%/150% 缩放时字体和控件不再模糊
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication([])
    app.setApplicationName("Board2TeX")
    window = MainWindow()
    window.show()
    app.exec_()
