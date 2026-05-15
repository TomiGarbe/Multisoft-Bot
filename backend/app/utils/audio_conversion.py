from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.services.transcription_errors import TranscriptionError

_SUPPORTED_AUDIO_SUFFIXES = {".ogg", ".opus", ".webm", ".mp3", ".wav", ".m4a", ".mp4", ".mov"}


@dataclass
class PreparedAudioFile:
    path: Path
    temporary: bool = False

    def cleanup(self) -> None:
        if self.temporary and self.path.exists():
            self.path.unlink(missing_ok=True)


def prepare_audio_for_whisper(*, input_path: Path, ffmpeg_timeout_seconds: float) -> PreparedAudioFile:
    source = Path(input_path)
    if not source.exists() or not source.is_file():
        raise TranscriptionError("audio_not_found", f"audio file not found: {source}", retryable=False)
    if source.stat().st_size == 0:
        raise TranscriptionError("audio_empty", f"audio file is empty: {source}", retryable=False)

    suffix = source.suffix.lower()
    if suffix not in _SUPPORTED_AUDIO_SUFFIXES:
        raise TranscriptionError("audio_format_invalid", f"unsupported audio extension: {suffix}", retryable=False)

    if suffix == ".wav":
        return PreparedAudioFile(path=source, temporary=False)

    ffmpeg_binary = shutil.which("ffmpeg")
    if not ffmpeg_binary:
        raise TranscriptionError("ffmpeg_missing", "ffmpeg binary not found in PATH", retryable=False)

    with tempfile.NamedTemporaryFile(prefix="whisper_input_", suffix=".wav", delete=False) as tmp:
        temp_path = Path(tmp.name)

    command = [
        ffmpeg_binary,
        "-nostdin",
        "-y",
        "-i",
        str(source),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(temp_path),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=ffmpeg_timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        temp_path.unlink(missing_ok=True)
        raise TranscriptionError("ffmpeg_timeout", str(exc), retryable=True) from exc
    except OSError as exc:
        temp_path.unlink(missing_ok=True)
        raise TranscriptionError("ffmpeg_execution_error", str(exc), retryable=False) from exc

    if completed.returncode != 0:
        temp_path.unlink(missing_ok=True)
        stderr = (completed.stderr or "").strip()
        raise TranscriptionError("ffmpeg_failed", stderr[:500] or "ffmpeg conversion failed", retryable=False)

    if not temp_path.exists() or os.path.getsize(temp_path) == 0:
        temp_path.unlink(missing_ok=True)
        raise TranscriptionError("ffmpeg_invalid_output", "ffmpeg produced empty output", retryable=False)

    return PreparedAudioFile(path=temp_path, temporary=True)
