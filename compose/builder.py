# -*- coding: utf-8 -*-
"""compose/builder.py —— Block 拼成可编译 .tex(主责: C 陶谱州;骨架: A 提供)

验证命令:
    python -m compose.builder
期望结果:
    data/compose_check/builder_test.tex 生成;本机装有 xelatex 时会自动
    编译出 builder_test.pdf。自测用的是假 Block,不加载识别模型。

AI 辅助说明: 见 README「诚信声明」。

谁在调用这两个函数(改签名前先看这里):
    - main.py 的 pipeline():      compose_document(regions)
    - D 的预览功能(分工文档 §4.2): build_body(blocks)
    所以这两个函数是冻结接口的组成部分。

冻结数据结构(字段名和类型不许改):
    Block    = {"order": int, "type": "text"|"formula", "content": str,
               "latex": str, "confidence": float, "bbox": (x, y, w, h)}
    Document = {"blocks": List[Block], "tex_source": str}

实现要点(2026-11-21 已实现):
    1. 一定要按 order 排序,不要依赖列表原顺序;
    2. 连续文字行合并成一个段落(用空格连接);公式行单独包在 $$...$$ 里,前后空行;
    3. compose_document 调 recog/engine.py 的 recognize() 完成识别;
    4. 英文换行交给 LaTeX,不要手动加 \\。
"""

from __future__ import annotations

from compose.template import TEMPLATE


def build_body(blocks: list[dict]) -> str:
    """把 Block 列表拼成 .tex 正文(不含模板头尾)。

    算法:
      1. blocks 按 order 排序;
      2. 遍历: 文字行攒进段落缓冲;遇到公式行,先把缓冲收尾成一段,
         再追加 "$$ {latex} $$";
      3. 段落之间用空行("\\n\\n")连接;
      4. 空 latex(识别失败/太窄的行)直接跳过,避免产出 $$ $$ 这种编译垃圾。

    分段规则(2026-11-21 实测补充):
      板书换行大多是"换一个意思",不是排版换行。所以只有**看起来是续行**时才合并:
      上一行没有以 . : ; ! ? 结尾,且这一行以小写字母开头。
      例: "Derivative Rules" / "Given ..." -> 两段(标题独立);
          "... a long sentence that" / "continues here" -> 一段(续行)。
    """
    parts: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        nonlocal buf
        if buf:
            parts.append(" ".join(buf))
            buf = []

    for b in sorted(blocks, key=lambda x: x["order"]):
        latex = (b.get("latex") or "").strip()
        if not latex:
            continue

        if b["type"] == "formula":
            flush()
            parts.append(f"$$ {latex} $$")
            continue

        if buf:
            prev = buf[-1]
            ends_sentence = prev.rstrip()[-1:] in ".:;!?"
            starts_lower = latex[:1].islower()
            if ends_sentence or not starts_lower:
                flush()          # 新的一句话/标题: 另起一段
        buf.append(latex)

    flush()
    return "\n\n".join(parts)


def compose_document(regions: list[dict]) -> dict:
    """layout 的 Region 列表 -> Document(识别 + 合成的总入口)。

    流程:
      blocks = [recognize(r) for r in regions]      # recog/engine.py
      body = build_body(blocks)
      return {"blocks": blocks, "tex_source": TEMPLATE.replace("% BODY", body)}
    """
    from recog.engine import recognize

    blocks = [recognize(r) for r in regions]
    body = build_body(blocks)
    return {
        "blocks": blocks,
        "tex_source": TEMPLATE.replace("% BODY", body),
    }


def merge_documents(docs: list[dict]) -> tuple[dict, list[int]]:
    """多张板书的 Document 合并成一份: 顺序拼接,每张之间 \\newpage。

    返回 (merged, page_sizes):
      merged     : 合并后的 Document(blocks 的 order 已重新连续编号);
      page_sizes : 每张图贡献多少 Block,GUI 用它画分页标题/重建 tex。

    空文档(没识别到行)会保留一个 0,保证页码与导入顺序一一对应。
    """
    blocks: list[dict] = []
    bodies: list[str] = []
    page_sizes: list[int] = []

    for doc in docs:
        page_blocks = sorted(doc.get("blocks", []), key=lambda b: b["order"])
        if not page_blocks:
            page_sizes.append(0)
            continue
        offset = len(blocks)
        page_blocks = [dict(b, order=b["order"] + offset) for b in page_blocks]
        blocks.extend(page_blocks)
        bodies.append(build_body(page_blocks))
        page_sizes.append(len(page_blocks))

    body = "\n\n\\newpage\n\n".join(b for b in bodies if b.strip())
    return {"blocks": blocks, "tex_source": TEMPLATE.replace("% BODY", body)}, page_sizes


if __name__ == "__main__":
    import os
    import shutil
    import subprocess

    os.makedirs("data/compose_check", exist_ok=True)

    # 假 Block: 只测"拼装",不加载任何识别模型
    fake_blocks = [
        {"order": 0, "type": "text", "content": "Given", "latex": "Given",
         "confidence": 0.9, "bbox": (10, 10, 100, 30)},
        {"order": 1, "type": "text", "content": " f(x)", "latex": "f(x)",
         "confidence": 0.9, "bbox": (10, 10, 100, 30)},
        {"order": 2, "type": "formula", "content": r"\int_0^1 x^2 dx",
         "latex": r"\int_0^1 x^2 \, dx", "confidence": 0.8,
         "bbox": (10, 50, 100, 40)},
    ]
    body = build_body(fake_blocks)
    doc = {"blocks": fake_blocks, "tex_source": TEMPLATE.replace("% BODY", body)}

    out = os.path.join("data", "compose_check", "builder_test.tex")
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc["tex_source"])
    print(f"tex 已生成: {out}")
    print(f"blocks 数: {len(doc['blocks'])}, 正文 {len(body)} 字符")

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
