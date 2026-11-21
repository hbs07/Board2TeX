# -*- coding: utf-8 -*-
"""gui/preview_pane.py —— 主界面里的实时编译预览(维护: A 胡秉善)

为什么单独一个文件:
    "编辑一下就重编一次 PDF"既慢又容易卡界面,所以这里做三件事:
      1. 防抖: 停止输入 0.9s 后才编译(不是每敲一个键就编);
      2. 后台线程: 编译在 QThreadPool 里跑,主界面不冻结;
      3. 只显示最新一次: 新的编辑会作废旧结果,避免"旧图闪一下"。

依赖: xelatex + pdftoppm(与「预览」按钮相同);缺了就只显示提示,不影响主流程。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

import glob
import os
import shutil

# 必须先于 PyQt5 导入(原因见 gui/torch_preload.py)
from gui import torch_preload  # noqa: F401

from PyQt5.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from gui.exporter import has_xelatex
from gui.preview import export_preview_pdf, render_pdf_pages

LIVE_DIR = os.path.join("data", "preview")
DEBOUNCE_MS = 900
MIN_PANE_WIDTH = 260


class _Signals(QObject):
    done = pyqtSignal(int, list)      # 代号, 页面 PNG 列表
    failed = pyqtSignal(int, str)     # 代号, 错误信息


class _CompileTask(QRunnable):
    """后台任务: tex -> PDF -> 逐页 PNG。"""

    def __init__(self, generation: int, tex_source: str, out_dir: str,
                 signals: _Signals):
        super().__init__()
        self.generation = generation
        self.doc = {"tex_source": tex_source}
        self.out_dir = out_dir
        self.signals = signals

    def run(self) -> None:                      # 在子线程执行
        try:
            pdf_path = export_preview_pdf(self.doc, self.out_dir)
            pages = render_pdf_pages(pdf_path, self.out_dir)
        except Exception as exc:                # 编译失败不该让程序崩
            self.signals.failed.emit(self.generation, str(exc))
            return
        self.signals.done.emit(self.generation, pages)


class PreviewPane(QFrame):
    """主界面右侧/底部的"实时预览"卡片。"""

    def __init__(self, parent=None, on_open=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._on_open = on_open
        self._tex: str | None = None
        self._generation = 0
        self._busy = False
        self._pending = False
        self._pixmaps: list[QPixmap] = []

        self._signals = _Signals()
        self._signals.done.connect(self._on_done)
        self._signals.failed.connect(self._on_failed)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(DEBOUNCE_MS)
        self._timer.timeout.connect(self._compile_latest)

        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(8)

        head = QHBoxLayout()
        title = QLabel("编译预览")
        title.setObjectName("cardTitle")
        self._status = QLabel("等待识别")
        self._status.setObjectName("previewStatus")
        self._zoom_btn = QPushButton("放大")
        self._zoom_btn.setCursor(Qt.PointingHandCursor)
        self._zoom_btn.setToolTip("在新窗口查看完整预览")
        self._zoom_btn.clicked.connect(self._open_large)
        self._zoom_btn.setEnabled(False)

        head.addWidget(title)
        head.addSpacing(8)
        head.addWidget(self._status)
        head.addStretch()
        head.addWidget(self._zoom_btn)
        layout.addLayout(head)

        self._scroll = QScrollArea()
        self._scroll.setObjectName("previewScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setMinimumWidth(MIN_PANE_WIDTH)

        self._host = QWidget()
        self._host.setObjectName("previewHost")
        self._host_layout = QVBoxLayout(self._host)
        self._host_layout.setContentsMargins(0, 0, 0, 0)
        self._host_layout.setSpacing(10)
        self._host_layout.addStretch()
        self._scroll.setWidget(self._host)
        layout.addWidget(self._scroll, 1)

    # -------------------------------------------------------------- 对外 API
    def clear(self):
        """清空预览(还没识别 / 换了图片时)。"""
        self._timer.stop()
        self._tex = None
        self._pixmaps = []
        self._clear_pages()
        self._status.setText("等待识别")
        self._zoom_btn.setEnabled(False)

    def schedule(self, tex_source: str):
        """编辑后调用: 防抖,停止输入后自动重编。"""
        self._tex = tex_source
        if not has_xelatex():
            self._status.setText("未安装 xelatex")
            return
        self._status.setText("编辑中…")
        self._timer.start()

    def compile_now(self, tex_source: str):
        """立刻编译(识别完成后调用,不等防抖)。"""
        self._tex = tex_source
        self._timer.stop()
        self._compile_latest()

    # -------------------------------------------------------------- 内部逻辑
    def _compile_latest(self):
        if not self._tex:
            return
        if self._busy:                 # 正在编译: 记一笔, 完成后再编最新的
            self._pending = True
            return
        if not has_xelatex():
            self._status.setText("未安装 xelatex,无法预览")
            return

        self._busy = True
        self._generation += 1
        self._status.setText("编译中…")
        out_dir = os.path.join(LIVE_DIR, f"live_{self._generation}")
        self._clean_old_dirs(out_dir)

        QThreadPool.globalInstance().start(
            _CompileTask(self._generation, self._tex, out_dir, self._signals)
        )

    def _clean_old_dirs(self, keep: str) -> None:
        os.makedirs(keep, exist_ok=True)
        for path in glob.glob(os.path.join(LIVE_DIR, "live_*")):
            if os.path.abspath(path) == os.path.abspath(keep):
                continue
            shutil.rmtree(path, ignore_errors=True)

    def _on_done(self, generation: int, pages: list):
        self._busy = False
        if generation != self._generation:
            return
        if self._pending:              # 编译期间又改过: 直接重编,不闪旧图
            self._pending = False
            self._compile_latest()
            return

        self._pixmaps = [QPixmap(p) for p in pages]
        self._render_pages()
        self._status.setText(f"第 1 页 / 共 {len(pages)} 页")
        self._zoom_btn.setEnabled(True)

    def _on_failed(self, generation: int, message: str):
        self._busy = False
        if generation != self._generation:
            return
        if self._pending:
            self._pending = False
            self._compile_latest()
            return
        self._clear_pages()
        self._status.setText("编译失败")
        error = QLabel(message.splitlines()[0][:120])
        error.setObjectName("previewError")
        error.setWordWrap(True)
        self._host_layout.insertWidget(0, error)
        self._zoom_btn.setEnabled(False)

    def _clear_pages(self):
        while self._host_layout.count():
            item = self._host_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._host_layout.addStretch()

    def _render_pages(self):
        self._clear_pages()
        width = max(self._scroll.viewport().width() - 16, MIN_PANE_WIDTH)
        for pixmap in self._pixmaps:
            label = QLabel()
            label.setObjectName("livePage")
            label.setAlignment(Qt.AlignCenter)
            label.setPixmap(pixmap.scaledToWidth(width, Qt.SmoothTransformation))
            self._host_layout.insertWidget(self._host_layout.count() - 1, label)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pixmaps:
            QTimer.singleShot(50, self._render_pages)

    def _open_large(self):
        if self._on_open is not None and self._pixmaps:
            self._on_open()
