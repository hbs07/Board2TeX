# -*- coding: utf-8 -*-
"""gui/torch_preload.py —— Windows 下的导入顺序兼容层(维护: A 胡秉善)

问题(2026-11-21 实测):
    在 Windows 上先 import PyQt5、再 import torch,会报
        OSError: [WinError 1114] Error loading "torch\\lib\\c10.dll"
    或直接 "Windows fatal exception: access violation"。
    反过来先 import torch、再 import PyQt5 就正常。

用法:
    **任何** import PyQt5 的 gui 模块,都要在 PyQt5 之前先 import 本模块:
        from gui import torch_preload  # noqa: F401  (必须早于 PyQt5)

    这样无论是先打开主窗口、还是先弹预览,都不会踩到这个顺序坑。

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

try:
    import torch  # noqa: F401  (只为提前加载 DLL,本模块不用它)
except Exception:      # 没装 torch / DLL 加载失败: 文字识别仍可用,公式识别会降级
    pass
