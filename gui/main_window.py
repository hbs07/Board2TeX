# -*- coding: utf-8 -*-
"""gui/main_window.py —— 主窗口框架(主责: A 胡秉善;控件逻辑: D 李若宸)

验证命令(会弹出窗口,人工确认):
    python -m gui.main_window
期望结果:
    窗口打开:左侧"识别结果"编辑区 + 右侧"编译预览"实时预览;
    顶部按钮: 导入图片 / 追加图片 / 查看原图 / 调整顺序 / 再次识别 /
    导出 .tex / 导出 PDF / 存入笔记 / 笔记。

AI 辅助说明: 见 README「诚信声明」。

布局(2026-11-21 调整):
    - 主区域两栏各占一半: 左=编辑区,右=实时预览;
    - 原图不常驻,点「查看原图」弹窗查看(可缩放);
    - self.editor_area / self.editor_layout : 编辑区容器,show_blocks() 往里加行;
    - self.doc / self.pre / self.regions : 识别结果(数据结构见冻结接口)。

编辑区实现:
    1. show_blocks(): 把 self.doc["blocks"] 渲染成一行一个输入框,低置信度标红;
    2. _on_block_edited(): 输入框改动实时写回 block["latex"],并触发右侧预览;
    3. 导出前统一 _rebuild_tex(),保证导出的是改过的版本;
    4. 笔记: 存入/新建/追加/预览/删除,数据库在 vault/board2tex.db。
"""

from __future__ import annotations

import os
import re

import numpy as np

# 必须先于 PyQt5 导入(原因见 gui/torch_preload.py 的说明与实测记录)
from gui import torch_preload  # noqa: F401

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QDialog, QFileDialog, QFrame, QHBoxLayout, QInputDialog,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QSplitter, QVBoxLayout, QWidget,
)

from config import TEXT_CONF_THRESHOLD
from gui.exporter import compile_pdf, has_xelatex
from gui.preview_pane import PreviewPane
from main import pipeline
from preprocess.pipeline import load_image


def _icon_path() -> str:
    """项目图标(窗口/快捷方式共用)。"""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "assets", "board2tex.ico")


def _natural_key(path: str):
    """按文件名自然排序: board_2 排在 board_10 前面(Windows 多选顺序不可靠)。"""
    name = os.path.basename(path).lower()
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name)]


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
        self.setWindowIcon(QIcon(_icon_path()))
        self.resize(1440, 860)
        self.setMinimumSize(1200, 680)

        # ---- 识别结果状态(冻结接口的数据在这里流转) ----
        self.image_paths: list[str] = []   # 导入的多张板书(已按文件名排序)
        self.pre: dict | None = None       # 第一张的 {"binary", "bgr"}
        self.regions: list[dict] = []      # 所有图的 layout 输出(合并)
        self.doc: dict | None = None       # 合并后的 {"blocks", "tex_source"}
        self._page_sizes: list[int] = []   # 每张图贡献多少 Block(分页依据)
        self.block_edits: dict[int, QLineEdit] = {}   # order -> 编辑框
        self._db = None                    # 笔记库连接(懒加载)
        self._image_pixmaps: list[QPixmap] = []       # 原图,供「查看原图」使用

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
            ("导入图片", self.on_import, "", "重新导入(替换当前所有图片与结果)"),
            ("追加图片", self.on_add_images, "", "在现有板书后面继续添加,只识别新图片"),
            ("查看原图", self.on_view_image, "", "对照原始板书照片(可缩放/翻页)"),
            ("调整顺序", self.on_reorder_images, "", "调整多张板书的合并顺序"),
            ("再次识别", self.on_recognize, "primary", "重新识别当前所有图片:已配置 API 用 AI,否则用本地模型"),
            ("导出 .tex", self.on_export_tex, "", "导出 LaTeX 源文件"),
            ("导出 PDF", self.on_export_pdf, "accent", "导出 .tex 并用 xelatex 编译成 PDF"),
            ("存入笔记", self.on_save_note, "", "把当前内容追加到某份笔记(可新建)"),
            ("笔记", self.on_show_notes, "", "新建 / 预览 / 删除笔记"),
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

        # ---- 左卡片: 编辑区(占一半) ----
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
            "识别结果会显示在这里,一行一个输入框。\n改完直接「导出」,右侧会实时编译。"
        )
        self._editor_hint.setObjectName("legend")
        self._editor_hint.setWordWrap(True)
        self.editor_layout.addWidget(self._editor_hint)
        self.editor_area.setWidget(editor_host)
        right_layout.addWidget(self.editor_area, 1)

        # ---- 右卡片: 实时编译预览(占一半) ----
        self.preview_pane = PreviewPane(self, on_open=self.on_preview)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(10)
        splitter.addWidget(right_card)
        splitter.addWidget(self.preview_pane)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([700, 700])
        root.addWidget(splitter, 1)

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
    # 编辑区
    # ------------------------------------------------------------------
    def show_blocks(self):
        """把 doc["blocks"] 渲染成"一行一个输入框",改哪个就写回哪个 Block。"""
        self._clear_editor()

        if not self.doc:
            hint = QLabel(
                "识别结果会显示在这里,一行一个输入框。\n改完直接「导出」,右侧会实时编译。"
            )
            hint.setObjectName("legend")
            hint.setWordWrap(True)
            self.editor_layout.addWidget(hint)
            return

        # 计算"每张图第一行"的 order,用于插分页标题
        blocks = self.doc["blocks"]
        sizes = self._page_sizes or ([len(blocks)] if blocks else [])
        self._page_headers: dict[int, int] = {}
        acc = 0
        for idx, size in enumerate(sizes):
            if size > 0:
                self._page_headers[acc] = idx
            acc += size

        for b in self.doc["blocks"]:
            # 每张图的第一行前插一条分页标题(多图时用来区分第几张)
            if b["order"] in self._page_headers:
                page_idx = self._page_headers[b["order"]]
                name = (
                    os.path.basename(self.image_paths[page_idx])
                    if page_idx < len(self.image_paths) else ""
                )
                header = QLabel(f"第 {page_idx + 1} 张 · {name}")
                header.setObjectName("pageHeader")
                self.editor_layout.addWidget(header)

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

            # 行内上移/下移(可跨页),用于修正识别顺序或重排内容
            up = QPushButton("↑")
            down = QPushButton("↓")
            up.setObjectName("rowBtn")
            down.setObjectName("rowBtn")
            for btn, tip in ((up, "上移一行"), (down, "下移一行")):
                btn.setFixedWidth(26)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setToolTip(tip)
            up.setEnabled(order > 0)
            down.setEnabled(order < len(self.doc["blocks"]) - 1)
            up.clicked.connect(lambda _=False, o=order: self._move_block(o, -1))
            down.clicked.connect(lambda _=False, o=order: self._move_block(o, 1))
            row_layout.addWidget(up)
            row_layout.addWidget(down)

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
                widget.setParent(None)     # 先从界面摘掉,避免和新建的行重叠
                widget.deleteLater()
        self.block_edits.clear()

    def _move_block(self, order: int, delta: int) -> None:
        """把某一行上移/下移(delta=±1),可跨页;不重新识别。"""
        if not self.doc:
            return
        if order + delta < 0 or order + delta >= len(self.doc["blocks"]):
            return

        from compose.builder import move_block

        self.doc["blocks"], self._page_sizes = move_block(
            self.doc["blocks"], self._page_sizes, order, delta
        )
        self._rebuild_tex()

        scroll = self.editor_area.verticalScrollBar().value()
        self.show_blocks()
        QTimer.singleShot(
            0, lambda: self.editor_area.verticalScrollBar().setValue(scroll)
        )
        self.preview_pane.compile_now(self.doc["tex_source"])
        self.statusBar().showMessage(
            f"已{'上' if delta < 0 else '下'}移第 {order} 行,预览已更新"
        )

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

    def _current_body(self) -> str:
        """当前编辑结果的 LaTeX 正文(多图按页用 \\newpage 分隔)。"""
        if not self.doc:
            return ""
        from compose.builder import build_body

        blocks = self.doc["blocks"]
        sizes = self._page_sizes or ([len(blocks)] if blocks else [])
        pages: list[str] = []
        start = 0
        for size in sizes:
            part = blocks[start:start + size]
            start += size
            if part:
                pages.append(build_body(part))
        return "\n\n\\newpage\n\n".join(p for p in pages if p.strip())

    def _rebuild_tex(self):
        """用当前(可能已被人工修改的)blocks 重建 tex_source。"""
        if not self.doc:
            return
        from compose.template import TEMPLATE

        self.doc["tex_source"] = TEMPLATE.replace("% BODY", self._current_body())

    def _get_db(self):
        """懒加载笔记库连接(第一次使用时才建库)。"""
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
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择板书照片(可多选)", "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not paths:
            return

        # 多选返回顺序不保证按文件名;按自然序排(第2张排在第10张前面)
        paths = sorted(paths, key=_natural_key)
        self.image_paths = paths

        # 换图后旧结果全部作废,避免"图是新的、编辑区还是上一张"的错位
        self.pre = None
        self.regions = []
        self.doc = None
        self._page_sizes = []
        self.show_blocks()
        self.preview_pane.clear()
        self.right_title.setText("识别结果 · 可直接编辑")

        # 原图只在弹窗里看,这里保存 QPixmap 供「查看原图」使用
        self._image_pixmaps = []
        self._load_pixmaps(paths)
        self.statusBar().showMessage(
            f"已导入 {len(paths)} 张(可点「查看原图」)"
        )
        from recog import vlm

        if vlm.is_configured():
            self.statusBar().showMessage(
                f"已导入 {len(paths)} 张;预处理后自动 AI 识别…"
            )
            self.on_ai_recognize()
        else:
            self.statusBar().showMessage(f"已导入 {len(paths)} 张;本地识别…")
            self.on_run()

    def _load_pixmaps(self, paths: list[str]) -> None:
        for path in paths:
            try:
                self._image_pixmaps.append(ndarray_to_qpixmap(load_image(path)))
            except Exception:
                self._image_pixmaps.append(QPixmap())   # 坏图占位,保证索引对齐

    def on_add_images(self):
        """追加导入: 只识别新图片,已有内容(含手工修改)保持不变。"""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "追加板书照片(可多选)", "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not paths:
            return
        new_paths = sorted(paths, key=_natural_key)

        if not self.image_paths:       # 还没有任何图: 等同于首次导入
            self.image_paths = new_paths
            self._load_pixmaps(new_paths)
            self.doc = None
            self._page_sizes = []
            self.show_blocks()
            self.preview_pane.clear()
            from recog import vlm

            if vlm.is_configured():
                self.on_ai_recognize()
            else:
                self.on_run()
            return

        before = len(self.image_paths)
        self.image_paths.extend(new_paths)
        self._load_pixmaps(new_paths)

        docs = self._ai_recognize_paths(new_paths)
        if docs is None:               # 失败则回滚,保持状态一致
            del self.image_paths[before:]
            del self._image_pixmaps[before:]
            return

        if self.doc is None:
            from compose.builder import merge_documents

            self.doc, self._page_sizes = merge_documents(docs)
        else:
            from compose.builder import append_documents

            self.doc["blocks"], self._page_sizes = append_documents(
                self.doc["blocks"], self._page_sizes, docs
            )

        self._rebuild_tex()
        self.show_blocks()
        self._update_result_title()
        self.preview_pane.compile_now(self.doc["tex_source"])
        self.statusBar().showMessage(
            f"已追加 {len(new_paths)} 张,共 {len(self.image_paths)} 张"
        )

    def on_reorder_images(self):
        if len(self.image_paths) < 2:
            QMessageBox.information(self, "提示", "至少导入两张图片才能调整顺序")
            return

        from gui.order_dialog import OrderDialog

        dialog = OrderDialog(
            self,
            [os.path.basename(p) for p in self.image_paths],
            self._image_pixmaps,
        )
        if dialog.exec_() != QDialog.Accepted:
            return

        order = dialog.order()
        if order == list(range(len(order))):
            return
        self._apply_page_order(order)
        self.statusBar().showMessage("已调整板书顺序,预览已更新")

    def _apply_page_order(self, order: list[int]) -> None:
        """按新顺序重排图片与 Blocks(不重新识别)。"""
        self.image_paths = [self.image_paths[i] for i in order]
        self._image_pixmaps = [self._image_pixmaps[i] for i in order]
        if not self.doc:
            return

        from compose.builder import reorder_pages

        self.doc["blocks"], self._page_sizes = reorder_pages(
            self.doc["blocks"], self._page_sizes, order
        )
        self._rebuild_tex()
        self.show_blocks()
        self.preview_pane.compile_now(self.doc["tex_source"])

    def on_view_image(self):
        if not self._image_pixmaps:
            QMessageBox.information(self, "提示", "请先导入图片")
            return
        from gui.image_view import show_image_dialog

        titles = [os.path.basename(p) for p in self.image_paths]
        show_image_dialog(self, self._image_pixmaps, titles)

    def on_recognize(self):
        """再次识别: 已配置 API 用 AI,否则用本地模型。"""
        if not self.image_paths:
            QMessageBox.information(self, "提示", "请先导入图片")
            return
        from recog import vlm

        if vlm.is_configured():
            self.on_ai_recognize()
        else:
            self.on_run()

    def on_run(self):
        if not self.image_paths:
            QMessageBox.information(self, "提示", "请先导入图片")
            return

        result = self._recognize_paths(self.image_paths)
        if result is None:
            return
        pres, regions_all, docs = result

        from compose.builder import merge_documents

        self.pre = pres[0] if pres else None
        self.regions = regions_all
        self.doc, self._page_sizes = merge_documents(docs)

        self.show_blocks()
        self._update_result_title()
        self.statusBar().showMessage(
            f"识别完成: {len(self.image_paths)} 张 / "
            f"{len(self.doc['blocks'])} 块,可直接修改"
        )
        self.preview_pane.compile_now(self.doc["tex_source"])

    def _recognize_paths(self, paths: list[str]):
        """逐张跑 pipeline,返回 (pres, regions, docs);任一张失败返回 None。"""
        total = len(paths)
        docs: list[dict] = []
        pres: list[dict] = []
        regions_all: list[dict] = []

        self.setEnabled(False)  # 同步版:识别期间界面禁点,CPU 推理需几秒~几十秒
        try:
            for index, path in enumerate(paths, 1):
                self.statusBar().showMessage(
                    f"正在识别 {index}/{total}: {os.path.basename(path)}"
                    f"(首次会加载模型,请稍候)"
                )
                QApplication.processEvents()
                try:
                    pre, regions, doc = pipeline(path)
                except Exception as exc:        # 识别失败要说清是哪张图
                    QMessageBox.critical(
                        self, "识别失败",
                        f"{os.path.basename(path)}\n{type(exc).__name__}: {exc}",
                    )
                    return None
                pres.append(pre)
                regions_all.extend(regions)
                docs.append(doc)
        finally:
            self.setEnabled(True)
        return pres, regions_all, docs

    def on_ai_recognize(self):
        """调用视觉大模型识别(手写/双栏),上传的是预处理后的图。"""
        if not self.image_paths:
            QMessageBox.information(self, "提示", "请先导入图片")
            return

        from recog import vlm

        if not vlm.is_configured():
            QMessageBox.warning(
                self, "未配置 AI 识别",
                "需要视觉模型 API。请设置环境变量后重启:\n\n"
                "  B2T_VLM_API_KEY=你的密钥\n"
                "  B2T_VLM_BASE_URL=https://hpc-api.westlake.edu.cn/v1\n"
                "  B2T_VLM_MODEL=Qwen\n\n"
                "(B2T_VLM_API_KEY 未设置时会尝试读取 WESTLAKE_API_KEY)",
            )
            return

        docs = self._ai_recognize_paths(self.image_paths)
        if docs is None:
            return

        from compose.builder import merge_documents

        self.doc, self._page_sizes = merge_documents(docs)
        self.regions = []
        self.show_blocks()
        self._update_result_title()
        self.statusBar().showMessage(
            f"AI 识别完成: {len(self.image_paths)} 张 / "
            f"{len(self.doc['blocks'])} 块"
        )
        self.preview_pane.compile_now(self.doc["tex_source"])

    def _ai_recognize_paths(self, paths: list[str]) -> list[dict] | None:
        """逐张 预处理 -> 上传视觉模型 -> Document 列表;失败返回 None。"""
        from compose.builder import build_body
        from compose.template import TEMPLATE
        from preprocess.pipeline import preprocess
        from recog import vlm

        docs: list[dict] = []
        total = len(paths)
        self.setEnabled(False)
        try:
            for index, path in enumerate(paths, 1):
                self.statusBar().showMessage(
                    f"预处理 + AI 识别 {index}/{total}: "
                    f"{os.path.basename(path)}…"
                )
                QApplication.processEvents()
                try:
                    pre = preprocess(path)
                    image = vlm.prepare_for_vlm(pre["binary"])
                    blocks = vlm.transcribe_array(image)
                except Exception as exc:        # 预处理/网络/解析错误都提示清楚
                    QMessageBox.critical(
                        self, "AI 识别失败",
                        f"{os.path.basename(path)}\n{exc}",
                    )
                    return None
                body = build_body(blocks)
                docs.append({
                    "blocks": blocks,
                    "tex_source": TEMPLATE.replace("% BODY", body),
                })
        finally:
            self.setEnabled(True)
        return docs

    def _update_result_title(self) -> None:
        blocks = self.doc["blocks"] if self.doc else []
        n_formula = sum(1 for b in blocks if b["type"] == "formula")
        self.right_title.setText(
            f"识别结果 · {len(blocks)} 行"
            f"(公式 {n_formula},共 {len(self.image_paths)} 张)"
        )

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
    # 笔记(D)
    # ------------------------------------------------------------------
    def on_save_note(self):
        if not self.doc:
            QMessageBox.information(self, "提示", "请先识别")
            return
        body = self._current_body()
        if not body.strip():
            QMessageBox.information(self, "提示", "当前没有可保存的正文")
            return

        try:
            from vault.db import append_to_note, create_note, list_notes

            con = self._get_db()
            notes = list_notes(con)
        except Exception as exc:
            QMessageBox.critical(self, "读取笔记失败", str(exc))
            return

        labels = [f"{title}    ({updated})" for _, title, updated in notes]
        new_label = "＋ 新建笔记…"
        choice, ok = QInputDialog.getItem(
            self, "存入笔记", "选择要追加到的笔记:",
            labels + [new_label], 0, False,
        )
        if not ok:
            return

        if choice == new_label:
            title, ok = QInputDialog.getText(self, "新建笔记", "笔记名称:")
            if not ok:
                return
            note_id = create_note(con, title)
            note_title = title.strip() or "未命名笔记"
        else:
            index = labels.index(choice)
            note_id, note_title, _ = notes[index]

        try:
            append_to_note(con, note_id, body)
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", str(exc))
            return
        self.statusBar().showMessage(f"已追加到笔记《{note_title}》")

    def on_show_notes(self):
        try:
            con = self._get_db()
        except Exception as exc:
            QMessageBox.critical(self, "打开笔记失败", str(exc))
            return

        from gui.notes_dialog import NotesDialog

        NotesDialog(self, con).exec_()


if __name__ == "__main__":
    # 高 DPI 缩放: 笔记本 125%/150% 缩放时字体和控件不再模糊
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication([])
    app.setApplicationName("Board2TeX")
    app.setWindowIcon(QIcon(_icon_path()))
    window = MainWindow()
    window.show()
    app.exec_()