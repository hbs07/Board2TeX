# -*- coding: utf-8 -*-
r"""
Board2TeX 环境验证脚本
======================
验证本机能否安装并运行项目依赖:
  - OpenCV / numpy / matplotlib / Pillow (图像处理)
  - paddlepaddle + paddleocr            (中文/印刷文字 OCR)
  - pix2tex (LaTeX-OCR) + torch         (公式 -> LaTeX)
  - PyQt5                               (桌面界面)

用法(在本目录下用系统 Python 执行):
  python check_env.py              完整检查: 建 venv + 装依赖 + import + 模型冒烟测试
  python check_env.py --fast       快速检查: 只装依赖 + import, 不下载模型权重(推荐先跑这个)
  python check_env.py --clean      先删除 .venv_b2t 再重建
  python check_env.py --no-mirror  不使用清华 PyPI 镜像(默认使用)

说明:
  - 本脚本在纯英文路径(LOCALAPPDATA)下创建独立虚拟环境 .venv_b2t(约 2 GB), 不污染系统 Python
  - 避免"项目在中文路径 + torch/paddle DLL 加载失败"的 Windows 经典坑
  - 冒烟测试首次运行会从 hf-mirror.com 下载模型权重(约 0.5~1 GB)
  - 结果逐项打印 [OK]/[FAIL], 并写入 env_check_report.txt
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except Exception:
    pass

BASE = Path(__file__).resolve().parent
REPORT_PATH = BASE / "env_check_report.txt"
SMOKE_PATH = BASE / "smoke_test.py"
TSINGHUA = "https://pypi.tuna.tsinghua.edu.cn/simple"

# venv 默认放在纯英文路径(如 C:\Users\xxx\AppData\Local\Board2TeX\.venv_b2t),
# 避免中文路径导致 torch / paddle 的 DLL 加载失败; 可用 --venv-dir 覆盖
_default_root = Path(os.environ.get("LOCALAPPDATA") or Path.home())
VENV_DIR = _default_root / "Board2TeX" / ".venv_b2t"

PKGS = [
    "numpy",
    "pillow",
    "matplotlib",
    "opencv-contrib-python",
    "PyQt5>=5.15",
    "paddlepaddle>=3.0,<4",
    "paddleocr>=3.0,<4",
    "transformers<5",
    "pix2tex",
]

IMPORTS = ["numpy", "cv2", "PIL", "matplotlib", "PyQt5",
           "torch", "paddle", "paddleocr", "pix2tex.cli"]
CRITICAL = {"cv2", "paddle", "paddleocr", "pix2tex.cli"}

results = []

SMOKE_CODE = r'''
# -*- coding: utf-8 -*-
import json, os
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
res = {}

from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

timg = Image.new("RGB", (820, 160), "white")
d = ImageDraw.Draw(timg)
font = None
for fp in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf",
           r"C:\Windows\Fonts\simsun.ttc", r"C:\Windows\Fonts\arial.ttf"]:
    try:
        font = ImageFont.truetype(fp, 46)
        break
    except Exception:
        pass
if font is None:
    font = ImageFont.load_default()
d.text((30, 50), u"板书识别测试: 设函数 f(x) 可导", fill="black", font=font)
timg.save("test_text.png")

fimg = plt.figure(figsize=(5, 1.4))
fimg.text(0.5, 0.5, r"$\int_0^1 x^2 \, dx = \frac{1}{3}$",
          ha="center", va="center", fontsize=24)
fimg.savefig("test_formula.png", dpi=160)
plt.close(fimg)
res["images"] = "OK"

try:
    os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
    from paddleocr import PaddleOCR
    got = None
    try:
        ocr = PaddleOCR(use_doc_orientation_classify=False,
                        use_doc_unwarping=False,
                        use_textline_orientation=False,
                        enable_mkldnn=False)
        out = ocr.predict("test_text.png")
        r0 = out[0]
        got = list(r0["rec_texts"])
    except Exception:
        ocr = PaddleOCR(lang="ch", use_angle_cls=False)
        out = ocr.ocr("test_text.png", cls=False)
        got = [seg[1][0] for line in (out or []) for seg in (line or [])]
    res["paddleocr"] = {"status": "OK",
                        "text": [str(t) for t in (got or [])][:10]}
except Exception as e:
    res["paddleocr"] = {"status": "FAIL",
                        "error": type(e).__name__ + ": " + str(e)[:200]}

try:
    from pix2tex.cli import LatexOCR
    from PIL import Image
    model = LatexOCR()
    latex = model(Image.open("test_formula.png").convert("RGB"))
    res["pix2tex"] = {"status": "OK", "latex": str(latex)}
except Exception as e:
    res["pix2tex"] = {"status": "FAIL",
                      "error": type(e).__name__ + ": " + str(e)[:200]}

print("SMOKE_JSON:" + json.dumps(res, ensure_ascii=False))
'''


def log(step, status, detail=""):
    mark = {"OK": "[OK]  ", "FAIL": "[FAIL]", "SKIP": "[SKIP]", "WARN": "[WARN]"}[status]
    line = f"{mark} {step}" + (f"  --  {detail}" if detail else "")
    print(line, flush=True)
    results.append((step, status, detail))


def run(cmd, timeout=None):
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=env, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"


def venv_python():
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def phase0():
    v = sys.version_info
    log("Python 版本", "OK", sys.version.split()[0])
    if not (3, 9) <= v < (3, 13):
        log("Python 兼容性", "WARN",
            f"{v.major}.{v.minor} 对 paddlepaddle 可能无轮子, 将尝试用 uv 提供 Python 3.12")
    return True


def phase1(clean=False):
    if clean and VENV_DIR.exists():
        shutil.rmtree(VENV_DIR, ignore_errors=True)
        log("清理旧虚拟环境", "OK")
    if venv_python().exists():
        log("虚拟环境", "SKIP", f"复用已存在的 {VENV_DIR}")
        return True
    v = sys.version_info
    uv = shutil.which("uv")
    if (not (3, 9) <= v < (3, 13)) and uv:
        rc, out = run(["uv", "venv", "--python", "3.12", str(VENV_DIR)], timeout=600)
        if rc == 0 and venv_python().exists():
            log("虚拟环境", "OK", "uv 提供 Python 3.12")
            return True
        log("uv 建 Python 3.12", "WARN", "失败, 回退到系统 Python")
    rc, out = run([sys.executable, "-m", "venv", str(VENV_DIR)], timeout=300)
    if rc == 0 and venv_python().exists():
        log("虚拟环境", "OK", str(VENV_DIR))
        return True
    log("虚拟环境", "FAIL", (out or "").strip()[-300:])
    return False


def phase2(use_mirror=True):
    index = TSINGHUA if use_mirror else None
    print("... 正在安装依赖(约 1.5~2 GB, 视网速 3~15 分钟, 请勿关闭) ...", flush=True)
    if shutil.which("uv"):
        cmd = ["uv", "pip", "install", "--python", str(venv_python())]
        if index:
            cmd += ["--index-url", index]
        cmd += PKGS
        rc, out = run(cmd, timeout=2400)
        if rc == 0:
            log("依赖安装(uv)", "OK")
            return True
        log("依赖安装(uv)", "WARN", "失败, 自动改用 venv 内 pip 重试")
    rc, out = run([str(venv_python()), "-m", "pip", "--version"], timeout=120)
    if rc != 0:
        run([sys.executable, "-m", "venv", str(VENV_DIR), "--upgrade-deps"], timeout=300)
    cmd = [str(venv_python()), "-m", "pip", "install", "--prefer-binary"]
    if index:
        cmd += ["--index-url", index]
    cmd += PKGS
    rc, out = run(cmd, timeout=2400)
    if rc == 0:
        log("依赖安装(pip)", "OK")
        return True
    tail = out.strip().splitlines()[-1] if out.strip() else "无输出"
    log("依赖安装", "FAIL", tail[:200])
    return False


def phase2b_repair_cv2():
    """pix2tex 会带上 opencv-python-headless(可能 5.x), 与 paddlex 需要的
    opencv-contrib-python(4.x) 相互覆盖导致 cv2 版本混乱; 这里统一修复为 contrib 4.x。"""
    code = "import cv2; print('CV2_OK', cv2.__version__)"
    rc, out = run([str(venv_python()), "-c", code], timeout=300)
    ver = ""
    if "CV2_OK" in out:
        ver = out.strip().splitlines()[-1].split(" ")[-1]
        if ver.startswith("4"):
            log("cv2 健康检查", "OK", f"cv2 {ver} (contrib 4.x)")
            return True
        log("cv2 健康检查", "WARN",
            f"cv2 为 {ver} (pix2tex 带入的 headless 5.x 覆盖了 contrib), 开始自动修复")
    else:
        log("cv2 健康检查", "WARN", "cv2 无法导入(多版本互相覆盖), 开始自动修复")
    run([str(venv_python()), "-m", "pip", "uninstall", "-y",
         "opencv-python", "opencv-contrib-python", "opencv-python-headless",
         "opencv-contrib-python-headless"], timeout=600)
    if shutil.which("uv"):
        cmd = ["uv", "pip", "install", "--reinstall", "--python", str(venv_python()),
               "--index-url", TSINGHUA, "opencv-contrib-python<5"]
    else:
        cmd = [str(venv_python()), "-m", "pip", "install", "--prefer-binary",
               "--index-url", TSINGHUA, "opencv-contrib-python<5"]
    rc, out = run(cmd, timeout=1200)
    rc2, out2 = run([str(venv_python()), "-c", code], timeout=300)
    if rc2 == 0 and "CV2_OK" in out2 and out2.strip().splitlines()[-1].split(" ")[-1].startswith("4"):
        log("cv2 自动修复", "OK", "已统一为 opencv-contrib-python 4.x")
        return True
    log("cv2 自动修复", "FAIL", (out2 or out).strip().splitlines()[-1][:200])
    return False


def phase3():
    all_ok = True
    for m in IMPORTS:
        code = (f"import importlib\nmod = importlib.import_module({m!r})\n"
                f"print('IMPORT_OK', str(getattr(mod, '__version__', '?')))")
        rc, out = run([str(venv_python()), "-c", code], timeout=600)
        ok = rc == 0 and "IMPORT_OK" in out
        ver = ""
        if ok:
            ver = [l for l in out.splitlines() if l.startswith("IMPORT_OK")][-1].split(" ", 1)[-1]
        else:
            err = out.strip().splitlines()[-1] if out.strip() else "无输出"
            log(f"import {m}", "FAIL", err[:180])
            if m in CRITICAL:
                all_ok = False
            continue
        log(f"import {m}", "OK", ver)
    return all_ok


def phase4():
    SMOKE_PATH.write_text(SMOKE_CODE, encoding="utf-8")
    print("... 冒烟测试: 首次会下载模型权重(约 0.5~1 GB), 请耐心等待 ...", flush=True)
    rc, out = run([str(venv_python()), str(SMOKE_PATH)], timeout=1800)
    if rc == 124:
        log("模型冒烟测试", "FAIL", "超时(30 分钟), 多为模型下载过慢; 可重跑本脚本或检查网络")
        return
    payload = None
    for line in out.splitlines():
        if line.startswith("SMOKE_JSON:"):
            payload = line.split("SMOKE_JSON:", 1)[1]
    if payload is None:
        log("模型冒烟测试", "FAIL", f"未获得结果 (exit={rc}): {out.strip()[-200:]}")
        return
    res = json.loads(payload)
    log("生成测试图片", "OK" if res.get("images") == "OK" else "FAIL")
    p = res.get("paddleocr", {})
    log("PaddleOCR 识别中文", p.get("status", "FAIL"),
        str(p.get("text", p.get("error", "")))[:150])
    x = res.get("pix2tex", {})
    log("LaTeX-OCR 识别公式", x.get("status", "FAIL"),
        str(x.get("latex", x.get("error", "")))[:150])


def write_report(t0):
    n_ok = sum(1 for _, s, _ in results if s == "OK")
    n_fail = sum(1 for _, s, _ in results if s == "FAIL")
    n_skip = sum(1 for _, s, _ in results if s == "SKIP")
    n_warn = sum(1 for _, s, _ in results if s == "WARN")
    lines = [
        "Board2TeX 环境验证报告",
        f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}    耗时: {time.time() - t0:.0f}s",
        "-" * 64,
    ]
    for step, st, detail in results:
        lines.append(f"{st:5} | {step}" + (f" | {detail}" if detail else ""))
    lines += [
        "-" * 64,
        f"汇总: OK={n_ok}  FAIL={n_fail}  SKIP={n_skip}  WARN={n_warn}",
        f"虚拟环境: {VENV_DIR}",
        "激活(PowerShell): .\\.venv_b2t\\Scripts\\Activate.ps1",
        "直接使用: & .\\.venv_b2t\\Scripts\\python.exe 你的脚本.py",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n报告已写入: {REPORT_PATH}", flush=True)


def main():
    t0 = time.time()
    ap = argparse.ArgumentParser(description="Board2TeX 环境验证")
    ap.add_argument("--fast", action="store_true", help="跳过模型下载的冒烟测试")
    ap.add_argument("--clean", action="store_true", help="删除旧 venv 后重建")
    ap.add_argument("--no-mirror", action="store_true", help="不使用清华镜像")
    ap.add_argument("--venv-dir", default=None,
                    help="虚拟环境位置(默认放在 LOCALAPPDATA 下的纯英文路径)")
    args = ap.parse_args()

    global VENV_DIR
    if args.venv_dir:
        VENV_DIR = Path(args.venv_dir).expanduser().resolve()

    print("=" * 64)
    print("Board2TeX 环境验证 开始")
    print("=" * 64, flush=True)

    ok = phase0()
    ok = phase1(args.clean) and ok
    ok = phase2(not args.no_mirror) and ok
    ok = phase2b_repair_cv2() and ok
    ok = phase3() and ok
    if ok and not args.fast:
        phase4()

    n_fail = sum(1 for _, s, _ in results if s == "FAIL")
    write_report(t0)
    print("=" * 64)
    if n_fail == 0:
        print("结论: 环境验证通过, 可以开始项目开发 [PASS]")
    else:
        print(f"结论: 存在 {n_fail} 项失败, 请查看上方 [FAIL] 条目与报告文件 [FAIL]")
    print("=" * 64)
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == "__main__":
    main()
