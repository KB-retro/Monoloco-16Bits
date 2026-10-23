#!/usr/bin/env python3
"""Draws Monoloco Saga's own artwork: launcher icon, logo, backdrop, the three
episode badges and the touch buttons (the neon-turquoise circle of KB-retro's
other ports). Nothing here comes from the games.

    python3 android/tools/make_art.py
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1] / "app" / "src" / "main" / "res"
NODPI = ROOT / "drawable-nodpi"
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT_SEMI = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"

NEON = (50, 255, 230)
DISC = (64, 112, 108)


def font(path, size):
    return ImageFont.truetype(path, size)


def glow(layer, radius, strength=1):
    blurred = layer.filter(ImageFilter.GaussianBlur(radius))
    out = blurred
    for _ in range(strength - 1):
        out = ImageChops.add(out, blurred)
    return out


def radial_disc(size, box, inner, outer):
    """A disc with a soft radial shade from inner (centre) to outer (edge)."""
    disc = Image.new("RGBA", size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    radius = (x1 - x0) / 2
    steps = 48
    draw = ImageDraw.Draw(disc)
    for i in range(steps, 0, -1):
        t = i / steps
        r = radius * t
        color = tuple(int(inner[c] + (outer[c] - inner[c]) * t) for c in range(3)) + (255,)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    return disc


def neon_frame(size, shape, box, radius=None):
    """The shared button body: dark shaded fill, thick neon rim and its glow."""
    w, h = size
    base = Image.new("RGBA", size, (0, 0, 0, 0))
    rim = Image.new("RGBA", size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim)
    if shape == "circle":
        rd.ellipse(box, outline=NEON + (255,), width=max(6, w // 48))
        body = radial_disc(size, box, (104, 150, 146), (70, 110, 106))
        mask = Image.new("L", size, 0)
        ImageDraw.Draw(mask).ellipse(box, fill=255)
    else:
        rd.rounded_rectangle(box, radius=radius, outline=NEON + (255,), width=max(6, h // 20))
        body = Image.new("RGBA", size, (0, 0, 0, 0))
        bd = ImageDraw.Draw(body)
        x0, y0, x1, y1 = box
        for i in range(24):
            t = i / 23
            color = (int(96 - 28 * t), int(142 - 34 * t), int(138 - 34 * t), 255)
            inset = t * (y1 - y0) * 0.02
            bd.rounded_rectangle((x0 + inset, y0 + inset + t * (y1 - y0) * 0.0, x1 - inset, y1 - inset),
                                 radius=radius, fill=color)
        mask = Image.new("L", size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)
    base.paste(body, (0, 0), mask)
    halo = glow(rim, w / 28, 3)
    out = Image.alpha_composite(halo, base)
    return Image.alpha_composite(out, rim)


def glyph_text(image, text, size, color=NEON, offset=(0, 0)):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(FONT_BOLD, size)
    bbox = d.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (image.size[0] - tw) / 2 - bbox[0] + offset[0]
    y = (image.size[1] - th) / 2 - bbox[1] + offset[1]
    d.text((x, y), text, font=f, fill=color + (255,))
    soft = glow(layer, size / 18)
    image.alpha_composite(soft)
    image.alpha_composite(layer)


def touch_round(name, letter):
    size = (512, 512)
    img = neon_frame(size, "circle", (64, 64, 448, 448))
    glyph_text(img, letter, 200, offset=(0, -6))
    img.save(NODPI / f"touch_{name}.png")


def touch_pill(name, text, width=640, height=320):
    size = (width, height)
    pad = 40
    img = neon_frame(size, "pill", (pad, pad, width - pad, height - pad), radius=(height - 2 * pad) // 2)
    glyph_text(img, text, int(height * (0.42 if len(text) <= 2 else 0.30)))
    img.save(NODPI / f"touch_{name}.png")


def touch_dpad():
    size = (640, 640)
    img = neon_frame(size, "circle", (56, 56, 584, 584))
    cross = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(cross)
    c, arm, half = 320, 190, 62
    d.rounded_rectangle((c - half, c - arm, c + half, c + arm), radius=26, fill=(214, 236, 232, 235))
    d.rounded_rectangle((c - arm, c - half, c + arm, c + half), radius=26, fill=(214, 236, 232, 235))
    # Arrow tips in neon on each arm.
    for angle in range(0, 360, 90):
        a = math.radians(angle)
        tip = (c + math.cos(a) * (arm - 24), c - math.sin(a) * (arm - 24))
        left = (c + math.cos(a + 2.5) * 42 + math.cos(a) * (arm - 70),
                c - math.sin(a + 2.5) * 42 - math.sin(a) * (arm - 70))
        right = (c + math.cos(a - 2.5) * 42 + math.cos(a) * (arm - 70),
                 c - math.sin(a - 2.5) * 42 - math.sin(a) * (arm - 70))
        d.polygon([tip, left, right], fill=(40, 120, 112, 255))
    img.alpha_composite(glow(cross, 6))
    img.alpha_composite(cross)
    img.save(NODPI / "touch_dpad.png")


# ── Logo, badges, backdrop ──────────────────────────────────────────────────────────────────────

def outlined_text(draw_image, xy, text, f, fill_top, fill_bottom, outline, stroke):
    """Text with a vertical gradient fill, a thick outline and a drop shadow."""
    w, h = draw_image.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text(xy, text, font=f, fill=255)
    stroke_mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(stroke_mask).text(xy, text, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 170), (0, 0), stroke_mask.filter(ImageFilter.GaussianBlur(stroke)))
    draw_image.alpha_composite(shadow, (stroke // 2, stroke))
    edge = Image.new("RGBA", (w, h), outline + (255,))
    draw_image.paste(edge, (0, 0), stroke_mask)
    gradient = Image.new("RGBA", (w, h))
    gd = ImageDraw.Draw(gradient)
    bbox = mask.getbbox() or (0, 0, w, h)
    for y in range(h):
        t = min(1, max(0, (y - bbox[1]) / max(1, bbox[3] - bbox[1])))
        gd.line([(0, y), (w, y)], fill=tuple(int(fill_top[c] + (fill_bottom[c] - fill_top[c]) * t) for c in range(3)) + (255,))
    draw_image.paste(gradient, (0, 0), mask)


def logo():
    w, h = 1400, 340
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    big = font(FONT_BOLD, 190)
    d = ImageDraw.Draw(img)
    text = "MONOLOCO"
    bbox = d.textbbox((0, 0), text, font=big)
    x = (w - (bbox[2] - bbox[0])) / 2 - bbox[0]
    outlined_text(img, (x, 10), text, big, (255, 226, 92), (240, 128, 24), (52, 26, 6), 14)
    small = font(FONT_BOLD, 96)
    text = "S A G A"
    bbox = d.textbbox((0, 0), text, font=small)
    x = (w - (bbox[2] - bbox[0])) / 2 - bbox[0]
    outlined_text(img, (x, 222), text, small, (120, 255, 214), (30, 190, 160), (6, 40, 34), 9)
    img = img.crop(img.getbbox())
    img.save(NODPI / "launcher_logo.png")


def badge(game, top, bottom, accent, scene):
    w, h = 704, 400
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((8, 8, w - 8, h - 8), radius=40, fill=255)
    bg = Image.new("RGBA", (w, h))
    bd = ImageDraw.Draw(bg)
    for y in range(h):
        t = y / h
        bd.line([(0, y), (w, y)], fill=tuple(int(top[c] + (bottom[c] - top[c]) * t) for c in range(3)) + (255,))
    scene(bd, w, h)
    img.paste(bg, (0, 0), mask)
    ImageDraw.Draw(img).rounded_rectangle((8, 8, w - 8, h - 8), radius=40, outline=accent + (255,), width=10)
    numeral = font(FONT_BOLD, 270)
    d = ImageDraw.Draw(img)
    bbox = d.textbbox((0, 0), str(game), font=numeral)
    outlined_text(img, (w - 60 - (bbox[2] - bbox[0]) - bbox[0], (h - (bbox[3] - bbox[1])) / 2 - bbox[1]),
                  str(game), numeral, (255, 236, 120), (244, 140, 30), (40, 20, 4), 14)
    # Each game is plain "Monoloco N"; "Saga" belongs only to the launcher's title.
    label = font(FONT_BOLD, 66)
    outlined_text(img, (44, 44), "MONOLOCO", label, (255, 255, 255), (220, 232, 228), (10, 20, 18), 6)
    img.save(NODPI / f"game{game}_logo.png")


def jungle_scene(d, w, h):
    rng = random.Random(1)
    d.ellipse((w * 0.08, h * 0.45, w * 0.38, h * 0.95), fill=(255, 214, 110, 255))
    for layer, color in enumerate([(30, 96, 56), (18, 70, 40), (10, 46, 26)]):
        base = h * (0.62 + layer * 0.1)
        points = [(0, h)]
        for x in range(0, w + 40, 40):
            points.append((x, base - 40 * math.sin(x / 70 + layer) - rng.randint(0, 20)))
        points.append((w, h))
        d.polygon(points, fill=color + (255,))
    for px in (w * 0.18, w * 0.5):
        d.line([(px, h), (px + 20, h * 0.35)], fill=(12, 34, 20, 255), width=14)
        for a in range(0, 360, 50):
            r = math.radians(a)
            d.line([(px + 20, h * 0.35), (px + 20 + 90 * math.cos(r), h * 0.35 + 40 * math.sin(r) + 20)],
                   fill=(14, 60, 30, 255), width=16)


def pirate_scene(d, w, h):
    d.ellipse((w * 0.1, h * 0.18, w * 0.3, h * 0.48), fill=(250, 240, 210, 255))
    for i in range(6):
        y = h * (0.7 + i * 0.05)
        d.rectangle((0, y, w, h), fill=(40 + i * 6, 30 + i * 4, 90 - i * 8, 255))
    d.polygon([(w * 0.12, h * 0.72), (w * 0.52, h * 0.72), (w * 0.46, h * 0.84), (w * 0.18, h * 0.84)],
              fill=(46, 22, 16, 255))
    d.line([(w * 0.32, h * 0.72), (w * 0.32, h * 0.3)], fill=(46, 22, 16, 255), width=10)
    d.polygon([(w * 0.33, h * 0.32), (w * 0.47, h * 0.5), (w * 0.33, h * 0.62)], fill=(214, 200, 176, 255))


def north_scene(d, w, h):
    rng = random.Random(3)
    for i in range(40):
        x, y = rng.randint(0, w), rng.randint(0, int(h * 0.5))
        d.ellipse((x, y, x + 5, y + 5), fill=(240, 250, 255, 255))
    for layer, color in enumerate([(150, 190, 220), (100, 150, 196), (60, 104, 156)]):
        base = h * (0.55 + layer * 0.12)
        points = [(0, h)]
        for x in range(0, w + 80, 80):
            peak = base - (90 if (x // 80 + layer) % 2 == 0 else 20)
            points.append((x, peak))
        points.append((w, h))
        d.polygon(points, fill=color + (255,))


def backdrop():
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=(int(14 + 40 * (1 - t)), int(52 + 60 * (1 - t)), int(40 + 30 * (1 - t))))
    sun = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sun).ellipse((w * 0.62, h * 0.12, w * 0.82, h * 0.48), fill=(255, 214, 120, 200))
    img.paste(sun.filter(ImageFilter.GaussianBlur(40)), (0, 0), sun.filter(ImageFilter.GaussianBlur(40)))
    rng = random.Random(7)
    for layer, color in enumerate([(26, 84, 50), (16, 62, 38), (8, 40, 24), (4, 22, 14)]):
        base = h * (0.5 + layer * 0.12)
        points = [(0, h)]
        for x in range(0, w + 60, 60):
            points.append((x, base - 70 * math.sin(x / 180 + layer * 1.7) - rng.randint(0, 30)))
        points.append((w, h))
        d.polygon(points, fill=color)
        for _ in range(3 + layer):
            px = rng.randint(0, w)
            top = base - rng.randint(200, 380)
            d.line([(px, base + 40), (px + 30, top)], fill=tuple(max(0, c - 6) for c in color), width=18 + layer * 4)
            for a in range(-20, 200, 34):
                r = math.radians(a)
                d.line([(px + 30, top), (px + 30 + 170 * math.cos(r), top - 60 * math.sin(r) + 70)],
                       fill=tuple(max(0, c - 4) for c in color), width=22 + layer * 4)
    vines = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vines)
    for i in range(9):
        x = rng.randint(0, w)
        length = rng.randint(200, 520)
        vd.line([(x, 0), (x + rng.randint(-30, 30), length)], fill=(6, 30, 18, 230), width=8)
        for y in range(20, length, 46):
            vd.ellipse((x - 18, y, x + 18, y + 22), fill=(10, 56, 30, 230))
    img.paste(vines, (0, 0), vines)
    img.save(NODPI / "launcher_backdrop.jpg", quality=88)


def monkey_icon(size):
    """The launcher icon: a cheeky monkey face on a jungle-green disc."""
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    brown, light, dark = (120, 70, 34, 255), (238, 196, 150, 255), (40, 20, 8, 255)
    d.ellipse((s * 0.12, s * 0.34, s * 0.34, s * 0.58), fill=brown)
    d.ellipse((s * 0.66, s * 0.34, s * 0.88, s * 0.58), fill=brown)
    d.ellipse((s * 0.17, s * 0.39, s * 0.29, s * 0.53), fill=light)
    d.ellipse((s * 0.71, s * 0.39, s * 0.83, s * 0.53), fill=light)
    d.ellipse((s * 0.22, s * 0.2, s * 0.78, s * 0.78), fill=brown)
    d.pieslice((s * 0.3, s * 0.22, s * 0.7, s * 0.5), 180, 360, fill=(90, 50, 22, 255))
    d.ellipse((s * 0.3, s * 0.38, s * 0.5, s * 0.6), fill=light)
    d.ellipse((s * 0.5, s * 0.38, s * 0.7, s * 0.6), fill=light)
    d.ellipse((s * 0.3, s * 0.5, s * 0.7, s * 0.76), fill=light)
    d.ellipse((s * 0.37, s * 0.44, s * 0.45, s * 0.53), fill=dark)
    d.ellipse((s * 0.55, s * 0.44, s * 0.63, s * 0.53), fill=dark)
    d.ellipse((s * 0.39, s * 0.455, s * 0.415, s * 0.48), fill=(255, 255, 255, 255))
    d.ellipse((s * 0.57, s * 0.455, s * 0.595, s * 0.48), fill=(255, 255, 255, 255))
    d.ellipse((s * 0.45, s * 0.57, s * 0.48, s * 0.6), fill=dark)
    d.ellipse((s * 0.52, s * 0.57, s * 0.55, s * 0.6), fill=dark)
    d.arc((s * 0.4, s * 0.58, s * 0.6, s * 0.71), 20, 160, fill=dark, width=max(2, s // 64))
    return img


def icons():
    densities = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
    for name, scale in densities.items():
        folder = ROOT / f"mipmap-{name}"
        folder.mkdir(parents=True, exist_ok=True)
        adaptive = int(108 * scale)
        background = Image.new("RGBA", (adaptive, adaptive))
        bd = ImageDraw.Draw(background)
        for y in range(adaptive):
            t = y / adaptive
            bd.line([(0, y), (adaptive, y)], fill=(int(24 + 20 * (1 - t)), int(110 + 50 * (1 - t)), int(70 + 30 * (1 - t)), 255))
        background.save(folder / "ic_launcher_background.png")
        foreground = Image.new("RGBA", (adaptive, adaptive), (0, 0, 0, 0))
        face = monkey_icon(int(adaptive * 0.62))
        foreground.alpha_composite(face, ((adaptive - face.size[0]) // 2, (adaptive - face.size[1]) // 2))
        foreground.save(folder / "ic_launcher_foreground.png")
        legacy = int(48 * scale)
        icon = Image.new("RGBA", (legacy, legacy), (0, 0, 0, 0))
        mask = Image.new("L", (legacy, legacy), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, legacy - 1, legacy - 1), fill=255)
        full = Image.alpha_composite(background, foreground).resize((legacy, legacy), Image.LANCZOS)
        icon.paste(full, (0, 0), mask)
        icon.save(folder / "ic_launcher.png")


def main():
    NODPI.mkdir(parents=True, exist_ok=True)
    for name, letter in (("a", "A"), ("b", "B"), ("x", "X"), ("y", "Y")):
        touch_round(name, letter)
    touch_pill("l", "L")
    touch_pill("r", "R")
    touch_pill("select", "SELECT")
    touch_pill("start", "START")
    touch_dpad()
    logo()
    badge(1, (60, 150, 90), (14, 60, 32), (255, 200, 60), jungle_scene)
    badge(2, (70, 40, 110), (20, 16, 50), (240, 90, 70), pirate_scene)
    badge(3, (120, 170, 220), (30, 60, 110), (180, 240, 255), north_scene)
    backdrop()
    icons()


if __name__ == "__main__":
    main()
