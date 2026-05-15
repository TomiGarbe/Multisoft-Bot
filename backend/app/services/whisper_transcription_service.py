from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path

from app.core.config import settings
from app.schemas.internal.transcription import WhisperSegment, WhisperTranscriptionResult
from app.services.transcription_errors import TranscriptionError
from app.utils.audio_conversion import prepare_audio_for_whisper

logger = logging.getLogger(__name__)


class WhisperTranscriptionService:
    _model = None
    _model_lock = threading.Lock()
    _model_cache_key: tuple[str, str, str] | None = None

    def transcribe_file(self, *, audio_path: str | Path) -> WhisperTranscriptionResult:
        source_path = Path(audio_path)
        started = time.perf_counter()
        logger.info("[WHISPER] transcription_started path=%s", source_path)

        prepared = prepare_audio_for_whisper(
            input_path=source_path,
            ffmpeg_timeout_seconds=settings.WHISPER_FFMPEG_TIMEOUT_SECONDS,
        )
        try:
            result = self._run_with_timeout(prepared_path=prepared.path)
            elapsed = time.perf_counter() - started
            logger.info(
                "[WHISPER] transcription_completed path=%s duration_seconds=%.3f detected_language=%s",
                source_path,
                elapsed,
                result.detected_language,
            )
            return result
        except TranscriptionError:
            logger.exception("[WHISPER] transcription_failed path=%s", source_path)
            raise
        finally:
            prepared.cleanup()

    def _run_with_timeout(self, *, prepared_path: Path) -> WhisperTranscriptionResult:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._transcribe_blocking, prepared_path)
            try:
                return future.result(timeout=settings.WHISPER_TRANSCRIPTION_TIMEOUT_SECONDS)
            except FutureTimeoutError as exc:
                future.cancel()
                raise TranscriptionError(
                    "whisper_timeout",
                    f"transcription exceeded {settings.WHISPER_TRANSCRIPTION_TIMEOUT_SECONDS} seconds",
                    retryable=True,
                ) from exc

    def _transcribe_blocking(self, prepared_path: Path) -> WhisperTranscriptionResult:
        model = self._get_or_create_model()

        try:
            segments_iter, info = model.transcribe(
                str(prepared_path),
                language=settings.WHISPER_LANGUAGE or None,
                task="transcribe",
            )
            segments = list(segments_iter)
        except Exception as exc:
            raise TranscriptionError("whisper_failed", str(exc), retryable=True) from exc

        mapped_segments = [
            WhisperSegment(
                id=segment.id,
                start_seconds=segment.start,
                end_seconds=segment.end,
                text=segment.text.strip(),
                avg_logprob=segment.avg_logprob,
                no_speech_prob=segment.no_speech_prob,
                compression_ratio=segment.compression_ratio,
            )
            for segment in segments
        ]
        text = " ".join(item.text for item in mapped_segments if item.text).strip()
        if not text:
            raise TranscriptionError("whisper_empty_result", "transcription produced no text", retryable=False)

        return WhisperTranscriptionResult(
            text=text,
            detected_language=getattr(info, "language", None),
            duration_seconds=getattr(info, "duration", None),
            segments=mapped_segments,
            metadata={
                "model": settings.WHISPER_MODEL,
                "device": settings.WHISPER_DEVICE,
                "compute_type": settings.WHISPER_COMPUTE_TYPE,
                "segment_count": len(mapped_segments),
            },
        )

    @classmethod
    def _get_or_create_model(cls):
        cache_key = (settings.WHISPER_MODEL, settings.WHISPER_DEVICE, settings.WHISPER_COMPUTE_TYPE)
        if cls._model is not None and cls._model_cache_key == cache_key:
            return cls._model

        with cls._model_lock:
            if cls._model is not None and cls._model_cache_key == cache_key:
                return cls._model
            try:
                from faster_whisper import WhisperModel
            except Exception as exc:
                raise TranscriptionError("whisper_dependency_missing", str(exc), retryable=False) from exc
            cls._model = WhisperModel(
                settings.WHISPER_MODEL,
                device=settings.WHISPER_DEVICE,
                compute_type=settings.WHISPER_COMPUTE_TYPE,
            )
            cls._model_cache_key = cache_key
            return cls._model
