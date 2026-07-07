"""AWS Transcribe backend."""

from __future__ import annotations

import importlib
import json
import time
import uuid
from pathlib import Path
from urllib.request import urlopen

from .formatting import SpeakerTurn, speaker_turns_to_srt, speaker_turns_to_text
from .options import TranscriptionOptions


def import_boto3() -> object:
    try:
        return importlib.import_module("boto3")
    except ImportError as exc:
        raise RuntimeError("AWS backend requires: python3 -m pip install 'castscribe[aws]'") from exc


def read_json_url(url: str) -> dict[str, object]:
    with urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def transcribe(media_path: Path, output_path: Path, options: TranscriptionOptions) -> None:
    if not options.cloud_uri:
        raise RuntimeError("AWS backend requires --cloud-uri with an s3:// media URI")

    boto3 = import_boto3()
    client = boto3.client("transcribe", region_name=options.cloud_region)
    job_name = f"castscribe-{uuid.uuid4().hex}"
    request: dict[str, object] = {
        "TranscriptionJobName": job_name,
        "Media": {"MediaFileUri": options.cloud_uri},
        "LanguageCode": options.cloud_language,
        "Settings": {
            "ShowSpeakerLabels": True,
            "MaxSpeakerLabels": options.effective_max_speakers,
        },
    }
    if options.cloud_output_uri:
        bucket, key = parse_s3_uri(options.cloud_output_uri)
        request["OutputBucketName"] = bucket
        if key:
            request["OutputKey"] = key

    client.start_transcription_job(**request)
    transcript_url = wait_for_job(client, job_name, options)
    payload = read_json_url(transcript_url)
    turns = aws_payload_to_turns(payload)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if options.output_format == "srt":
        output_path.write_text(speaker_turns_to_srt(turns), encoding="utf-8")
    else:
        output_path.write_text(speaker_turns_to_text(turns), encoding="utf-8")


def wait_for_job(client: object, job_name: str, options: TranscriptionOptions) -> str:
    deadline = time.monotonic() + options.timeout
    while time.monotonic() < deadline:
        status = client.get_transcription_job(TranscriptionJobName=job_name)
        job = status["TranscriptionJob"]
        state = job["TranscriptionJobStatus"]
        if state == "COMPLETED":
            return job["Transcript"]["TranscriptFileUri"]
        if state == "FAILED":
            raise RuntimeError(f"AWS transcription failed: {job.get('FailureReason', 'unknown error')}")
        time.sleep(options.poll_interval)
    raise TimeoutError("AWS transcription timed out")


def parse_s3_uri(uri: str) -> tuple[str, str]:
    if not uri.startswith("s3://"):
        raise RuntimeError("--cloud-output-uri for AWS must be an s3:// URI")
    rest = uri[5:]
    bucket, _, key = rest.partition("/")
    if not bucket:
        raise RuntimeError("--cloud-output-uri for AWS must include a bucket")
    return bucket, key


def aws_payload_to_turns(payload: dict[str, object]) -> list[SpeakerTurn]:
    results = payload.get("results", {})
    items = results.get("items", []) if isinstance(results, dict) else []
    speaker_labels = results.get("speaker_labels", {}) if isinstance(results, dict) else {}
    label_by_start: dict[str, str] = {}
    segment_times: dict[str, tuple[float | None, float | None]] = {}

    for segment in speaker_labels.get("segments", []):
        speaker = segment.get("speaker_label", "Unknown")
        start = parse_float(segment.get("start_time"))
        end = parse_float(segment.get("end_time"))
        for item in segment.get("items", []):
            item_start = item.get("start_time")
            if item_start is not None:
                label_by_start[str(item_start)] = speaker
                segment_times[str(item_start)] = (start, end)

    turns: list[SpeakerTurn] = []
    current_speaker = "Unknown"
    for item in items:
        alternatives = item.get("alternatives") or []
        if not alternatives:
            continue
        content = alternatives[0].get("content", "")
        if item.get("type") == "punctuation" and turns:
            previous = turns[-1]
            turns[-1] = SpeakerTurn(previous.speaker, previous.text + content, previous.start, previous.end)
            continue
        start_key = str(item.get("start_time"))
        current_speaker = label_by_start.get(start_key, current_speaker)
        start, end = segment_times.get(start_key, (parse_float(item.get("start_time")), parse_float(item.get("end_time"))))
        turns.append(SpeakerTurn(current_speaker, content, start, end))
    return turns


def parse_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
