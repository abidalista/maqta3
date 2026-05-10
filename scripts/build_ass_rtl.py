#!/usr/bin/env python3
"""Build RTL Arabic ASS subtitles from whisper-style JSON.

Two modes:
  --mode netflix  (default)  one Dialogue per sentence (split on . ! ? ؟ from the transcript),
                             period appended only on real sentence ends, non-overlapping spans
  --mode word                one Dialogue per word with active-word highlight in its phrase chunk

libass + harfbuzz handle bidi automatically. Do not pre-reverse strings.
The macos libass+harfbuzz pipeline emits a phantom .notdef glyph before every lam-alef
ligature regardless of font, so this builder pre-substitutes the precomposed Arabic
Presentation Forms-A glyph (U+FEFB / U+FEFC etc.) before writing dialogue text.
See KNOWN-ISSUES.md for repro details.

Usage:
  python3 build_ass_rtl.py <whisper.json> <out.ass>
      [--style cairo-bold|tajawal-clean|naskh]
      [--mode word|netflix]
      [--chunk 1]
      [--strip-tashkeel]

Styles:
  cairo-bold      (default)  Cairo 80pt bold, white + yellow active word, thick black outline
  tajawal-clean              Tajawal 70pt, no highlight, soft shadow
  naskh                      Noto Naskh Arabic 75pt, traditional look
"""
import argparse
import json
import re
import shutil
import subprocess
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
TASHKEEL_RE = re.compile(r"[ً-ٰٟۖ-ۭ]")

# lam-alef precomposed substitutions (workaround for libass+harfbuzz tofu boxes)
LAM_ALEF = {
    ("ل", "ا"): ("ﻻ", "ﻼ"),  # lam-alef
    ("ل", "أ"): ("ﻷ", "ﻸ"),  # lam-alef-with-hamza-above
    ("ل", "إ"): ("ﻹ", "ﻺ"),  # lam-alef-with-hamza-below
    ("ل", "آ"): ("ﻵ", "ﻶ"),  # lam-alef-with-madda-above
}
# letters with initial/medial connecting forms (non-exhaustive but covers all standard letters)
CONNECTING = set("بتثجحخسشصضطظعغفقكلمنهي")

SENTENCE_END = re.compile(r"[.!?؟]$")


def fmt_time(t: float) -> str:
    """ASS time format: H:MM:SS.cs. Cascades centisecond → second → minute carry."""
    if t < 0:
        t = 0
    cs_total = int(round(t * 100))
    cs = cs_total % 100
    s = (cs_total // 100) % 60
    m = (cs_total // 6000) % 60
    h = cs_total // 360000
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def strip_tashkeel(s: str) -> str:
    return TASHKEEL_RE.sub("", s)


def precompose_lam_alef(text: str) -> str:
    """Replace lam-alef sequences with their precomposed presentation-form glyph.

    Picks final form when preceded by a connecting letter, isolated form otherwise.
    Bypasses the macos libass+harfbuzz shaping bug that emits a phantom missing-mark
    slot before every lam-alef cluster.
    """
    out = []
    i = 0
    while i < len(text):
        if i + 1 < len(text) and (text[i], text[i + 1]) in LAM_ALEF:
            iso, fin = LAM_ALEF[(text[i], text[i + 1])]
            prev = out[-1] if out else ""
            out.append(fin if prev in CONNECTING else iso)
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def escape_ass(text: str) -> str:
    """Escape ASS dialogue control characters.

    ASS interprets {...} as override-tag groups and \\N as a hard line break, so any
    transcript containing these would be mis-rendered.
    """
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def prepare_text(raw: str, do_strip: bool) -> str:
    """Apply tashkeel, lam-alef, and ASS escapes in the right order."""
    t = raw
    if do_strip:
        t = strip_tashkeel(t)
    t = precompose_lam_alef(t)
    t = escape_ass(t)
    return t


def warn_if_font_missing(style: dict) -> None:
    """fc-match the requested font and warn on stderr if it's not actually installed."""
    if not shutil.which("fc-match"):
        return
    try:
        res = subprocess.run(
            ["fc-match", style["font"]],
            capture_output=True, text=True, timeout=5,
        )
    except (subprocess.SubprocessError, OSError):
        return
    out = res.stdout.strip()
    # fc-match output: "<file>: \"<family>\" \"<style>\""
    if style["font"].lower() not in out.lower():
        print(
            f"[build_ass_rtl] WARNING: requested font '{style['font']}' not found by fc-match. "
            f"libass will silently fall back. fc-match said: {out}",
            file=sys.stderr,
        )


def build_header(style: dict) -> str:
    return f"""[Script Info]
ScriptType: v4.00+
WrapStyle: 0
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


def collect_words(data: dict, do_strip: bool):
    """Flatten word-level timestamps. Strip leading/trailing whitespace only.

    Sentence-ending punctuation is preserved on the word that carries it so netflix
    mode can detect sentence boundaries.
    """
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


def build_dialogues_word(words, chunk_size, style):
    """One Dialogue per word, highlighted within its chunk_size phrase window."""
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
                tok = escape_ass(precompose_lam_alef(ww["word"]))
                if k == j and show_highlight:
                    parts.append(f"{{\\c{highlight}}}{tok}{{\\c{primary}}}")
                else:
                    parts.append(tok)
            text = " ".join(parts)
            lines.append(f"Dialogue: 0,{fmt_time(ws)},{fmt_time(we)},Default,,0,0,0,,{text}")
    return lines


def build_dialogues_netflix(words, _style):
    """One Dialogue per sentence. Period only on real sentence ends. Non-overlapping spans."""
    if not words:
        return []
    # bucket into sentences using trailing punctuation on the original token
    sentences = []
    cur = []
    for w in words:
        ends = bool(SENTENCE_END.search(w["word"]))
        clean = w["word"].rstrip(".!?؟،")
        cur.append({"start": w["start"], "end": w["end"], "word": clean, "ends": ends})
        if ends:
            sentences.append({"words": cur, "closes": True})
            cur = []
    if cur:
        sentences.append({"words": cur, "closes": False})
    # non-overlapping spans. ordering matters: extend → readability minimum →
    # clamp by next sentence start (clamp wins to prevent overlap, even if it makes
    # the line shorter than the readability minimum).
    lines = []
    for i, sent in enumerate(sentences):
        s = sent["words"][0]["start"]
        e = sent["words"][-1]["end"] + 0.25
        if e - s < 0.9:
            e = s + 0.9
        if i + 1 < len(sentences):
            e = min(e, sentences[i + 1]["words"][0]["start"] - 0.02)
        if e <= s:
            e = s + 0.05  # next sentence overlaps this one in transcript; blink fast
        text = " ".join(w["word"] for w in sent["words"]).strip()
        text = precompose_lam_alef(text)
        text = escape_ass(text)
        if sent["closes"]:
            text += "."
        lines.append(f"Dialogue: 0,{fmt_time(s)},{fmt_time(e)},Default,,0,0,0,,{text}")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="whisper-style JSON")
    ap.add_argument("output", help="output .ass path")
    ap.add_argument("--style", default="cairo-bold", choices=list(STYLES))
    ap.add_argument("--mode", default="netflix", choices=["word", "netflix"],
                    help="netflix: per-sentence captions (default). word: per-word with active highlight.")
    ap.add_argument("--chunk", type=int, default=1,
                    help="word mode only: words per phrase chunk for highlight (default 1)")
    ap.add_argument("--strip-tashkeel", action="store_true", help="remove arabic diacritics")
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    style = STYLES[args.style]
    warn_if_font_missing(style)

    words = collect_words(data, args.strip_tashkeel)
    if not words:
        print("no word timestamps found in input JSON", file=sys.stderr)
        sys.exit(1)

    if args.mode == "netflix":
        body = build_dialogues_netflix(words, style)
    else:
        body = build_dialogues_word(words, args.chunk, style)

    out = build_header(style) + "\n".join(body) + "\n"
    Path(args.output).write_text(out, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
