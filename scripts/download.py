#!/usr/bin/env python3
"""yt-dlp wrapper. Download a URL into a directory, prefer mp4, print final path.

Usage:
  python3 download.py <url> <out_dir>

Requires:
  brew install yt-dlp     (or pip install yt-dlp)

Minimum yt-dlp version: 2022.04.08 (introduces the `after_move:filepath` print key
this script relies on for its primary path resolution). Older yt-dlp will silently
fall through to the newest-mp4-in-dir fallback.
"""
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 3:
        print("usage: download.py <url> <out_dir>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    if not shutil.which("yt-dlp"):
        print("yt-dlp not found. install with: brew install yt-dlp (need ≥ 2022.04.08)", file=sys.stderr)
        sys.exit(2)

    template = str(out_dir / "%(title).80s_%(id)s.%(ext)s")
    cmd = [
        "yt-dlp",
        "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "-o", template,
        "--print", "after_move:filepath",
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
