# known issues

## libass + harfbuzz emits a phantom `.notdef` glyph before every lam-alef

discovered: 2026-05-09 while burning the estraha door clip.

### symptom

burning RTL arabic captions with the `subtitles=` ffmpeg filter renders a missing-glyph
box (`.notdef`) immediately before every lam-alef cluster (`لا` `لأ` `لإ` `لآ`).

example: `رحنا للاستراحة` renders as `رحنا ل[box]لاستراحة`.

### scope

- reproduces with: SF Arabic, Geeza Pro, Damascus, DecoType Naskh, Cairo, Tajawal.
  every macos system arabic font we tested.
- reproduces in isolation against a 1080×1920 black canvas — not source-video specific.
- tested on: ffmpeg 8.1.1 (homebrew), libass 9.x, harfbuzz linked.

### root cause

shaping pipeline bug. libass + harfbuzz on macos appears to insert a missing-mark
slot before the lam-alef ligature cluster regardless of font glyph coverage. confirmed
the source unicode is clean (only U+0644 + U+0627 etc., no invisibles, no BOM).

### workaround (shipped in build_ass_rtl.py)

substitute precomposed lam-alef glyphs from the arabic presentation forms-A block
before writing dialogue text:

| sequence | isolated | final form (after connecting letter) |
|----------|----------|---------------------------------------|
| ل + ا    | ﻻ U+FEFB | ﻼ U+FEFC                              |
| ل + أ    | ﻷ U+FEF7 | ﻸ U+FEF8                              |
| ل + إ    | ﻹ U+FEF9 | ﻺ U+FEFA                              |
| ل + آ    | ﻵ U+FEF5 | ﻶ U+FEF6                              |

implemented in `scripts/build_ass_rtl.py:precompose_lam_alef`. context detection uses
`CONNECTING` set of arabic letters that have initial/medial connecting forms.

### isolation test (if you want to reproduce)

```bash
cat > /tmp/test_lamalef.ass <<'EOF'
[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, ...
Style: Default,SF Arabic,80,&H00FFFFFF,...

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,لا الا للا الاستراحة
EOF

ffmpeg -f lavfi -i color=c=black:s=1080x1920:d=2 \
  -vf "subtitles=/tmp/test_lamalef.ass" /tmp/test_lamalef.mp4
```

every `لا` will have a phantom box preceding it. swap the source text for
`ﻻ اﻻ ﻟﻼ اﻻستراحة` (precomposed forms) and the boxes vanish.

### upstream tracking

not yet filed upstream. if anyone hits this and chases it: libass issue tracker is
at github.com/libass/libass/issues; harfbuzz at github.com/harfbuzz/harfbuzz/issues.
the substitution workaround is reliable enough that we haven't bothered.

---

## scribe stutter on ambiguous tokens

scribe occasionally repeats a word three or four times when audio quality drops or
when it can't decide between alternates ("جيبوا جيبوا جيبوا"). post-processing
de-duplication is not implemented; manual fix is cheap for short clips. consider a
`--dedupe-stutter` mode if this becomes routine.
