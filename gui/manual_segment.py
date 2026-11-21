# -*- coding: utf-8 -*-
"""gui/manual_segment.py —— 手动框选板书区域(维护: A 胡秉善)

为什么需要它:
    自动切行依赖"行与行之间有空白",手写/双栏/擦痕多的照片往往切不出来。
    这个对话框让用户在图片上直接拖框,按画框顺序作为阅读顺序,再逐框识别。

操作:
    1. 在图上按住左键拖出矩形(一行一个框);
    2. 框可以拖动位置;选中后按「删除」或 Delete 键移除;
    3. 「上移 / 下移」调整顺序(默认按画框先后);
    4. 「识别并替换」-> 每个框裁剪出来单独识别,替换该图片原来的结果。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

# 必须先于 PyQt5 导入(原因见 gui/torch_preload.py)
from gui import torch_preload  # noqa: F401

from PyQt5.QtCore import QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import (
    QAbstractItemView, QDialog, QGraphicsItem, QGraphicsScene, QGraphicsView,
    QHBoxLayout, QLabel, QListWidget, QMessageBox, QPushButton, QVBoxLayout,
)


class _Canvas(QGraphicsView):
    """支持"在空白处拖框"的画布;已有的框可以选中并拖动。"""

    box_added = pyqtSignal(QRectF)

    def __init__(self, scene: QGraphicsScene, parent=None):
        super().__init__(scene, parent)
        self._pixmap_item = None
        self._origin = None
        self._rubber = None
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setBackgroundBrush(QColor("#F8FAFC"))
        self.setDragMode(QGraphicsView.NoDrag)

    def set_pixmap_item(self, item) -> None:
        self._pixmap_item = item

    def fit_all(self) -> None:
        if self._pixmap_item is not None:
            self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)

    def mousePressEvent(self, event):
        if (event.button() == Qt.LeftButton
                and self._pixmap_item is not None
                and self.itemAt(event.pos()) is self._pixmap_item):
            self._origin = self.mapToScene(event.pos())
            pen = QPen(QColor("#94A3B8"), 1, Qt.DashLine)
            pen.setCosmetic(True)
            self._rubber = self.scene().addRect(
                QRectF(self._origin, self._origin), pen
            )
            self._rubber.setZValue(1000)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._rubber is not None and self._origin is not None:
            rect = QRectF(self._origin, self.mapToScene(event.pos())).normalized()
            self._rubber.setRect(rect)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._rubber is not None:
            rect = self._rubber.rect().normalized()
            self.scene().removeItem(self._rubber)
            self._rubber = None
            self._origin = None
            if rect.width() >= 8 and rect.height() >= 8:
                self.box_added.emit(rect)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """Ctrl + 滚轮缩放,方便框小字;不按 Ctrl 时正常滚动。"""
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.25 if event.angleDelta().y() > 0 else 0.8
            self.scale(factor, factor)
            event.accept()
            return
        super().wheelEvent(event)


class ManualSegmentDialog(QDialog):
    """返回按阅读顺序排列的矩形列表(图片像素坐标)。"""

    def __init__(self, parent, pixmap, title: str = "手动切分"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(1100, 820)
        self._pixmap = pixmap
        self._boxes: list[QGraphicsItem] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        hint = QLabel(
            "在图上按住左键拖出每一行(手写/双栏建议手动框);按住 Ctrl 滚轮可缩放。"
            "框可拖动、可删除,顺序按画框先后,可用右侧按钮调整。"
        )
        hint.setObjectName("previewInfo")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        body = QHBoxLayout()
        body.setSpacing(10)

        self._scene = QGraphicsScene(self)
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._pixmap_item.setZValue(-10)
        self._view = _Canvas(self._scene, self)
        self._view.set_pixmap_item(self._pixmap_item)
        self._view.box_added.connect(self._add_box)
        body.addWidget(self._view, 1)

        side = QVBoxLayout()
        side.setSpacing(6)
        side.addWidget(QLabel("已框选:"))
        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list.currentRowChanged.connect(self._highlight)
        side.addWidget(self._list, 1)

        up = QPushButton("上移")
        down = QPushButton("下移")
        delete = QPushButton("删除")
        clear = QPushButton("清空")
        fit = QPushButton("适应窗口")
        for btn in (up, down, delete, clear, fit):
            btn.setCursor(Qt.PointingHandCursor)
        up.clicked.connect(lambda: self._move(-1))
        down.clicked.connect(lambda: self._move(1))
        delete.clicked.connect(self._delete_selected)
        clear.clicked.connect(self._clear)
        fit.clicked.connect(self._view.fit_all)
        side.addWidget(up)
        side.addWidget(down)
        side.addWidget(delete)
        side.addWidget(clear)
        side.addWidget(fit)

        body.addLayout(side)
        layout.addLayout(body, 1)

        bottom = QHBoxLayout()
        note = QLabel("识别后仍可在主界面逐行修改")
        note.setObjectName("legend")
        ok = QPushButton("识别并替换")
        ok.setProperty("class", "primary")
        ok.setCursor(Qt.PointingHandCursor)
        cancel = QPushButton("取消")
        cancel.setCursor(Qt.PointingHandCursor)
        ok.clicked.connect(self._accept)
        cancel.clicked.connect(self.reject)
        bottom.addWidget(note)
        bottom.addStretch()
        bottom.addWidget(ok)
        bottom.addWidget(cancel)
        layout.addLayout(bottom)

    # ------------------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        self._view.fit_all()

    def _add_box(self, rect: QRectF) -> None:
        pen = QPen(QColor("#2563EB"), 2)
        pen.setCosmetic(True)
        item = self._scene.addRect(rect, pen)
        item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        item.setFlag(QGraphicsItem.ItemIsMovable, True)
        item.setZValue(10)
        self._boxes.append(item)
        self._refresh_list()
        self._list.setCurrentRow(len(self._boxes) - 1)

    def _refresh_list(self) -> None:
        self._list.blockSignals(True)
        self._list.clear()
        for i, item in enumerate(self._boxes):
            r = item.sceneBoundingRect()
            self._list.addItem(
                f"{i + 1}.  {int(r.width())} × {int(r.height())}"
            )
        self._list.blockSignals(False)

    def _highlight(self, row: int) -> None:
        for i, item in enumerate(self._boxes):
            item.setSelected(i == row)

    def _delete_selected(self) -> None:
        row = self._list.currentRow()
        if 0 <= row < len(self._boxes):
            item = self._boxes.pop(row)
            self._scene.removeItem(item)
            self._refresh_list()
            if self._boxes:
                self._list.setCurrentRow(min(row, len(self._boxes) - 1))

    def _clear(self) -> None:
        for item in self._boxes:
            self._scene.removeItem(item)
        self._boxes.clear()
        self._list.clear()

    def _move(self, delta: int) -> None:
        row = self._list.currentRow()
        target = row + delta
        if row < 0 or target < 0 or target >= len(self._boxes):
            return
        self._boxes[row], self._boxes[target] = self._boxes[target], self._boxes[row]
        self._refresh_list()
        self._list.setCurrentRow(target)

    def _accept(self) -> None:
        if not self._boxes:
            QMessageBox.information(self, "提示", "请先在图上拖出至少一个框")
            return
        self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self._delete_selected()
            return
        super().keyPressEvent(event)

    # ------------------------------------------------------------------
    def boxes(self) -> list[tuple[int, int, int, int]]:
        """返回按顺序排列的框(裁剪到图片范围内)。"""
        bounds = QRectF(0, 0, self._pixmap.width(), self._pixmap.height())
        result = []
        for item in self._boxes:
            rect = item.sceneBoundingRect().intersected(bounds)
            if rect.width() < 4 or rect.height() < 4:
                continue
            result.append((int(rect.x()), int(rect.y()),
                           int(rect.width()), int(rect.height())))
        return result
