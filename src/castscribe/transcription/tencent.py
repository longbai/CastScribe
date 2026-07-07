"""Tencent Cloud transcription provider placeholder."""

from __future__ import annotations

from pathlib import Path

from .options import TranscriptionOptions


def transcribe(media_path: Path, output_path: Path, options: TranscriptionOptions) -> None:
    raise NotImplementedError(
        "Tencent Cloud backend is not implemented yet. Expected future credentials: "
        "TENCENTCLOUD_SECRET_ID, TENCENTCLOUD_SECRET_KEY, and TENCENTCLOUD_REGION."
    )
