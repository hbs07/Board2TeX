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
    - 5 个按钮已接线:导入图片 / 运行识别 / 预览 / 导出 .tex / 导出 PDF;
    - _show_image(): ndarray 上屏(含 .copy() 防花屏,别删)。

D 的任务(按分工文档 §4,在 TODO(D) 处填):
    1. show_blocks(): 把 self.doc["blocks"] 渲染成可编辑行(gui/widgets.py);
    2. on_edit(): 编辑写回 self.doc["blocks"];
    3. on_preview(): 简单文字预览(文档 §4.2);
    4. "存入错题本"按钮 + 错题本列表页(vault/db.py 就绪后加)。
"""

from __future__ import annotations

import os

import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from gui.exporter import compile_pdf, has_xelatex
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
        self.resize(1100, 680)

        # ---- 识别结果状态(冻结接口的数据在这里流转) ----
        self.image_path: str | None = None
        self.pre: dict | None = None       # {"binary", "bgr"}
        self.regions: list[dict] = []      # layout 输出
        self.doc: dict | None = None       # {"blocks", "tex_source"}

        self._build_ui()

    # ------------------------------------------------------------------
    # 界面搭建(A)
    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # 顶部按钮行
        btn_row = QHBoxLayout()
        for text, slot in [
            ("导入图片", self.on_import),
            ("运行识别", self.on_run),
            ("预览", self.on_preview),
            ("导出 .tex", self.on_export_tex),
            ("导出 PDF", self.on_export_pdf),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)
        root.addLayout(btn_row)

        # 左:图像显示区
        self.image_label = QLabel("先点「导入图片」,再「运行识别」")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(560, 420)
        self.image_label.setStyleSheet(
            "border: 1px solid #cccccc; background: #fafafa;"
        )
        # 右:编辑区(D 在 self.editor_layout 里加可编辑行)
        self.editor_area = QScrollArea()
        self.editor_area.setWidgetResizable(True)
        editor_host = QWidget()
        self.editor_layout = QVBoxLayout(editor_host)
        self.editor_layout.setAlignment(Qt.AlignTop)
        self.editor_layout.addWidget(
            QLabel("(编辑行将显示在这里 —— D 填 show_blocks)")
        )
        self.editor_area.setWidget(editor_host)

        content_row = QHBoxLayout()
        content_row.addWidget(self.image_label, 3)
        content_row.addWidget(self.editor_area, 2)
        root.addLayout(content_row)

        self.statusBar().showMessage("就绪")

    # ------------------------------------------------------------------
    # 图像上屏(A)
    # ------------------------------------------------------------------
    def _show_image(self, img, note: str = ""):
        pixmap = ndarray_to_qpixmap(img)
        scaled = pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)
        if note:
            self.statusBar().showMessage(note)

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
        # TODO(D): 调 self.show_blocks() 把 self.doc["blocks"] 渲染成可编辑行
        QMessageBox.information(
            self, "识别完成",
            f"{len(self.regions)} 个区域 / {len(self.doc['blocks'])} 个块\n"
            "(编辑行显示: D 填 show_blocks)",
        )

    def on_preview(self):
        # TODO(D): 按分工文档 §4.2 实现预览(matplotlib 画 tex 文本即可)
        QMessageBox.information(self, "提示", "预览功能: D 待实现(文档 §4.2)")

    def on_export_tex(self):
        if not self.doc:
            QMessageBox.information(self, "提示", "请先运行识别")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 .tex", "result.tex", "LaTeX (*.tex)"
        )
        if not path:
            return
        # TODO(D): 编辑功能就绪后,这里先写回编辑再导出(见 exporter.export_tex)
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
        from gui.exporter import export_tex
        export_tex(self.doc, path)
        out_dir = os.path.dirname(os.path.abspath(path)) or "."
        try:
            pdf = compile_pdf(path, out_dir)
        except RuntimeError as e:
            QMessageBox.critical(self, "编译失败", str(e))
            return
        self.statusBar().showMessage(f"已导出: {pdf}")


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
