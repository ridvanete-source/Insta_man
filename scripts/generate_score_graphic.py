"""Generate a Fenerbahçe "MAÇ SONUCU" (full-time result) graphic for an
Instagram Story, modeled on the club's own official full-time posts.

Layout (1080x1920 - Story aspect ratio), top to bottom:
    competition/season label (small, changes per match/competition)
    "MAC SONUCU" title + divider line
    [Fenerbahce logo]   score  VS  score   [opponent logo]
    thin accent bar at the very bottom

Fenerbahçe is always shown on the left with its own score first, regardless
of home/away - this is the club's own account, so it always leads with
itself, matching the reference design it's modeled on.

Background is a supplied match photo (e.g. a pre-match/celebration shot),
darkened with a navy tint for text legibility. Falls back to a plain navy
gradient if no photo is given.

Usage:
    python scripts/generate_score_graphic.py \
        --opponent "STURM GRAZ" --opponent-logo scripts/assets/sturm_graz_logo.png \
        --fener-score 2 --opponent-score 0 \
        --competition-label "2026-2027 SEZONU UEFA ŞAMPİYONLAR LİGİ PLAY-OFF TURU" \
        --background content_library/media/sturm_graz_pre_match.jpg \
        --out content_library/media/score.jpg

Standalone script, not part of the insta_man package - only needed for
one-off score-graphic posts, not the general publishing pipeline.

Logo licensing note: the Fenerbahçe crest bundled in scripts/assets is
Wikipedia non-free "fair use" material (trademarked, not freely licensed
for reuse) - used here at the account owner's own risk/discretion for a
personal fan account. The Sturm Graz crest (scripts/assets/sturm_graz_logo.png)
is sourced from Wikimedia Commons, marked public domain there (simple
geometric shapes/text). Check licensing before reusing this script with a
different opponent's crest.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

NAVY = (10, 22, 58)
NAVY_DARK = (5, 12, 34)
YELLOW = (255, 209, 0)
WHITE = (245, 245, 245)
SILVER = (196, 202, 214)

W, H = 1080, 1920
MARGIN = 90
FONT_DIR = Path("C:/Windows/Fonts")
ASSETS_DIR = Path(__file__).parent / "assets"
FENER_LOGO = ASSETS_DIR / "fenerbahce_logo.png"


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def _fit_font(draw: ImageDraw.ImageDraw, text: str, font_name: str, max_width: int,
              start_size: int, min_size: int = 20) -> ImageFont.FreeTypeFont:
    """Shrink the font until `text` fits max_width - competition/season
    labels vary a lot in length, so this can't be a fixed size."""
    size = start_size
    while size > min_size:
        font = _font(font_name, size)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 2
    return _font(font_name, min_size)


def _paste_logo(img: Image.Image, path: Path, center: tuple[int, int], size: int) -> None:
    logo = Image.open(path).convert("RGBA")
    logo.thumbnail((size, size), Image.LANCZOS)
    lx = center[0] - logo.width // 2
    ly = center[1] - logo.height // 2
    img.alpha_composite(logo, (lx, ly))


def _build_background(background: Path | None) -> Image.Image:
    if background and background.exists():
        photo = Image.open(background).convert("RGB")
        scale = max(W / photo.width, H / photo.height)
        photo = photo.resize((round(photo.width * scale), round(photo.height * scale)), Image.LANCZOS)
        x = (photo.width - W) // 2
        y = (photo.height - H) // 2
        photo = photo.crop((x, y, x + W, y + H))
        base = photo.convert("RGBA")
        tint = Image.new("RGBA", (W, H), (*NAVY, 175))
        return Image.alpha_composite(base, tint)

    gradient = Image.new("RGB", (W, H), NAVY)
    for y in range(H):
        t = y / H
        r = round(NAVY_DARK[0] + (NAVY[0] - NAVY_DARK[0]) * t)
        g = round(NAVY_DARK[1] + (NAVY[1] - NAVY_DARK[1]) * t)
        b = round(NAVY_DARK[2] + (NAVY[2] - NAVY_DARK[2]) * t)
        ImageDraw.Draw(gradient).line([(0, y), (W, y)], fill=(r, g, b))
    return gradient.convert("RGBA")


def _gradient_bar(img: Image.Image, x0: int, x1: int, y: int, height: int) -> None:
    bar = Image.new("RGBA", (x1 - x0, height), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(bar)
    for i in range(x1 - x0):
        t = i / (x1 - x0)
        shade = round(90 + 140 * (1 - abs(t - 0.5) * 2))
        bdraw.line([(i, 0), (i, height)], fill=(shade, shade, shade + 6, 255))
    img.alpha_composite(bar, (x0, y))


def generate(
    opponent_logo: Path | None,
    fener_score: int,
    opponent_score: int,
    competition_label: str,
    background: Path | None,
    out_path: Path,
) -> None:
    img = _build_background(background)
    draw = ImageDraw.Draw(img, "RGBA")

    label_font = _fit_font(draw, competition_label.upper(), "segoeuib.ttf", W - 2 * MARGIN, start_size=34)
    draw.text((MARGIN, 120), competition_label.upper(), font=label_font, fill=WHITE)

    title_font = _font("segoeuib.ttf", 108)
    draw.text((MARGIN, 175), "MAÇ SONUCU", font=title_font, fill=YELLOW)

    _gradient_bar(img, MARGIN, W - MARGIN, 340, 6)

    # --- Score row: [Fenerbahce logo]  score  VS  score  [opponent logo] ---
    row_y = 900
    logo_size = 230
    left_logo_x = MARGIN + logo_size // 2
    right_logo_x = W - MARGIN - logo_size // 2

    if FENER_LOGO.exists():
        _paste_logo(img, FENER_LOGO, (left_logo_x, row_y), size=logo_size)
    if opponent_logo and opponent_logo.exists():
        _paste_logo(img, opponent_logo, (right_logo_x, row_y), size=logo_size)

    score_font = _font("segoeuib.ttf", 130)
    vs_font = _font("segoeuib.ttf", 56)

    left_text, right_text = str(fener_score), str(opponent_score)
    left_w = draw.textlength(left_text, font=score_font)
    vs_w = draw.textlength("VS", font=vs_font)
    right_w = draw.textlength(right_text, font=score_font)
    gap = 38
    total = left_w + gap + vs_w + gap + right_w
    x = (W - total) / 2

    score_y_offset = -65  # score_font's ascent sits above the logo centerline
    draw.text((x, row_y + score_y_offset), left_text, font=score_font, fill=WHITE)
    x += left_w + gap
    draw.text((x, row_y - vs_font.size / 2), "VS", font=vs_font, fill=YELLOW)
    x += vs_w + gap
    draw.text((x, row_y + score_y_offset), right_text, font=score_font, fill=WHITE)

    # --- Bottom accent bar ---
    draw.rectangle([(0, H - 14), (W, H)], fill=(*YELLOW, 255))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_path, quality=95)
    print(f"Saved {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--opponent-logo", type=Path, default=None)
    parser.add_argument("--fener-score", type=int, required=True)
    parser.add_argument("--opponent-score", type=int, required=True)
    parser.add_argument("--competition-label", required=True,
                         help='e.g. "2026-2027 SEZONU UEFA ŞAMPİYONLAR LİGİ PLAY-OFF TURU"')
    parser.add_argument("--background", type=Path, default=None,
                         help="Match photo to use as the tinted background; falls back to a navy gradient")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    generate(
        args.opponent_logo, args.fener_score, args.opponent_score,
        args.competition_label, args.background, args.out,
    )


if __name__ == "__main__":
    main()
