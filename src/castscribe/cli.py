"""CastScribe command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .downloader import YtDlpDownloader
from .pipeline import process_source, write_failure
from .sources import collect_sources
from .transcriber import OUTPUT_FORMATS
from .transcription.options import SUPPORTED_BACKENDS, TranscriptionOptions


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download or read subtitles/media and convert them to transcript files.",
    )
    parser.add_argument("urls", nargs="*", help="Remote URLs, file:// URLs, local files, or local directories")
    parser.add_argument("-i", "--input", type=Path, help="Text file with one URL per line")
    parser.add_argument("-o", "--output", type=Path, help="Write all transcript files to this directory")
    parser.add_argument("--format", choices=OUTPUT_FORMATS, default="txt", help="Transcript output format")
    parser.add_argument("--model", default="base", help="Whisper/faster-whisper model name for non-macOS")
    parser.add_argument("--locale", help="Transcription locale for yap on macOS, for example zh_CN or en_US")
    parser.add_argument("--backend", choices=SUPPORTED_BACKENDS, default="local", help="Transcription backend")
    parser.add_argument("--language", help="Cloud transcription language, for example en-US or zh-CN")
    parser.add_argument("--min-speakers", type=int, default=2, help="Minimum speaker count for diarization")
    parser.add_argument("--max-speakers", type=int, default=10, help="Maximum speaker count for diarization")
    parser.add_argument("--speaker-count", type=int, help="Fixed speaker count for providers that accept one value")
    parser.add_argument("--cloud-uri", help="Cloud media URI, for example s3://bucket/audio.mp3 for AWS")
    parser.add_argument("--cloud-output-uri", help="Cloud output URI or prefix for providers that support it")
    parser.add_argument("--cloud-region", help="Cloud region for providers that require it")
    parser.add_argument("--poll-interval", type=float, default=5.0, help="Cloud job polling interval in seconds")
    parser.add_argument("--timeout", type=float, default=3600.0, help="Cloud transcription timeout in seconds")
    parser.add_argument("--cookies", type=Path, help="yt-dlp cookies.txt file for sites that require sign-in")
    parser.add_argument("--cookies-from-browser", help="Browser name for yt-dlp cookies, for example chrome or safari")
    parser.add_argument("--playlist-items", help="Limit playlist/channel items, for example 1:10 or 3,5,8")
    parser.add_argument("--keep-subtitles", action="store_true", help="Keep downloaded subtitle files")
    parser.add_argument("--stop-on-error", action="store_true", help="Stop at the first failed URL")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    sources = collect_sources(args.urls, args.input)
    if not sources:
        print("No sources provided. Pass URLs/paths as arguments or use --input urls.txt.", file=sys.stderr)
        return 2

    downloader = YtDlpDownloader(
        cookies=args.cookies,
        cookies_from_browser=args.cookies_from_browser,
        playlist_items=args.playlist_items,
    )
    transcription_options = TranscriptionOptions(
        backend=args.backend,
        model=args.model,
        output_format=args.format,
        language=args.language,
        locale=args.locale,
        min_speakers=args.min_speakers,
        max_speakers=args.max_speakers,
        speaker_count=args.speaker_count,
        cloud_uri=args.cloud_uri,
        cloud_output_uri=args.cloud_output_uri,
        cloud_region=args.cloud_region,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
    )
    if args.output is not None:
        args.output.mkdir(parents=True, exist_ok=True)

    for source in sources:
        try:
            process_source(
                source,
                args.output,
                downloader,
                args.model,
                args.keep_subtitles,
                args.format,
                args.locale,
                transcription_options=transcription_options,
            )
        except Exception as exc:
            write_failure(args.output or Path.cwd(), source, "process", exc)
            print(f"Failed: {source}: {exc}", file=sys.stderr)
            if args.stop_on_error:
                return 1

    return 0
