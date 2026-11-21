# -*- coding: utf-8 -*-
"""gui/style.py —— 界面主题(维护: A 胡秉善)

一个文件集中管"长什么样": 颜色、圆角、按钮状态、滚动条。
改配色只动这里的 COLORS,不要把颜色写回 main_window.py。

用法:
    from gui.style import apply_theme
    apply_theme(app)          # QApplication 建好之后、窗口显示之前

注意:
    1. Qt 的 QSS 只支持 CSS 子集(没有 flex/grid,选择器有限);
    2. 用 Fusion 基础风格,避免 Windows 原生风格盖掉圆角和内边距;
    3. 属性选择器 QPushButton[class="primary"] 依赖 setProperty("class", ...),
       属性必须在控件 polish 之前设置(本项目的按钮都是在创建时设的)。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

COLORS = {
    "bg": "#F1F5F9",
    "card": "#FFFFFF",
    "border": "#E2E8F0",
    "text": "#0F172A",
    "muted": "#64748B",
    "faint": "#94A3B8",
    "primary": "#2563EB",
    "primary_hover": "#1D4ED8",
    "primary_press": "#1E40AF",
    "accent_bg": "#EFF6FF",
    "accent_border": "#BFDBFE",
    "danger": "#DC2626",
    "danger_bg": "#FEF2F2",
    "danger_border": "#FCA5A5",
}

QSS = f"""
/* ---------------------------------------------------------------- 全局 */
* {{
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
}}
QMainWindow, QWidget#root {{
    background: {COLORS["bg"]};
}}
QToolTip {{
    background: {COLORS["text"]};
    color: white;
    border: none;
    padding: 5px 8px;
    border-radius: 6px;
}}

/* ---------------------------------------------------------------- 标题区 */
QLabel#appTitle {{
    font-size: 21px;
    font-weight: 700;
    color: {COLORS["text"]};
}}
QLabel#appSubtitle {{
    font-size: 12px;
    color: {COLORS["muted"]};
}}
QLabel#badge {{
    background: #E0E7FF;
    color: #3730A3;
    border-radius: 9px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 700;
}}

/* ---------------------------------------------------------------- 卡片 */
QFrame#card {{
    background: {COLORS["card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 14px;
}}
QLabel#cardTitle {{
    color: #334155;
    font-size: 12px;
    font-weight: 600;
    padding-left: 2px;
}}

/* ---------------------------------------------------------------- 按钮 */
QPushButton {{
    background: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 8px 14px;
    color: {COLORS["text"]};
    font-size: 13px;
}}
QPushButton:hover {{
    background: #F8FAFC;
    border-color: #94A3B8;
}}
QPushButton:pressed {{
    background: #E2E8F0;
}}
QPushButton:disabled {{
    color: {COLORS["faint"]};
    background: {COLORS["bg"]};
    border-color: {COLORS["border"]};
}}
QPushButton[class="primary"] {{
    background: {COLORS["primary"]};
    border: 1px solid {COLORS["primary"]};
    color: white;
    font-weight: 600;
}}
QPushButton[class="primary"]:hover {{
    background: {COLORS["primary_hover"]};
    border-color: {COLORS["primary_hover"]};
}}
QPushButton[class="primary"]:pressed {{
    background: {COLORS["primary_press"]};
}}
QPushButton[class="accent"] {{
    background: {COLORS["accent_bg"]};
    border: 1px solid {COLORS["accent_border"]};
    color: #1D4ED8;
    font-weight: 600;
}}
QPushButton[class="accent"]:hover {{
    background: #DBEAFE;
}}

/* ---------------------------------------------------------------- 图像区 */
QLabel#imageCanvas {{
    background: #F8FAFC;
    border: 1px dashed #CBD5E1;
    border-radius: 10px;
    color: {COLORS["faint"]};
    font-size: 13px;
}}
QLabel#imageCanvas[filled="true"] {{
    background: #FFFFFF;
    border: 1px solid {COLORS["border"]};
}}

/* ---------------------------------------------------------------- 编辑区 */
QScrollArea#editorScroll {{
    border: none;
    background: transparent;
}}
QScrollArea#editorScroll > QWidget > QWidget {{
    background: transparent;
}}
QWidget#editorHost {{
    background: transparent;
}}
QFrame#blockRow {{
    background: #F8FAFC;
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
}}
QLabel#orderLabel {{
    color: {COLORS["faint"]};
    font-size: 11px;
    font-family: Consolas, "Cascadia Mono", monospace;
}}
QLabel#chipText {{
    background: #DBEAFE;
    color: #1D4ED8;
    border-radius: 6px;
    padding: 2px 6px;
    font-size: 10px;
    font-weight: 700;
}}
QLabel#chipFormula {{
    background: #FEF3C7;
    color: #B45309;
    border-radius: 6px;
    padding: 2px 6px;
    font-size: 10px;
    font-weight: 700;
}}
QLabel#confLabel {{
    color: {COLORS["muted"]};
    font-size: 11px;
}}
QLabel#confLabel[risky="true"] {{
    color: {COLORS["danger"]};
    font-weight: 700;
}}
QLineEdit#blockEdit {{
    background: #FFFFFF;
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 6px 10px;
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 13px;
    color: {COLORS["text"]};
    selection-background-color: #BFDBFE;
}}
QLineEdit#blockEdit:focus {{
    border: 1px solid {COLORS["primary"]};
}}
QLineEdit#blockEdit[risky="true"] {{
    background: {COLORS["danger_bg"]};
    border: 1px solid {COLORS["danger_border"]};
}}
QLabel#legend {{
    color: {COLORS["faint"]};
    font-size: 11px;
    padding-top: 6px;
}}

/* ---------------------------------------------------------------- 滚动条 */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px 0 2px 0;
}}
QScrollBar::handle:vertical {{
    background: #CBD5E1;
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: #94A3B8;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

/* ---------------------------------------------------------------- 状态栏 */
QStatusBar {{
    background: transparent;
    color: {COLORS["muted"]};
    font-size: 12px;
}}
QStatusBar::item {{
    border: none;
}}
QLabel#statusBadge {{
    color: {COLORS["faint"]};
    font-size: 11px;
    padding-right: 10px;
}}

/* ---------------------------------------------------------------- 预览 */
QLabel#previewInfo {{
    color: {COLORS["muted"]};
    font-size: 12px;
}}
QLabel#previewStatus {{
    color: {COLORS["faint"]};
    font-size: 11px;
}}
QLabel#previewError {{
    color: {COLORS["danger"]};
    font-size: 11px;
}}
QLabel#livePage {{
    background: white;
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 4px;
}}
QPushButton#zoomBtn {{
    padding: 2px 8px;
    font-size: 14px;
    font-weight: 600;
    min-width: 18px;
}}
QLabel#zoomLabel {{
    color: {COLORS["muted"]};
    font-size: 11px;
    min-width: 32px;
}}
QSplitter::handle {{
    background: transparent;
}}
QScrollArea#previewScroll {{
    border: none;
    background: transparent;
}}
QWidget#previewHost {{
    background: transparent;
}}
QLabel#previewPage {{
    background: white;
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    padding: 6px;
}}

/* ---------------------------------------------------------------- 对话框 */
QDialog {{
    background: {COLORS["bg"]};
}}
QTextEdit {{
    background: white;
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    padding: 8px;
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 12px;
}}
QMessageBox {{
    background: white;
}}
"""


def apply_theme(app) -> None:
    """把主题应用到整个 QApplication(重复调用无副作用)。"""
    try:
        app.setStyle("Fusion")       # 统一各平台的基础风格,圆角才不会被原生风格吃掉
    except Exception:
        pass
    app.setStyleSheet(QSS)
