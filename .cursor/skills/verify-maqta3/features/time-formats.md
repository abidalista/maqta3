# Time formats

Time formats let a user pass start and end as `HH:MM:SS`, `MM:SS`, or plain seconds; maqta3 treats them as the same span and names the reel from the duration in seconds.

## Sub-features

- `time-hms` accepts `HH:MM:SS`.
- `time-ms` accepts `MM:SS`.
- `time-seconds` accepts a plain number (including a decimal).
- `time-mixed` accepts a mix of those forms in one command.

## How to get to it (user POV)

- Pass times as the second and third arguments to `python3 scripts/make.py <url> <start> <end>`.
- Pass the same forms to `/maqta3`.

## Driving it with control-maqta3

Preconditions:

- Baseline launch + `control-maqta3 doctor` reports `ok: yes`.
- Network can reach YouTube.
- Use `https://www.youtube.com/watch?v=jNQXAC9IVRw` (clip is ~19s, so 2-second windows fit).

- **Plain seconds.** Run `control-maqta3 make "https://www.youtube.com/watch?v=jNQXAC9IVRw" 2 4`. Exit `0`. stdout path ends with `_reel_2s.mp4` and `(2s)`.
- **MM:SS.** Run `control-maqta3 cleanup` then `control-maqta3 launch` and `control-maqta3 doctor` (the work dir is shared; do not overlap runs). Then run `control-maqta3 make "https://www.youtube.com/watch?v=jNQXAC9IVRw" 0:02 0:04`. Exit `0`. stdout path ends with `_reel_2s.mp4` and `(2s)`.
- **HH:MM:SS.** After a fresh launch, run `control-maqta3 make "https://www.youtube.com/watch?v=jNQXAC9IVRw" 00:00:02 00:00:04`. Exit `0`. stdout path ends with `_reel_2s.mp4` and `(2s)`.
- **Confirm span.** For each successful clip, `control-maqta3 probe "$CLIP"` reports `duration` between `1.5` and `2.5` and `width: 1080`.
- **Proof.** Keep the last successful drive. Run `control-maqta3 evidence time-formats --clip "$CLIP"`. Artifacts include `cmd.json` showing the `HH:MM:SS` (or last) invocation and `probe.txt` with the 2s span.

## Gotchas

- Each `make` reuses `/tmp/maqta3`. Do not start the next format until the previous `make` has exited. Prefer cleanup+launch between makes so `maqta3_out` does not mix same-name files for the same date.
- `int(round(end - start))` of a 2.0s span is `2`. A `2.4` to `4.4` span is also `2s` on the filename; assert times you actually passed.
- Parsing-only Python imports of `to_seconds` are not this feature. The user path is `make.py` arguments.
- Same YouTube failure rule as make-clip: network errors fail the feature.
