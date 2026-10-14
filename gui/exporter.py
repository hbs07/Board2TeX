# -*- coding: utf-8 -*-
"""gui/exporter.py —— 导出与 PDF 编译(compile_pdf: A;export_tex: D 填)

验证命令:
    python -c "from gui.exporter import has_xelatex; print(has_xelatex())"
    期望: True(装了 TeX Live/MiKTeX 的机器)。

AI 辅助范围(课程要求):
    has_xelatex / compile_pdf 由 AI 依据项目指南 §4.4 生成、经 A 验证,
    属 A 的固定资产;export_tex 为 D 的骨架(见函数内 TODO)。

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


def compile_pdf(tex_path: str, out_dir: str) -> str:
    """用 xelatex 把 .tex 编译成 PDF,返回 PDF 路径。

    - 未安装 xelatex 时抛 RuntimeError(调用方捕获后弹窗提示);
    - 编译失败抛 RuntimeError 并带上 .log 路径,方便定位;
    - xelatex 的控制台输出直接透传,联调时方便看进度。
    """
    if not has_xelatex():
        raise RuntimeError("未安装 xelatex, 请先安装 TeX Live 或 MiKTeX")
    # TeX 会把反斜杠当控制符,统一转成正斜杠(Windows 下 xelatex 也接受 /)
    tex_arg = tex_path.replace("\\", "/")
    out_arg = out_dir.replace("\\", "/")
    subprocess.run(
        ["xelatex", "-interaction=nonstopmode",
         "-output-directory", out_arg, tex_arg],
        check=False,
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

    ⚠️ TODO(D): 目前只写 doc["tex_source"]。等你把"编辑写回"做完后,
    导出前必须先用编辑后的 blocks 重建 tex_source(调 C 的 build_body +
    TEMPLATE),否则导出的永远是识别原始结果——这是分工文档 §5.2 强调的坑。
    参考实现:《分工_D_应用与评估.md》§5.1(3 行)。
    """
    # TODO(D): 参考文档 §5.1 实现,并补上"重建 tex_source"逻辑
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc["tex_source"])
