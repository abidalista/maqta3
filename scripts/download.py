#!/usr/bin/env python3
"""yt-dlp wrapper. Download a URL into a directory, prefer mp4, print final path.

Usage:
  python3 download.py <url> <out_dir> [--start HH:MM:SS] [--end HH:MM:SS]

With --start/--end, only that span is downloaded (yt-dlp --download-sections),
which is far faster than pulling a full-length video just to trim it.

Requires:
  brew install yt-dlp     (or pip install yt-dlp)   + ffmpeg for span cuts

Minimum yt-dlp version: 2022.04.08 (introduces the `after_move:filepath` print key
this script relies on for its primary path resolution). Older yt-dlp will silently
fall through to the newest-mp4-in-dir fallback. Span downloads need ≥ 2023.01.06.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def to_seconds(t: str) -> str:
    """Accept HH:MM:SS, MM:SS, or seconds; return seconds as a string."""
    t = t.strip()
    if ":" not in t:
        return str(float(t))
    parts = [float(p) for p in t.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    h, m, s = parts
    return str(h * 3600 + m * 60 + s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("out_dir")
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--cookies-from-browser", default="none",
                    help="Browser to read YouTube cookies from. Default 'none' — the "
                         "tv player client (below) already bypasses the bot block, so "
                         "no cookies (and no macOS Keychain prompt) are needed. Only set "
                         "this for age-restricted or members-only videos.")
    args = ap.parse_args()

    cookie_args = []
    if args.cookies_from_browser and args.cookies_from_browser.lower() != "none":
        cookie_args = ["--cookies-from-browser", args.cookies_from_browser]

    # YouTube bot-blocks the default web client ("Sign in to confirm you're not a
    # bot") and the plain tv client hands back DRM-only formats. These clients
    # return real formats with NO cookies (so no macOS Keychain prompt). Prepend
    # to every yt-dlp call.
    client_args = ["--extractor-args", "youtube:player_client=tv_embedded,web_safari,android"]
    base = client_args + cookie_args

    url = args.url
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not shutil.which("yt-dlp"):
        print("yt-dlp not found. install with: brew install yt-dlp (need ≥ 2022.04.08)", file=sys.stderr)
        sys.exit(2)

    # Span path: yt-dlp's section MERGE corrupts audio (truncates or drops it),
    # so download video-only and audio-only over a PADDED window separately,
    # then mux + trim precisely with ffmpeg. Streams stay aligned.
    if args.start is not None and args.end is not None:
        if not shutil.which("ffmpeg"):
            print("ffmpeg not found (needed for span mux/trim). install: brew install ffmpeg", file=sys.stderr)
            sys.exit(2)
        s = float(to_seconds(args.start))
        e = float(to_seconds(args.end))
        dur = e - s
        pad = 12.0
        p_start = max(0.0, s - pad)
        offset = s - p_start  # where the real start sits inside the padded window
        section = f"*{p_start}-{e + pad}"
        v = out_dir / "v.mp4"
        a = out_dir / "a.m4a"
        for spec, dest in (("bv*[ext=mp4]/bv*/b[ext=mp4]/b", v),
                           ("ba[ext=m4a]/ba/b[ext=mp4]/b", a)):
            r = subprocess.run(
                ["yt-dlp", "-f", spec, "--no-playlist", "--download-sections", section,
                 *base, "-o", str(dest), url],
                capture_output=True, text=True,
            )
            if r.returncode != 0:
                print(r.stderr, file=sys.stderr)
                sys.exit(r.returncode)
        out = out_dir / "clip.mp4"
        r = subprocess.run(
            ["ffmpeg", "-y", "-hwaccel", "videotoolbox",
             "-ss", str(offset), "-t", str(dur), "-i", str(v),
             "-ss", str(offset), "-t", str(dur), "-i", str(a),
             "-map", "0:v", "-map", "1:a",
             "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
            sys.exit(r.returncode)
        print(out)
        return

    template = str(out_dir / "%(title).80s_%(id)s.%(ext)s")
    cmd = [
        "yt-dlp",
        "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "-o", template,
        "--print", "after_move:filepath",
        *base,
        url,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stderr, file=sys.stderr)
        sys.exit(res.returncode)

    final = res.stdout.strip().splitlines()
    if final:
        print(final[-1])
        return

    # fallback: newest mp4 in out_dir
    files = sorted(out_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if files:
        print(files[0])
    else:
        print("download produced no mp4", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
