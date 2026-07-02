#!/usr/bin/env python3
"""maqta3 — one command: YouTube URL + start + end → 9:16 vertical clip.

Runs the whole pipeline in a single process so the skill never has to chain
shell commands (and the user never gets a pile of permission prompts):

  1. download only the requested span (aligned video+audio) via download.py
  2. full-bleed center-crop to 1080x1920
  3. save to ~/maqta3_out/<date>_reel_<dur>s.mp4 and open it

Usage:
  python3 make.py <url> <start> <end>

Times accept HH:MM:SS, MM:SS, or plain seconds.
"""
import subprocess
import sys
from datetime import date
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
WORK = Path("/tmp/maqta3")
OUT_DIR = Path.home() / "maqta3_out"


def to_seconds(t: str) -> float:
    t = t.strip()
    if ":" not in t:
        return float(t)
    parts = [float(p) for p in t.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    h, m, s = parts
    return h * 3600 + m * 60 + s


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        sys.exit(r.returncode)
    return r.stdout.strip()


def main():
    if len(sys.argv) != 4:
        print("usage: make.py <url> <start> <end>", file=sys.stderr)
        sys.exit(1)
    url, start, end = sys.argv[1:4]
    dur = int(round(to_seconds(end) - to_seconds(start)))

    WORK.mkdir(parents=True, exist_ok=True)
    for f in ("clip.mp4", "v.mp4", "a.m4a"):
        (WORK / f).unlink(missing_ok=True)

    # 1 — download the exact span (video+audio aligned)
    clip = run([
        "python3", str(SKILL_DIR / "download.py"), url, str(WORK),
        "--start", start, "--end", end,
    ]).splitlines()[-1]

    # 2 + 3 — full-bleed 9:16 center crop, straight into the output file
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{date.today():%Y%m%d}_reel_{dur}s.mp4"
    run([
        "ffmpeg", "-y", "-hwaccel", "videotoolbox", "-i", clip,
        "-filter_complex",
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[v]",
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", str(out),
    ])

    subprocess.run(["open", str(out)])
    print(f"{out}  ({dur}s)")


if __name__ == "__main__":
    main()
