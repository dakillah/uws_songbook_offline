# UWS Songbook

Localhost web app and offline PDF generator for the Ukulele Wednesdays Singapore songbook.

## Web App (localhost)

Requires Node.js and a running MongoDB instance.

```bash
npm install
node server.js
```

Then open `http://localhost:3000` in your browser.

## PDF Generator

Compiles all songs from the `Songbook/` folder into a single PDF.

### Requirements

Python 3.8+ and the `reportlab` library. Use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Generating the PDF

```bash
# Full songbook with defaults (landscape A4, sorted by title)
python generate_songbook.py

# Different orientation or page size
python generate_songbook.py --orientation portrait --page-size A4

# Sort songs by artist (also changes TOC and page headers)
python generate_songbook.py --sort-by artist --output by_artist.pdf

# Quick test using the smaller Testbook folder
python generate_songbook.py --songbook-dir Testbook --output test.pdf

# Compact version with smaller font
python generate_songbook.py --font-size 8 --output compact.pdf

# Disable two-column layout
python generate_songbook.py --no-two-column
```

```
Options:
  --songbook-dir DIR    Folder with .json song files  (default: Songbook)
  --chord-dir DIR       Folder with chord images      (default: chords)
  --output FILE         Output PDF path               (default: songbook.pdf)
  --config FILE         Python config file            (default: songbook_config.py)
  --orientation         landscape | portrait
  --page-size           A4 | Letter | A5
  --sort-by             title | artist
  --font-size PT        Lyrics font size in points
  --no-two-column       Disable two-column mode for long songs
```

### Customising the PDF

Edit `songbook_config.py` to change any aspect of the output without touching the script:

| Setting | Default | Description |
|---|---|---|
| `PAGE_ORIENTATION` | `"landscape"` | `"landscape"` or `"portrait"` |
| `PAGE_SIZE` | `"A4"` | `"A4"`, `"Letter"`, or `"A5"` |
| `MARGIN_MM` | `15` | Page margin in millimetres |
| `SORT_BY` | `"title"` | Sort & display order: `"title"` or `"artist"` |
| `TWO_COLUMN_LONG_SONGS` | `True` | Fit 2-page songs into 2 columns on 1 page |
| `LYRICS_FONT_SIZE` | `9` | Body text size in points |
| `TITLE_FONT_SIZE` | `12` | Song title header size in points |
| `TOC_FONT_SIZE` | `9` | Table of contents text size |
| `CHORD_COL_WIDTH_MM` | `36` | Width of the chord diagram column |
| `FOOTER_LEFT` | `"Compiled and prepared by…"` | Left footer text |
| `FOOTER_RIGHT` | `"Page {page}"` | Right footer text (`{page}` = page number) |
| `COLOR_CHORDS` | `"#CC0000"` | Colour of chord markers in lyrics |
| `COLOR_ACCENT` | `"#CC0000"` | Colour of decorative lines |
| `COLOR_SECTION` | `"#1144AA"` | Colour of section labels like `[chorus]` |

You can also keep multiple config files (e.g. `config_portrait.py`, `config_gig.py`) and switch between them with `--config`.

### PDF features

- **Table of Contents** – two-column, linked entries that jump directly to the song page. Sorted and labelled according to `SORT_BY`.
- **Chord diagrams** – stacked in a right-side column on every song's first page. Images are sourced from the `chords/` folder.
- **Formatted lyrics** – chords are **bold red** (including parentheses); section labels like `[chorus]` are bold italic blue.
- **Two-column mode** – songs that would span two pages are automatically reflowed into two equal columns on a single page.
- **Auto font-shrink** – if a song still doesn't fit in two pages, the font is reduced incrementally (down to 7 pt) before giving up.
- **PDF outline** – every song is added to the PDF bookmark panel for quick navigation.
- **Full Unicode rendering** – see note below.

### Unicode / special characters

Song lyrics are rendered with the **Bitstream Vera** TrueType font (bundled with reportlab), which covers all Latin characters including accented letters (é, ñ, ü…), curly quotes, en/em dashes, and ellipsis. Chinese, Japanese, and Korean lyrics are rendered with the **STSong-Light** CID font (embedded on-the-fly by PDF viewers — no extra files required).

**Known gotcha — Cyrillic lookalikes:** Copy-pasting lyrics from some websites sometimes smuggles in Cyrillic Unicode characters that look identical to Latin letters (e.g. Cyrillic `е` U+0435 instead of Latin `e`). Built-in PDF fonts cannot render these, causing them to appear as black filled squares ■ in the output. The generator automatically replaces the most common Cyrillic/Latin lookalikes and other problematic characters:

| Source character | Codepoint | Replaced with |
|---|---|---|
| е (Cyrillic small ie) | U+0435 | e |
| С (Cyrillic capital es) | U+0421 | C |
| а о р с х і А О Р Х | U+0430… | a o r c x i A O R X |
| ʼ (modifier apostrophe) | U+02BC | ' |
| ↓ (downward arrow) | U+2193 | v |
| (four-per-em space) | U+2005 | (regular space) |

If you see black squares in the output, check the raw JSON for characters with codepoints above U+00FF that are not accented Latin or CJK. Add them to the `_SUBS` table in `generate_songbook.py`.

### Song JSON format

Each song file in `Songbook/` follows this schema:

```json
{
  "_id": "...",
  "title": "What's Up",
  "artist": "4 Non Blondes",
  "lyrics": "[intro] (G) (Am) (C) (G)\n\n(G) 25 years of my life...",
  "chords": ["Am", "C", "G"]
}
```

- Chord placements within lyrics are marked with parentheses: `(G)`, `(Am)`, etc.
- Section labels use square brackets on their own line: `[chorus]`, `[intro]`, `[end]`.

### Chord images

Chord diagrams live in `chords/` as `.png` or `.jpg` files named after the chord (e.g. `Am.png`, `G7.jpg`). If an image is missing for a chord listed in a song's `chords` array, a placeholder box is drawn instead.
