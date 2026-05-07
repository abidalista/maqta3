---
name: maqta3
description: Find quotable moments in long-form Arabic videos (especially Saudi and Gulf dialect podcasts, interviews, and lectures), cut them as standalone clips, optionally reformat 16:9 → 9:16 (face-pan or split-screen), and burn RTL Arabic captions in phrase chunks. Use when the user mentions "maqta3", "مقطع", "saudi clip", "arabic clip", "thmanyah", "finjan", "socrate", "podcast clip arabic", "longform arabic", "بودكاست", or pastes a video file path or youtube url with arabic content.
---

# maqta3 (مقطع)

Find quotable moments in long-form Arabic content (Saudi and Gulf especially), cut them as standalone clips, reformat for vertical, and burn RTL Arabic captions.

## Inputs

- A video file path OR a youtube / podcast URL
- Optional: requested format (9:16, 16:9, 1:1)
- Optional: caption style preference

## Tooling (use only the fastest path)

- **yt-dlp:** URL inputs (`brew install yt-dlp`)
- **faster-whisper:** local ASR, large-v3 by default (`pip install faster-whisper`). 4 to 6x faster than openai whisper, same model.
- **ffmpeg:** with libx264 (`brew install ffmpeg`). Use `-hwaccel videotoolbox` on macOS.
- **Python 3** with numpy
- **Optional cloud ASR fallback:** ElevenLabs Scribe or AssemblyAI for thick Najdi or far field mics. Set `ELEVENLABS_API_KEY` or `ASSEMBLYAI_API_KEY` then pass `--cloud`.

Scripts in `<skill-dir>/scripts/` (where `<skill-dir>` is this folder, typically `~/.claude/skills/maqta3/`):

- `download.py` — yt-dlp wrapper
- `transcribe.py` — faster-whisper with VAD, cloud fallback hooks
- `analyze.py` — speaker timeline from two ROI motion files
- `build_pan.py` — ffmpeg crop x expression with hard cuts
- `build_ass_rtl.py` — RTL Arabic ASS captions, phrase chunks, active word highlight

Working dir: `/tmp/maqta3/` (mkdir at start, leave artifacts for debugging).

---

## Workflow

### Step 0 — Acquire source

If the user pastes a URL:

```bash
mkdir -p /tmp/maqta3
VIDEO=$(python3 <skill-dir>/scripts/download.py "$URL" /tmp/maqta3)
```

Else use the file path they gave directly.

### Step 1 — Transcribe

```bash
ffmpeg -y -hwaccel videotoolbox -i "$VIDEO" -vn -ac 1 -ar 16000 /tmp/maqta3/audio.wav
python3 <skill-dir>/scripts/transcribe.py /tmp/maqta3/audio.wav /tmp/maqta3 --model large-v3 --lang ar
```

Output: `/tmp/maqta3/audio.json` with segments and word timestamps.

The script auto picks cloud (ElevenLabs Scribe or AssemblyAI) when a key is set, else local faster-whisper. Pass `--local` to force local, `--cloud` to force cloud.

If the user reports the transcript is garbage (thick Najdi, far field mic, music bed) and they're on local:

1. suggest setting `ELEVENLABS_API_KEY` in their shell (Scribe handles Saudi dialect way better than vanilla whisper)
2. rerun, the skill will auto switch to cloud

### Step 2 — Find quotable moments

Read the transcript JSON. Do not run regex. Read it like a smart editor.

For sources over 30 minutes, chunk the transcript into 10 minute windows and review each window separately so candidates spread across the full source.

Saudi and Gulf longform signals (different from English punchline structure):

- **Story openers waiting for payoff:** "أذكر مرة" "صار لي موقف" "تذكرون لما" "في يوم من الأيام" → the punchline lands 30 to 90 seconds later, not immediately
- **Wisdom drops:** quotable one liners that stand alone, often after a pause. The thmanyah / finjan / socrate / mishwar format leans heavily on these.
- **Reversal markers:** "بس" "لكن" "المفاجأة" "والمصيبة" "الغريب" → the hook is the next sentence
- **Rhetorical setups:** "ليش؟" "وش يعني" "تدري ليش" → followed by the real answer
- **Emphatic affirmations:** "والله" "أقسم بالله" "صدق" "بصراحة" usually precede a strong statement worth clipping
- **Code switching humor:** sudden english word in arabic flow ("يعني he was like…") often marks comedic beats
- **Reactions:** laughter, "لا والله" "إيش؟" "ما يصير" "يا شيخ"
- **Religious or cultural references** that crystallize a point
- **Numbers and specifics:** dates, money amounts, ages. concrete details = clippable.

For each candidate, propose:

```
[start, end, why-it-lands, arabic title, english title, dur]
```

Aim for 30 to 90 seconds for wisdom drops, 15 to 30 for punchlines or reactions. Show 3 to 5 candidates and let the user pick.

### Step 3 — Trim

```bash
ffmpeg -y -ss "$START" -t "$DURATION" -i "$VIDEO" -c copy /tmp/maqta3/clip_$N.mp4
```

`-c copy` for instant trim. Re encode only if frame accurate cuts matter.

### Step 4 — Output format

Ask (skip if specified): "9:16 (TikTok / Reels / Shorts), 16:9 (YouTube), or 1:1 (Insta feed)?"

### Step 5 — If 16:9 → 9:16: pan vs split-screen

Detect aspect with `ffprobe`. If source is 16:9 and target is 9:16, ask:

> "(a) hard-cut pan that follows whoever is speaking (single face on screen at a time), or (b) split-screen stack with both faces visible?"

Skip the question if there is only one speaker (single talker = center crop).

#### Step 5a — Pan-between-faces (recommended for two person podcasts)

1. Sample one frame: `ffmpeg -ss <middle> -i clip.mp4 -frames:v 1 /tmp/maqta3/probe.jpg`. Read it. Eyeball each face's mouth + chin area as `x,y,w,h`. Verify with drawbox if uncertain. Iterate at most twice.

2. Per frame motion energy in each ROI:

   ```bash
   ffmpeg -y -i clip.mp4 -filter_complex "
   [0:v]split=2[a][b];
   [a]crop=$LW:$LH:$LX:$LY,format=gray,tblend=all_mode=difference,signalstats,metadata=mode=print:key=lavfi.signalstats.YAVG:file=/tmp/maqta3/L.txt[la];
   [b]crop=$RW:$RH:$RX:$RY,format=gray,tblend=all_mode=difference,signalstats,metadata=mode=print:key=lavfi.signalstats.YAVG:file=/tmp/maqta3/R.txt[ra]
   " -map "[la]" -f null - -map "[ra]" -f null -
   ```

3. Speaker timeline (min dwell 1.0s):

   ```bash
   python3 <skill-dir>/scripts/analyze.py /tmp/maqta3/L.txt /tmp/maqta3/R.txt 1.0 > /tmp/maqta3/segments.json
   ```

4. Pan x coords (source W=1920, target strip W=608):
   - LEFT_X = `face_left_center_x - 304` (clamp ≥ 0)
   - RIGHT_X = `face_right_center_x - 304` (clamp ≤ source_W - 608)

5. Render:

   ```bash
   EXPR=$(python3 <skill-dir>/scripts/build_pan.py /tmp/maqta3/segments.json $LEFT_X $RIGHT_X)
   ffmpeg -y -hwaccel videotoolbox -i clip.mp4 -filter_complex \
     "[0:v]crop=608:1080:x='$EXPR':y=0,scale=1080:1920:flags=lanczos[v]" \
     -map "[v]" -map 0:a -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p \
     -c:a aac -b:a 192k /tmp/maqta3/clip_panned.mp4
   ```

#### Step 5b — Split-screen

Two stacked tiles, 1080×960 each. Active speaker on top. The overlay flips at speaker changes.

```
[0:v]split=2[a0][a1];
[a0]crop=Wcrop:Hcrop:LX_tile:LY_tile,scale=1080:960,split=2[lt0][lt1];
[a1]crop=Wcrop:Hcrop:RX_tile:RY_tile,scale=1080:960,split=2[rt0][rt1];
[lt0][rt0]vstack[layoutL];
[rt1][lt1]vstack[layoutR];
[layoutL][layoutR]overlay=0:0:enable='<RIGHT_SPEAKER_ENABLE>'[v]
```

Build `<RIGHT_SPEAKER_ENABLE>` from `segments.json` as `between(t,a,b)+between(t,a,b)+...` over the right-speaker segments. Tile crops should target ~720×640 around each face (1.125:1 ratio to match 1080×960 after scale).

For single talker (one face only), just center crop:

```bash
ffmpeg -y -hwaccel videotoolbox -i clip.mp4 -filter_complex \
  "[0:v]crop=608:1080:656:0,scale=1080:1920:flags=lanczos[v]" \
  -map "[v]" -map 0:a -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 192k /tmp/maqta3/clip_centered.mp4
```

(`656` = `(1920 - 608) / 2` for 1920 wide source.)

### Step 6 — Captions (RTL Arabic)

Re run whisper on the trimmed clip for accurate timestamps relative to clip start:

```bash
python3 <skill-dir>/scripts/transcribe.py /tmp/maqta3/clip_panned.mp4 /tmp/maqta3 --lang ar
python3 <skill-dir>/scripts/build_ass_rtl.py /tmp/maqta3/clip_panned.json /tmp/maqta3/captions.ass --style cairo-bold
```

Default is word by word with active word highlight (matches what saudi social audiences expect). Pass `--chunk 2` or `--chunk 3` if you want phrase chunks instead.

Built in styles:

- `cairo-bold` (default): Cairo font 80pt bold, white with yellow active word, thick black outline
- `tajawal-clean`: Tajawal 70pt, no highlight, soft shadow
- `naskh`: Noto Naskh Arabic 75pt, traditional look

If the user pastes a reference image, match font + size + position by hand. Edit `build_ass_rtl.py` styles dict to add a new preset.

Required fonts (install once):

```bash
brew tap homebrew/cask-fonts
brew install --cask font-cairo font-tajawal font-noto-naskh-arabic font-ibm-plex-sans-arabic
```

Burn captions:

```bash
ffmpeg -y -i /tmp/maqta3/clip_panned.mp4 \
  -vf "subtitles=/tmp/maqta3/captions.ass" \
  -c:v libx264 -preset fast -crf 20 -c:a copy "$OUTPUT.mp4"
```

Note: libass + harfbuzz handle bidi automatically. Do not pre reverse strings. Mixed Arabic + English code switching renders correctly out of the box.

### Step 7 — Hooks and metadata

For each finished clip, generate (claude writes these directly):

- 3 Arabic hook lines (for first frame text or caption opener)
- 3 English hook lines (for cross posting)
- 5 hashtag suggestions split by platform (tiktok, reels, x, shorts)
- 1 sentence summary in arabic and english

### Step 8 — Deliver

- Save to `<source_dir>/maqta3_out/<YYYYMMDD>_<topic-slug>_<duration>s.mp4`
- Print one line per clip: arabic title, why it lands, output path
- Open the first clip with `open <path>`
- Offer to iterate: different style, retime captions, swap to split-screen, different ROI

---

## Pitfalls (read before running)

- **Long sources can OOM whisper.** faster-whisper with `vad_filter=True` handles 1+ hour fine on 16GB. If you OOM, chunk to 30 min slices and stitch JSON manually.
- **Code switching trips whisper.** Saudi speakers drop english constantly. With `--lang ar`, whisper still phoneticizes english into arabic letters sometimes. If clippability hinges on a specific english phrase, retranscribe that span with `--lang` removed (auto detect).
- **RTL ASS gotchas.** libass + harfbuzz handle bidi automatically. Do not manually reverse strings. Mixed punctuation (parens, quotes) follows source order in the file but renders with bidi rules.
- **Word by word is the default** for arabic social videos. If a clip has very fast speech and individual words flicker too quickly to read, bump to `--chunk 2`.
- **Diacritics (tashkeel)** are usually absent in social videos. If source has them, strip with `--strip-tashkeel`.
- **Najdi vs Hijazi vs Khaleeji.** Vanilla whisper handles MSA best, then Egyptian, then Khaleeji. For thick Najdi, cloud fallback is sometimes the only path.
- **Don't over tune ROIs.** Two iterations max. Motion diff is forgiving.
- **Source resolution.** If 4K, downscale to 1920×1080 first or multiply all coordinates by 2.
- **Don't run whisper on the full source twice.** Step 1 transcribes the whole thing. Step 6 transcribes only the trimmed clip.
- **State the plan in one line, then act.** Do not narrate every iteration.
