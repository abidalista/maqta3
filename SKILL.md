---
name: maqta3
description: Turn a YouTube URL plus a start and end timestamp into a 9:16 TikTok/Reels clip of that exact span. Use when the user runs /maqta3 or pastes a youtube url with an in/out time and wants a vertical reel. Triggers on "maqta3", "مقطع", "reel", "tiktok clip", "بودكاست", or a youtube url + timestamps.
---

# maqta3 (مقطع)

One job: take a **YouTube URL + start time + end time**, and produce a **9:16 vertical clip** of that exact span, ready for TikTok / Reels / Shorts.

No clip-hunting. No captions. No questions. No hooks or metadata. Just cut the span the user gave and format it vertical.

## Input

The user gives three things (in any reasonable phrasing):

- a YouTube URL
- a start time
- an end time

Accept `HH:MM:SS`, `MM:SS`, or seconds. If any of the three is missing, ask once for the missing piece and stop — do not guess.

## Fixed defaults (do not ask)

- Output: **9:16**, 1080×1920
- No captions, no transcription
- Output dir: `~/maqta3_out/`

`<skill-dir>` = this folder (`~/.claude/skills/maqta3/`).

## Workflow

State the plan in one line, then run it top to bottom.

### 1 — Download only the requested span

```bash
mkdir -p /tmp/maqta3
python3 <skill-dir>/scripts/download.py "$URL" /tmp/maqta3 --start "$START" --end "$END"
```

Result: `/tmp/maqta3/clip.mp4` = exactly the requested span, video + audio aligned.

**Why the script downloads video and audio separately:** yt-dlp's `--download-sections` corrupts the *merged* output — it truncates or drops the audio stream (e.g. 123s video but only 112s audio, so sound cuts out early). The script instead pulls a padded video-only section and a padded audio-only section, then muxes and trims to the exact window with ffmpeg. Do not "simplify" it back to a single merged `--download-sections` call.

### 2 — Make it 9:16 (full-bleed center crop)

Scale the source to **cover** the whole 1080×1920 frame, then center-crop. Sharp, full-screen, no blur, no bars, no letterbox — ready to upload straight to TikTok. Moderate zoom (shows the center of the frame filling the full height), works for one speaker or a centered two-shot.

```bash
ffmpeg -y -hwaccel videotoolbox -i /tmp/maqta3/clip.mp4 -filter_complex \
  "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[v]" \
  -map "[v]" -map 0:a -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 192k /tmp/maqta3/clip_916.mp4
```

Result: `/tmp/maqta3/clip_916.mp4`.

(If the framing ever needs to favor a side — e.g. the subject sits off-center — shift the crop with `crop=1080:1920:x=<px>:0` instead of the default centered crop. Default is centered.)

### 3 — Deliver

The 9:16 file from step 2 is the final clip. No captions, no transcription.

```bash
mkdir -p ~/maqta3_out
OUT=~/maqta3_out/$(date +%Y%m%d)_reel_${DUR}s.mp4
cp /tmp/maqta3/clip_916.mp4 "$OUT"
open "$OUT"
```

Print one line: the output path and duration. Done.

## Notes / pitfalls

- Source 4K → downscale to 1920×1080 first, or double all crop coordinates.
- Never transcribe or burn captions — the deliverable is just the vertical cut.
