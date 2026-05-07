#!/usr/bin/env python3
"""Speaker timeline from two ROI motion log files.

Each input is the metadata file produced by ffmpeg
"signalstats,metadata=mode=print:key=lavfi.signalstats.YAVG:file=...".
The script parses (t, YAVG) per ROI, smooths, picks the louder ROI per frame,
collapses runs, and merges runs shorter than min_dwell into the prior speaker.

Usage:
  python3 analyze.py <L.txt> <R.txt> <min_dwell_seconds> [> segments.json]
"""
import json
import re
import sys


PTS_RE = re.compile(r"pts_time:([\d.]+)")
VAL_RE = re.compile(r"lavfi\.signalstats\.YAVG=([\d.]+)")


def parse_motion(path: str):
    rows = []
    cur_t = None
    with open(path) as f:
        for line in f:
            m = PTS_RE.search(line)
            if m:
                cur_t = float(m.group(1))
                continue
            m = VAL_RE.search(line)
            if m and cur_t is not None:
                rows.append((cur_t, float(m.group(1))))
                cur_t = None
    return rows


def smooth(vals, window=5):
    if not vals:
        return vals
    half = window // 2
    out = []
    for i in range(len(vals)):
        a = max(0, i - half)
        b = min(len(vals), i + half + 1)
        out.append(sum(vals[a:b]) / (b - a))
    return out


def main():
    if len(sys.argv) < 4:
        print("usage: analyze.py L.txt R.txt min_dwell_seconds", file=sys.stderr)
        sys.exit(1)

    L = parse_motion(sys.argv[1])
    R = parse_motion(sys.argv[2])
    min_dwell = float(sys.argv[3])

    n = min(len(L), len(R))
    if n == 0:
        print("[]")
        return

    times = [L[i][0] for i in range(n)]
    lv = smooth([L[i][1] for i in range(n)])
    rv = smooth([R[i][1] for i in range(n)])

    # bias toward whichever has consistently higher motion; ties go to last speaker
    last = "L" if lv[0] >= rv[0] else "R"
    speakers = []
    for i in range(n):
        diff = lv[i] - rv[i]
        if abs(diff) < 0.05:
            speakers.append(last)
        else:
            last = "L" if diff > 0 else "R"
            speakers.append(last)

    # collapse runs
    runs = []
    cur = speakers[0]
    start_t = times[0]
    for i in range(1, n):
        if speakers[i] != cur:
            runs.append({"start": start_t, "end": times[i], "speaker": cur})
            cur = speakers[i]
            start_t = times[i]
    runs.append({"start": start_t, "end": times[-1], "speaker": cur})

    # merge runs shorter than min_dwell into the prior run
    merged = []
    for r in runs:
        dur = r["end"] - r["start"]
        if merged and dur < min_dwell:
            merged[-1]["end"] = r["end"]
        else:
            merged.append(r)

    print(json.dumps(merged, indent=2))


if __name__ == "__main__":
    main()
