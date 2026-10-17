# -*- coding: utf-8 -*-
"""main.py —— Board2TeX 集成入口(主责: A 胡秉善)

验证命令(端到端冒烟,会生成 .tex 并尝试编译 PDF):
    python main.py assets/test_text.png data/exports
期望结果:
    终端打印区域/块数量;data/exports/result.tex 生成;
    本机装有 xelatex 时 result.pdf 一并生成。
    骨架阶段 layout 返回 0 个区域、正文为空,属预期;
    B/C 填完各自模块后,同一条命令直接产出真实结果。

AI 辅助说明: 见 README「诚信声明」。

冻结的模块调用链(每一步的数据结构见各模块文件头):
    pipeline(image_path)
      = preprocess(image_path)            # A  + B 的 enhance
      + analyze_layout(pre["binary"])     # B  (经 layout/pipeline.py)
      + compose_document(regions)         # C  (经 compose/builder.py)
    返回 (pre, regions, doc),GUI 的「运行识别」按钮也走这里。
"""

from __future__ import annotations

from compose.builder import compose_document
from layout.pipeline import analyze_layout
from preprocess.pipeline import preprocess


def pipeline(image_path: str):
    """板书照片路径 -> (pre, regions, doc) —— 全项目唯一的一条龙入口。"""
    pre = preprocess(image_path)               # A + B
    regions = analyze_layout(pre["binary"])    # B
    doc = compose_document(regions)            # C
    return pre, regions, doc


if __name__ == "__main__":
    import os
    import sys

    from gui.exporter import compile_pdf, has_xelatex

    if len(sys.argv) < 2:
        print("用法: python main.py <板书图片路径> [输出目录,默认 data/exports]")
        raise SystemExit(1)

    src = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join("data", "exports")
    os.makedirs(out_dir, exist_ok=True)

    pre, regions, doc = pipeline(src)

    tex_path = os.path.join(out_dir, "result.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(doc["tex_source"])

    print(f"区域数: {len(regions)}")
    print(f"块数  : {len(doc['blocks'])}")
    print(f".tex  : {tex_path}")

    if has_xelatex():
        try:
            pdf_path = compile_pdf(tex_path, out_dir)
            print(f"PDF   : {pdf_path}")
        except RuntimeError as e:
            print(f"PDF 编译失败: {e}")
    else:
        print("PDF   : 未安装 xelatex,跳过编译(只导出 .tex)")
