"""Regenerate anchor.ico and anchor.png from the Unicode anchor glyph.

Not run at build time; regenerate manually if the icon ever changes:
    python assets/_generate.py
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import sys

HERE = Path(__file__).parent
SIZE = 256
COLOR = (137, 180, 250, 255)  # Catppuccin blue #89B4FA


def find_font():
    candidates = [
        "C:/Windows/Fonts/seguisym.ttf",                 # Windows (Segoe UI Symbol)
        "/System/Library/Fonts/Apple Color Emoji.ttc",    # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux fallback
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    raise SystemExit("No suitable font found to render the anchor glyph.")


def render():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(find_font(), int(SIZE * 0.78))

    glyph = "⚓"  # ⚓
    left, top, right, bottom = draw.textbbox((0, 0), glyph, font=font)
    w, h = right - left, bottom - top
    x = (SIZE - w) / 2 - left
    y = (SIZE - h) / 2 - top
    draw.text((x, y), glyph, font=font, fill=COLOR)
    return img


def main():
    img = render()
    img.save(HERE / "anchor.png")
    img.save(
        HERE / "anchor.ico",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"Wrote {HERE / 'anchor.png'} and {HERE / 'anchor.ico'}")


if __name__ == "__main__":
    main()
