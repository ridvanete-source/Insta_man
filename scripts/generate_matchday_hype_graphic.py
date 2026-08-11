"""Generate a pre-match "hype" graphic for tonight's Fenerbahçe match, in a
framed-poster layout: the supplied hero photo (e.g. a fan-art / squad photo)
is kept completely untouched in the middle, with solid navy bars added
above and below it (expanding the canvas, not overlaying the photo) to hold
the text. Modeled on the same navy/gold visual language as
generate_score_graphic.py.

Layout, top to bottom (each section lives in its own bar, never over the
photo):
    [top bar]    competition label (centered) + first-leg result
                 (small, top-right corner - a footnote, not a headline)
    ---- thin gold divider ----
    [hero photo, completely unmodified]
    ---- thin gold divider ----
    [bottom bar] "BU AKŞAM" label -> team names (poster headline) -> short
                 gold rule -> kickoff time -> hashtag (small footer)

Usage:
    python scripts/generate_matchday_hype_graphic.py \
        --background content_library/media/fenerbahce_ileri.png \
        --competition-label "UEFA ŞAMPİYONLAR LİGİ 3. ELEME TURU - RÖVANŞ" \
        --first-leg-result "İLK MAÇ: FB 2-0 STURM GRAZ" \
        --match-line "STURM GRAZ  -  FENERBAHÇE" \
        --kickoff-label "21:30" \
        --hashtag "#fenerinmaçıvar" \
        --out content_library/media/fenerbahce_sturmgraz_macgunu.jpg

Standalone script, not part of the insta_man package - only needed for
one-off matchday hype posts, not the general publishing pipeline.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

NAVY = (10, 22, 58)
NAVY_DARK = (6, 14, 38)
GOLD = (255, 199, 44)
WHITE = (245, 245, 245)
SILVER = (176, 184, 202)

MARGIN = 70
TOP_BAR_H = 190
BOTTOM_BAR_H = 400
DIVIDER_H = 5

ASSETS_DIR = Path(__file__).parent / "assets"
FONT_DIR = ASSETS_DIR / "fonts"
BOLD_FONT = FONT_DIR / "Montserrat-Bold.ttf"


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(BOLD_FONT), size)


def _fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int,
              start_size: int, min_size: int = 18) -> ImageFont.FreeTypeFont:
    """Shrink the font until `text` fits max_width - line lengths vary a lot
    depending on opponent name/competition, so this can't be a fixed size."""
    size = start_size
    while size > min_size:
        font = _font(size)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 2
    return _font(min_size)


def _centered_text(draw: ImageDraw.ImageDraw, text: str, cx: int, y: int,
                    max_width: int, start_size: int, fill: tuple,
                    min_size: int = 18) -> int:
    """Draws horizontally-centered text around cx, returns the font size
    used (so callers can space the next line based on rendered height)."""
    font = _fit_font(draw, text, max_width, start_size, min_size)
    w = draw.textlength(text, font=font)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)
    return font.size


def _right_text(draw: ImageDraw.ImageDraw, text: str, right_x: int, y: int,
                 size: int, fill: tuple) -> None:
    font = _font(size)
    w = draw.textlength(text, font=font)
    draw.text((right_x - w, y), text, font=font, fill=fill)


def generate(
    background: Path,
    competition_label: str,
    first_leg_result: str,
    match_line: str,
    kickoff_label: str,
    hashtag: str,
    out_path: Path,
) -> None:
    photo = Image.open(background).convert("RGB")
    W, H = photo.size
    total_h = TOP_BAR_H + H + BOTTOM_BAR_H

    canvas = Image.new("RGB", (W, total_h), NAVY_DARK)
    canvas.paste(photo, (0, TOP_BAR_H))
    draw = ImageDraw.Draw(canvas)

    # --- Divider lines framing the untouched photo ---
    draw.rectangle([(0, TOP_BAR_H - DIVIDER_H), (W, TOP_BAR_H)], fill=GOLD)
    draw.rectangle([(0, TOP_BAR_H + H), (W, TOP_BAR_H + H + DIVIDER_H)], fill=GOLD)

    cx = W // 2

    # --- Top bar: competition label + first-leg result as a small corner detail ---
    _centered_text(draw, competition_label, cx, 58, W - 2 * MARGIN,
                    start_size=34, fill=WHITE, min_size=20)
    _right_text(draw, first_leg_result, W - MARGIN, 122, size=24, fill=SILVER)

    # --- Bottom bar: poster headline (teams + kickoff), hashtag as footer ---
    y = TOP_BAR_H + H + 34
    y += _centered_text(draw, "BU AKŞAM", cx, y, W - 2 * MARGIN,
                         start_size=28, fill=SILVER, min_size=20) + 14

    y += _centered_text(draw, match_line, cx, y, W - 2 * MARGIN,
                         start_size=72, fill=GOLD, min_size=32) + 24

    draw.rectangle([(cx - 110, y), (cx + 110, y + 4)], fill=GOLD)
    y += 4 + 26

    y += _centered_text(draw, kickoff_label, cx, y, W - 2 * MARGIN,
                         start_size=100, fill=WHITE, min_size=44) + 30

    _centered_text(draw, hashtag, cx, y, W - 2 * MARGIN,
                    start_size=34, fill=GOLD, min_size=20)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, quality=95)
    print(f"Saved {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--background", type=Path, required=True)
    parser.add_argument("--competition-label", required=True)
    parser.add_argument("--first-leg-result", required=True)
    parser.add_argument("--match-line", required=True)
    parser.add_argument("--kickoff-label", required=True)
    parser.add_argument("--hashtag", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    generate(
        args.background, args.competition_label, args.first_leg_result,
        args.match_line, args.kickoff_label, args.hashtag, args.out,
    )


if __name__ == "__main__":
    main()
