# maqta3 (مَقطع)

أداة لـ Claude Code تحول الفيديوهات العربية الطويلة إلى مقاطع قصيرة جاهزة للنشر في تيك توك، انستغرام ريلز، يوتيوب شورتس، سناب، وإكس، مع ترجمة عربية محروقة على الفيديو.

A Claude Code tool that turns long-form Arabic videos into short clips ready to post on TikTok, Instagram Reels, YouTube Shorts, Snapchat, and X, with Arabic captions burned onto the video.

---

## بالعربي

أداة لـ Claude Code مصممة للمحتوى السعودي والخليجي الطويل (ثمانية، فنجان، سقراط، مشوار، وغيرها).

### وش تسوي

تعطيها رابط يوتيوب أو ملف فيديو من جهازك، وراح تنسخ الكلام كله، محلياً ومجاناً، أو عبر ElevenLabs لو عندك API key. بعدها راح تقرأ النص وتختار لك أفضل 3 إلى 5 مقاطع، مع عنوان بالعربي والانجليزي وسبب اختيار كل مقطع.

تختار اللي يعجبك، فتقصّه وتسوي له فريم عمودي يناسب تيك توك، انستغرام ريلز، يوتيوب شورتس، سناب، وإكس. لو في شخصين في الكادر، الكاميرا تنتقل بين الاثنين تلقائياً حسب من يتكلم.

وأخيراً تحرق الترجمة العربية على الفيديو كلمة بكلمة، مع تظليل الكلمة الحالية باللون الأصفر، وتكتب لك هاشتاقات وعناوين جاهزة للنشر.

### التركيب

```bash
git clone https://github.com/abidalista/maqta3.git ~/.claude/skills/maqta3
brew install ffmpeg yt-dlp
python3 -m pip install --user faster-whisper numpy
brew install --cask font-cairo font-tajawal font-noto-naskh-arabic
```

أعد فتح Claude Code، واكتب `/maqta3` في أي محادثة.

### نصيحة للمحتوى السعودي

النموذج المحلي يفهم الفصحى واللهجات النظيفة. لكن لو الفيديو فيه لكنة سعودية ثقيلة أو ميكروفون بعيد، الأفضل تستخدم ElevenLabs Scribe:

```bash
export ELEVENLABS_API_KEY="مفتاحك"
```

تكتشفه الأداة تلقائياً وتستخدمه. التكلفة تقريباً 0.40$ للساعة.

---

## English

Built for long-form Saudi and Gulf Arabic content (podcasts, interviews, lectures, sermons).

### What it does

Give it a youtube URL or a local mp4, and it transcribes everything (locally for free, or via ElevenLabs if you set an API key). Then it reads the transcript and picks the best 3 to 5 moments, with Arabic and English titles and a reason each clip is worth cutting.

You pick the one you like, and the tool trims it and reframes it into a vertical clip ready for TikTok, Instagram Reels, YouTube Shorts, Snapchat, and X. If two people are in the frame, the camera automatically follows whoever is speaking.

Finally, it burns Arabic captions onto the video word by word, highlighting the current word in yellow, and writes ready-to-post hooks and hashtags.

### Install

```bash
git clone https://github.com/abidalista/maqta3.git ~/.claude/skills/maqta3
brew install ffmpeg yt-dlp
python3 -m pip install --user faster-whisper numpy
brew install --cask font-cairo font-tajawal font-noto-naskh-arabic
```

Restart Claude Code and `/maqta3` becomes a slash command.

### Tip for thick Saudi accents

Local works for clean studio audio. For heavy Najdi or far-field mics, set an ElevenLabs key:

```bash
export ELEVENLABS_API_KEY="your_key"
```

The tool auto-detects it. Roughly $0.40 per hour of audio.

## License

MIT — see [LICENSE](LICENSE).
