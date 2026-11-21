# -*- coding: utf-8 -*-
"""gui/image_view.py —— 板书原图查看器(维护: A 胡秉善)

主界面不再常驻原图,改成一个弹窗:需要对照时点「查看原图」。
支持多张(多选导入时)左右切换,可缩放/适应窗口;按屏幕 DPR 渲染,不发糊。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

# 必须先于 PyQt5 导入(原因见 gui/torch_preload.py)
from gui import torch_preload  # noqa: F401

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

MIN_SCALE = 0.1
MAX_SCALE = 4.0


class ImageDialog(QDialog):
    """可缩放的原图查看窗口(支持多张切换)。"""

    def __init__(self, parent, images, titles=None, start: int = 0):
        super().__init__(parent)
        if isinstance(images, QPixmap):        # 兼容只传一张的旧用法
            images = [images]
        self._images: list[QPixmap] = list(images)
        self._titles: list[str] = list(titles) if titles else [
            f"第 {i + 1} 张" for i in range(len(self._images))
        ]
        self._index = max(0, min(start, len(self._images) - 1))
        self._dpr = float(self.devicePixelRatioF() or 1.0)
        self._scale = 1.0
        self._pixmap = self._images[self._index]

        self.resize(980, 760)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(8)

        head = QHBoxLayout()
        self._info = QLabel()
        self._info.setObjectName("previewInfo")

        self._prev_btn = QPushButton("‹")
        self._next_btn = QPushButton("›")
        for btn, tip in ((self._prev_btn, "上一张"), (self._next_btn, "下一张")):
            btn.setObjectName("zoomBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(tip)
            btn.setFixedWidth(30)
        self._prev_btn.clicked.connect(lambda: self._step(-1))
        self._next_btn.clicked.connect(lambda: self._step(1))

        self._zoom_label = QLabel("100%")
        self._zoom_label.setObjectName("zoomLabel")

        zoom_out = QPushButton("−")
        zoom_out.setObjectName("zoomBtn")
        zoom_out.setCursor(Qt.PointingHandCursor)
        zoom_out.setToolTip("缩小")
        zoom_out.clicked.connect(lambda: self._set_scale(self._scale / 1.25))

        zoom_in = QPushButton("+")
        zoom_in.setObjectName("zoomBtn")
        zoom_in.setCursor(Qt.PointingHandCursor)
        zoom_in.setToolTip("放大")
        zoom_in.clicked.connect(lambda: self._set_scale(self._scale * 1.25))

        fit_btn = QPushButton("适应窗口")
        fit_btn.setCursor(Qt.PointingHandCursor)
        fit_btn.setToolTip("按窗口大小完整显示")
        fit_btn.clicked.connect(self._fit_to_window)

        head.addWidget(self._info)
        if len(self._images) > 1:
            head.addSpacing(8)
            head.addWidget(self._prev_btn)
            head.addWidget(self._next_btn)
        head.addStretch()
        head.addWidget(zoom_out)
        head.addWidget(self._zoom_label)
        head.addWidget(zoom_in)
        head.addSpacing(6)
        head.addWidget(fit_btn)
        layout.addLayout(head)

        self._scroll = QScrollArea()
        self._scroll.setObjectName("previewScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setAlignment(Qt.AlignCenter)

        self._host = QWidget()
        self._host.setObjectName("previewHost")
        host_layout = QVBoxLayout(self._host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.setAlignment(Qt.AlignCenter)

        self._page = QLabel()
        self._page.setObjectName("imagePage")
        self._page.setAlignment(Qt.AlignCenter)
        host_layout.addWidget(self._page)

        self._scroll.setWidget(self._host)
        layout.addWidget(self._scroll, 1)

        self._show_index(self._index)

    # -------------------------------------------------------------- 内部
    def _show_index(self, index: int) -> None:
        self._index = max(0, min(index, len(self._images) - 1))
        self._pixmap = self._images[self._index]
        title = self._titles[self._index] if self._index < len(self._titles) else ""
        self.setWindowTitle(f"板书原图 · {title}")
        self._info.setText(
            f"{self._index + 1} / {len(self._images)} · "
            f"{self._pixmap.width()} × {self._pixmap.height()} px"
        )
        if len(self._images) > 1:
            self._prev_btn.setEnabled(self._index > 0)
            self._next_btn.setEnabled(self._index < len(self._images) - 1)

        # 换图时重新按"适应宽度"的比例显示
        self._scale = min(1.0, (900 * self._dpr) / max(self._pixmap.width(), 1))
        self._render()

    def _step(self, delta: int) -> None:
        self._show_index(self._index + delta)

    def _set_scale(self, value: float) -> None:
        self._scale = max(MIN_SCALE, min(MAX_SCALE, value))
        self._render()

    def _fit_to_window(self) -> None:
        viewport = self._scroll.viewport()
        if self._pixmap.isNull():
            return
        scale = min(
            (viewport.width() * self._dpr) / self._pixmap.width(),
            (viewport.height() * self._dpr) / self._pixmap.height(),
            self._dpr,                 # 最多 1 图像像素 : 1 屏幕像素,不放大
        )
        self._set_scale(scale)

    def _render(self) -> None:
        pixel_w = max(int(self._pixmap.width() * self._scale), 1)
        pixel_h = max(int(self._pixmap.height() * self._scale), 1)
        pixmap = self._pixmap.scaled(
            pixel_w, pixel_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        pixmap.setDevicePixelRatio(self._dpr)
        self._page.setPixmap(pixmap)
        self._zoom_label.setText(f"{self._scale * 100:.0f}%")


def show_image_dialog(parent, images, titles=None) -> None:
    """images: 单个 QPixmap 或 QPixmap 列表。"""
    dialog = ImageDialog(parent, images, titles)
    dialog.exec_()
