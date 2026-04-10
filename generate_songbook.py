#!/usr/bin/env python3
"""
UWS Songbook PDF Generator
Compiles song JSON files into a single paginated PDF with:
  - Linked, two-column Table of Contents (sort by title or artist)
  - Chord diagrams in a right-side column (images contain their own labels)
  - Lyrics in black; chord markers in bold red (parentheses included)
  - Section labels in bold italic blue
  - Optional two-column layout to fit long songs on one page
  - Full Unicode rendering: Latin (Vera TTF), CJK (STSong-Light CID)
  - Configurable header/footer/layout via songbook_config.py

Usage:
    pip install reportlab
    python generate_songbook.py [options]
    python generate_songbook.py --help
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4, letter, A5
    from reportlab.lib.units import mm
    from reportlab.lib.colors import black, grey, white, HexColor
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.pdfmetrics import stringWidth
    import reportlab as _rl
except ImportError:
    print("Error: reportlab is not installed.\n  Run: pip install reportlab", file=sys.stderr)
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# FONT REGISTRATION
# ═══════════════════════════════════════════════════════════════════════════════

_RL_FONTS = os.path.join(os.path.dirname(_rl.__file__), "fonts")

def _reg_ttf(alias: str, filename: str):
    pdfmetrics.registerFont(TTFont(alias, os.path.join(_RL_FONTS, filename)))

_reg_ttf("Vera",           "Vera.ttf")
_reg_ttf("Vera-Bold",      "VeraBd.ttf")
_reg_ttf("Vera-Italic",    "VeraIt.ttf")
_reg_ttf("Vera-BoldItalic","VeraBI.ttf")

pdfmetrics.registerFontFamily(
    "Vera",
    normal="Vera", bold="Vera-Bold",
    italic="Vera-Italic", boldItalic="Vera-BoldItalic",
)

# CJK font for Chinese / Japanese / Korean lyrics.
# STSong-Light is a standard CID font embedded by PDF viewers — no extra files needed.
try:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    CJK_FONT = "STSong-Light"       # type: str | None
except Exception:
    CJK_FONT = None                 # type: str | None  # unavailable; CJK chars left as-is

FONT_NORMAL      = "Vera"
FONT_BOLD        = "Vera-Bold"
FONT_ITALIC      = "Vera-Italic"
FONT_BOLD_ITALIC = "Vera-BoldItalic"


# ═══════════════════════════════════════════════════════════════════════════════
# UNICODE SANITISATION
# ═══════════════════════════════════════════════════════════════════════════════

# Characters that Vera does NOT contain → explicit substitutions.
# Vera already handles: curly quotes, en/em dash, ellipsis, all Latin-1 accented chars.
_SUBS = str.maketrans({
    # Cyrillic lookalikes (accidental copy-paste artefacts)
    "\u0430": "a",   # а → a
    "\u0435": "e",   # е → e  (the reported problem char)
    "\u043E": "o",   # о → o
    "\u0440": "r",   # р → r
    "\u0441": "c",   # с → c
    "\u0445": "x",   # х → x
    "\u0456": "i",   # і → i  (Ukrainian)
    "\u0410": "A",   # А → A
    "\u0415": "E",   # Е → E
    "\u041E": "O",   # О → O
    "\u0420": "R",   # Р → R
    "\u0421": "C",   # С → C
    "\u0425": "X",   # Х → X
    # Other Vera gaps
    "\u02BC": "'",   # modifier letter apostrophe
    "\u2005": " ",   # four-per-em space → regular space
    "\u2193": "v",   # ↓ downward arrow → v (approximation)
})


def sanitize_text(text: str) -> str:
    """
    Apply explicit substitutions for characters that Vera does not contain
    (Cyrillic lookalikes, modifier apostrophe, four-per-em space, etc.).

    Vera already natively covers: all Latin-1 accented chars, curly quotes,
    en/em dash, ellipsis, OE ligature, and many other Latin-extended glyphs.
    CJK characters are left untouched and rendered via STSong-Light in _draw_run.
    Any remaining unrecognised character is passed through; if Vera cannot render
    it the PDF viewer will display a placeholder box (acceptable behaviour).
    """
    return text.translate(_SUBS)


def _is_cjk(cp: int) -> bool:
    """Return True for CJK Unified Ideographs and common extensions."""
    return (0x4E00 <= cp <= 0x9FFF  or
            0x3400 <= cp <= 0x4DBF  or
            0xF900 <= cp <= 0xFAFF  or
            0x20000 <= cp <= 0x2A6DF)


def _split_by_script(text: str):
    """
    Yield (chunk, is_cjk) runs. Adjacent characters of the same script
    are grouped into one chunk for efficient font switching.
    """
    if not text:
        return
    current, current_cjk = "", _is_cjk(ord(text[0]))
    for ch in text:
        cjk = _is_cjk(ord(ch))
        if cjk == current_cjk:
            current += ch
        else:
            yield current, current_cjk
            current, current_cjk = ch, cjk
    if current:
        yield current, current_cjk


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT MEASUREMENT
# ═══════════════════════════════════════════════════════════════════════════════

def measure_run(text: str, base_font: str, fs: float) -> float:
    """Measure the pixel width of a text run, accounting for CJK font switching."""
    clean = sanitize_text(text)
    total = 0.0
    for chunk, cjk in _split_by_script(clean):
        font = CJK_FONT if (cjk and CJK_FONT) else base_font
        total += stringWidth(chunk, font, fs)
    return total


def token_w(typ: str, text: str, fs: float) -> float:
    """Width of a single lyrics token (chord or text)."""
    base = FONT_BOLD if typ == "chord" else FONT_NORMAL
    return measure_run(text, base, fs)


# ═══════════════════════════════════════════════════════════════════════════════
# REGEX & CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

CHORD_RE   = re.compile(r"(\([A-Za-z0-9#b+\-/]+\))")
SECTION_RE = re.compile(r"^\s*\[.+\]\s*$")
PAGE_SIZES = {"A4": A4, "Letter": letter, "A5": A5}

DEFAULT_CONFIG = dict(
    # Source data
    SONGBOOK_DIR           = "Songbook",   # folder containing .json song files
    # Layout
    PAGE_ORIENTATION       = "landscape",  # "landscape" | "portrait"
    PAGE_SIZE              = "A4",         # "A4" | "Letter" | "A5"
    MARGIN_MM              = 15,
    CHORD_COL_WIDTH_MM     = 36,
    CHORD_SPLIT_THRESHOLD  = 6,    # split chord images into 2 sub-cols when count exceeds this
    TWO_COLUMN_LONG_SONGS  = True,
    # Sort / display order
    SORT_BY                = "title",      # "title" | "artist"
    # Font sizes (points)
    LYRICS_FONT_SIZE       = 9,
    TITLE_FONT_SIZE        = 12,
    TOC_FONT_SIZE          = 9,
    # Footer
    FOOTER_LEFT            = "Compiled and prepared by Ukulele Wednesdays Singapore",
    FOOTER_RIGHT           = "Page {page}",
    FOOTER_FONT_SIZE       = 7,
    # Colours
    COLOR_CHORDS           = "#CC0000",
    COLOR_ACCENT           = "#CC0000",
    COLOR_SECTION          = "#1144AA",
    # PDF metadata
    PDF_TITLE              = "UWS Songbook",
    PDF_AUTHOR             = "Ukulele Wednesdays Singapore",
    PDF_SUBJECT            = "Ukulele Chord Songbook",
    TOC_TITLE              = "Table of Contents",
)

LINE_COST = {"blank": 0.5, "section": 0.85, "content": 1.0}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def song_display_str(song: dict, sort_by: str) -> str:
    """Format the canonical display string for a song (TOC + page header)."""
    title  = sanitize_text(song.get("title",  ""))
    artist = sanitize_text(song.get("artist", ""))
    if sort_by == "artist":
        return f"{artist}  —  {title}"
    return f"{title}  —  {artist}"


# ═══════════════════════════════════════════════════════════════════════════════
# LYRICS PARSING
# ═══════════════════════════════════════════════════════════════════════════════

def tokenize_line(line: str) -> list:
    """Split one lyrics line into (type, text) tokens."""
    if SECTION_RE.match(line.strip()):
        return [("section", line.strip())]
    tokens = []
    for part in CHORD_RE.split(line):
        if not part:
            continue
        if CHORD_RE.fullmatch(part):
            tokens.append(("chord", part))
        else:
            tokens.append(("text", part))
    return tokens


def wrap_tokens(tokens: list, max_w: float, fs: float) -> list:
    """Wrap a token list into display rows that fit within max_w."""
    if not tokens:
        return [[]]
    if sum(token_w(t, s, fs) for t, s in tokens) <= max_w:
        return [tokens]

    groups, pending_chords = [], []
    for typ, text in tokens:
        if typ == "chord":
            pending_chords.append((typ, text))
        else:
            for part in re.split(r"(\s+)", text):
                if not part:
                    continue
                groups.append(pending_chords + [(typ, part)])
                pending_chords = []
    if pending_chords:
        groups.append(pending_chords)

    rows, cur_row, cur_w = [], [], 0.0
    for group in groups:
        gw = sum(token_w(t, s, fs) for t, s in group)
        if cur_w + gw > max_w and cur_row:
            rows.append(cur_row)
            cur_row, cur_w = [], 0.0
            group = [(t, s.lstrip()) if t == "text" else (t, s) for t, s in group]
        cur_row.extend(group)
        cur_w += gw
    if cur_row:
        rows.append(cur_row)
    return rows or [[]]


def compute_display_lines(song: dict, text_w: float, fs: float) -> list:
    """Convert raw lyrics string into flat list of (type, tokens) display lines."""
    out = []
    for raw in song["lyrics"].split("\n"):
        if not raw.strip():
            out.append(("blank", []))
            continue
        tokens = tokenize_line(raw)
        if tokens and tokens[0][0] == "section":
            out.append(("section", tokens))
        else:
            for row in wrap_tokens(tokens, text_w, fs):
                out.append(("content", row))
    return out


def paginate_lines(display_lines: list, lines_per_page: float) -> list:
    """Split display lines into pages using fractional line costs."""
    pages, cur_page, cur_cost = [], [], 0.0
    for dl in display_lines:
        cost = LINE_COST.get(dl[0], 1.0)
        if cur_cost + cost > lines_per_page and cur_page:
            pages.append(cur_page)
            cur_page, cur_cost = [], 0.0
        cur_page.append(dl)
        cur_cost += cost
    if cur_page:
        pages.append(cur_page)
    return pages or [[]]


def split_two_columns(display_lines: list, lines_per_page: float):
    """
    If total line cost ≤ 2 × lines_per_page, split into (left_lines, right_lines)
    for a two-column single-page layout. Returns None if content doesn't fit.
    """
    total = sum(LINE_COST.get(dl[0], 1.0) for dl in display_lines)
    if total > 2 * lines_per_page:
        return None
    target = total / 2
    left, right, acc = [], [], 0.0
    for dl in display_lines:
        cost = LINE_COST.get(dl[0], 1.0)
        if acc < target:
            left.append(dl)
        else:
            right.append(dl)
        acc += cost
    return left, right


# ═══════════════════════════════════════════════════════════════════════════════
# CHORD IMAGE LOOKUP
# ═══════════════════════════════════════════════════════════════════════════════

def find_chord_image(name: str, chord_dir: Path):
    """Return Path to chord image (.png preferred). None if not found."""
    for ext in (".png", ".jpg"):
        p = chord_dir / f"{name}{ext}"
        if p.exists():
            return p
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# DRAWING PRIMITIVES
# ═══════════════════════════════════════════════════════════════════════════════

def _draw_run(c, text: str, x: float, y: float, base_font: str, fs: float) -> float:
    """
    Draw a single text run at (x, y), switching to the CJK font where needed.
    Applies sanitize_text before rendering. Returns the new x position.
    """
    clean = sanitize_text(text)
    cur_x = x
    for chunk, cjk in _split_by_script(clean):
        font = CJK_FONT if (cjk and CJK_FONT) else base_font
        c.setFont(font, fs)
        c.drawString(cur_x, y, chunk)
        cur_x += stringWidth(chunk, font, fs)
    return cur_x


def draw_tokens(c, tokens: list, x: float, y: float, fs: float, cfg: dict):
    """Render a token row at (x, y). Chords are bold red, text is black."""
    chord_color = HexColor(cfg["COLOR_CHORDS"])
    cur_x = x
    for typ, text in tokens:
        if typ == "chord":
            c.setFillColor(chord_color)
            cur_x = _draw_run(c, text, cur_x, y, FONT_BOLD, fs)
        else:
            c.setFillColor(black)
            cur_x = _draw_run(c, text, cur_x, y, FONT_NORMAL, fs)


def draw_song_header(c, song: dict, ph: float,
                     margin: float, text_w: float, cfg: dict,
                     continuation_note: str = ""):
    """Draw song title + accent line in the header band."""
    fs       = cfg["TITLE_FONT_SIZE"]
    sort_by  = cfg.get("SORT_BY", "title")
    display  = song_display_str(song, sort_by)

    title_y  = ph - margin - fs - 1 * mm
    c.setFillColor(black)
    _draw_run(c, display, margin, title_y, FONT_BOLD, fs)

    if continuation_note:
        c.setFont(FONT_ITALIC, 7)
        c.setFillColor(HexColor(cfg["COLOR_SECTION"]))
        c.drawRightString(margin + text_w, title_y, continuation_note)

    accent_y = title_y - 2 * mm
    c.setStrokeColor(HexColor(cfg["COLOR_ACCENT"]))
    c.setLineWidth(0.75)
    c.line(margin, accent_y, margin + text_w, accent_y)


def draw_footer(c, page_num: int, pw: float, margin: float, cfg: dict):
    """Draw footer separator line, left text, and right page number."""
    fy    = margin * 0.42
    sep_y = margin * 0.75
    c.setStrokeColor(HexColor("#CCCCCC"))
    c.setLineWidth(0.4)
    c.line(margin, sep_y, pw - margin, sep_y)

    fs = cfg["FOOTER_FONT_SIZE"]
    c.setFont(FONT_NORMAL, fs)
    c.setFillColor(HexColor("#888888"))
    c.drawString(margin, fy, cfg["FOOTER_LEFT"])
    c.drawRightString(pw - margin, fy, cfg["FOOTER_RIGHT"].format(page=page_num))


def _draw_chord_subcol(c, chord_images: list,
                       col_x: float, col_top_y: float,
                       col_w: float, avail_h: float):
    """Render one sub-column of chord diagram images (internal helper)."""
    n = len(chord_images)
    if not n:
        return
    gap      = 5
    img_max  = min(col_w, (avail_h - n * gap) / n)
    img_size = max(10, min(img_max, col_w))

    y = col_top_y
    for name, img_path in chord_images:
        img_y = y - gap / 2 - img_size
        if img_y < 0:
            break
        if img_path:
            try:
                c.drawImage(str(img_path), col_x, img_y,
                            width=img_size, height=img_size,
                            preserveAspectRatio=True, anchor="nw",
                            mask="auto")
            except Exception:
                c.setStrokeColor(grey)
                c.rect(col_x, img_y, img_size, img_size)
        else:
            c.setStrokeColor(grey)
            c.setFillColor(HexColor("#F5F5F5"))
            c.rect(col_x, img_y, img_size, img_size, fill=1)
            c.setFillColor(grey)
            c.setFont(FONT_NORMAL, 7)
            c.drawCentredString(col_x + img_size / 2, img_y + img_size / 2 - 3, name)
        y -= gap / 2 + img_size + gap / 2


def draw_chord_column(c, chord_images: list,
                      col_x: float, col_top_y: float,
                      col_w: float, avail_h: float,
                      split_threshold: int = 6):
    """
    Stack chord diagram images in the right column.
    Images already contain their own chord-name labels.

    When len(chord_images) > split_threshold, the column is divided into two
    equal sub-columns so more chords fit at a usable size.  The left sub-column
    gets the first ceil(n/2) chords; the right gets the rest.
    """
    n = len(chord_images)
    if not n:
        return

    if n > split_threshold:
        sub_gap = 3                        # pt between the two sub-columns
        sub_w   = (col_w - sub_gap) / 2
        half    = (n + 1) // 2            # ceiling: left col gets the extra if odd
        _draw_chord_subcol(c, chord_images[:half],
                           col_x, col_top_y, sub_w, avail_h)
        _draw_chord_subcol(c, chord_images[half:],
                           col_x + sub_w + sub_gap, col_top_y, sub_w, avail_h)
    else:
        _draw_chord_subcol(c, chord_images, col_x, col_top_y, col_w, avail_h)


def draw_lyric_column(c, display_lines: list, x: float, text_start_y: float,
                      fs: float, lh: float, cfg: dict):
    """Render one column of display lines starting at (x, text_start_y)."""
    section_color = HexColor(cfg["COLOR_SECTION"])
    y = text_start_y
    for line_type, tokens in display_lines:
        if line_type == "blank":
            y -= lh * 0.5
        elif line_type == "section":
            c.setFillColor(section_color)
            label = sanitize_text(tokens[0][1] if tokens else "")
            _draw_run(c, label, x + 1 * mm, y, FONT_BOLD_ITALIC, fs - 1)
            y -= lh * 0.85
        else:
            draw_tokens(c, tokens, x, y, fs, cfg)
            y -= lh


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS
# ═══════════════════════════════════════════════════════════════════════════════

def render_toc(c, songs: list, song_page_nums: dict,
               toc_page_count: int, pw: float, ph: float,
               margin: float, cfg: dict):
    """Render the Table of Contents."""
    sort_by          = cfg.get("SORT_BY", "title")
    fs               = cfg["TOC_FONT_SIZE"] - 1
    lh               = fs * 1.38
    toc_title_h      = 22 * mm
    col_gap          = 8 * mm
    col_w            = (pw - 2 * margin - col_gap) / 2
    usable_h         = ph - margin - toc_title_h - margin
    entries_per_col  = max(1, int(usable_h / lh))
    entries_per_page = entries_per_col * 2
    accent           = HexColor(cfg["COLOR_ACCENT"])

    for page_idx in range(toc_page_count):
        page_songs  = songs[page_idx * entries_per_page:(page_idx + 1) * entries_per_page]
        actual_page = page_idx + 1

        if page_idx == 0:
            c.setFont(FONT_BOLD, 18)
            c.setFillColor(black)
            c.drawString(margin, ph - margin - 14 * mm,
                         sanitize_text(cfg["TOC_TITLE"]))
            c.setStrokeColor(accent)
            c.setLineWidth(1.2)
            c.line(margin, ph - margin - 16.5 * mm, pw - margin, ph - margin - 16.5 * mm)

        text_start_y = ph - margin - toc_title_h + fs

        for entry_idx, song in enumerate(page_songs):
            col_idx    = entry_idx // entries_per_col
            row_idx    = entry_idx % entries_per_col
            x          = margin + col_idx * (col_w + col_gap)
            y          = text_start_y - row_idx * lh

            song_pg    = song_page_nums.get(song["_id"], "?")
            entry_text = song_display_str(song, sort_by)
            pg_text    = str(song_pg)

            pg_w  = stringWidth(pg_text, FONT_BOLD, fs)
            dot_w = stringWidth(".", FONT_NORMAL, fs)

            max_text_w = col_w - pg_w - dot_w * 4 - 3 * mm
            text_w_cur = measure_run(entry_text, FONT_NORMAL, fs)
            if text_w_cur > max_text_w:
                while text_w_cur > max_text_w and len(entry_text) > 5:
                    entry_text = entry_text[:-1]
                    text_w_cur = measure_run(entry_text, FONT_NORMAL, fs)
                entry_text = entry_text.rstrip() + "…"
                text_w_cur = measure_run(entry_text, FONT_NORMAL, fs)

            num_dots = max(2, int((col_w - text_w_cur - pg_w - 2 * mm) / dot_w))

            c.setFillColor(black)
            end_x = _draw_run(c, entry_text, x, y, FONT_NORMAL, fs)
            c.setFont(FONT_NORMAL, fs)
            c.drawString(end_x + 1, y, "." * num_dots)
            c.setFont(FONT_BOLD, fs)
            c.drawRightString(x + col_w, y, pg_text)

            c.linkAbsolute("", f"song_{song['_id']}",
                           Rect=(x, y - 2, x + col_w, y + lh - 2),
                           Border="[0 0 0]")

        draw_footer(c, actual_page, pw, margin, cfg)
        c.showPage()


# ═══════════════════════════════════════════════════════════════════════════════
# SONG RENDERING
# ═══════════════════════════════════════════════════════════════════════════════

def render_song(c, song: dict, layout: dict,
                song_start_page: int,
                pw: float, ph: float, margin: float,
                text_w: float, chord_col_x: float, chord_col_w: float,
                header_h: float, cfg: dict):
    """Render all pages for one song (single-column or two-column mode)."""
    fs           = layout["fs"]
    lh           = layout["lh"]
    chord_images = layout["chord_images"]
    two_col      = layout.get("two_column", False)
    col_lines    = layout.get("col_lines")
    pages        = layout["pages"]
    n_pages      = 1 if two_col else len(pages)
    text_start_y = ph - margin - header_h - fs

    for page_idx in range(n_pages):
        actual_page = song_start_page + page_idx
        is_first    = page_idx == 0

        if is_first:
            c.bookmarkPage(f"song_{song['_id']}")
            c.addOutlineEntry(
                song_display_str(song, cfg.get("SORT_BY", "title")),
                f"song_{song['_id']}",
                level=0,
                closed=True,
            )

        note = ""
        if n_pages > 1:
            note = "(cont. →)" if is_first else f"(continued  {page_idx + 1}/{n_pages})"
        draw_song_header(c, song, ph, margin, text_w, cfg, continuation_note=note)

        if chord_images:
            chord_top   = ph - margin - header_h
            chord_avail = chord_top - margin - (margin * 0.8)
            draw_chord_column(c, chord_images, chord_col_x, chord_top,
                              chord_col_w, chord_avail,
                              split_threshold=int(cfg.get("CHORD_SPLIT_THRESHOLD", 6)))

        if two_col and col_lines:
            inner_gap  = 6 * mm
            each_col_w = (text_w - inner_gap) / 2
            draw_lyric_column(c, col_lines[0], margin,
                              text_start_y, fs, lh, cfg)
            draw_lyric_column(c, col_lines[1], margin + each_col_w + inner_gap,
                              text_start_y, fs, lh, cfg)
        else:
            draw_lyric_column(c, pages[page_idx], margin,
                              text_start_y, fs, lh, cfg)

        draw_footer(c, actual_page, pw, margin, cfg)
        c.showPage()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATION PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def generate_pdf(songs: list, chord_dir: Path, output_path: Path, cfg: dict):
    """Compute layout for every song, then render TOC + song pages."""
    # Page geometry
    base_size   = PAGE_SIZES.get(cfg["PAGE_SIZE"], A4)
    orientation = cfg["PAGE_ORIENTATION"].lower()
    pw, ph      = (max(base_size), min(base_size)) if orientation == "landscape" \
                  else (min(base_size), max(base_size))

    margin      = cfg["MARGIN_MM"] * mm
    chord_col_w = cfg["CHORD_COL_WIDTH_MM"] * mm
    text_gap    = 5 * mm
    text_w      = pw - 2 * margin - chord_col_w - text_gap
    chord_col_x = pw - margin - chord_col_w

    fs          = float(cfg["LYRICS_FONT_SIZE"])
    lh          = fs * 1.45
    title_fs    = float(cfg["TITLE_FONT_SIZE"])
    header_h    = title_fs + 6 * mm
    footer_h    = margin * 0.9
    usable_h    = ph - margin - header_h - footer_h - 3 * mm
    lines_pp    = max(1, usable_h / lh)

    use_two_col = bool(cfg.get("TWO_COLUMN_LONG_SONGS", True))
    inner_gap   = 6 * mm
    col_w_two   = (text_w - inner_gap) / 2

    print(f"  Page:      {pw/mm:.0f} × {ph/mm:.0f} mm  ({orientation})")
    print(f"  Text area: {text_w/mm:.0f} × {usable_h/mm:.0f} mm")
    print(f"  Lines/page ≈ {lines_pp:.1f}  (font {fs}pt)")

    # Layout pass
    print("Computing song layouts …")
    song_layouts     = []
    two_col_count    = 0
    multi_page_count = 0

    for song in songs:
        chords     = song.get("chords", [])
        chord_imgs = [(ch, find_chord_image(ch, chord_dir)) for ch in chords]

        pages, used_fs, used_lh = None, fs, lh
        for attempt_fs in [fs, fs - 0.5, fs - 1.0, fs - 1.5, fs - 2.0]:
            if attempt_fs < 6:
                break
            dl        = compute_display_lines(song, text_w, attempt_fs)
            lh_a      = attempt_fs * 1.45
            lpp_a     = max(1, usable_h / lh_a)
            candidate = paginate_lines(dl, lpp_a)
            if len(candidate) <= 2:
                pages, used_fs, used_lh = candidate, attempt_fs, lh_a
                break

        if pages is None:
            min_fs   = max(6.0, fs - 2.0)
            dl_min   = compute_display_lines(song, text_w, min_fs)
            lh_min   = min_fs * 1.45
            lpp_min  = max(1, usable_h / lh_min)
            pages    = paginate_lines(dl_min, lpp_min)
            used_fs, used_lh = min_fs, lh_min

        entry = {
            "song":         song,
            "chord_images": chord_imgs,
            "pages":        pages,
            "fs":           used_fs,
            "lh":           used_lh,
            "two_column":   False,
            "col_lines":    None,
        }

        if use_two_col and len(pages) == 2:
            dl_two  = compute_display_lines(song, col_w_two, used_fs)
            lpp_two = max(1, usable_h / used_lh)
            result  = split_two_columns(dl_two, lpp_two)
            if result is not None:
                entry["two_column"] = True
                entry["col_lines"]  = result
                entry["pages"]      = [[]]
                two_col_count += 1

        if len(entry["pages"]) > 1:
            multi_page_count += 1

        song_layouts.append(entry)

    print(f"  {two_col_count} song(s) use two-column layout")
    print(f"  {multi_page_count} song(s) still span multiple pages")

    # TOC page count
    toc_fs           = cfg["TOC_FONT_SIZE"] - 1
    toc_lh           = toc_fs * 1.38
    toc_title_h      = 22 * mm
    entries_per_col  = max(1, int((ph - margin - toc_title_h - margin) / toc_lh))
    entries_per_page = entries_per_col * 2
    toc_page_count   = max(1, -(-len(songs) // entries_per_page))
    print(f"  TOC: {toc_page_count} page(s)  ({entries_per_page} entries/page)")

    # Assign page numbers
    current_page   = toc_page_count + 1
    song_page_nums = {}
    for layout in song_layouts:
        sid                 = layout["song"]["_id"]
        song_page_nums[sid] = current_page
        current_page       += len(layout["pages"])
    total_pages = current_page - 1
    print(f"  Total pages: {total_pages}  ({toc_page_count} TOC + {total_pages - toc_page_count} songs)")

    # Render
    print(f"Rendering → {output_path} …")
    c = pdf_canvas.Canvas(str(output_path), pagesize=(pw, ph))
    c.setTitle(cfg["PDF_TITLE"])
    c.setAuthor(cfg["PDF_AUTHOR"])
    c.setSubject(cfg["PDF_SUBJECT"])
    c.setCreator("UWS Songbook Generator")

    render_toc(c, songs, song_page_nums, toc_page_count, pw, ph, margin, cfg)

    for layout in song_layouts:
        render_song(
            c,
            song            = layout["song"],
            layout          = layout,
            song_start_page = song_page_nums[layout["song"]["_id"]],
            pw=pw, ph=ph, margin=margin,
            text_w=text_w,
            chord_col_x=chord_col_x,
            chord_col_w=chord_col_w,
            header_h=header_h,
            cfg=cfg,
        )

    c.save()
    print(f"Done ✓  →  {output_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def load_songs(songbook_dir: Path, sort_by: str = "title") -> list:
    """Load all JSON song files and sort by the given field."""
    songs = []
    for p in sorted(songbook_dir.glob("*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                songs.append(json.load(f))
        except Exception as e:
            print(f"  Warning: skipping {p.name} – {e}", file=sys.stderr)

    if sort_by == "artist":
        songs.sort(key=lambda s: (s.get("artist", "").lower(), s.get("title", "").lower()))
    else:
        songs.sort(key=lambda s: (s.get("title", "").lower(), s.get("artist", "").lower()))
    return songs


def load_config(config_path: Path) -> dict:
    """Load songbook_config.py and merge values over DEFAULT_CONFIG."""
    cfg = dict(DEFAULT_CONFIG)
    if config_path and config_path.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("songbook_config", config_path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for key in DEFAULT_CONFIG:
            if hasattr(mod, key):
                cfg[key] = getattr(mod, key)
        print(f"Config loaded from {config_path}")
    else:
        print("No config file found – using built-in defaults.")
    return cfg


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Generate a UWS Songbook PDF from JSON song files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python generate_songbook.py
  python generate_songbook.py --orientation portrait
  python generate_songbook.py --sort-by artist --output by_artist.pdf
  python generate_songbook.py --songbook-dir Testbook --output test.pdf
  python generate_songbook.py --font-size 8 --output compact.pdf
""",
    )
    parser.add_argument("--songbook-dir", type=Path, metavar="DIR",
                        help="Folder with .json song files (overrides config SONGBOOK_DIR)")
    parser.add_argument("--chord-dir", type=Path, default=Path("chords"), metavar="DIR",
                        help="Folder with chord images  (default: chords)")
    parser.add_argument("--output", "-o", type=Path, default=Path("songbook.pdf"), metavar="FILE",
                        help="Output PDF path  (default: songbook.pdf)")
    parser.add_argument("--config", type=Path, default=Path("songbook_config.py"), metavar="FILE",
                        help="Python config file  (default: songbook_config.py)")
    parser.add_argument("--orientation", choices=["landscape", "portrait"],
                        help="Page orientation (overrides config)")
    parser.add_argument("--page-size", choices=["A4", "Letter", "A5"], metavar="SIZE",
                        help="Page size: A4 | Letter | A5  (overrides config)")
    parser.add_argument("--sort-by", choices=["title", "artist"], metavar="FIELD",
                        help="Sort by: title | artist  (overrides config)")
    parser.add_argument("--font-size", type=float, metavar="PT",
                        help="Lyrics font size in points  (overrides config)")
    parser.add_argument("--no-two-column", action="store_true",
                        help="Disable two-column layout for long songs")
    args = parser.parse_args()

    cfg = load_config(args.config)

    # CLI flags override config
    if args.orientation:
        cfg["PAGE_ORIENTATION"] = args.orientation
    if args.page_size:
        cfg["PAGE_SIZE"] = args.page_size
    if args.sort_by:
        cfg["SORT_BY"] = args.sort_by
    if args.font_size:
        cfg["LYRICS_FONT_SIZE"] = args.font_size
    if args.no_two_column:
        cfg["TWO_COLUMN_LONG_SONGS"] = False

    # Resolve songbook directory: CLI flag > config > default
    if args.songbook_dir:
        songbook_dir = args.songbook_dir
    else:
        songbook_dir = Path(cfg.get("SONGBOOK_DIR", "Songbook"))

    if not songbook_dir.exists():
        print(f"Error: songbook directory not found: {songbook_dir}", file=sys.stderr)
        sys.exit(1)
    if not args.chord_dir.exists():
        print(f"Error: chord images directory not found: {args.chord_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading songs from {songbook_dir} …")
    songs = load_songs(songbook_dir, sort_by=cfg.get("SORT_BY", "title"))
    if not songs:
        print("No songs found – nothing to do.", file=sys.stderr)
        sys.exit(1)
    print(f"  {len(songs)} songs loaded  (sorted by {cfg.get('SORT_BY', 'title')})")

    generate_pdf(songs, args.chord_dir, args.output, cfg)


if __name__ == "__main__":
    main()
