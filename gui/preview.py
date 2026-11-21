# -*- coding: utf-8 -*-
"""gui/preview.py —— 编译结果预览(维护: A 胡秉善)

预览 = 用当前 tex 调 xelatex 编译,再把 PDF 逐页渲染成图片显示。
不是显示源码,也不是"大致排版":所见即导出结果。

依赖:
    xelatex   —— 编译(texlive/miktex 自带);
    pdftoppm  —— PDF 转 PNG(poppler,texlive 自带的版本里有)。
    两者缺一时给出明确提示,不会静默退回显示源码。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess

# 必须先于 PyQt5 导入(原因见 gui/torch_preload.py)
from gui import torch_preload  # noqa: F401

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QDialog, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from gui.exporter import compile_pdf, has_pdflatex, has_xelatex

PREVIEW_DIR = os.path.join("data", "preview")
PAGE_DPI = 200          # 渲染精度: 200dpi 保证放大/缩小时字口仍然干净
PAGE_WIDTH = 820        # 页面上屏宽度(px)


def _clean(out_dir: str, pattern: str) -> None:
    for path in glob.glob(os.path.join(out_dir, pattern)):
        try:
            os.remove(path)
        except OSError:
            pass


def export_preview_pdf(doc: dict, out_dir: str = PREVIEW_DIR,
                       engine: str | None = None) -> str:
    """把 doc 写成 preview.tex 并编译,返回 PDF 路径。

    预览优先用 pdflatex(本机实测 0.6s,xelatex 要 3.2s);
    pdflatex 编不过时(比如混进 Unicode 字符)自动回退 xelatex,保证"能预览"。
    """
    os.makedirs(out_dir, exist_ok=True)
    _clean(out_dir, "preview*")
    tex_path = os.path.join(out_dir, "preview.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(doc["tex_source"])

    if engine is None:
        engine = "pdflatex" if has_pdflatex() else "xelatex"
    try:
        return compile_pdf(tex_path, out_dir, engine=engine, quiet=True)
    except RuntimeError:
        if engine != "xelatex" and has_xelatex():
            return compile_pdf(tex_path, out_dir, engine="xelatex", quiet=True)
        raise


def render_pdf_pages(pdf_path: str, out_dir: str = PREVIEW_DIR,
                     dpi: int = PAGE_DPI,
                     width_px: int | None = None) -> list[str]:
    """用 pdftoppm 把 PDF 每页转成 PNG,返回按页序排好的路径列表。

    width_px 不为空时按"目标像素宽"渲染(-scale-to-x),这样上屏是 1:1,
    不会因为二次缩放把细笔画糊掉;为空则按 dpi 渲染。
    """
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm is None:
        raise RuntimeError(
            "未找到 pdftoppm(PDF 转图片工具)。\n"
            "TeX Live 一般自带;若用 MiKTeX,可先只导出 PDF 查看。"
        )

    _clean(out_dir, "page-*.png")
    prefix = os.path.join(out_dir, "page")
    cmd = [pdftoppm, "-png"]
    if width_px:
        cmd += ["-scale-to-x", str(max(int(width_px), 50)), "-scale-to-y", "-1"]
    else:
        cmd += ["-r", str(dpi)]
    cmd += [pdf_path.replace("\\", "/"), prefix.replace("\\", "/")]
    subprocess.run(cmd, check=False, capture_output=True)

    pages = sorted(glob.glob(os.path.join(out_dir, "page-*.png")), key=_page_number)
    if not pages:
        raise RuntimeError("PDF 已生成,但渲染成图片失败,请直接打开 PDF 查看。")
    return pages


def _page_number(path: str) -> int:
    """"page-12.png" -> 12,保证 10 页以上时页序不乱。"""
    stem = os.path.splitext(os.path.basename(path))[0]
    try:
        return int(stem.rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return 0


def create_preview_dialog(parent, doc: dict) -> QDialog:
    """编译 + 渲染,返回"可 exec 的预览对话框"(调用方负责 exec_)。"""
    if not has_xelatex():
        raise RuntimeError("预览需要 xelatex。\n请安装 TeX Live / MiKTeX,或先只导出 .tex。")

    QApplication.setOverrideCursor(Qt.WaitCursor)
    try:
        pdf_path = export_preview_pdf(doc)
        pages = render_pdf_pages(pdf_path, width_px=PAGE_WIDTH)
    finally:
        QApplication.restoreOverrideCursor()

    dialog = QDialog(parent)
    dialog.setWindowTitle("预览 · 编译结果")
    dialog.resize(900, 780)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(10)

    top = QHBoxLayout()
    info = QLabel(f"xelatex 编译通过 · 共 {len(pages)} 页")
    info.setObjectName("previewInfo")
    open_btn = QPushButton("打开 PDF")
    open_btn.setCursor(Qt.PointingHandCursor)
    open_btn.clicked.connect(
        lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(pdf_path)))
    )
    top.addWidget(info)
    top.addStretch()
    top.addWidget(open_btn)
    layout.addLayout(top)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setObjectName("previewScroll")
    host = QWidget()
    host.setObjectName("previewHost")
    host_layout = QVBoxLayout(host)
    host_layout.setContentsMargins(4, 4, 4, 4)
    host_layout.setSpacing(12)

    for page_path in pages:
        page = QLabel()
        page.setObjectName("previewPage")
        page.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(page_path)
        page.setPixmap(pixmap)      # 已按 PAGE_WIDTH 渲染,1:1 上屏,不再二次缩放
        host_layout.addWidget(page)

    host_layout.addStretch()
    scroll.setWidget(host)
    layout.addWidget(scroll, 1)
    return dialog


def show_compiled_preview(parent, doc: dict) -> None:
    """on_preview 的入口: 编译 -> 渲染 -> 弹窗,失败时用弹窗说明原因。"""
    from PyQt5.QtWidgets import QMessageBox

    try:
        dialog = create_preview_dialog(parent, doc)
    except RuntimeError as exc:
        QMessageBox.critical(parent, "预览失败", str(exc))
        return
    dialog.exec_()
