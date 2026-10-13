# Span download

Span download pulls only a padded window of a YouTube URL and writes an aligned `clip.mp4` (video + audio) into a directory the caller names, without cropping to 9:16.

## Sub-features

- `span-write` prints the path of `clip.mp4` and exits `0`.
- `span-av` produces a file with both a video stream and an audio stream.
- `span-duration` trims to the requested start/end, not the padded window.

## How to get to it (user POV)

- Run `python3 scripts/download.py <url> <out_dir> --start <t> --end <t>`.
- Run `python3 scripts/make.py …` (it calls this helper; prove that coupling via [make-clip](./make-clip.md), not here).

## Driving it with control-maqta3

Preconditions:

- Baseline launch + `control-maqta3 doctor` reports `ok: yes`.
- Network can reach YouTube.
- Out dir is `$verify_home/span-out` and does not yet contain `clip.mp4`.

- **Download span.** Run `control-maqta3 download "https://www.youtube.com/watch?v=jNQXAC9IVRw" "$verify_home/span-out" --start 1 --end 4`. Exit code `0`. stdout's last path line is `$verify_home/span-out/clip.mp4`.
- **Confirm AV.** Run `control-maqta3 probe "$verify_home/span-out/clip.mp4"`. `vcodec` and `acodec` are both set (h264 and aac). `duration` is between `2.5` and `3.5`. Width/height are the **source** dimensions, not 1080×1920.
- **Proof.** Run `control-maqta3 evidence span-download --clip "$verify_home/span-out/clip.mp4"`. Artifacts include `cmd.json` with `--start`/`--end` and `probe.txt` showing audio + video. Geometry must **not** be asserted as 1080×1920 (crop is make-clip).

## Gotchas

- `--start`/`--end` must both be present. Omitting one takes the full-video download path, which is a different command and not this feature.
- yt-dlp `--download-sections` on a non-YouTube URL is not this user path. Do not substitute a local HTTP mp4 and call span-download verified.
- `make.py` deletes `clip.mp4` / `v.mp4` / `a.m4a` in `/tmp/maqta3` before it downloads. Drive this feature into `$verify_home/span-out`, not `/tmp/maqta3`, so a later make-clip run cannot eat the evidence source before you copy it.
- Audio/video alignment is the reason this helper exists. A clip whose audio ends early (duration much shorter than the requested span, or missing `acodec`) is a fail.
