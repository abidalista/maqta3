# Usage errors

Usage errors tell the user how to invoke maqta3 when the URL, start, or end is missing, and they do not write a clip.

## Sub-features

- `usage-no-args` with zero arguments prints usage and exits `1`.
- `usage-partial` with one or two arguments prints usage and exits `1`.
- `usage-no-file` does not create a reel under `$verify_home/maqta3_out/`.

## How to get to it (user POV)

- Run `python3 scripts/make.py` with no arguments.
- Run `python3 scripts/make.py <url>` or `python3 scripts/make.py <url> <start>` (any missing piece).
- Invoke `/maqta3` without a URL, start, and end.

## Driving it with control-maqta3

Preconditions:

- Baseline launch + `control-maqta3 doctor` reports `ok: yes`.
- `$verify_home/maqta3_out/` is empty.

- **No args.** Run `control-maqta3 make`. Exit code `1`. stderr contains `usage: make.py <url> <start> <end>`.
- **URL only.** Run `control-maqta3 make "https://www.youtube.com/watch?v=jNQXAC9IVRw"`. Exit code `1`. stderr contains the same usage line.
- **URL + start.** Run `control-maqta3 make "https://www.youtube.com/watch?v=jNQXAC9IVRw" 1`. Exit code `1`. stderr contains the same usage line.
- **No clip.** `$verify_home/maqta3_out/` still has no `*.mp4`.
- **Proof.** After the last failing drive, run `control-maqta3 evidence usage`. `artifacts/usage/exit.txt` is `1` and `stderr.txt` contains `usage: make.py <url> <start> <end>`. No `--clip` (no file was written).

## Gotchas

- The harness prints `exit: 1` on stdout after forwarding make.py. Assert make.py's own usage line on **stderr**, not the harness `exit:` line.
- This path must not hit YouTube. If yt-dlp runs, arguments were forwarded wrong.
- Do not treat a missing `open` window as this feature.
