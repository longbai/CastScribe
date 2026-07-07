"""Google Cloud Speech-to-Text backend."""

from __future__ import annotations

import importlib
from pathlib import Path

from .formatting import SpeakerTurn, speaker_turns_to_srt, speaker_turns_to_text
from .options import TranscriptionOptions


def import_google_speech() -> object:
    try:
        return importlib.import_module("google.cloud.speech")
    except ImportError as exc:
        raise RuntimeError("Google backend requires: python3 -m pip install 'castscribe[google]'") from exc


def transcribe(media_path: Path, output_path: Path, options: TranscriptionOptions) -> None:
    speech = import_google_speech()
    client = speech.SpeechClient()
    content = media_path.read_bytes()
    audio = speech.RecognitionAudio(content=content)
    diarization_config = speech.SpeakerDiarizationConfig(
        enable_speaker_diarization=True,
        min_speaker_count=options.effective_min_speakers,
        max_speaker_count=options.effective_max_speakers,
    )
    config = speech.RecognitionConfig(
        language_code=options.cloud_language,
        enable_word_time_offsets=True,
        diarization_config=diarization_config,
    )
    response = client.recognize(config=config, audio=audio)
    turns = google_response_to_turns(response)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if options.output_format == "srt":
        output_path.write_text(speaker_turns_to_srt(turns), encoding="utf-8")
    else:
        output_path.write_text(speaker_turns_to_text(turns), encoding="utf-8")


def google_response_to_turns(response: object) -> list[SpeakerTurn]:
    results = getattr(response, "results", [])
    if not results:
        return []
    words = getattr(results[-1].alternatives[0], "words", [])
    turns: list[SpeakerTurn] = []
    for word in words:
        speaker = getattr(word, "speaker_label", None) or getattr(word, "speaker_tag", "Unknown")
        turns.append(
            SpeakerTurn(
                str(speaker),
                getattr(word, "word", ""),
                offset_seconds(getattr(word, "start_offset", None)),
                offset_seconds(getattr(word, "end_offset", None)),
            )
        )
    return turns


def offset_seconds(offset: object) -> float | None:
    if offset is None:
        return None
    total_seconds = getattr(offset, "total_seconds", None)
    if callable(total_seconds):
        return float(total_seconds())
    seconds = getattr(offset, "seconds", 0)
    nanos = getattr(offset, "nanos", 0)
    return float(seconds) + float(nanos) / 1_000_000_000
