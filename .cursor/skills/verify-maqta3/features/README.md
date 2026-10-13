# maqta3 verification map

This directory is the maintained source for verifying the user-facing behavior of maqta3. Read the index before driving the app, then use the matching feature file as the recipe.

## Baseline preconditions

- Put `.cursor/skills/verify-maqta3/bin` and `$HOME/.local/bin` on `PATH`.
- Run `control-maqta3 launch` and require `ready: yes`.
- Run `control-maqta3 doctor` and require `ok: yes`, the expected `verify_home` (`/tmp/maqta3-verify-<run_id>`), `work_dir: /tmp/maqta3`, and this checkout's `make.py`.
- `HOME` for every `make` is that `verify_home`. Clips must appear under `$verify_home/maqta3_out/`, never the operator's real `~/maqta3_out`.
- Never drive `/tmp/maqta3` without this run's lock. Two instances cannot share it.
- Network is required for YouTube-backed features. ffmpeg and yt-dlp ≥ 2023.01.06 are required for every feature except usage errors.

## Driving conventions

- Start every recipe from the baseline state unless its preconditions say otherwise.
- Treat every command as literal. Keep quoted names, URLs, and flags unchanged.
- Run user actions through `control-maqta3 make` and `control-maqta3 download`.
- Inspect results through `control-maqta3 probe` and `control-maqta3 frame`.
- Restore scratch state with `control-maqta3 cleanup`. Do not remove proof artifacts during cleanup.

## Proof and skip reporting

- Capture the user action and the resulting state, not only the final path line.
- CLI proof includes the command, stdout, stderr, and exit code (`artifacts/<id>/cmd.json` and siblings).
- Mutation proof includes a read-only second view of the stored file (`probe.txt`, and `frame.png` when an mp4 was written).
- Record the feature ID and entry point used with every artifact.
- Report an unreachable path with the attempted command and the unmet precondition (for example yt-dlp bot-block stderr).
- Do not report a skipped entry point as verified through a different path. A local fixture is not a YouTube make-clip proof.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible behavior. It then uses exactly four H2 sections in this order.

1. `Sub-features` lists short IDs with one line for each behavior.
2. `How to get to it (user POV)` lists every user entry point.
3. `Driving it with control-maqta3` starts with `Preconditions:` and uses labeled bullets that pair each user action with an exact command and observable result.
4. `Gotchas` lists traps that can waste or invalidate a verification run.

Keep implementation details out of the map. Name only user paths, stable handles, required state, commands, and observable proof.

## Features

- [Cut a 9:16 reel](./make-clip.md) covers the primary YouTube URL + timestamps → vertical mp4 path.
- [Time formats](./time-formats.md) covers `HH:MM:SS`, `MM:SS`, and plain-second inputs.
- [Usage errors](./usage.md) covers missing arguments.
- [Span download](./span-download.md) covers `download.py` pulling only the padded window and emitting an aligned `clip.mp4`.
