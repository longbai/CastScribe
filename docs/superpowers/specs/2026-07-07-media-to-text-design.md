# Media To Text Design

## Goal

Create a Python CLI that accepts video, playlist, channel, and podcast URLs from command arguments or a text file, downloads available media or subtitles, and produces plain text transcripts.

## Scope

The program supports YouTube, Bilibili, Xiaoyuzhou podcast pages, and any other URL that `yt-dlp` can handle. It supports single items and channel or playlist URLs. Existing `.txt` outputs are skipped by default so interrupted channel jobs can be rerun.

## Architecture

The CLI is a thin orchestration layer around `yt-dlp` and a local transcription engine.

- `media_to_text.py` owns argument parsing, source collection, download decisions, subtitle cleanup, and transcription dispatch.
- `yt-dlp` is integrated through its Python package when importable. If the package is not installed, the program calls the `yt-dlp` executable.
- macOS transcription uses `yap transcribe`.
- Other platforms use Whisper through `faster-whisper` when installed, with a clear installation error if missing.

## Download Flow

For each input source:

1. Try to download subtitles only, preferring `zh-Hans`, `zh-CN`, `zh`, then `en`.
2. If subtitle files are produced, convert them to plain `.txt`.
3. If no subtitles are produced, download best available audio.
4. If audio-only download fails, download the lowest quality combined audio/video format.
5. Transcribe downloaded media to `.txt`.

Channel and playlist URLs use the same flow. `yt-dlp` expands the collection and writes each item using a stable title plus ID filename template.

## Error Handling

Missing external tools fail with explicit messages. Failed sources are appended to `failures.jsonl` with URL, stage, and error text. The program continues with later sources unless `--stop-on-error` is passed.

## Testing

Tests cover source collection, subtitle cleanup, transcription backend selection, and downloader fallback behavior with mocked subprocess calls. Network downloads and real transcription are not run in unit tests.

