#!/usr/bin/env python3
"""Build an ffmpeg crop x expression with hard cuts at speaker changes.

Input: segments.json (list of {start, end, speaker: L|R}) + LEFT_X + RIGHT_X.
Output: a single expression suitable for ffmpeg crop=W:H:x='<EXPR>':y=0.

Form: nested if(between(t, a, b), x_for_segment, ... else last_x)

Usage:
  python3 build_pan.py <segments.json> <LEFT_X> <RIGHT_X>
"""
import json
import sys


def main():
    if len(sys.argv) < 4:
        print("usage: build_pan.py segments.json LEFT_X RIGHT_X", file=sys.stderr)
        sys.exit(1)

    segs = json.loads(open(sys.argv[1]).read())
    LX = int(sys.argv[2])
    RX = int(sys.argv[3])

    if not segs:
        print(LX)
        return

    parts = []
    for s in segs:
        x = LX if s["speaker"] == "L" else RX
        parts.append((float(s["start"]), float(s["end"]), x))

    expr = str(parts[-1][2])
    for start, end, x in reversed(parts[:-1]):
        expr = f"if(between(t,{start:.3f},{end:.3f}),{x},{expr})"
    print(expr)


if __name__ == "__main__":
    main()
