"""Transcription backend dispatcher."""

from __future__ import annotations

from pathlib import Path

from .options import SUPPORTED_BACKENDS, TranscriptionOptions


def transcribe_media(media_path: Path, output_path: Path, options: TranscriptionOptions) -> None:
    if options.backend == "local":
        from . import local

        local.transcribe(media_path, output_path, options)
        return
    if options.backend == "azure":
        from . import azure

        azure.transcribe(media_path, output_path, options)
        return
    if options.backend == "aws":
        from . import aws

        aws.transcribe(media_path, output_path, options)
        return
    if options.backend == "google":
        from . import google

        google.transcribe(media_path, output_path, options)
        return
    if options.backend == "tencent":
        from . import tencent

        tencent.transcribe(media_path, output_path, options)
        return
    if options.backend == "aliyun":
        from . import aliyun

        aliyun.transcribe(media_path, output_path, options)
        return
    raise ValueError(f"Unsupported transcription backend: {options.backend}")
