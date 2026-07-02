---
name: maqta3
description: Turn a YouTube URL plus a start and end timestamp into a 9:16 TikTok/Reels clip of that exact span. Use when the user runs /maqta3 or pastes a youtube url with an in/out time and wants a vertical reel. Triggers on "maqta3", "مقطع", "reel", "tiktok clip", "بودكاست", or a youtube url + timestamps.
---

# maqta3 (مقطع)

One job: take a **YouTube URL + start time + end time**, and produce a **9:16 vertical clip** of that exact span, ready for TikTok / Reels / Shorts.

No clip-hunting. No captions. No hooks or metadata. Just cut the span the user gave and format it vertical.

## Act, don't ask

Once you have the URL, start, and end, **run it — do not ask for confirmation.** No "want me to proceed?", no "should I go ahead?", no yes/no checkpoints. The user already told you what they want by giving you the three inputs. The whole thing is one command. Run it and report the result.

The ONLY time you may ask is if one of the three inputs is genuinely missing — then ask once for just the missing piece and stop.

## Input

The user gives three things (in any reasonable phrasing): a **YouTube URL**, a **start time**, an **end time**. Times accept `HH:MM:SS`, `MM:SS`, or plain seconds.

## Run it

One command does everything — download the exact span, crop to full-bleed 9:16, save to `~/maqta3_out/`, and open it:

```bash
python3 <skill-dir>/scripts/make.py "$URL" "$START" "$END"
```

`<skill-dir>` = `~/.claude/skills/maqta3/`. It prints the output path and duration. That's the whole job — relay that one line and stop.

## What it does under the hood (don't re-implement — just call make.py)

- **Span download** (`download.py`): pulls video-only + audio-only over a padded window, then muxes/trims with ffmpeg. This exists because yt-dlp's `--download-sections` corrupts the *merged* audio (e.g. 123s video but 112s audio → sound cuts out early). It also uses `player_client=tv_embedded,web_safari,android` to bypass YouTube's bot-block with **no cookies** (so no macOS Keychain prompt). Do not "simplify" either of these back.
- **9:16 crop**: scales the source to *cover* 1080×1920, then center-crops. Sharp, full-screen, no blur/bars/letterbox. Works for one speaker or a centered two-shot.

## Notes / pitfalls

- If framing needs to favor a side (subject sits off-center), edit the `crop` in `make.py` to `crop=1080:1920:x=<px>:0`. Default is centered.
- Never transcribe or burn captions — the deliverable is just the vertical cut.
