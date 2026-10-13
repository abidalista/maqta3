---
name: verify-maqta3
description: Drive the maqta3 CLI the way a user does — YouTube URL + start + end into a 9:16 clip via scripts/make.py. Use when proving maqta3 behavior, after changing scripts/make.py or scripts/download.py, or when a change might affect clip output, time parsing, span downloads, or usage errors.
---

# Verify maqta3

maqta3 is a **short-lived CLI**, not a server. A user (or the `/maqta3` skill) runs one command: `python3 scripts/make.py <url> <start> <end>`. That downloads only the requested YouTube span, center-crops it to 1080×1920, and writes `~/maqta3_out/<YYYYMMDD>_reel_<dur>s.mp4`.

There is no web UI, TUI, daemon, or HTTP API. `scripts/download.py` is the span-download helper `make.py` calls; it is also a CLI of its own. Drive both through `control-maqta3` so HOME, PATH, and the shared work dir stay isolated.

Read `features/README.md` before driving. Use the matching feature file as the recipe. Prove the real user path, not `to_seconds` in isolation.

## Launch

Install/check deps once, then start each drive as its own process. There is no process to keep alive.

From the repo root:

```bash
export PATH="$PWD/.cursor/skills/verify-maqta3/bin:$HOME/.local/bin:$PATH"
control-maqta3 cleanup    # only if a previous verify run left a lock
control-maqta3 launch
control-maqta3 doctor     # must print `ok: yes` before any drive
```

Launch is ready when it prints `ready: yes` and `control-maqta3 doctor` prints `ok: yes`. Ready means:

- `python3`, `ffmpeg`, and `yt-dlp` (≥ 2023.01.06) are on `PATH`
- `scripts/make.py` and `scripts/download.py` exist in this checkout
- exclusive lock `/tmp/maqta3-verify.lock` is held by this run
- disposable `HOME` is `verify_home` from launch (`/tmp/maqta3-verify-<run_id>`), so clips land in `$verify_home/maqta3_out/` rather than the operator's real `~/maqta3_out`
- work dir `/tmp/maqta3` exists (hardcoded by `make.py`)

If `yt-dlp` is missing, launch runs `python3 -m pip install --user 'yt-dlp>=2023.1.6'` and prepends `~/.local/bin`. That is verification scaffolding for the documented dependency, not a mock of YouTube. Drives set `PYTHONUSERBASE` to the operator's `~/.local` so a HOME override cannot hide that install.

**Do not launch a second instance.** `make.py` always uses `/tmp/maqta3` for `clip.mp4` / `v.mp4` / `a.m4a`. Two runs will clobber each other. If launch prints `refusing to double-drive`, run `control-maqta3 cleanup` and launch again. Never drive the operator's real `HOME` or an unlocked `/tmp/maqta3`.

Teardown: `control-maqta3 cleanup` (see Cleanup). After every failed iteration, run cleanup before the next launch.

## Doctor

Read-only. Run first whenever anything looks off, and always after launch:

```bash
control-maqta3 doctor
```

Require `ok: yes` plus:

- `make.py` / `download.py` paths under this repo
- `verify_home` is `/tmp/maqta3-verify-<run_id>`
- `work_dir: /tmp/maqta3`
- `lock: held`
- `yt-dlp` version ≥ 2023.01.06
- `hwaccel: videotoolbox` on Darwin, `software` otherwise

If doctor prints `ok: no`, do not drive. An instance that is not this run's lock + verify_home is not worth driving.

## Drive

Harness: `control-maqta3`. It runs the **real** scripts with `HOME=$verify_home` and `PATH` including `~/.local/bin`.

```bash
control-maqta3 make <url> <start> <end>
control-maqta3 make                          # missing args — usage path
control-maqta3 download <url> <out_dir> --start <t> --end <t>
control-maqta3 probe <file>
control-maqta3 frame <file> <png-path>
control-maqta3 evidence <feature-id> [--clip FILE]
```

Times are the same as the user-facing CLI: `HH:MM:SS`, `MM:SS`, or plain seconds. Keep quoted names and flags unchanged.

Every `make` / `download` writes `$verify_home/last.json` (cmd, stdout, stderr, exit). Parse `exit:` from stdout (harness appends it) and the clip path from `make.py`'s last line: `<path>  (<dur>s)`.

Recipes live in `features/`. Start from the baseline in `features/README.md`. Prefer the commands written there over improvising.

On Darwin, `make.py` passes `-hwaccel videotoolbox` and runs `open` on the clip. On Linux/Windows it uses software decode and skips `open` (xdg-open can hang headless). Do not re-add videotoolbox on Linux to "match production" — production on Linux is software.

## Evidence

Location: `.cursor/skills/verify-maqta3/artifacts/<feature-id>/`

Proof standards:

- Exercise the real user path: `scripts/make.py` / `scripts/download.py` talking to YouTube via yt-dlp and writing an mp4. Do not call `to_seconds` as a unit test and call it proven. Do not stub yt-dlp. Do not feed `make.py` a pre-cropped file.
- Capture the action and the resulting state: the exact command (`cmd.json`), stdout, stderr, exit code, **and** a second look at the file (`probe.txt` + `frame.png`). A status line alone is not proof.
- Verify side effects: the clip exists under `$verify_home/maqta3_out/`, name matches `<YYYYMMDD>_reel_<dur>s.mp4`, ffprobe shows 1080×1920, h264, aac, yuv420p, duration ≈ requested span.
- Mocks only at a production boundary that already isolates an external system. YouTube is not isolated — a make-clip proof must hit the network. If YouTube/yt-dlp fails, report that feature failed with the stderr; do not switch to a local fixture and call make-clip verified.
- Record the feature ID and entry point (`make` vs `download`, URL, timestamps) in the artifact dir.

```bash
control-maqta3 evidence make-clip --clip "$CLIP"
```

That copies `cmd.json`, `stdout.txt`, `stderr.txt`, `exit.txt`, `clip.mp4`, `probe.txt`, `frame.png` into `artifacts/<feature-id>/`. Capture evidence **before** cleanup.

## Cleanup

```bash
control-maqta3 cleanup
```

Removes `$verify_home` (`/tmp/maqta3-verify-*` only), deletes `/tmp/maqta3/{clip.mp4,v.mp4,a.m4a}`, and releases `/tmp/maqta3-verify.lock`.

Never kill by process name (`pkill ffmpeg`, `killall yt-dlp`, …). This CLI is short-lived; if a drive is still running, wait for it or kill **that** child by the pid you started.

Cleanup must **not** touch `.cursor/skills/verify-maqta3/artifacts/`. After cleanup, confirm the evidence files are still there.

## Helpers

`control-maqta3` is executable at `.cursor/skills/verify-maqta3/bin/control-maqta3`. Invocation is the commands above. Put `bin/` on `PATH` as shown in Launch.

```bash
control-maqta3 launch|doctor|make|download|probe|frame|evidence|cleanup
```

A helper you have to reverse-engineer is not a helper: `control-maqta3` with no args prints usage.

## Isolation and stand-ins

Two instances cannot run side by side. Shared mutable paths:

- `/tmp/maqta3` (hardcoded work dir)
- `~/maqta3_out` unless `HOME` is the disposable verify home

This skill always overrides `HOME` for `make`. It does not patch `/tmp/maqta3`.

If you proved on Linux instead of macOS, these steps were extra relative to a Mac user with Homebrew:

1. `pip install --user yt-dlp` and `PATH` prepend `~/.local/bin` (Mac users typically `brew install yt-dlp`)
2. Software ffmpeg path (no VideoToolbox). The Darwin `-hwaccel videotoolbox` and `open` branches stay unverified until a macOS run covers them.

This environment's datacenter IP is YouTube-bot-blocked (`Sign in to confirm you’re not a bot`) for every player client tried, with no cookies. `make-clip`, `time-formats`, and `span-download` therefore cannot be proven here; do not substitute a local fixture. Re-run those features on a residential/macOS network. `usage` does not need YouTube and is the feature proven in this checkout.
