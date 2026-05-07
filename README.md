# maqta3 (مَقطع)

أداة لـ Claude Code تحول الفيديوهات الطويلة بالعربي إلى مقاطع قصيرة جاهزة للسوشل ميديا، بترجمة عربية وتنسيق عمودي.

A Claude Code tool that turns long-form Arabic videos into ready-to-post vertical clips with RTL captions.

---

## بالعربي

أداة لـ Claude Code مصممة للمحتوى السعودي والخليجي الطويل (ثمانية، فنجان، سقراط، مشوار، وغيرها).

### وش تسوي

تعطيها رابط يوتيوب أو ملف فيديو من جهازك، تسوي التالي:

1. تنسخ الكلام (محلياً مجاناً، أو عبر ElevenLabs لو في API key)
2. تختار لك أفضل 3 إلى 5 مقاطع، مع عنوان عربي وانجليزي وسبب اختيار كل مقطع
3. تقصه وتحوله عمودي 9:16 مع تتبع المتكلم تلقائياً
4. تضيف الترجمة العربية على الفيديو، كلمة كلمة، مع تظليل الكلمة الحالية
5. تكتب لك هاشتاقات وعناوين بالعربي والانجليزي

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

Give it a youtube URL or a local mp4, and it will:

1. Transcribe (locally for free, or via ElevenLabs if an API key is set)
2. Propose the best 3 to 5 clips with Arabic + English titles and why each one lands
3. Trim and reframe to vertical 9:16, following whoever is speaking
4. Burn word-by-word Arabic captions with active word highlight
5. Generate Arabic + English hooks and hashtags

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
