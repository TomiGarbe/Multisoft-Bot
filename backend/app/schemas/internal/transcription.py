from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class WhisperSegment(BaseModel):
    id: int
    start_seconds: float
    end_seconds: float
    text: str
    avg_logprob: Optional[float] = None
    no_speech_prob: Optional[float] = None
    compression_ratio: Optional[float] = None


class WhisperTranscriptionResult(BaseModel):
    text: str
    detected_language: Optional[str] = None
    duration_seconds: Optional[float] = None
    segments: list[WhisperSegment] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
