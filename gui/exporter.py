# -*- coding: utf-8 -*-
"""gui/exporter.py —— 导出与 PDF 编译(compile_pdf: A;export_tex: D 填)

验证命令:
    python -c "from gui.exporter import has_xelatex; print(has_xelatex())"
    期望: True(装了 TeX Live/MiKTeX 的机器)。

AI 辅助说明: 见 README「诚信声明」。

设计约束(改前先看):
    本文件**不 import PyQt5**——main.py 的命令行模式也要用 compile_pdf,
    保证纯命令行环境(无显示器/无 GUI)可编译 PDF。

D 需要知道的流程(分工文档 §5.2):
    导出 PDF = export_tex(写 .tex) -> compile_pdf(xelatex 编译)。
    调用方(main_window 的"导出 PDF"按钮)已按此顺序接线。
"""

from __future__ import annotations

import os
import shutil
import subprocess


def has_xelatex() -> bool:
    """检测本机是否安装 xelatex。GUI 在导出前应先检查并友好提示。"""
    return shutil.which("xelatex") is not None


def has_pdflatex() -> bool:
    """检测本机是否安装 pdflatex(预览用的快速引擎)。"""
    return shutil.which("pdflatex") is not None


def compile_pdf(tex_path: str, out_dir: str, engine: str = "xelatex",
                quiet: bool = False) -> str:
    """把 .tex 编译成 PDF,返回 PDF 路径。

    - engine="xelatex": 最终导出用(支持 Unicode/中文,慢一点);
    - engine="pdflatex": 实时预览用(纯英文模板下快 5 倍,约 0.6s);
    - quiet=True: 不把 TeX 日志打到控制台(实时预览每几秒一次,刷屏没意义);
    - 未安装该引擎时抛 RuntimeError(调用方捕获后弹窗提示);
    - 编译失败抛 RuntimeError 并带上 .log 路径,方便定位。
    """
    if engine == "xelatex":
        installed = has_xelatex()
    else:
        installed = shutil.which(engine) is not None
    if not installed:
        raise RuntimeError(f"未安装 {engine}, 请先安装 TeX Live 或 MiKTeX")
    # TeX 会把反斜杠当控制符,统一转成正斜杠(Windows 下也接受 /)
    tex_arg = tex_path.replace("\\", "/")
    out_arg = out_dir.replace("\\", "/")
    subprocess.run(
        [engine, "-interaction=nonstopmode",
         "-output-directory", out_arg, tex_arg],
        check=False,
        stdout=subprocess.DEVNULL if quiet else None,
        stderr=subprocess.DEVNULL if quiet else None,
    )
    pdf_path = os.path.join(
        out_dir, os.path.splitext(os.path.basename(tex_path))[0] + ".pdf"
    )
    if not os.path.exists(pdf_path):
        log_path = os.path.splitext(tex_path)[0] + ".log"
        raise RuntimeError(
            f"PDF 未生成,请查看编译日志: {log_path}"
        )
    return pdf_path


def export_tex(doc: dict, path: str) -> None:
    """把 Document 的 tex_source 写成 .tex 文件。

    本函数只负责"落盘",不重建 tex_source——重建由调用方在导出前完成
    (GUI 里是 MainWindow._rebuild_tex():用编辑后的 blocks 调 build_body + 模板)。
    这样 CLI、GUI、测试三处复用同一份导出逻辑,不会出现"谁忘了重建"的分叉。
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc["tex_source"])
