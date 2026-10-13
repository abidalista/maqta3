# Cut a 9:16 reel

Cut a 9:16 reel takes a YouTube URL plus a start and end time and writes a 1080×1920 mp4 of that exact span, named by date and duration, into the user's `maqta3_out` directory.

## Sub-features

- `make-run` runs the one-command pipeline from URL + timestamps to a saved clip.
- `make-span-only` downloads only the requested window, not the full video.
- `make-crop` emits 1080×1920 full-bleed (no letterbox).
- `make-name` writes `$verify_home/maqta3_out/<YYYYMMDD>_reel_<dur>s.mp4` and prints that path with `(<dur>s)`.

## How to get to it (user POV)

- Run `python3 scripts/make.py <url> <start> <end>` in a terminal.
- Invoke `/maqta3 <url> <start> <end>` in Claude Code (that command is this same script).

## Driving it with control-maqta3

Preconditions:

- Baseline launch + `control-maqta3 doctor` reports `ok: yes`.
- Network can reach YouTube.
- No clip named with today's date and `_reel_3s.mp4` already sits in `$verify_home/maqta3_out/` (a fresh verify_home satisfies this).

- **Cut clip.** Ask maqta3 for seconds 1–4 of the public 19s sample `jNQXAC9IVRw`. Run `control-maqta3 make "https://www.youtube.com/watch?v=jNQXAC9IVRw" 1 4`. Exit code `0`. stdout contains a path under `$verify_home/maqta3_out/` matching `*_reel_3s.mp4` and the suffix `(3s)`.
- **Confirm file.** The printed path exists on disk. Run `control-maqta3 probe` on that path. `width: 1080`, `height: 1920`, `pix_fmt: yuv420p`, `vcodec: h264`, `acodec: aac`, `duration` between `2.5` and `3.5`.
- **Visual frame.** Run `control-maqta3 frame "$CLIP" artifacts/make-clip/frame.png`. The PNG exists. A second `control-maqta3 probe artifacts/make-clip/frame.png` is not required; the mp4 probe is the geometry proof.
- **Proof.** Capture action + file. Run `control-maqta3 evidence make-clip --clip "$CLIP"`. `artifacts/make-clip/` contains `cmd.json`, `stdout.txt`, `exit.txt` (`0`), `clip.mp4`, `probe.txt` with 1080×1920, and `frame.png`.

## Gotchas

- YouTube bot-blocks or format failures show up on stderr from yt-dlp. That is a failed proof, not a reason to swap in a local mp4.
- `make.py` work files live in `/tmp/maqta3`. A second run without this lock overwrites `v.mp4` / `a.m4a` / `clip.mp4` mid-flight.
- Duration in the filename is `int(round(end - start))`, so `1` to `4` is `3s`. Assert the name from that rule, not from ffprobe's fractional duration.
- On Linux, VideoToolbox is off and `open` is skipped. Do not treat a missing QuickTime window as failure. On Darwin, `open` should launch the clip; that branch is unverified until a macOS run.
- Capture evidence before `control-maqta3 cleanup`. Cleanup deletes `$verify_home` (including the original clip) and keeps `artifacts/`.
