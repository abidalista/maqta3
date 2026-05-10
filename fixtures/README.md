# fixtures

golden-file regression test inputs for the caption pipeline.

- `estraha-door.json` — scribe transcript of the 2026-05-09 estraha door clip
  (108s vertical center-crop from a thmanyah youtube source). canonical input for
  testing `build_ass_rtl.py`.
- `estraha-door.netflix.ass` — golden output of `build_ass_rtl.py --mode netflix
  --style cairo-bold` for that input. 29 sentence-level dialogue lines.

## regenerate the golden

```bash
python3 scripts/build_ass_rtl.py \
  fixtures/estraha-door.json \
  fixtures/estraha-door.netflix.ass \
  --mode netflix --style cairo-bold
```

if the golden changes after a refactor, diff the result. small reorderings or
timing tweaks are fine. text changes mean either the chunker or the lam-alef fix
moved — check intentional.

## sanity properties

properties the golden should always satisfy:

1. exactly 29 `Dialogue:` lines (one per scribe-detected sentence)
2. every line that ends a sentence has a trailing `.`
3. no consecutive lines overlap (each `End` ≤ next `Start`)
4. no raw `لا/لأ/لإ/لآ` sequences anywhere — all replaced with U+FEFB-FEFC
5. no unescaped `{` or `}` (transcript wouldn't contain these but the escape pass
   should be visible in the code path)
