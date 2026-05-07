# maqta3 (مقطع)

A Claude Code skill that turns long-form Arabic videos (Saudi and Gulf especially) into social-ready clips with RTL captions.

> سكِل لـ Claude Code يحول البودكاست والمقابلات الطويلة إلى مقاطع جاهزة للسوشل ميديا، بترجمة عربية وتنسيق عمودي.

[العربية في الأسفل](#بالعربي)

---

## What it does

Point it at an Arabic video file or a youtube URL and it will:

1. Transcribe with faster-whisper large-v3 (local, free) or fall back to ElevenLabs Scribe / AssemblyAI for thick dialect
2. Read the transcript like an editor and propose 3 to 5 clip candidates tuned to Saudi longform signals (story openers, wisdom drops, reversal markers, code switching)
3. Trim the chosen moment, reframe 16:9 to 9:16 with face-pan or split-screen, burn RTL Arabic captions word by word with active word highlight
4. Generate Arabic + English hooks and hashtags for cross posting

Built for talking head dialogue (interviews, podcasts, sermons, lectures, two person setups).

## Why this skill

The Arabic and Saudi case needs more than a generic clipper:

- An ASR path that handles dialect (faster-whisper large-v3 + cloud fallback for thick Najdi)
- RTL captions with bidi handling and Arabic fonts (Cairo, Tajawal, Naskh)
- Word by word captions with active word highlight (the Saudi social standard)
- Saudi specific quotable signals (والله, لكن, أذكر مرة, story arc payoffs that take 30 to 90 seconds, not 10 second punchlines)
- yt-dlp built in for podcast URLs

## Requirements

- macOS (uses VideoToolbox for hwaccel. Linux works if you drop the `-hwaccel videotoolbox` flags)
- [Claude Code](https://claude.com/claude-code)
- `ffmpeg` with libx264 (`brew install ffmpeg`)
- `yt-dlp` (`brew install yt-dlp`) for URL inputs
- Python 3 with `numpy` and `faster-whisper`:
  ```bash
  python3 -m pip install --user faster-whisper numpy
  ```
- Arabic fonts:
  ```bash
  brew install --cask font-cairo font-tajawal font-noto-naskh-arabic font-ibm-plex-sans-arabic
  ```

Optional but strongly recommended for Saudi / Khaleeji content:

```bash
export ELEVENLABS_API_KEY=...     # https://elevenlabs.io  (best for saudi)
# or
export ASSEMBLYAI_API_KEY=...     # https://www.assemblyai.com
```

When either key is set, the skill auto switches to cloud ASR. Pass `--local` to skip the bill on a specific run.

Cost reference: ElevenLabs Scribe is roughly $0.40 per audio hour. Local stays free.

## Install

```bash
git clone https://github.com/abidalista/maqta3.git ~/.claude/skills/maqta3
```

Then dependencies:

```bash
brew install ffmpeg yt-dlp
python3 -m pip install --user faster-whisper numpy
brew install --cask font-cairo font-tajawal font-noto-naskh-arabic
```

Restart Claude Code and `/maqta3` is available as a slash command.

## Usage

In Claude Code:

```
/maqta3
```

Then paste a video file path OR a youtube URL. The skill will:

1. Download (if URL) and transcribe
2. Propose 3 to 5 candidate clips with arabic title, english title, and why it lands
3. Ask which to cut
4. Ask 9:16 / 16:9 / 1:1
5. If 9:16 from 16:9 with two faces: ask pan vs split-screen
6. Ask caption style (cairo-bold, tajawal-clean, naskh, or paste a reference image)
7. Render and open the result, plus print arabic + english hook variants

Final clips land in `<source-video-dir>/maqta3_out/`.

## Repo structure

```
maqta3/
├── SKILL.md                 # the skill prompt Claude Code reads
├── scripts/
│   ├── download.py          # yt-dlp wrapper
│   ├── transcribe.py        # faster-whisper + cloud fallback
│   ├── analyze.py           # speaker timeline from two ROI motion logs
│   ├── build_pan.py         # ffmpeg crop x expression with hard cuts
│   └── build_ass_rtl.py     # RTL Arabic ASS captions, word by word
└── README.md
```

## Notes on Arabic ASR quality

| Source quality                            | Recommended path                  |
| ----------------------------------------- | --------------------------------- |
| MSA (news, formal speech)                 | faster-whisper large-v3, default  |
| Egyptian / Levantine podcast              | faster-whisper large-v3           |
| Gulf / Khaleeji clean studio              | faster-whisper large-v3           |
| Thick Najdi or far field mic              | ElevenLabs Scribe (cloud)         |
| Heavy code switching (ar + en in 1 line)  | drop `--lang ar` to auto detect   |

## License

MIT — see [LICENSE](LICENSE).

Maintained by [abidalista](https://github.com/abidalista).

---

## بالعربي

`maqta3` (مَقطع) سكِل لـ Claude Code يحول البودكاست والمقابلات والمحاضرات الطويلة إلى مقاطع قصيرة جاهزة للسوشل ميديا، مع ترجمة عربية محروقة على الفيديو، وتنسيق عمودي للتيك توك والريلز والشورتس.

مصمم خصيصاً للمحتوى السعودي والخليجي الطويل (ثمانية، فنجان، سقراط، مشوار، وما شابه).

### وش يسوي

تعطيه فيديو من اليوتيوب أو ملف على جهازك، يسوي التالي:

1. ينسخ كل اللي يقال في الفيديو (نسخ صوتي) محلياً مجاناً، أو عبر ElevenLabs لو في API key.
2. يقرأ النص ويختار لك أحسن 3 إلى 5 مقاطع مع:
   - وقت البداية والنهاية
   - عنوان عربي وانجليزي
   - شرح ليش هذا المقطع يستاهل
3. تختار اللي تبيه، يقصه ويحوله عمودي 9:16 مع تتبع المتكلم تلقائياً.
4. يضيف الترجمة العربية على الفيديو، كلمة كلمة، مع تظليل الكلمة الحالية باللون الأصفر.
5. يحفظ المقطع جاهز للنشر، ويعطيك أفكار للهاشتاقات والكابشن بالعربي والانجليزي.

### كيف تركبه

```bash
git clone https://github.com/abidalista/maqta3.git ~/.claude/skills/maqta3

# الأدوات
brew install ffmpeg yt-dlp
python3 -m pip install --user faster-whisper numpy

# الخطوط العربية
brew install --cask font-cairo font-tajawal font-noto-naskh-arabic
```

أعد فتح Claude Code، واكتب `/maqta3` في أي محادثة.

### نصيحة مهمة للمحتوى السعودي

النموذج المحلي (faster-whisper) يفهم الفصحى والمصري واللهجة الخليجية النظيفة. لكن لو الفيديو فيه لكنة سعودية ثقيلة، أو الميكروفون بعيد عن المتكلم، الأحسن تستخدم ElevenLabs Scribe:

```bash
export ELEVENLABS_API_KEY="مفتاحك_هنا"
```

السكِل يكتشف المفتاح تلقائياً ويستخدمه. التكلفة تقريباً 0.40 دولار للساعة.

### كيف تستخدمه

افتح محادثة جديدة في Claude Code واكتب:

```
/maqta3
```

يطلب منك ترسل رابط يوتيوب أو مسار ملف فيديو. بعدها:

1. يحمل الفيديو (لو رابط) وينسخه
2. يعرض عليك 3 إلى 5 مقاطع مرشحة، تختار رقم اللي يعجبك
3. يسألك التنسيق: عمودي (9:16) أو أفقي (16:9) أو مربع (1:1)
4. لو في شخصين في الكادر، يسألك: تتبع المتكلم بقفز الكاميرا، أو شاشة مقسومة
5. يسألك ستايل الترجمة: cairo-bold (الافتراضي وهو الأفضل)، tajawal-clean، أو naskh
6. يبدأ يشتغل، ويفتح لك الفيديو الجاهز

المقاطع تنحفظ في مجلد `maqta3_out/` جنب الفيديو الأصلي.

### ملاحظات

- ولا يحتاج إنترنت لو تستخدم النموذج المحلي. كل شي يشتغل على جهازك.
- الترجمة كلمة بكلمة هي الستايل المعتاد للسوشل العربي. لو الكلام سريع جداً والكلمات ترفرف، تقدر تبدلها لمجموعات صغيرة بإضافة `--chunk 2`.
- خطوط Cairo و Tajawal و Naskh لازم تكون مركبة على الجهاز عشان الترجمة تطلع صحيحة.

### الترخيص

MIT. تقدر تستخدمه وتعدله وتنشره بدون قيود.
