#!/usr/bin/env python3
"""Build RTL Arabic ASS subtitles from whisper-style JSON.

Word by word by default (chunk=1) with active word highlight.
libass + harfbuzz handle bidi automatically. Do not pre-reverse strings.

Usage:
  python3 build_ass_rtl.py <whisper.json> <out.ass> [--style cairo-bold|tajawal-clean|naskh] [--chunk 1] [--strip-tashkeel]

Styles:
  cairo-bold      (default)  Cairo 80pt bold, white + yellow active word, thick black outline
  tajawal-clean              Tajawal 70pt, no highlight, soft shadow
  naskh                      Noto Naskh Arabic 75pt, traditional look
"""
import argparse
import json
import re
import sys
from pathlib import Path

PLAY_W = 1080
PLAY_H = 1920

# ASS color is &HAABBGGRR (alpha first, then BGR). 00 alpha = opaque.
STYLES = {
    "cairo-bold": {
        "font": "Cairo",
        "size": 80,
        "primary": "&H00FFFFFF",   # white
        "highlight": "&H0000FFFF", # yellow
        "outline": "&H00000000",   # black
        "back": "&H80000000",      # 50% black
        "bold": 1,
        "border_style": 1,
        "outline_w": 4,
        "shadow": 2,
        "alignment": 2,            # bottom center
        "margin_v": 240,
    },
    "tajawal-clean": {
        "font": "Tajawal",
        "size": 70,
        "primary": "&H00FFFFFF",
        "highlight": "&H00FFFFFF", # no highlight
        "outline": "&H00000000",
        "back": "&H80000000",
        "bold": 0,
        "border_style": 1,
        "outline_w": 2,
        "shadow": 3,
        "alignment": 2,
        "margin_v": 220,
    },
    "naskh": {
        "font": "Noto Naskh Arabic",
        "size": 75,
        "primary": "&H00F0F0F0",
        "highlight": "&H0000D7FF", # gold
        "outline": "&H00000000",
        "back": "&H80000000",
        "bold": 1,
        "border_style": 1,
        "outline_w": 3,
        "shadow": 2,
        "alignment": 2,
        "margin_v": 220,
    },
}

# Arabic tashkeel range (combining diacritics)
TASHKEEL_RE = re.compile(r"[ً-ٰٟۖ-ۭ]")


def fmt_time(t: float) -> str:
    if t < 0:
        t = 0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    cs = int(round((s - int(s)) * 100))
    if cs == 100:
        cs = 0
        s += 1
    return f"{h}:{m:02d}:{int(s):02d}.{cs:02d}"


def build_header(style: dict) -> str:
    return f"""[Script Info]
ScriptType: v4.00+
WrapStyle: 1
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {PLAY_W}
PlayResY: {PLAY_H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style['font']},{style['size']},{style['primary']},&H000000FF,{style['outline']},{style['back']},{style['bold']},0,0,0,100,100,0,0,{style['border_style']},{style['outline_w']},{style['shadow']},{style['alignment']},60,60,{style['margin_v']},178

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def strip_tashkeel(s: str) -> str:
    return TASHKEEL_RE.sub("", s)


def collect_words(data: dict, do_strip: bool):
    words = []
    for seg in data.get("segments", []):
        for w in seg.get("words", []) or []:
            tok = w.get("word", "").strip()
            if not tok:
                continue
            if do_strip:
                tok = strip_tashkeel(tok)
            words.append({"start": float(w["start"]), "end": float(w["end"]), "word": tok})
    return words


def build_dialogues(words, chunk_size, style):
    """Emit one Dialogue line per word with that word highlighted in its phrase chunk."""
    lines = []
    primary = style["primary"]
    highlight = style["highlight"]
    show_highlight = highlight != primary

    for i in range(0, len(words), chunk_size):
        chunk = words[i:i + chunk_size]
        if not chunk:
            continue
        for j, w in enumerate(chunk):
            ws = w["start"]
            we = w["end"]
            parts = []
            for k, ww in enumerate(chunk):
                tok = ww["word"]
                if k == j and show_highlight:
                    parts.append(f"{{\\c{highlight}}}{tok}{{\\c{primary}}}")
                else:
                    parts.append(tok)
            text = " ".join(parts)
            lines.append(f"Dialogue: 0,{fmt_time(ws)},{fmt_time(we)},Default,,0,0,0,,{text}")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="whisper-style JSON")
    ap.add_argument("output", help="output .ass path")
    ap.add_argument("--style", default="cairo-bold", choices=list(STYLES))
    ap.add_argument("--chunk", type=int, default=1, help="words per phrase chunk (default 1, word by word)")
    ap.add_argument("--strip-tashkeel", action="store_true", help="remove arabic diacritics")
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    style = STYLES[args.style]
    words = collect_words(data, args.strip_tashkeel)
    if not words:
        print("no word timestamps found in input JSON", file=sys.stderr)
        sys.exit(1)

    out = build_header(style)
    out += "\n".join(build_dialogues(words, args.chunk, style)) + "\n"
    Path(args.output).write_text(out, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
