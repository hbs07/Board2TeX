# -*- coding: utf-8 -*-
"""gui/notes_dialog.py —— 笔记管理(新建 / 预览 / 删除)(维护: A 胡秉善)

笔记存的是 LaTeX 正文,可多次追加;预览时套上模板编译成 PDF 看效果。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

# 必须先于 PyQt5 导入(原因见 gui/torch_preload.py)
from gui import torch_preload  # noqa: F401

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView, QDialog, QHBoxLayout, QInputDialog, QLabel,
    QListWidget, QMessageBox, QPushButton, QVBoxLayout,
)

from compose.template import TEMPLATE
from gui.preview import show_compiled_preview
from vault.db import create_note, delete_note, get_note, list_notes


class NotesDialog(QDialog):
    def __init__(self, parent, con):
        super().__init__(parent)
        self._con = con
        self.setWindowTitle("笔记")
        self.resize(680, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        hint = QLabel("识别完成后用「存入笔记」追加到这里;每份笔记可多次追加。")
        hint.setObjectName("previewInfo")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list.itemDoubleClicked.connect(lambda _item: self._preview())
        layout.addWidget(self._list, 1)

        row = QHBoxLayout()
        new_btn = QPushButton("新建笔记")
        preview_btn = QPushButton("预览")
        delete_btn = QPushButton("删除")
        close_btn = QPushButton("关闭")
        for btn in (new_btn, preview_btn, delete_btn, close_btn):
            btn.setCursor(Qt.PointingHandCursor)
        preview_btn.setProperty("class", "primary")
        new_btn.clicked.connect(self._new)
        preview_btn.clicked.connect(self._preview)
        delete_btn.clicked.connect(self._delete)
        close_btn.clicked.connect(self.accept)

        row.addWidget(new_btn)
        row.addWidget(preview_btn)
        row.addWidget(delete_btn)
        row.addStretch()
        row.addWidget(close_btn)
        layout.addLayout(row)

        self._refresh()

    # ------------------------------------------------------------------
    def _refresh(self) -> None:
        self._list.clear()
        self._notes = list_notes(self._con)
        for _, title, updated in self._notes:
            self._list.addItem(f"{title}    · 更新 {updated}")

    def _selected(self):
        row = self._list.currentRow()
        if 0 <= row < len(self._notes):
            return self._notes[row]
        return None

    def _new(self) -> None:
        title, ok = QInputDialog.getText(self, "新建笔记", "笔记名称:")
        if not ok:
            return
        try:
            create_note(self._con, title)
        except Exception as exc:
            QMessageBox.critical(self, "新建失败", str(exc))
            return
        self._refresh()
        self._list.setCurrentRow(0)

    def _preview(self) -> None:
        selected = self._selected()
        if selected is None:
            QMessageBox.information(self, "提示", "请先选择一份笔记")
            return
        note_id, title, _ = selected
        note = get_note(self._con, note_id)
        if note is None:
            return
        _title, body = note
        if not body.strip():
            QMessageBox.information(self, "提示", "这份笔记还是空的")
            return
        doc = {"tex_source": TEMPLATE.replace("% BODY", body)}
        show_compiled_preview(self, doc)

    def _delete(self) -> None:
        selected = self._selected()
        if selected is None:
            QMessageBox.information(self, "提示", "请先选择一份笔记")
            return
        note_id, title, _ = selected
        confirm = QMessageBox.question(
            self, "删除笔记", f"确定删除《{title}》?此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            delete_note(self._con, note_id)
        except Exception as exc:
            QMessageBox.critical(self, "删除失败", str(exc))
            return
        self._refresh()
