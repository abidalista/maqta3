# maqta3 caption pipeline — code review

scope: `scripts/build_ass_rtl.py`, `scripts/transcribe.py`, `scripts/build_pan.py`, `scripts/analyze.py`, `scripts/download.py`, plus inline caption logic written during the 2026-05-09/10 session.

reviewed against the actual rendered output of the estraha door clip (108s, 9:16, scribe + sf arabic + lam-alef precomposed). findings ordered by severity.

## critical

### C-01. arabic captions render with phantom `.notdef` boxes before every lam-alef
- file: `scripts/build_ass_rtl.py` (any style)
- repro: any caption containing `لا` `لأ` `لإ` `لآ`. confirmed with sf arabic, geeza pro, damascus, decotype naskh, cairo, tajawal — all macos system fonts.
- root cause: libass + harfbuzz on macos emits a missing-mark slot before the lam-alef ligature cluster, regardless of font. it's a shaping pipeline bug, not a font coverage bug. confirmed in isolation against a 1080×1920 black canvas.
- impact: every clip the skill produces has visible boxes mid-sentence. shipping-default failure for a saudi-arabic-first tool.
- fix: substitute precomposed arabic presentation forms (u+fefb / u+fefc, plus the three hamza variants) before writing dialogue text. context-aware (final form when preceded by a connecting letter, isolated otherwise).
- the working code lives in the inline python from this session; needs to be lifted into `build_ass_rtl.py` as a helper, e.g. `_precompose_lam_alef(text)`, applied at the same point as `strip_tashkeel`.

```python
LAM_ALEF = {('ل','ا'):('ﻻ','ﻼ'),('ل','أ'):('ﻷ','ﻸ'),('ل','إ'):('ﻹ','ﻺ'),('ل','آ'):('ﻵ','ﻶ')}
CONNECTING = set('بتثجحخسشصضطظعغفقكلمنهي')
def _precompose_lam_alef(t):
    out=[]; i=0
    while i<len(t):
        if i+1<len(t) and (t[i],t[i+1]) in LAM_ALEF:
            iso,fin = LAM_ALEF[(t[i],t[i+1])]
            out.append(fin if (out[-1] if out else '') in CONNECTING else iso); i+=2
        else: out.append(t[i]); i+=1
    return ''.join(out)
```

### C-02. dialogue text is written into ASS unescaped
- file: `build_ass_rtl.py:144`, also the inline builder
- code: `f"...,,{text}"` writes raw transcript into ASS dialogue.
- problem: ASS uses `{...}` for inline override tags and `\N` for hard line breaks. if a transcript ever contains `{` `}` `\N` or `\h`, libass will reinterpret. arabic text won't trigger this in practice, but code-switched english (the skill explicitly supports it: "ar+en in one line") and any future user-edited captions will.
- fix: escape `{` `}` and any leading whitespace; replace literal `\N` with `\\N` if you ever pass it through. one-liner: `text = text.replace('{','\\{').replace('}','\\}')`

## warning

### W-01. word-by-word default conflicts with what the user actually wants
- file: `SKILL.md` (caption section), `scripts/build_ass_rtl.py` (chunk default = 1), `CLAUDE.md` ("captions are word by word per user preference")
- evidence: in this session the user pushed back on word-by-word ("you are not doing the sentences properly... full stop at the end of each sentence... like done professionally on youtube cc or netflix").
- conflict: CLAUDE.md says word-by-word is the preference. the user is telling us otherwise.
- fix: confirm with user, then either flip the default or add a sentence-aware mode. the existing `--chunk N` is fixed-N grouping, doesn't respect sentence boundaries. add `--mode netflix` (or `--chunk sentence`) that breaks on punctuation tokens from the transcript.

### W-02. sentence-aware chunking is not in any committed file
- this session's chunker (split on `.` `؟` `!` from word.word, time spans clamped non-overlapping, period appended only on real sentence ends) lives only in conversation history. next session it's gone.
- fix: lift into `build_ass_rtl.py` alongside the lam-alef fix. tests against the scribe-generated json for the estraha clip would be useful pinning.

### W-03. cloud → local fallback in transcribe.py is silently expensive
- file: `scripts/transcribe.py:259-272`
- if cloud raises anything other than `SystemExit`, we silently re-decode the same audio against faster-whisper large-v3 (slow, big memory). worse, if local is what failed, we silently call cloud, which may already have a partial-billed request behind it.
- the user has no signal which path produced their final transcript.
- fix: log the provider that produced the result into the json (`"provider": "elevenlabs_scribe"` or `"faster-whisper-large-v3"`); print a single bold line on fallback so it's noticeable.

### W-04. `_normalize_elevenlabs` and `_normalize_assemblyai` reset segment start to 0.0
- file: `transcribe.py:142, 157, 209, 221`
- new segment is initialized with `"start": 0.0`. the `if not cur["words"]: cur["start"] = start` patch on the first word covers it in practice, but the initial value is a footgun. someone refactoring later and adding text accumulation before words gets bitten.
- fix: initialize segment with `"start": None` and assert it's set before append.

### W-05. `build_pan.py` falls through to the last segment as the "before any range" default
- file: `scripts/build_pan.py:34`
- `expr = str(parts[-1][2])` — the *last* segment's x becomes the default for any t outside any `between(...)`. if speaker timeline doesn't start at t=0, the very first frames get the wrong x.
- fix: prepend a segment `(0.0, parts[0][0], parts[0][2])` before the fold, so `t < parts[0][0]` mirrors the first speaker.

## info

### I-01. fonts assumed installed; libass silently falls back if missing
- `build_ass_rtl.py` ships three styles each pinning a specific font. no `fc-match` check. if the user installed the skill but skipped the brew cask install, the chosen style will silently render with whatever libass picks. could be obvious garbage or could be subtle (different x-height).
- fix: at script start, `subprocess.run(['fc-match', style['font']])`, warn if the match family doesn't include the requested font.

### I-02. `fmt_time` carry handles seconds rollover but not minutes
- `build_ass_rtl.py:80-83`. `cs == 100 → cs=0; s+=1` works for the centiseconds carry, but if `s` was already 59 you produce `0:00:60.00`. ASS parsers (libass) tolerate it; mpv warns.
- fix: cascade the carry. trivial.

### I-03. `download.py` uses `--print after_move:filepath` which needs yt-dlp ≥ 2022.04
- `scripts/download.py:36`. older yt-dlp prints nothing to stdout and the script falls back to "newest mp4 in dir" — works but obscures errors.
- fix: pin the version in the install hint.

### I-04. ElevenLabs scribe upload reads the entire file into memory
- `transcribe.py:114-115`. fine for clips, but a 1-hour podcast wav at 16khz mono is ~115mb — okay; longer or higher-rate inputs will spike RSS.
- fix: stream the multipart body via a generator, or chunk-encode. low priority for the use case.

### I-05. transcribe.py auto-mode `condition_on_previous_text=False` deserves a comment
- `transcribe.py:71`. this is the right call for podcasts (avoids hallucination loops), but a future maintainer may flip it back. one-line comment locks the intent.

### I-06. analyze.py `smooth` window is fixed at 5 with no cli flag
- `scripts/analyze.py:37, 64-65`. the SKILL.md `min_dwell` is exposed but the smoothing window isn't. for low-fps source or sparse motion logs, 5 frames may be too tight and produce flapping speaker labels.
- fix: optional `--smooth N` arg.

### I-07. SKILL.md says "phrase chunks" in the front-matter description but the workflow defaults to word-by-word
- `SKILL.md:3` description says "burn RTL Arabic captions in phrase chunks". the actual default in the script is chunk=1 (word). pick one and align both files.

### I-08. CLAUDE.md is stale after this session
- ElevenLabs key state is now "set in /tmp/maqta3/.env" (not exported globally yet).
- lam-alef + bidi-shaping bug discovered and worked around.
- estraha door clip rendered as the first end-to-end test (was the open item in CLAUDE.md).
- worth updating before the next session.

## not findings, but notable

- the inline approach used in this session (heredoc python in bash) was the fastest path to debug, but for anything you'd run twice, it should land in `scripts/`. half a dozen workarounds (precomposed glyphs, sentence-aware chunking, non-overlapping spans, scribe re-transcription) are still only in conversation memory.
- the source clip has whisper-style stutters from scribe too ("جيبوا جيبوا جيبوا"). that's source-data quality, not pipeline. add a `--dedupe-stutter` post-processing step if it shows up regularly.

## suggested next steps

1. lift the lam-alef precomposition + sentence-aware chunking + escape fix into `build_ass_rtl.py`. add a `--mode netflix` flag.
2. update `CLAUDE.md` open items: end-to-end test passed, key configured locally, bug + workaround documented.
3. add a small fixtures dir with the estraha clip's `clip_8_centered.json` and a golden ASS so future regressions are obvious.
4. document the libass + lam-alef bug somewhere durable (a `KNOWN-ISSUES.md` is fine) so we don't rediscover it next time.
