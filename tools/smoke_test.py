
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
