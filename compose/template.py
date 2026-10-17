# -*- coding: utf-8 -*-
"""compose/template.py —— .tex 文档模板(主责: A 提供,C 直接使用)

验证命令:
    python -m compose.template
期望结果:
    data/compose_check/empty.tex 生成;终端打印本机是否装有 xelatex。
    装了的话可顺手编译验证模板本身没有语法问题:
        xelatex -interaction=nonstopmode -output-directory data/compose_check data/compose_check/empty.tex

AI 辅助说明: 见 README「诚信声明」。

说明:
    MVP 边界 = 英文+公式混排,所以用 article 即可(pdflatex/xelatex 均可编译)。
    日后若板书出现中文,再换成 ctexart + xelatex(记入 Future Work,现在不动)。
    C 的 builder.py 用 TEMPLATE.replace("% BODY", body) 把正文填进来。
"""

TEMPLATE = r"""\documentclass[12pt]{article}
\usepackage{amsmath, amssymb}
\usepackage[margin=2.5cm]{geometry}
\begin{document}
\section*{Board2TeX Export}
% BODY
\end{document}
"""

if __name__ == "__main__":
    import os
    import shutil

    os.makedirs("data/compose_check", exist_ok=True)
    out = os.path.join("data", "compose_check", "empty.tex")
    with open(out, "w", encoding="utf-8") as f:
        f.write(TEMPLATE)

    xelatex = shutil.which("xelatex")
    print(f"模板已写入 {out}")
    if xelatex:
        print(f"检测到 xelatex: {xelatex} ,可按文件头命令编译验证")
    else:
        print("未检测到 xelatex: 请安装 TeX Live 或 MiKTeX(组内统一环境)")
