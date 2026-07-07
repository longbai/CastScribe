"""Alibaba Cloud transcription provider placeholder."""

from __future__ import annotations

from pathlib import Path

from .options import TranscriptionOptions


def transcribe(media_path: Path, output_path: Path, options: TranscriptionOptions) -> None:
    raise NotImplementedError(
        "Alibaba Cloud backend is not implemented yet. Expected future credentials: "
        "ALIBABA_CLOUD_ACCESS_KEY_ID, ALIBABA_CLOUD_ACCESS_KEY_SECRET, and ALIBABA_CLOUD_REGION."
    )
