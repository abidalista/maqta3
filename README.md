# maqta3 (مَقطع)

أداة لـ [Claude Code](https://claude.com/claude-code) تقصّ أي لحظة من فيديو يوتيوب وتحوّلها لمقطع عمودي جاهز لتيك توك وريلز وشورتس.

A [Claude Code](https://claude.com/claude-code) skill that cuts any moment out of a YouTube video and turns it into a vertical clip ready for TikTok, Reels, and Shorts.

---

## بالعربي

### وش تسوي

تعطيها رابط يوتيوب، ووقت البداية، ووقت النهاية. تسوي لك مقطع عمودي (9:16) بجودة عالية، جاهز ترفعه على تيك توك مباشرة. بدون تفريغ نص، بدون ترجمة، بدون أسئلة. شيء واحد بس، ويسويه صح.

### التركيب

```bash
git clone https://github.com/abidalista/maqta3.git ~/.claude/skills/maqta3
brew install ffmpeg yt-dlp
```

أعد فتح Claude Code، واكتب `/maqta3` في أي محادثة.

### الاستخدام

في Claude Code اكتب:

```
/maqta3 https://youtube.com/watch?v=xxxx 34:57 37:00
```

الرابط، ثم وقت البداية، ثم وقت النهاية. المقطع ينحفظ في `~/maqta3_out/` ويفتح لك تلقائياً.

---

## English

### What it does

Give it a YouTube URL, a start time, and an end time. It hands you a high-quality vertical (9:16) clip, ready to upload straight to TikTok. No transcription, no captions, no questions. It does one thing and does it right.

Under the hood it downloads **only** the span you asked for (fast — it never pulls the whole video), then scales it full-bleed into a 1080×1920 frame with hardware acceleration.

### Requirements

- [Claude Code](https://claude.com/claude-code)
- `ffmpeg` and `yt-dlp` (`brew install ffmpeg yt-dlp`)
- macOS (uses VideoToolbox for hardware-accelerated encoding — works on Linux/Windows if you drop the `-hwaccel videotoolbox` flag)

### Install

```bash
git clone https://github.com/abidalista/maqta3.git ~/.claude/skills/maqta3
```

Restart Claude Code and `/maqta3` is available as a slash command.

### Usage

```
/maqta3 https://youtube.com/watch?v=xxxx 34:57 37:00
```

URL, start time, end time. Times accept `HH:MM:SS`, `MM:SS`, or plain seconds. The clip lands in `~/maqta3_out/` and opens automatically.

## Repo structure

```
maqta3/
├── SKILL.md            # the skill prompt Claude Code reads
├── scripts/
│   └── download.py     # yt-dlp wrapper — downloads and trims just the span
└── README.md
```

## License

MIT — see [LICENSE](LICENSE).

Built by [abidalista](https://github.com/abidalista).
