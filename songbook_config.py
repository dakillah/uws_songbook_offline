# songbook_config.py
"""
UWS Songbook PDF – Configuration Template
==========================================
Edit this file to customise the generated PDF.
All settings here override the built-in defaults in generate_songbook.py.

Run:
    python generate_songbook.py               # picks up this file automatically
    python generate_songbook.py --config path/to/other_config.py
"""

# ── Source data ───────────────────────────────────────────────────────────────
# Folder containing the .json song files. Change to "Testbook" for quick tests.
SONGBOOK_DIR = "Songbook"

# ── Page layout ───────────────────────────────────────────────────────────────
PAGE_ORIENTATION = "landscape"   # "landscape"  |  "portrait"
PAGE_SIZE        = "A4"          # "A4"  |  "Letter"  |  "A5"

# ── Margins ───────────────────────────────────────────────────────────────────
MARGIN_MM = 15                   # millimetres – applied to all four sides

# ── Font sizes (points) ───────────────────────────────────────────────────────
LYRICS_FONT_SIZE = 9             # lyrics body text
TITLE_FONT_SIZE  = 12            # song title in page header
TOC_FONT_SIZE    = 9             # table of contents entries

# ── Chord diagram column ──────────────────────────────────────────────────────
CHORD_COL_WIDTH_MM    = 36       # width of the right-side chord column (mm)
                                  # images contain their own chord-name labels
CHORD_SPLIT_THRESHOLD = 6        # when a song has more chords than this, the chord
                                  # column is split into two equal sub-columns so the
                                  # images remain a usable size

# ── Song ordering ─────────────────────────────────────────────────────────────
# Controls both the sort order and how entries are displayed in the TOC and
# as the page header for each song.
#   "title"  → sorted A–Z by title;  displayed as  Title — Artist
#   "artist" → sorted A–Z by artist; displayed as  Artist — Title
SORT_BY = "title"

# ── Two-column layout for long songs ─────────────────────────────────────────
# When True, songs that would otherwise span 2 pages are instead typeset in
# two equal columns on a single page, keeping everything on one page.
TWO_COLUMN_LONG_SONGS = True

# ── Footer ────────────────────────────────────────────────────────────────────
# {page} is replaced with the current page number at render time.
FOOTER_LEFT      = "Compiled and prepared by Ukulele Wednesdays Singapore"
FOOTER_RIGHT     = "Page {page}"
FOOTER_FONT_SIZE = 7

# ── Colours (CSS hex strings) ─────────────────────────────────────────────────
COLOR_CHORDS  = "#CC0000"        # chord markers in lyrics  e.g. (G), (Am)
COLOR_ACCENT  = "#CC0000"        # decorative lines under song title
COLOR_SECTION = "#1144AA"        # section labels  e.g. [chorus], [intro]
                                  # displayed in bold italic

# ── PDF metadata ──────────────────────────────────────────────────────────────
PDF_TITLE   = "UWS Songbook"
PDF_AUTHOR  = "Ukulele Wednesdays Singapore"
PDF_SUBJECT = "Ukulele Chord Songbook"

# ── Table of Contents ─────────────────────────────────────────────────────────
TOC_TITLE = "Table of Contents"
