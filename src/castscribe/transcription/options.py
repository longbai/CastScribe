"""Shared transcription backend options."""

from __future__ import annotations

from dataclasses import dataclass


SUPPORTED_BACKENDS = ("local", "azure", "aws", "google", "tencent", "aliyun")


@dataclass(frozen=True)
class TranscriptionOptions:
    backend: str = "local"
    model: str = "base"
    output_format: str = "txt"
    language: str | None = None
    locale: str | None = None
    min_speakers: int = 2
    max_speakers: int = 10
    speaker_count: int | None = None
    cloud_uri: str | None = None
    cloud_output_uri: str | None = None
    cloud_region: str | None = None
    poll_interval: float = 5.0
    timeout: float = 3600.0

    def __post_init__(self) -> None:
        if self.backend not in SUPPORTED_BACKENDS:
            raise ValueError(f"Unsupported transcription backend: {self.backend}")
        if self.min_speakers < 1:
            raise ValueError("min_speakers must be at least 1")
        if self.max_speakers < self.min_speakers:
            raise ValueError("min_speakers must be less than or equal to max_speakers")
        if self.speaker_count is not None and self.speaker_count < 1:
            raise ValueError("speaker_count must be at least 1")
        if self.poll_interval <= 0:
            raise ValueError("poll_interval must be greater than 0")
        if self.timeout <= 0:
            raise ValueError("timeout must be greater than 0")

    @property
    def cloud_language(self) -> str:
        return self.language or "en-US"

    @property
    def effective_min_speakers(self) -> int:
        return self.speaker_count or self.min_speakers

    @property
    def effective_max_speakers(self) -> int:
        return self.speaker_count or self.max_speakers
