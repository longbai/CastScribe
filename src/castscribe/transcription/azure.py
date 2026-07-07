"""Azure Speech transcription backend."""

from __future__ import annotations

import importlib
import os
import threading
from pathlib import Path

from .formatting import SpeakerTurn, speaker_turns_to_text
from .options import TranscriptionOptions


def import_azure_speech() -> object:
    try:
        return importlib.import_module("azure.cognitiveservices.speech")
    except ImportError as exc:
        raise RuntimeError("Azure backend requires: python3 -m pip install 'castscribe[azure]'") from exc


def transcribe(media_path: Path, output_path: Path, options: TranscriptionOptions) -> None:
    speech_key = os.environ.get("SPEECH_KEY")
    endpoint = os.environ.get("ENDPOINT")
    if not speech_key or not endpoint:
        raise RuntimeError("Azure backend requires SPEECH_KEY and ENDPOINT environment variables")
    if options.output_format == "srt":
        raise RuntimeError("Azure backend srt output is not supported yet because reliable timestamps are not exposed here")

    speechsdk = import_azure_speech()
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, endpoint=endpoint)
    speech_config.speech_recognition_language = options.cloud_language
    if hasattr(speech_config, "set_property"):
        speech_config.set_property(
            property_id=speechsdk.PropertyId.SpeechServiceResponse_DiarizeIntermediateResults,
            value="true",
        )
    audio_config = speechsdk.audio.AudioConfig(filename=str(media_path))
    transcriber = speechsdk.transcription.ConversationTranscriber(
        speech_config=speech_config,
        audio_config=audio_config,
    )
    done = threading.Event()
    turns: list[SpeakerTurn] = []

    def on_transcribed(event: object) -> None:
        result = getattr(event, "result", None)
        if result is None or getattr(result, "reason", None) != speechsdk.ResultReason.RecognizedSpeech:
            return
        text = getattr(result, "text", "").strip()
        if text:
            turns.append(SpeakerTurn(getattr(result, "speaker_id", None) or "Unknown", text))

    def on_stop(_event: object) -> None:
        done.set()

    transcriber.transcribed.connect(on_transcribed)
    transcriber.session_stopped.connect(on_stop)
    transcriber.canceled.connect(on_stop)
    transcriber.start_transcribing_async().get()
    if not done.wait(options.timeout):
        raise TimeoutError("Azure transcription timed out")
    transcriber.stop_transcribing_async().get()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(speaker_turns_to_text(turns), encoding="utf-8")
