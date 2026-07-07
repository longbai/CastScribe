"""Source processing pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .downloader import YtDlpDownloader
from .sources import local_source_path, resolve_remote_source
from .subtitles import SUBTITLE_EXTENSIONS, subtitle_file_to_output
from .transcriber import MEDIA_EXTENSIONS, transcribe_media


def iter_local_inputs(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if is_supported_local_file(path) else []
    if path.is_dir():
        return sorted(
            child
            for child in path.rglob("*")
            if child.is_file() and is_supported_local_file(child)
        )
    raise FileNotFoundError(f"Local source does not exist: {path}")


def is_supported_local_file(path: Path) -> bool:
    suffix = path.suffix.lower()
    return suffix in SUBTITLE_EXTENSIONS or suffix in MEDIA_EXTENSIONS


def transcript_path_for(source_path: Path, output_dir: Path | None, output_format: str) -> Path:
    if output_dir is None:
        return source_path.with_suffix(f".{output_format}")
    return output_dir / f"{source_path.with_suffix('').name}.{output_format}"


def process_local_source(
    source_path: Path,
    output_dir: Path | None,
    model: str,
    output_format: str,
    transcription_locale: str | None,
) -> None:
    for local_file in iter_local_inputs(source_path):
        output_path = transcript_path_for(local_file, output_dir, output_format)
        if output_path.exists():
            continue
        if local_file.suffix.lower() in SUBTITLE_EXTENSIONS:
            subtitle_file_to_output(local_file, output_path, output_format)
        else:
            transcribe_media(local_file, output_path, model, output_format, transcription_locale)


def write_failure(output_dir: Path, source: str, stage: str, error: Exception) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    record = {"source": source, "stage": stage, "error": str(error)}
    with (output_dir / "failures.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def process_source(
    source: str,
    output_dir: Path | None,
    downloader: YtDlpDownloader,
    model: str,
    keep_subtitles: bool,
    output_format: str = "txt",
    transcription_locale: str | None = None,
    url_opener: Callable[[str], bytes] | None = None,
) -> None:
    local_path = local_source_path(source)
    if local_path is not None:
        process_local_source(local_path, output_dir, model, output_format, transcription_locale)
        return

    source = resolve_remote_source(source, url_opener)
    downloads_dir = (output_dir / "downloads") if output_dir is not None else Path.cwd()

    subtitles = downloader.download_subtitles(source, downloads_dir)
    if subtitles:
        for subtitle in subtitles:
            output_path = transcript_path_for(subtitle, output_dir, output_format)
            if not output_path.exists():
                subtitle_file_to_output(subtitle, output_path, output_format)
            if not keep_subtitles:
                subtitle.unlink(missing_ok=True)
        return

    try:
        media_files = downloader.download_audio(source, downloads_dir)
    except Exception:
        media_files = downloader.download_lowest_media(source, downloads_dir)
    else:
        if not media_files:
            media_files = downloader.download_lowest_media(source, downloads_dir)

    for media in media_files:
        output_path = transcript_path_for(media, output_dir, output_format)
        if not output_path.exists():
            transcribe_media(media, output_path, model, output_format, transcription_locale)
