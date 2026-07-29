"""Generate a modern Fenerbahçe-colored score graphic for an Instagram Story.

Layout (top to bottom, 1080x1920 - Story aspect ratio):
    label ("ILK YARI")
    opponent - small, quiet (logo + name)
    SCORE - big, sits between the two teams
    Fenerbahçe - large, glowing logo + bold name (the "grand" side)

Home/away only affects which score number is on the left vs. right; which
side is visually "grand" is always Fenerbahçe, regardless of home/away.

Usage:
    python scripts/generate_score_graphic.py \
        --opponent "GORNIK ZABRZE" --opponent-logo scripts/assets/gornik_zabrze_logo.png \
        --fener-score 1 --opponent-score 0 --fener-home false \
        --label "ILK YARI" \
        --target story \
        --out content_library/media/score.jpg

Standalone script, not part of the insta_man package - only needed for
one-off score-graphic posts, not the general publishing pipeline.

Logo licensing note: the Fenerbahçe crest bundled in scripts/assets is
Wikipedia non-free "fair use" material (trademarked, not freely licensed
for reuse) - used here at the account owner's own risk/discretion for a
personal fan account. The opponent crest license varies per club; check
before reusing this script for a different match.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

NAVY = (10, 22, 58)
NAVY_DARK = (5, 12, 34)
YELLOW = (255, 209, 0)
WHITE = (245, 245, 245)
MUTED = (150, 163, 196)

W, H = 1080, 1920
FONT_DIR = Path("C:/Windows/Fonts")
ASSETS_DIR = Path(__file__).parent / "assets"
FENER_LOGO = ASSETS_DIR / "fenerbahce_logo.png"


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def _centered_text(draw: ImageDraw.ImageDraw, y: int, text: str, font, fill, tracking: int = 0) -> float:
    if tracking:
        widths = [draw.textlength(ch, font=font) for ch in text]
        total = sum(widths) + tracking * (len(text) - 1)
        x = (W - total) / 2
        for ch, w in zip(text, widths):
            draw.text((x, y), ch, font=font, fill=fill)
            x += w + tracking
        return total
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((W - w) / 2, y), text, font=font, fill=fill)
    return w


def _line_fan(overlay: ImageDraw.ImageDraw, origin: tuple[int, int], angle_start: float, angle_end: float,
              count: int, length: int, color: tuple[int, int, int], alpha_start: int, alpha_end: int,
              width: int = 2) -> None:
    ox, oy = origin
    for i in range(count):
        t = i / max(count - 1, 1)
        angle = math.radians(angle_start + (angle_end - angle_start) * t)
        alpha = int(alpha_start + (alpha_end - alpha_start) * t)
        x2 = ox + length * math.cos(angle)
        y2 = oy + length * math.sin(angle)
        overlay.line([(ox, oy), (x2, y2)], fill=(*color, alpha), width=width)


def _chevrons(overlay: ImageDraw.ImageDraw, cx: int, y: int, direction: int, color: tuple[int, int, int],
              alpha: int, count: int = 3, gap: int = 16, size: int = 10) -> None:
    for i in range(count):
        x = cx + direction * (i * gap)
        pts = [
            (x - direction * size, y - size),
            (x, y),
            (x - direction * size, y + size),
        ]
        overlay.line(pts, fill=(*color, alpha), width=3, joint="curve")


def _paste_logo(img: Image.Image, path: Path, center: tuple[int, int], size: int, glow: bool = False) -> None:
    logo = Image.open(path).convert("RGBA")
    logo.thumbnail((size, size), Image.LANCZOS)
    lx = center[0] - logo.width // 2
    ly = center[1] - logo.height // 2

    if glow:
        glow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        alpha_mask = logo.split()[3]
        halo = Image.new("RGBA", logo.size, (*YELLOW, 200))
        halo.putalpha(alpha_mask)
        glow_layer.paste(halo, (lx, ly), halo)
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(26))
        img.alpha_composite(glow_layer)

    img.alpha_composite(logo, (lx, ly))


def generate(
    opponent: str,
    opponent_logo: Path | None,
    fener_score: int,
    opponent_score: int,
    fener_home: bool,
    label: str,
    out_path: Path,
) -> None:
    base = Image.new("RGB", (W, H), NAVY)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    # Corner sunbursts - dense thin lines fading outward, modern/dynamic feel.
    _line_fan(odraw, (-40, -40), 0, 90, count=26, length=680, color=YELLOW, alpha_start=190, alpha_end=0, width=2)
    _line_fan(odraw, (W + 40, H + 40), 180, 270, count=26, length=680, color=YELLOW, alpha_start=190, alpha_end=0, width=2)
    _line_fan(odraw, (-40, H + 40), 270, 360, count=16, length=380, color=WHITE, alpha_start=40, alpha_end=0, width=1)
    _line_fan(odraw, (W + 40, -40), 90, 180, count=16, length=380, color=WHITE, alpha_start=40, alpha_end=0, width=1)

    # A quiet diagonal weave through the middle band, behind the scoreline.
    for off in range(-40, 41, 14):
        alpha = 22 - abs(off) // 2
        odraw.line([(0, H // 2 - 90 + off), (W, H // 2 - 170 + off)], fill=(*YELLOW, max(alpha, 3)), width=2)

    img = Image.alpha_composite(base.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img, "RGBA")

    draw.polygon([(-10, -10), (170, -10), (-10, 170)], fill=YELLOW)
    draw.polygon([(-10, -10), (110, -10), (-10, 110)], fill=NAVY)
    draw.polygon([(W + 10, H + 10), (W - 170, H + 10), (W + 10, H - 170)], fill=YELLOW)
    draw.polygon([(W + 10, H + 10), (W - 110, H + 10), (W + 10, H - 110)], fill=NAVY)

    label_font = _font("segoeuib.ttf", 42)
    opp_font = _font("segoeui.ttf", 38)
    fener_font = _font("segoeuib.ttf", 96)
    score_font = _font("segoeuib.ttf", 150)
    fener_score_font = _font("segoeuib.ttf", 240)
    dash_font = _font("segoeuib.ttf", 110)

    # --- Label ---
    label_w = _centered_text(draw, 150, label.upper(), label_font, YELLOW, tracking=14)
    _chevrons(draw, int(W / 2 - label_w / 2 - 36), 171, direction=-1, color=YELLOW, alpha=255)
    _chevrons(draw, int(W / 2 + label_w / 2 + 36), 171, direction=1, color=YELLOW, alpha=255)

    # --- Opponent: small, quiet, near the top ---
    opp_y = 330
    if opponent_logo and opponent_logo.exists():
        _paste_logo(img, opponent_logo, (W // 2 - 190, opp_y + 40), size=100)
    _centered_text(draw, opp_y, opponent.upper(), opp_font, MUTED)

    # --- Score: between the two teams ---
    home_score, away_score = (fener_score, opponent_score) if fener_home else (opponent_score, fener_score)
    home_is_fener = fener_home

    left_font = fener_score_font if home_is_fener else score_font
    right_font = score_font if home_is_fener else fener_score_font

    left_text, right_text = f"{home_score}", f"{away_score}"
    left_w = draw.textlength(left_text, font=left_font)
    dash_w = draw.textlength("-", font=dash_font)
    right_w = draw.textlength(right_text, font=right_font)
    gap = 56
    total = left_w + gap + dash_w + gap + right_w
    x = (W - total) / 2
    score_y = 620
    left_y_offset = 0 if home_is_fener else 55
    right_y_offset = 55 if home_is_fener else 0
    draw.text((x, score_y + left_y_offset), left_text, font=left_font, fill=YELLOW)
    x += left_w + gap
    draw.text((x, score_y + 90), "-", font=dash_font, fill=WHITE)
    x += dash_w + gap
    draw.text((x, score_y + right_y_offset), right_text, font=right_font, fill=YELLOW)

    draw.line([(W / 2 - 110, score_y + 300), (W / 2 + 110, score_y + 300)], fill=(*YELLOW, 130), width=3)

    # --- Fenerbahçe: large, glowing logo + bold name - the grand side ---
    fener_logo_cy = 1180
    if FENER_LOGO.exists():
        _paste_logo(img, FENER_LOGO, (W // 2, fener_logo_cy), size=380, glow=True)
    _centered_text(draw, fener_logo_cy + 260, "FENERBAHÇE", fener_font, YELLOW, tracking=4)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_path, quality=95)
    print(f"Saved {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--opponent", required=True)
    parser.add_argument("--opponent-logo", type=Path, default=None)
    parser.add_argument("--fener-score", type=int, required=True)
    parser.add_argument("--opponent-score", type=int, required=True)
    parser.add_argument("--fener-home", type=lambda s: s.lower() in ("1", "true", "yes"), default=False)
    parser.add_argument("--label", default="ILK YARI")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    generate(
        args.opponent, args.opponent_logo, args.fener_score, args.opponent_score,
        args.fener_home, args.label, args.out,
    )


if __name__ == "__main__":
    main()
