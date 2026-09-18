#!/usr/bin/env python3
"""生成抽象科技渐变背景图（暗色 + 磷光绿，风格统一）"""
from PIL import Image, ImageDraw, ImageFilter
import os

OUT = os.path.dirname(os.path.abspath(__file__))
BASE = (10, 15, 12)       # #0A0F0C
GREEN = (61, 240, 138)    # #3DF08A 磷光绿
TEAL = (45, 210, 160)


def canvas(w, h):
    return Image.new("RGB", (w, h), BASE)


def radial(size, cx, cy, radius, color, amax, blur=None):
    """柔和高斯光晕：中心 alpha=amax，向外衰减"""
    w, h = size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    steps = 160
    for i in range(steps, 0, -1):
        r = radius * i / steps
        a = int(amax * (1 - i / steps) ** 1.7)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=a)
    mask = mask.filter(ImageFilter.GaussianBlur(blur or max(8, radius // 18)))
    layer = Image.new("RGBA", (w, h), color + (0,))
    layer.putalpha(mask)
    return layer


def grid(img, step=120, color=(23, 33, 27)):
    d = ImageDraw.Draw(img)
    w, h = img.size
    for x in range(step, w, step):
        d.line([(x, 0), (x, h)], fill=color, width=1)
    for y in range(step, h, step):
        d.line([(0, y), (w, y)], fill=color, width=1)
    return img


def scanlines(img, gap=5, alpha=6):
    w, h = img.size
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for y in range(0, h, gap):
        d.line([(0, y), (w, y)], fill=(0, 0, 0, alpha), width=1)
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")


def noise(img, opacity=0.05):
    w, h = img.size
    n = Image.effect_noise((w, h), 18).convert("L")
    layer = Image.merge("RGBA", (n, n, n, n.point(lambda v: int(opacity * 255))))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def hshade(img, a_left=0.93, a_right=0.28):
    """水平方向暗化遮罩（烤进图里，替代 CSS overlay——遮罩进不了 PPTX）"""
    w, h = img.size
    mask = Image.new("L", (w, 1))
    for x in range(w):
        t = x / (w - 1)
        # 中点前线性 .93→.78，之后 .78→.28（近似原 CSS 渐变）
        a = a_left + (0.78 - a_left) * min(1, t / 0.48) if t < 0.48 else 0.78 + (a_right - 0.78) * ((t - 0.48) / 0.52)
        mask.putpixel((x, 0), int(a * 255))
    mask = mask.resize((w, h))
    black = Image.new("RGBA", (w, h), (5, 8, 6, 255))
    black.putalpha(mask)
    return Image.alpha_composite(img.convert("RGBA"), black).convert("RGB")


def vshade(img, stops=((0.0, 0.92), (0.55, 0.55), (1.0, 0.75))):
    """垂直方向暗化遮罩（分段线性）"""
    w, h = img.size
    mask = Image.new("L", (1, h))
    for y in range(h):
        t = y / (h - 1)
        for (t0, a0), (t1, a1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                a = a0 + (a1 - a0) * (t - t0) / (t1 - t0)
                break
        mask.putpixel((0, y), int(a * 255))
    mask = mask.resize((w, h))
    black = Image.new("RGBA", (w, h), (5, 8, 6, 255))
    black.putalpha(mask)
    return Image.alpha_composite(img.convert("RGBA"), black).convert("RGB")


def finish(img):
    return noise(scanlines(img))


# ── 封面：右上主光晕 + 左下副光晕 + 烤入水平暗化 ──────────
img = canvas(1920, 1080)
img = grid(img)
img = Image.alpha_composite(img.convert("RGBA"),
                            radial((1920, 1080), 1520, 210, 780, GREEN, 64)).convert("RGB")
img = Image.alpha_composite(img.convert("RGBA"),
                            radial((1920, 1080), 190, 980, 600, TEAL, 38)).convert("RGB")
img = hshade(img)
finish(img).save(os.path.join(OUT, "grad-cover.png"), optimize=True)

# ── 横幅带：中部光带 ─────────────────────────────────────────
img = canvas(1920, 420)
img = grid(img, step=120)
img = Image.alpha_composite(img.convert("RGBA"),
                            radial((1920, 420), 960, 210, 640, GREEN, 46)).convert("RGB")
finish(img).save(os.path.join(OUT, "grad-band.png"), optimize=True)

# ── 结尾页：中央偏下大光晕 + 烤入垂直暗化 ──────────────────
img = canvas(1920, 1080)
img = grid(img)
img = Image.alpha_composite(img.convert("RGBA"),
                            radial((1920, 1080), 960, 760, 880, GREEN, 56)).convert("RGB")
img = Image.alpha_composite(img.convert("RGBA"),
                            radial((1920, 1080), 300, 170, 460, TEAL, 26)).convert("RGB")
img = vshade(img)
finish(img).save(os.path.join(OUT, "grad-cta.png"), optimize=True)

for f in ("grad-cover.png", "grad-band.png", "grad-cta.png"):
    p = os.path.join(OUT, f)
    print(f, os.path.getsize(p) // 1024, "KB")
