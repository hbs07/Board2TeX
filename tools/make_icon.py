# -*- coding: utf-8 -*-
"""tools/make_icon.py —— 生成应用图标 assets/board2tex.ico(维护: A 胡秉善)

用法:
    python tools/make_icon.py

产物:
    assets/board2tex.ico —— 圆角蓝底 + 白色 "B2T",含 16~256 多种尺寸

用途:
    - Qt 窗口图标(gui/main_window.py 启动时加载);
    - Windows 桌面快捷方式的图标(快捷方式指向同一个 .ico)。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

SIZE = 256


def main() -> None:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([6, 6, SIZE - 6, SIZE - 6], radius=56,
                           fill=(37, 99, 235, 255))

    font = None
    for path in (r"C:\Windows\Fonts\segoeuib.ttf",
                 r"C:\Windows\Fonts\arialbd.ttf"):
        try:
            font = ImageFont.truetype(path, 110)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    text = "B2T"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((SIZE - tw) / 2 - bbox[0], (SIZE - th) / 2 - bbox[1]),
              text, font=font, fill="white")

    out = os.path.join("assets", "board2tex.ico")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                         (64, 64), (128, 128), (256, 256)])
    print(f"已生成 {out}")


if __name__ == "__main__":
    main()
