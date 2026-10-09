"""
Builds transparent logo files from scripts/logo/logo-source.jpg (logo on pure black,
taken from the cover of the terms PDF).
Run with Pillow installed:  python3 scripts/logo/make-logos.py
Output in scripts/logo/out/: spatime-logo.png, spatime-emblem.png, spatime-favicon.png
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)

src = Image.open(os.path.join(HERE, 'logo-source.jpg')).convert('RGB')
w, h = src.size

# Black background → alpha: alpha = brightest channel, colour un-premultiplied.
px = src.load()
rgba = Image.new('RGBA', (w, h))
dst = rgba.load()
for y in range(h):
    for x in range(w):
        r, g, b = px[x, y]
        m = max(r, g, b)
        a = 0 if m < 16 else min(255, round((m - 16) / 239 * 255 * 1.04))
        if a:
            k = 255 / m
            dst[x, y] = (min(255, round(r * k)), min(255, round(g * k)), min(255, round(b * k)), a)
        else:
            dst[x, y] = (0, 0, 0, 0)

alpha = rgba.getchannel('A')
full_box = alpha.point(lambda v: 255 if v > 40 else 0).getbbox()

# Emblem = everything above the first empty row band below the circle.
rows = [sum(1 for x in range(full_box[0], full_box[2], 4) if alpha.getpixel((x, y)) > 40) for y in range(h)]
start = full_box[1] + int((full_box[3] - full_box[1]) * 0.45)
gap = next(y for y in range(start, full_box[3]) if rows[y] == 0)
emblem_box = alpha.crop((0, 0, w, gap)).point(lambda v: 255 if v > 40 else 0).getbbox()


def save(img, name, width):
    img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
    img.save(os.path.join(OUT, name), optimize=True)
    print(name, img.size)


pad = 12
logo = rgba.crop((full_box[0] - pad, full_box[1] - pad, full_box[2] + pad, full_box[3] + pad))
save(logo, 'spatime-logo.png', 800)

emblem = rgba.crop(emblem_box)
side = max(emblem.size)
square = Image.new('RGBA', (side, side), (0, 0, 0, 0))
square.paste(emblem, ((side - emblem.width) // 2, (side - emblem.height) // 2))
save(square, 'spatime-emblem.png', 256)

# Favicon: emblem on the dark brand colour, readable on light browser tabs too.
fav = Image.new('RGBA', (512, 512), (21, 18, 15, 255))
inner = square.resize((420, 420), Image.LANCZOS)
fav.alpha_composite(inner, (46, 46))
fav.save(os.path.join(OUT, 'spatime-favicon.png'), optimize=True)
print('spatime-favicon.png', fav.size)
