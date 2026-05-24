FONT_DISPLAY_NAMES = {
    "Microsoft YaHei": "微软雅黑",
    "SimSun": "宋体",
    "SimHei": "黑体",
    "KaiTi": "楷体",
    "FangSong": "仿宋",
    "Microsoft JhengHei": "微软正黑体",
    "DengXian": "等线",
    "YouYuan": "幼圆",
    "Source Han Sans SC": "思源黑体",
    "Source Han Serif SC": "思源宋体",
    "Noto Sans SC": "Noto无衬线简体",
    "Noto Serif SC": "Noto衬线简体",
    "STKaiti": "华文楷体",
    "STSong": "华文宋体",
    "STHeiti": "华文黑体",
    "STXihei": "华文细黑",
    "PMingLiU": "细明体",
    "DFKai-SB": "标楷体",
    "Arial": "Arial（英）",
    "Consolas": "Consolas（英/等宽）",
    "Segoe UI": "Segoe UI（英）",
    "Times New Roman": "Times New Roman（英）",
}

EXTRA_FONT_KEYWORDS = [
    "Noto Sans", "Noto Serif", "Source Han", "HarmonyOS",
    "文泉驿", "方正", "华文",
]


def get_chinese_fonts():
    from PyQt5.QtGui import QFontDatabase
    families = set(QFontDatabase().families())
    result = []
    for pf in FONT_DISPLAY_NAMES:
        if pf in families:
            result.append((FONT_DISPLAY_NAMES[pf], pf))
    for fname in families:
        if fname in FONT_DISPLAY_NAMES:
            continue
        for kw in EXTRA_FONT_KEYWORDS:
            if kw.lower() in fname.lower():
                result.append((fname, fname))
                break
    return result