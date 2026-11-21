# -*- coding: utf-8 -*-
"""eval/run_eval.py —— 评估入口(主责: D 李若宸)

用法:
    python tools/make_eval_assets.py          # 第一次先造评估图与真值
    python eval/run_eval.py                   # 自动指标(会加载两个模型,约 1~2 分钟)
    python eval/run_eval.py --mode manual     # 人工可用率(读 eval/labels.csv)

产物:
    data/eval/report.md     给人看的评估报告(可直接贴进项目报告)
    data/eval/results.json  逐行明细(排查用)
    data/eval/manual.txt    人工可用率(manual 模式)

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from eval.dataset import load_auto_dataset, load_manual_rows
from eval.metrics import (cer, formula_exact, formula_similarity,
                          normalize_latex, normalize_text, usable_rate)
from main import pipeline


def evaluate_board(image_path: str, expected: list[dict]) -> dict:
    """跑一张图,返回逐行对比结果。"""
    pre, regions, doc = pipeline(image_path)
    blocks = sorted(doc["blocks"], key=lambda b: b["order"])

    rows = []
    for exp in expected:
        idx = exp["order"]
        pred = blocks[idx] if idx < len(blocks) else None

        row = {
            "order": idx,
            "expected_type": exp["type"],
            "predicted_type": pred["type"] if pred else "",
            "type_ok": bool(pred and pred["type"] == exp["type"]),
        }
        if exp["type"] == "text":
            hyp = pred["content"] if pred else ""
            row.update(ref=exp["text"], hyp=hyp, cer=cer(exp["text"], hyp))
        else:
            hyp = pred["latex"] if pred else ""
            row.update(
                ref=exp["latex"], hyp=hyp,
                exact=formula_exact(exp["latex"], hyp),
                similarity=formula_similarity(exp["latex"], hyp),
            )
        rows.append(row)

    return {
        "image": os.path.basename(image_path),
        "expected_lines": len(expected),
        "predicted_lines": len(regions),
        "count_ok": len(regions) == len(expected),
        "rows": rows,
    }


def summarize(boards: list[dict]) -> dict:
    all_rows = [r for b in boards for r in b["rows"]]
    text_rows = [r for r in all_rows if r["expected_type"] == "text"]
    form_rows = [r for r in all_rows if r["expected_type"] == "formula"]

    def _mean(xs):
        return sum(xs) / len(xs) if xs else 0.0

    return {
        "boards": len(boards),
        "lines": len(all_rows),
        "count_accuracy": _mean([1.0 if b["count_ok"] else 0.0 for b in boards]),
        "type_accuracy": _mean([1.0 if r["type_ok"] else 0.0 for r in all_rows]),
        "text_lines": len(text_rows),
        "text_cer": _mean([r["cer"] for r in text_rows]),
        "text_exact": _mean([1.0 if r["cer"] == 0 else 0.0 for r in text_rows]),
        "formula_lines": len(form_rows),
        "formula_exact": _mean([1.0 if r["exact"] else 0.0 for r in form_rows]),
        "formula_similarity": _mean([r["similarity"] for r in form_rows]),
    }


def write_report(summary: dict, boards: list[dict], out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "report.md")

    lines = [
        "# Board2TeX 自动评估报告",
        "",
        f"> 生成时间: {time.strftime('%Y-%m-%d %H:%M')}",
        "> 数据: `assets/eval/` 的合成板书(纯白底、印刷体、无透视)。",
        "> **口径说明**:这组数字衡量的是算法链路是否正确,不代表手机实拍效果;",
        "> 实拍可用率请用 `--mode manual` 按 `eval/labels.csv` 统计。",
        "",
        "## 汇总",
        "",
        "| 指标 | 数值 |",
        "|---|---|",
        f"| 图片数 | {summary['boards']} |",
        f"| 总行数 | {summary['lines']} |",
        f"| 行数完全正确 | {summary['count_accuracy']:.0%} |",
        f"| 行分类准确率 | {summary['type_accuracy']:.1%} |",
        f"| 文字行 CER(越低越好) | {summary['text_cer']:.1%} |",
        f"| 文字行完全正确 | {summary['text_exact']:.0%} |",
        f"| 公式行完全匹配 | {summary['formula_exact']:.0%} |",
        f"| 公式行相似度(1 - CER) | {summary['formula_similarity']:.1%} |",
        "",
        "## 逐图明细",
        "",
        "| 图片 | 期望行/实际行 | 行数 | 分类准确 | 文字 CER | 公式完全匹配 |",
        "|---|---|---|---|---|---|",
    ]

    for b in boards:
        text_rows = [r for r in b["rows"] if r["expected_type"] == "text"]
        form_rows = [r for r in b["rows"] if r["expected_type"] == "formula"]
        t_cer = sum(r["cer"] for r in text_rows) / len(text_rows) if text_rows else 0.0
        f_ok = sum(1 for r in form_rows if r["exact"])
        lines.append(
            f"| {b['image']} | {b['expected_lines']}/{b['predicted_lines']} | "
            f"{'OK' if b['count_ok'] else 'X'} | "
            f"{sum(1 for r in b['rows'] if r['type_ok'])}/{len(b['rows'])} | "
            f"{t_cer:.1%} | {f_ok}/{len(form_rows)} |"
        )

    lines += ["", "## 逐行明细", ""]
    for b in boards:
        lines.append(f"### {b['image']}")
        lines.append("")
        lines.append("| # | 期望 | 预测 | 结果 |")
        lines.append("|---|---|---|---|")
        for r in b["rows"]:
            if r["expected_type"] == "text":
                result = f"CER {r['cer']:.0%}"
            else:
                result = "完全匹配" if r["exact"] else f"相似 {r['similarity']:.0%}"
            expected = normalize_text(r["ref"]) if r["expected_type"] == "text" \
                else normalize_latex(r["ref"])
            predicted = normalize_text(r["hyp"]) if r["expected_type"] == "text" \
                else normalize_latex(r["hyp"])
            lines.append(f"| {r['order']} | `{expected}` | `{predicted}` | {result} |")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Board2TeX 评估")
    parser.add_argument("--mode", choices=["auto", "manual"], default="auto")
    parser.add_argument("--eval-dir", default=os.path.join("assets", "eval"))
    parser.add_argument("--out-dir", default=os.path.join("data", "eval"))
    parser.add_argument("--csv", default=os.path.join("eval", "labels.csv"))
    parser.add_argument("--max-edits", type=int, default=3)
    args = parser.parse_args(argv)

    if args.mode == "manual":
        try:
            rows = load_manual_rows(args.csv)
        except FileNotFoundError:
            print(f"找不到 {args.csv};请先按 eval/labels.example.csv 的格式记录试跑结果")
            return 1
        rate = usable_rate(rows, args.max_edits)
        os.makedirs(args.out_dir, exist_ok=True)
        out = os.path.join(args.out_dir, "manual.txt")
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"样本数: {len(rows)}\n改动 <= {args.max_edits} 处算可用\n"
                    f"端到端可用率: {rate:.1%}\n")
        print(f"样本 {len(rows)} 张,可用率 {rate:.1%};结果写入 {out}")
        return 0

    try:
        dataset = load_auto_dataset(args.eval_dir)
    except FileNotFoundError:
        print("缺少 assets/eval/labels.json,请先运行: python tools/make_eval_assets.py")
        return 1

    boards = []
    for name, expected in dataset.items():
        image_path = os.path.join(args.eval_dir, name)
        print(f"评估 {name} ...", flush=True)
        boards.append(evaluate_board(image_path, expected))

    summary = summarize(boards)
    report = write_report(summary, boards, args.out_dir)

    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "boards": boards}, f,
                  ensure_ascii=False, indent=2)

    print(f"\n行数正确 {summary['count_accuracy']:.0%} | "
          f"分类 {summary['type_accuracy']:.1%} | "
          f"文字 CER {summary['text_cer']:.1%} | "
          f"公式匹配 {summary['formula_exact']:.0%}")
    print(f"报告: {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
