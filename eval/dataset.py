# -*- coding: utf-8 -*-
"""eval/dataset.py —— 评估数据读取(主责: D 李若宸)

两种数据:
    assets/eval/labels.json  —— 合成板书的逐行真值(自动指标用);
    eval/labels.csv          —— 真实照片的人工试跑记录(可用率用),
                                列: image,usable_after_edits

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

import csv
import json
import os

EVAL_DIR = os.path.join("assets", "eval")
MANUAL_CSV = os.path.join("eval", "labels.csv")


def load_auto_dataset(eval_dir: str = EVAL_DIR) -> dict[str, list[dict]]:
    """读 labels.json -> {图片文件名: [ {order, type, text|latex}, ... ]}。"""
    path = os.path.join(eval_dir, "labels.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_manual_rows(csv_path: str = MANUAL_CSV) -> list[tuple[str, int]]:
    """读人工试跑记录 -> [(image, edits), ...];文件不存在时抛 FileNotFoundError。"""
    rows: list[tuple[str, int]] = []
    with open(csv_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append((r["image"], int(r["usable_after_edits"])))
    return rows
