#!/usr/bin/env python3
"""Transcribe audio or video. Auto picks cloud (ElevenLabs Scribe / AssemblyAI) if a key is set, else local (faster-whisper).

Output JSON shape mirrors openai-whisper output:
{
  "language": "ar",
  "duration": 1234.5,
  "segments": [
    {"id": 0, "start": 0.0, "end": 3.2, "text": "...", "words": [{"start": ..., "end": ..., "word": "..."}, ...]},
    ...
  ]
}

Usage:
  python3 transcribe.py <audio_or_video> <out_dir> [--model large-v3] [--lang ar] [--local | --cloud]

Default behavior:
  - if ELEVENLABS_API_KEY or ASSEMBLYAI_API_KEY is set → use cloud
  - else → use local faster-whisper
  - --local forces local even if a key is set
  - --cloud forces cloud (errors if no key)

Env:
  FW_DEVICE=auto|cpu|cuda     (default auto)
  FW_COMPUTE_TYPE=int8|float16|float32  (default int8 for cpu, float16 for cuda)
  ELEVENLABS_API_KEY=...      (preferred for saudi / khaleeji)
  ASSEMBLYAI_API_KEY=...      (alt cloud option)
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def ensure_wav(src: Path, out_dir: Path) -> Path:
    """Decode any input to mono 16kHz wav. Returns wav path."""
    if src.suffix.lower() == ".wav":
        return src
    wav = out_dir / (src.stem + ".wav")
    cmd = ["ffmpeg", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(wav)]
    if sys.platform == "darwin":
        cmd = cmd[:1] + ["-hwaccel", "videotoolbox"] + cmd[1:]
    subprocess.run(cmd, check=True, capture_output=True)
    return wav


def transcribe_local(audio_path: str, model_name: str, lang: str | None) -> dict:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("install with: pip install faster-whisper", file=sys.stderr)
        sys.exit(2)

    device = os.environ.get("FW_DEVICE", "auto")
    compute_type = os.environ.get("FW_COMPUTE_TYPE", "int8" if device != "cuda" else "float16")

    t0 = time.time()
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    print(f"[transcribe] loaded {model_name} on {device}/{compute_type} in {time.time()-t0:.1f}s", file=sys.stderr)

    segments_iter, info = model.transcribe(
        audio_path,
        language=lang,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        beam_size=5,
        condition_on_previous_text=False,
    )

    out = {"language": info.language, "duration": info.duration, "segments": []}
    for s in segments_iter:
        words = []
        if s.words:
            for w in s.words:
                words.append({"start": w.start, "end": w.end, "word": w.word})
        out["segments"].append({
            "id": s.id,
            "start": s.start,
            "end": s.end,
            "text": s.text,
            "words": words,
        })
        if s.id % 25 == 0:
            print(f"[transcribe] {s.end:.1f}s done", file=sys.stderr)
    return out


def transcribe_cloud(audio_path: str, lang: str | None) -> dict:
    if os.environ.get("ELEVENLABS_API_KEY"):
        return transcribe_elevenlabs(audio_path, lang)
    if os.environ.get("ASSEMBLYAI_API_KEY"):
        return transcribe_assemblyai(audio_path, lang)
    print("no cloud ASR keys set. export ELEVENLABS_API_KEY or ASSEMBLYAI_API_KEY", file=sys.stderr)
    sys.exit(2)


def transcribe_elevenlabs(audio_path: str, lang: str | None) -> dict:
    """ElevenLabs Scribe (https://elevenlabs.io/docs/api-reference/speech-to-text)."""
    import urllib.request
    import urllib.parse
    import mimetypes

    api_key = os.environ["ELEVENLABS_API_KEY"]
    url = "https://api.elevenlabs.io/v1/speech-to-text"

    boundary = "----maqta3" + str(int(time.time()))
    fname = Path(audio_path).name
    content_type = mimetypes.guess_type(audio_path)[0] or "audio/wav"

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    parts = []
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"model_id\"\r\n\r\nscribe_v1\r\n".encode())
    if lang:
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"language_code\"\r\n\r\n{lang}\r\n".encode())
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"timestamps_granularity\"\r\n\r\nword\r\n".encode())
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{fname}\"\r\nContent-Type: {content_type}\r\n\r\n".encode())
    parts.append(audio_bytes)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("xi-api-key", api_key)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

    print(f"[transcribe] calling ElevenLabs Scribe ({len(audio_bytes)/1e6:.1f} MB)", file=sys.stderr)
    with urllib.request.urlopen(req, timeout=600) as r:
        data = json.loads(r.read())

    return _normalize_elevenlabs(data)


def _normalize_elevenlabs(data: dict) -> dict:
    """Map Scribe response to whisper-style schema."""
    words_in = data.get("words", []) or []
    segments = []
    cur = {"id": 0, "start": 0.0, "end": 0.0, "text": "", "words": []}
    for w in words_in:
        if w.get("type") != "word":
            continue
        start = w.get("start", 0.0)
        end = w.get("end", start)
        token = w.get("text", "")
        if not cur["words"]:
            cur["start"] = start
        cur["end"] = end
        cur["text"] += (" " if cur["text"] else "") + token
        cur["words"].append({"start": start, "end": end, "word": token})
        # break a segment after long pause
        if cur["words"] and end - cur["start"] > 8.0:
            segments.append(cur)
            cur = {"id": len(segments), "start": 0.0, "end": 0.0, "text": "", "words": []}
    if cur["words"]:
        segments.append(cur)
    return {"language": data.get("language_code", "ar"), "duration": data.get("audio_duration_seconds", 0.0), "segments": segments}


def transcribe_assemblyai(audio_path: str, lang: str | None) -> dict:
    """AssemblyAI (https://www.assemblyai.com/docs)."""
    import urllib.request

    api_key = os.environ["ASSEMBLYAI_API_KEY"]
    base = "https://api.assemblyai.com/v2"

    # upload
    with open(audio_path, "rb") as f:
        req = urllib.request.Request(base + "/upload", data=f.read(), method="POST")
        req.add_header("authorization", api_key)
        with urllib.request.urlopen(req, timeout=600) as r:
            upload_url = json.loads(r.read())["upload_url"]

    # request transcription
    body = json.dumps({
        "audio_url": upload_url,
        "language_code": lang or "ar",
        "punctuate": True,
        "format_text": True,
    }).encode()
    req = urllib.request.Request(base + "/transcript", data=body, method="POST")
    req.add_header("authorization", api_key)
    req.add_header("content-type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        tid = json.loads(r.read())["id"]

    # poll
    poll_url = f"{base}/transcript/{tid}"
    while True:
        req = urllib.request.Request(poll_url)
        req.add_header("authorization", api_key)
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        if data["status"] == "completed":
            break
        if data["status"] == "error":
            raise RuntimeError(data.get("error"))
        time.sleep(3)

    return _normalize_assemblyai(data)


def _normalize_assemblyai(data: dict) -> dict:
    words_in = data.get("words", []) or []
    segments = []
    cur = {"id": 0, "start": 0.0, "end": 0.0, "text": "", "words": []}
    for w in words_in:
        start = w["start"] / 1000.0
        end = w["end"] / 1000.0
        token = w["text"]
        if not cur["words"]:
            cur["start"] = start
        cur["end"] = end
        cur["text"] += (" " if cur["text"] else "") + token
        cur["words"].append({"start": start, "end": end, "word": token})
        if end - cur["start"] > 8.0:
            segments.append(cur)
            cur = {"id": len(segments), "start": 0.0, "end": 0.0, "text": "", "words": []}
    if cur["words"]:
        segments.append(cur)
    return {"language": data.get("language_code", "ar"), "duration": data.get("audio_duration", 0.0), "segments": segments}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="audio or video file")
    ap.add_argument("out_dir", help="output directory")
    ap.add_argument("--model", default="large-v3", help="faster-whisper model (default large-v3)")
    ap.add_argument("--lang", default="ar", help="language code (default ar). pass empty string to auto detect.")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--cloud", action="store_true", help="force cloud ASR (errors if no key)")
    mode.add_argument("--local", action="store_true", help="force local faster-whisper even if a cloud key is set")
    args = ap.parse_args()

    src = Path(args.input)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    wav = ensure_wav(src, out_dir)
    lang = args.lang if args.lang else None

    has_cloud_key = bool(os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("ASSEMBLYAI_API_KEY"))
    if args.cloud:
        use_cloud = True
    elif args.local:
        use_cloud = False
    else:
        use_cloud = has_cloud_key  # auto: prefer cloud when a key is set

    if use_cloud:
        provider = "ElevenLabs Scribe" if os.environ.get("ELEVENLABS_API_KEY") else "AssemblyAI"
        print(f"[transcribe] using cloud ({provider}). pass --local to skip.", file=sys.stderr)
    else:
        print(f"[transcribe] using local faster-whisper {args.model}. set ELEVENLABS_API_KEY for higher saudi accuracy.", file=sys.stderr)

    try:
        if use_cloud:
            result = transcribe_cloud(str(wav), lang)
        else:
            result = transcribe_local(str(wav), args.model, lang)
    except SystemExit:
        raise
    except Exception as e:
        if use_cloud:
            print(f"[transcribe] cloud failed: {e}. falling back to local.", file=sys.stderr)
            result = transcribe_local(str(wav), args.model, lang)
        else:
            print(f"[transcribe] local failed: {e}. trying cloud fallback.", file=sys.stderr)
            result = transcribe_cloud(str(wav), lang)

    out_json = out_dir / (src.stem + ".json")
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(str(out_json))


if __name__ == "__main__":
    main()
