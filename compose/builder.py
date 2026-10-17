# -*- coding: utf-8 -*-
"""compose/builder.py —— Block 拼成可编译 .tex(主责: C 陶谱州;骨架: A 提供)

验证命令:
    python -m compose.builder
期望结果:
    data/compose_check/builder_test.tex 生成;本机装有 xelatex 时会自动
    编译出 builder_test.pdf。骨架阶段 tex 正文为空属预期。

AI 辅助说明: 见 README「诚信声明」。

谁在调用这两个函数(改签名前先看这里):
    - main.py 的 pipeline():      compose_document(regions)
    - D 的预览功能(分工文档 §4.2): build_body(blocks)
    所以这两个函数是冻结接口的组成部分。

冻结数据结构(字段名和类型不许改):
    Block    = {"order": int, "type": "text"|"formula", "content": str,
               "latex": str, "confidence": float, "bbox": (x, y, w, h)}
    Document = {"blocks": List[Block], "tex_source": str}

给 C 的实现要点(完整参考代码在文档 §7.2):
    1. 一定要按 order 排序,不要依赖列表原顺序;
    2. 连续文字行合并成一个段落;公式行单独包在 $$...$$ 里,前后空行;
    3. compose_document 现在的占位版"跳过了识别"直接透传 region 字段;
       正式版必须改成: blocks = [recognize(r) for r in regions]
       (recognize 来自 recog/engine.py,也是你要写的);
    4. 英文换行交给 LaTeX,不要手动加 \\。
"""

from __future__ import annotations

from compose.template import TEMPLATE


def build_body(blocks: list[dict]) -> str:
    """把 Block 列表拼成 .tex 正文(不含模板头尾)。

    算法(参考《分工_C_识别与合成.md》§7.2,文档里有完整参考代码):
      1. blocks 按 order 排序;
      2. 遍历: 文字行攒进段落缓冲;遇到公式行,先把缓冲收尾成一段,
         再追加 "$$ {latex} $$";
      3. 遍历结束收尾最后一段;段落之间用空行("\\n\\n")连接。
    """
    # TODO(C): 参考文档 §7.2 实现(约 12 行)
    return "\n\n".join(b["latex"] for b in blocks)  # 占位: 不分段不分类型


def compose_document(regions: list[dict]) -> dict:
    """layout 的 Region 列表 -> Document(识别 + 合成的总入口)。

    正式版流程(参考文档 §7.2):
      blocks = [recognize(r) for r in regions]      # recog/engine.py
      body = build_body(blocks)
      return {"blocks": blocks, "tex_source": TEMPLATE.replace("% BODY", body)}

    占位版说明: recog/engine.py 还没写,这里先跳过识别,把 region 字段
    原样转成 Block(latex 留空),保证 main.py 的链路现在就能跑通。
    """
    # TODO(C): 按上面的正式版流程实现(约 3 行,含 import recog.engine)
    blocks = [
        {
            "order": r["order"],
            "type": r["type"],
            "content": "",
            "latex": "",
            "confidence": r["confidence"],
            "bbox": r["bbox"],
        }
        for r in regions
    ]
    return {
        "blocks": blocks,
        "tex_source": TEMPLATE.replace("% BODY", build_body(blocks)),
    }


if __name__ == "__main__":
    import os
    import shutil
    import subprocess

    os.makedirs("data/compose_check", exist_ok=True)

    # 两个假 Region: 占位链路自测用,不依赖 B/C 的模块
    fake_regions = [
        {"order": 0, "type": "text", "confidence": 0.9,
         "bbox": (10, 10, 100, 30), "image": None},
        {"order": 1, "type": "formula", "confidence": 0.8,
         "bbox": (10, 50, 100, 40), "image": None},
    ]
    doc = compose_document(fake_regions)

    out = os.path.join("data", "compose_check", "builder_test.tex")
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc["tex_source"])
    print(f"tex 已生成: {out}")
    print(f"blocks 数: {len(doc['blocks'])}(占位阶段 latex 为空属预期)")

    if shutil.which("xelatex"):
        proc = subprocess.run(
            ["xelatex", "-interaction=nonstopmode",
             "-output-directory", "data/compose_check", out],
            check=False, capture_output=True, text=True,
        )
        pdf = out.replace(".tex", ".pdf")
        if os.path.exists(pdf):
            print("编译成功: " + pdf)
        else:
            print(f"编译失败(xelatex 退出码 {proc.returncode})")
            if proc.stderr:
                print("stderr:", proc.stderr[-500:])
            print("完整日志: data/compose_check/builder_test.log")
    else:
        print("未检测到 xelatex,跳过编译")
