"""Generate a pre-match "hype" graphic for tonight's Fenerbahçe match, for
either the feed or a Story - the two targets need different canvases and
can't share one output file (see --target below).

Feed layout ("framed poster"): the supplied hero photo (e.g. a fan-art /
squad photo) is kept completely untouched in the middle, with solid navy
bars added above and below it (expanding the canvas, not overlaying the
photo) to hold the text.
    [top bar]    competition label (centered) + first-leg result
                 (small, top-right corner - a footnote, not a headline)
    ---- thin gold divider ----
    [hero photo, completely unmodified]
    ---- thin gold divider ----
    [bottom bar] "BU AKŞAM" label -> team names (poster headline) -> short
                 gold rule -> kickoff time -> hashtag (small footer)

Story layout: Instagram Stories render full-bleed at a fixed 1080x1920
(9:16) canvas - reusing the feed poster file here (which takes on whatever
aspect ratio the hero photo happens to have, e.g. a landscape photo made it
~1536x1614) makes Instagram scale/crop it unpredictably and the top/bottom
text bars can end up pushed off-screen. So --target story instead cover-crops
the hero photo to fill a fixed 1080x1920 canvas (same technique as
generate_score_graphic.py's _build_background) and overlays the same text
content on darkened bands near the top/bottom, matching the feed poster's
navy/gold visual language without expanding the canvas.

Usage:
    python scripts/generate_matchday_hype_graphic.py \
        --background content_library/media/fenerbahce_ileri.png \
        --competition-label "UEFA ŞAMPİYONLAR LİGİ 3. ELEME TURU - RÖVANŞ" \
        --first-leg-result "İLK MAÇ: FB 2-0 STURM GRAZ" \
        --match-line "STURM GRAZ  -  FENERBAHÇE" \
        --kickoff-label "21:30" \
        --hashtag "#fenerinmaçıvar" \
        --target feed \
        --out content_library/media/fenerbahce_sturmgraz_macgunu.jpg

    # For the Story post, run again with --target story and a distinct --out
    # (e.g. the same filename with a "_story" suffix) - never point the feed
    # and story queue entries at the same file.

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

STORY_W, STORY_H = 1080, 1920
STORY_MARGIN = 90

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


def _dark_band(img: Image.Image, y_center: int, half_height: int, max_alpha: int) -> None:
    """Soft horizontal darkening band so text stays legible over a busy
    background photo, regardless of what's behind it."""
    band = Image.new("RGBA", (img.width, half_height * 2), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(band)
    for i in range(half_height * 2):
        d = abs(i - half_height) / half_height
        alpha = round(max_alpha * max(0.0, 1 - d))
        bdraw.line([(0, i), (img.width, i)], fill=(0, 0, 0, alpha))
    img.alpha_composite(band, (0, y_center - half_height))


def generate(
    background: Path,
    competition_label: str,
    first_leg_result: str,
    match_line: str,
    kickoff_label: str,
    hashtag: str,
    out_path: Path,
) -> None:
    """Feed layout: hero photo kept fully untouched, bars expand the canvas."""
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


def generate_story(
    background: Path,
    competition_label: str,
    first_leg_result: str,
    match_line: str,
    kickoff_label: str,
    hashtag: str,
    out_path: Path,
) -> None:
    """Story layout: fixed 1080x1920 canvas, hero photo cover-cropped to
    fill it completely (no letterboxing, no unpredictable IG-side cropping),
    text overlaid on darkened bands near the top/bottom instead of bars that
    would need extra canvas height Stories don't have room for."""
    photo = Image.open(background).convert("RGB")
    scale = max(STORY_W / photo.width, STORY_H / photo.height)
    photo = photo.resize(
        (round(photo.width * scale), round(photo.height * scale)), Image.LANCZOS
    )
    x = (photo.width - STORY_W) // 2
    y = (photo.height - STORY_H) // 2
    photo = photo.crop((x, y, x + STORY_W, y + STORY_H))

    canvas = photo.convert("RGBA")
    draw = ImageDraw.Draw(canvas, "RGBA")
    cx = STORY_W // 2
    max_width = STORY_W - 2 * STORY_MARGIN

    # --- Top: competition label + first-leg result, on a darkened band ---
    _dark_band(canvas, y_center=140, half_height=140, max_alpha=190)
    _centered_text(draw, competition_label, cx, 70, max_width,
                    start_size=34, fill=WHITE, min_size=20)
    _centered_text(draw, first_leg_result, cx, 150, max_width,
                    start_size=26, fill=SILVER, min_size=18)

    # --- Bottom: poster headline (teams + kickoff), hashtag as footer ---
    block_top = STORY_H - 560
    _dark_band(canvas, y_center=block_top + 280, half_height=300, max_alpha=210)

    y = block_top
    y += _centered_text(draw, "BU AKŞAM", cx, y, max_width,
                         start_size=32, fill=SILVER, min_size=20) + 18

    y += _centered_text(draw, match_line, cx, y, max_width,
                         start_size=64, fill=GOLD, min_size=30) + 28

    draw.rectangle([(cx - 110, y), (cx + 110, y + 4)], fill=GOLD)
    y += 4 + 30

    y += _centered_text(draw, kickoff_label, cx, y, max_width,
                         start_size=90, fill=WHITE, min_size=44) + 36

    _centered_text(draw, hashtag, cx, y, max_width,
                    start_size=32, fill=GOLD, min_size=20)

    # --- Thin gold accent bar at the very bottom, matching the brand language ---
    draw.rectangle([(0, STORY_H - 10), (STORY_W, STORY_H)], fill=(*GOLD, 255))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, quality=95)
    print(f"Saved {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--background", type=Path, required=True)
    parser.add_argument("--competition-label", required=True)
    parser.add_argument("--first-leg-result", required=True)
    parser.add_argument("--match-line", required=True)
    parser.add_argument("--kickoff-label", required=True)
    parser.add_argument("--hashtag", required=True)
    parser.add_argument("--target", choices=["feed", "story"], default="feed",
                         help="feed: untouched photo + expanding bars. "
                              "story: fixed 1080x1920 cover-cropped canvas.")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    fn = generate_story if args.target == "story" else generate
    fn(
        args.background, args.competition_label, args.first_leg_result,
        args.match_line, args.kickoff_label, args.hashtag, args.out,
    )


if __name__ == "__main__":
    main()
