# -*- coding: utf-8 -*-
"""recog/vlm.py —— 视觉大模型识别(手写/双栏板书的兜底方案)

为什么需要:
    PaddleOCR + pix2tex 是印刷体模型;手写、双栏、擦痕多的真实黑板
    切行和识别都会失效。这里把整张图交给视觉大模型,让模型直接输出
    "一行一个对象"的 JSON,再进现有的 Block/Document 流程。

配置(环境变量,不写进仓库):
    B2T_VLM_BASE_URL   默认 https://hpc-api.westlake.edu.cn/v1
    B2T_VLM_API_KEY    必填;没有时读 WESTLAKE_API_KEY
    B2T_VLM_MODEL      默认 Qwen(需支持 image 输入)

调用的是 OpenAI 兼容的 /chat/completions 接口。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

import base64
import json
import os
import re

import cv2
import requests

from preprocess.pipeline import load_image
from recog.postprocess import clean_latex, escape_latex

DEFAULT_BASE = "https://hpc-api.westlake.edu.cn/v1"
DEFAULT_MODEL = "Qwen"
TIMEOUT = 180

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_CONFIG = os.path.join(_ROOT, "vlm.local.json")   # 本地密钥,已 gitignore

PROMPT = (
    "Transcribe this blackboard photo into LaTeX. Return a JSON object:\n"
    '{"lines": [{"type": "text" | "formula", "latex": "..."}]}\n'
    "Rules:\n"
    "- one entry per visual line, reading order: finish the left column "
    "top-to-bottom, then the right column;\n"
    "- type text: plain text exactly as written (no LaTeX escaping);\n"
    "- type formula: valid LaTeX math, WITHOUT $ delimiters;\n"
    "- keep every readable line; do not explain or add anything else.\n"
)


def _local() -> dict:
    try:
        with open(LOCAL_CONFIG, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def api_key() -> str:
    # 优先级: 本应用专用变量 > 本地 vlm.local.json > 兼容旧的 WESTLAKE_API_KEY
    return (os.environ.get("B2T_VLM_API_KEY")
            or _local().get("api_key", "")
            or os.environ.get("WESTLAKE_API_KEY", ""))


def base_url() -> str:
    return (os.environ.get("B2T_VLM_BASE_URL")
            or _local().get("base_url")
            or DEFAULT_BASE).rstrip("/")


def model_name() -> str:
    return (os.environ.get("B2T_VLM_MODEL")
            or _local().get("model")
            or DEFAULT_MODEL)


def is_configured() -> bool:
    return bool(api_key())


def _image_data_uri(img) -> str:
    """BGR/灰度 numpy 图 -> data URI。"""
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
    if not ok:
        raise RuntimeError("图片编码失败")
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()


def _message_text(content) -> str:
    """兼容 content 为字符串或 [{type:text,text:...}] 两种返回。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content
                       if isinstance(part, dict))
    return str(content)


def _strip_delimiters(latex: str) -> str:
    s = latex.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    s = s.strip()
    if s.startswith("$$") and s.endswith("$$"):
        s = s[2:-2]
    elif s.startswith("$") and s.endswith("$"):
        s = s[1:-1]
    return s.strip()


def parse_blocks(content: str) -> list[dict]:
    """把模型输出解析成 Block 列表;解析失败抛 ValueError。"""
    text = _strip_delimiters(content)
    starts = [i for i in (text.find("{"), text.find("[")) if i >= 0]
    if not starts:
        raise ValueError("模型输出里没有 JSON")
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[min(starts):])
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 解析失败: {exc}") from exc

    raw = obj.get("lines") if isinstance(obj, dict) else obj
    if not isinstance(raw, list):
        raise ValueError("模型返回的不是 lines 数组")

    blocks: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("type", "")).strip().lower()
        latex = _strip_delimiters(str(item.get("latex", "")))
        if not latex:
            continue
        if kind not in ("text", "formula"):
            kind = "formula" if ("\\" in latex or "^" in latex or "_" in latex) \
                else "text"
        if kind == "text":
            block = {"content": latex, "latex": escape_latex(latex)}
        else:
            block = {"content": latex, "latex": clean_latex(latex)}
        block.update({
            "order": len(blocks),
            "type": kind,
            "confidence": 0.9,
            "bbox": (0, 0, 0, 0),
        })
        blocks.append(block)
    return blocks


def transcribe_array(img) -> list[dict]:
    """BGR/灰度图 -> Block 列表。网络/接口错误抛 RuntimeError。"""
    if not is_configured():
        raise RuntimeError(
            "未配置视觉模型 API。\n"
            "请设置环境变量 B2T_VLM_API_KEY(或 WESTLAKE_API_KEY),\n"
            "可选:B2T_VLM_BASE_URL、B2T_VLM_MODEL。"
        )

    payload = {
        "model": model_name(),
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url",
                 "image_url": {"url": _image_data_uri(img)}},
            ],
        }],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    def _post(body):
        return requests.post(
            f"{base_url()}/chat/completions",
            headers={"Authorization": f"Bearer {api_key()}"},
            json=body,
            timeout=TIMEOUT,
        )

    try:
        resp = _post(payload)
        if resp.status_code == 400:      # 个别网关不支持 response_format
            payload.pop("response_format", None)
            resp = _post(payload)
    except requests.RequestException as exc:
        raise RuntimeError(f"请求失败: {exc}") from exc

    if resp.status_code != 200:
        raise RuntimeError(f"接口返回 {resp.status_code}: {resp.text[:300]}")

    try:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError) as exc:
        raise RuntimeError(f"响应格式异常: {resp.text[:300]}") from exc

    blocks = parse_blocks(_message_text(content))
    if not blocks:
        raise RuntimeError("模型没有识别出任何行")
    return blocks


def transcribe_image(image_path: str) -> list[dict]:
    """路径入口: 读图(兼容中文路径)后交给 transcribe_array。"""
    return transcribe_array(load_image(image_path))


def prepare_for_vlm(binary) -> "np.ndarray":
    """把预处理得到的二值图变成 VLM 更稳的"黑字白底"三通道图。

    preprocess() 的 binary 约定不保证极性(通常黑字白底,也可能是黑底白字);
    统一翻成黑字白底再上传,模型对这类输入最稳定。
    """
    import numpy as np

    img = binary
    if float(np.mean(img)) < 127:          # 背景偏黑 -> 字是白的,反转
        img = 255 - img
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return img
