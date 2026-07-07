"""Local transcription backend using yap or faster-whisper."""

from __future__ import annotations

import importlib
import locale
import platform
import subprocess
import sys
from pathlib import Path

from .options import TranscriptionOptions


MEDIA_EXTENSIONS = {
    ".aac",
    ".flac",
    ".m4a",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".ogg",
    ".opus",
    ".wav",
    ".webm",
}
OUTPUT_FORMATS = ("txt", "srt")
YAP_SUPPORTED_LOCALES = {
    "fr_FR",
    "fr_CH",
    "fr_CA",
    "fr_BE",
    "ko_KR",
    "pt_BR",
    "pt_PT",
    "de_AT",
    "de_CH",
    "de_DE",
    "it_IT",
    "it_CH",
    "zh_CN",
    "zh_TW",
    "es_CL",
    "es_ES",
    "es_US",
    "es_MX",
    "en_ZA",
    "en_CA",
    "en_SG",
    "en_IN",
    "en_NZ",
    "en_GB",
    "en_AU",
    "en_US",
    "en_IE",
    "yue_CN",
    "zh_HK",
    "ja_JP",
}


def build_transcription_command(
    media_path: Path,
    text_path: Path,
    model: str,
    output_format: str,
    transcription_locale: str | None,
) -> list[str]:
    if platform.system() == "Darwin":
        return [
            "yap",
            "transcribe",
            str(media_path),
            "--locale",
            resolve_yap_locale(transcription_locale),
            f"--{output_format}",
            "-o",
            str(text_path),
        ]
    return [
        sys.executable,
        "-m",
        "whisper",
        str(media_path),
        "--model",
        model,
        "--output_format",
        output_format,
        "--output_dir",
        str(text_path.parent),
    ]


def resolve_yap_locale(transcription_locale: str | None) -> str:
    if transcription_locale:
        return transcription_locale

    system_locale = locale.getlocale()[0] or "en_US"
    if system_locale in YAP_SUPPORTED_LOCALES:
        return system_locale
    if system_locale.endswith("_CN") or system_locale.startswith("zh"):
        return "zh_CN"
    if system_locale.startswith("en"):
        return "en_US"
    return "en_US"


def transcribe(media_path: Path, output_path: Path, options: TranscriptionOptions) -> None:
    transcribe_media(media_path, output_path, options.model, options.output_format, options.locale)


def transcribe_media(
    media_path: Path,
    output_path: Path,
    model: str,
    output_format: str = "txt",
    transcription_locale: str | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if platform.system() == "Darwin":
        command = build_transcription_command(media_path, output_path, model, output_format, transcription_locale)
        try:
            subprocess.run(command, check=True, text=True)
        except subprocess.CalledProcessError:
            if transcription_locale is not None or resolve_yap_locale(transcription_locale) == "zh_CN":
                raise
            subprocess.run(
                build_transcription_command(media_path, output_path, model, output_format, "zh_CN"),
                check=True,
                text=True,
            )
        return

    try:
        faster_whisper = importlib.import_module("faster_whisper")
    except ImportError as exc:
        raise RuntimeError(
            "Non-macOS transcription requires faster-whisper. Install it with: "
            "python3 -m pip install faster-whisper"
        ) from exc

    whisper_model = faster_whisper.WhisperModel(model)
    segments, _info = whisper_model.transcribe(str(media_path))
    if output_format == "srt":
        output_path.write_text(segments_to_srt(segments), encoding="utf-8")
    else:
        text = "\n".join(segment.text.strip() for segment in segments if segment.text.strip())
        output_path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def segments_to_srt(segments: object) -> str:
    cues = []
    for index, segment in enumerate(segments, start=1):
        text = segment.text.strip()
        if text:
            cues.append(f"{index}\n{seconds_to_srt_time(segment.start)} --> {seconds_to_srt_time(segment.end)}\n{text}")
    return "\n\n".join(cues) + ("\n" if cues else "")


def seconds_to_srt_time(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds_part, millis_part = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{seconds_part:02},{millis_part:03}"
