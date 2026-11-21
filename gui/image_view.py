# -*- coding: utf-8 -*-
"""gui/image_view.py —— 板书原图查看器(维护: A 胡秉善)

主界面不再常驻原图,改成一个弹窗:需要对照时点「查看原图」,
默认适应窗口大小,可放大到 400% 看细节。

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
    """可缩放的原图查看窗口。"""

    def __init__(self, parent, pixmap: QPixmap, title: str = "板书原图"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(980, 760)
        self._pixmap = pixmap
        self._scale = 1.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(8)

        head = QHBoxLayout()
        info = QLabel(f"{pixmap.width()} × {pixmap.height()} px")
        info.setObjectName("previewInfo")
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
        fit_btn.setToolTip("按窗口大小完整显示(不放大)")
        fit_btn.clicked.connect(self._fit_to_window)

        head.addWidget(info)
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

        self._scale = min(1.0, 900 / max(pixmap.width(), 1))
        self._render()

    def _set_scale(self, value: float) -> None:
        self._scale = max(MIN_SCALE, min(MAX_SCALE, value))
        self._render()

    def _fit_to_window(self) -> None:
        viewport = self._scroll.viewport()
        if self._pixmap.isNull():
            return
        scale = min(
            viewport.width() / self._pixmap.width(),
            viewport.height() / self._pixmap.height(),
            1.0,                       # 不放大,避免糊
        )
        self._set_scale(scale)

    def _render(self) -> None:
        pixmap = self._pixmap.scaled(
            max(int(self._pixmap.width() * self._scale), 1),
            max(int(self._pixmap.height() * self._scale), 1),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self._page.setPixmap(pixmap)
        self._zoom_label.setText(f"{self._scale * 100:.0f}%")


def show_image_dialog(parent, pixmap: QPixmap, title: str = "板书原图") -> None:
    dialog = ImageDialog(parent, pixmap, title)
    dialog.exec_()
