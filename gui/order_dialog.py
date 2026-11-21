# -*- coding: utf-8 -*-
"""gui/order_dialog.py —— 调整多张板书的合并顺序(维护: A 胡秉善)

打开后列出已导入的图片(带缩略图):
    - 直接拖动列表项调整顺序,或用「上移 / 下移」;
    - 「按文件名」恢复导入时的默认顺序;
    - 确定后主窗口按新顺序重排页面,不需要重新识别。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

# 必须先于 PyQt5 导入(原因见 gui/torch_preload.py)
from gui import torch_preload  # noqa: F401

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView, QDialog, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QVBoxLayout,
)

THUMB_W = 96
THUMB_H = 54


class OrderDialog(QDialog):
    def __init__(self, parent, titles: list[str], pixmaps=None):
        super().__init__(parent)
        self.setWindowTitle("调整板书顺序")
        self.resize(620, 480)
        self._titles = list(titles)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        hint = QLabel("拖动列表项,或用「上移 / 下移」调整;合并与导出按此顺序。")
        hint.setObjectName("previewInfo")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._list = QListWidget()
        self._list.setDragDropMode(QAbstractItemView.InternalMove)
        self._list.setDefaultDropAction(Qt.MoveAction)
        self._list.setIconSize(QSize(THUMB_W, THUMB_H))
        self._list.setSpacing(2)

        for index, title in enumerate(self._titles):
            item = QListWidgetItem(f"{index + 1}. {title}")
            item.setData(Qt.UserRole, index)
            item.setSizeHint(QSize(0, 72))
            if pixmaps and index < len(pixmaps):
                icon = pixmaps[index].scaled(
                    THUMB_W, THUMB_H, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                item.setIcon(QIcon(icon))
            self._list.addItem(item)

        self._list.model().rowsMoved.connect(self._renumber)
        layout.addWidget(self._list, 1)

        row = QHBoxLayout()
        up = QPushButton("上移")
        down = QPushButton("下移")
        reset = QPushButton("按文件名")
        up.clicked.connect(lambda: self._move(-1))
        down.clicked.connect(lambda: self._move(1))
        reset.clicked.connect(self._reset)
        for btn in (up, down, reset):
            btn.setCursor(Qt.PointingHandCursor)

        ok = QPushButton("确定")
        ok.setProperty("class", "primary")
        ok.setCursor(Qt.PointingHandCursor)
        cancel = QPushButton("取消")
        cancel.setCursor(Qt.PointingHandCursor)
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)

        row.addWidget(up)
        row.addWidget(down)
        row.addWidget(reset)
        row.addStretch()
        row.addWidget(ok)
        row.addWidget(cancel)
        layout.addLayout(row)

    # ------------------------------------------------------------------
    def _renumber(self, *args) -> None:
        for row in range(self._list.count()):
            item = self._list.item(row)
            original = item.data(Qt.UserRole)
            item.setText(f"{row + 1}. {self._titles[original]}")

    def _move(self, delta: int) -> None:
        row = self._list.currentRow()
        target = row + delta
        if row < 0 or target < 0 or target >= self._list.count():
            return
        item = self._list.takeItem(row)
        self._list.insertItem(target, item)
        self._list.setCurrentRow(target)
        self._renumber()

    def _reset(self) -> None:
        """恢复导入时的顺序(按文件名自然排序的结果)。"""
        items = [self._list.takeItem(0) for _ in range(self._list.count())]
        items.sort(key=lambda it: it.data(Qt.UserRole))
        for item in items:
            self._list.addItem(item)
        self._renumber()

    def order(self) -> list[int]:
        """返回按界面顺序排列的"原索引"列表,如 [2, 0, 1]。"""
        return [self._list.item(row).data(Qt.UserRole)
                for row in range(self._list.count())]
