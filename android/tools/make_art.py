#!/usr/bin/env python3
"""Draws Monoloco Saga's artwork: the launcher icon, logo, backdrop and the
three game badges come from KB-retro's cover art (android/art/); the touch buttons are drawn here with the
neon-turquoise circle of KB-retro's other ports. Nothing comes from the games.

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


ART = Path(__file__).resolve().parents[1] / "art"
# KB-retro's cover art: the icon card on the left, the poster on the right.
COVER = ART / "cover-source.jpg"
LOGO_CUT = ART / "logo-cut.png"       # its logo, cut from the sky behind it
ICON = (60, 230, 755, 925)            # logo, explorer and aviator from the card
SCENE_BACKDROP = (880, 380, 1500, 668)  # the poster's islands, waterfalls and sunset
# One hero per game, facing the number; the explorer is mirrored to look right.
SCENES = {1: ((270, 570, 710, 820), False), 2: ((135, 560, 575, 810), True), 3: ((982, 660, 1382, 887), False)}


def cover_crop(box):
    return Image.open(COVER).convert("RGB").crop(box)


def cover_fit(image, size):
    """Scales to cover size and crops the middle."""
    w, h = size
    scale = max(w / image.width, h / image.height)
    image = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left, top = (image.width - w) // 2, (image.height - h) // 2
    return image.crop((left, top, left + w, top + h))


def logo():
    Image.open(LOGO_CUT).convert("RGBA").save(NODPI / "launcher_logo.png")


def badge(game, accent):
    w, h = 704, 400
    box, mirror = SCENES[game]
    scene = cover_fit(cover_crop(box), (w, h)).convert("RGBA")
    if mirror:
        scene = scene.transpose(Image.FLIP_LEFT_RIGHT)
    # Darker on the left, where the name sits.
    shade = Image.new("RGBA", (w, h))
    sd = ImageDraw.Draw(shade)
    for x in range(w):
        sd.line([(x, 0), (x, h)], fill=(10, 16, 8, int(170 * max(0, 1 - x / (w * 0.6)))))
    scene.alpha_composite(shade)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((8, 8, w - 8, h - 8), radius=40, fill=255)
    img.paste(scene, (0, 0), mask)
    ImageDraw.Draw(img).rounded_rectangle((8, 8, w - 8, h - 8), radius=40, outline=(92, 52, 22, 255), width=14)
    ImageDraw.Draw(img).rounded_rectangle((15, 15, w - 15, h - 15), radius=34, outline=accent + (255,), width=4)
    # "MONOLOCO" in the logo's own letters (its top half), plus the number.
    cut = Image.open(LOGO_CUT).convert("RGBA")
    word = cut.crop((0, 0, cut.width, int(cut.height * 0.47)))
    fade = Image.new("L", word.size, 255)  # soften the cut above the "SAGA" plank
    for y in range(word.height - 14, word.height):
        ImageDraw.Draw(fade).line([(0, y), (word.width, y)], fill=int(255 * (word.height - y) / 14))
    word.putalpha(ImageChops.multiply(word.getchannel("A"), fade))
    word.thumbnail((380, 200))
    img.alpha_composite(word, (32, 36))
    numeral = font(FONT_BOLD, 230)
    d = ImageDraw.Draw(img)
    bbox = d.textbbox((0, 0), str(game), font=numeral)
    outlined_text(img, (32 + (word.width - (bbox[2] - bbox[0])) / 2 - bbox[0], h - 34 - bbox[3]),
                  str(game), numeral, (255, 226, 92), (240, 128, 24), (60, 30, 8), 16)
    img.save(NODPI / f"game{game}_logo.png")


def backdrop():
    w, h = 1920, 1080
    scene = cover_fit(cover_crop(SCENE_BACKDROP), (w, h)).filter(ImageFilter.GaussianBlur(1.5))
    scene.save(NODPI / "launcher_backdrop.jpg", quality=88)


def icons():
    """The cover's icon card; its middle sits in the adaptive icon's safe zone over a blurred copy."""
    densities = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
    art = cover_crop(ICON).convert("RGBA")
    for name, scale in densities.items():
        folder = ROOT / f"mipmap-{name}"
        folder.mkdir(parents=True, exist_ok=True)
        adaptive = int(108 * scale)
        background = art.resize((adaptive, adaptive), Image.LANCZOS).filter(ImageFilter.GaussianBlur(scale * 4))
        background.save(folder / "ic_launcher_background.png")
        inner = int(adaptive * 0.70)
        sharp = art.resize((inner, inner), Image.LANCZOS)
        feather = Image.new("L", (inner, inner), 0)
        edge = max(2, inner // 24)
        ImageDraw.Draw(feather).rectangle((edge, edge, inner - edge, inner - edge), fill=255)
        sharp.putalpha(feather.filter(ImageFilter.GaussianBlur(edge / 2)))
        foreground = Image.new("RGBA", (adaptive, adaptive), (0, 0, 0, 0))
        foreground.alpha_composite(sharp, ((adaptive - inner) // 2, (adaptive - inner) // 2))
        foreground.save(folder / "ic_launcher_foreground.png")
        legacy = int(48 * scale)
        mask = Image.new("L", (legacy, legacy), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, legacy - 1, legacy - 1), radius=legacy // 6, fill=255)
        icon = Image.new("RGBA", (legacy, legacy), (0, 0, 0, 0))
        icon.paste(art.resize((legacy, legacy), Image.LANCZOS), (0, 0), mask)
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
    badge(1, (255, 200, 60))
    badge(2, (255, 150, 70))
    badge(3, (130, 230, 255))
    backdrop()
    icons()


if __name__ == "__main__":
    main()
