# CastScribe

CastScribe downloads subtitles or media from YouTube, Bilibili, Xiaoyuzhou, Apple Podcasts, playlists, feeds, and channel URLs, then writes transcript files.

It first tries subtitles. If subtitles are unavailable, it downloads audio. If audio-only download is unavailable, it downloads the lowest quality combined audio/video format and transcribes that.

## Requirements

- Python 3.10+
- `yt-dlp` Python package, installed automatically when installing this project
- Or `yt-dlp` CLI available on `PATH`
- macOS transcription: `yap`
- non-macOS transcription: `python3 -m pip install faster-whisper`

## Install

From this repository:

```bash
python3 -m pip install -e .
```

Then run:

```bash
castscribe --help
```

You can also run without installing:

```bash
PYTHONPATH=src python3 -m castscribe --help
```

The old script entry remains available for compatibility:

```bash
PYTHONPATH=src python3 media_to_text.py --help
```

## Usage

Single or multiple remote URLs:

```bash
castscribe "https://www.youtube.com/watch?v=..."
castscribe "https://space.bilibili.com/..." "https://www.xiaoyuzhoufm.com/episode/..."
```

URL file:

```bash
castscribe --input urls.txt
```

Channel or playlist URL:

```bash
castscribe --output transcripts "https://www.youtube.com/@channel/videos"
castscribe --output transcripts "https://www.youtube.com/playlist?list=..."
castscribe --locale en_US --output transcripts "https://podcasts.apple.com/cn/podcast/the-economics-of-everyday-things/id1666678354"
```

Local files, `file://` URLs, and local directories:

```bash
castscribe ./audio.mp3
castscribe file:///Users/me/Downloads/captions.vtt
castscribe --output transcripts ./podcast-downloads
```

SRT output:

```bash
castscribe --format srt ./audio.mp3
castscribe --format srt --output transcripts "https://www.youtube.com/watch?v=..."
```

YouTube or Bilibili may require cookies when they show bot, sign-in, or HTTP 412 checks:

```bash
castscribe --cookies-from-browser chrome "https://www.youtube.com/shorts/JLV1YqS445I"
castscribe --cookies cookies.txt "https://www.youtube.com/watch?v=HjDsO0RHQHg&t=303s"
castscribe --cookies-from-browser chrome "https://space.bilibili.com/266765166/lists/2621160?type=season"
```

Limit a channel, playlist, or podcast feed while testing:

```bash
castscribe --playlist-items 1:2 --locale en_US --output transcripts "https://podcasts.apple.com/cn/podcast/the-economics-of-everyday-things/id1666678354"
```

## Behavior

The program first tries subtitles, preferring `zh-Hans`, `zh-CN`, `zh`, then `en`.

Apple Podcasts show pages are resolved through Apple's lookup API to their RSS feed before downloading episodes.

Local subtitle files are converted directly to `.txt` or `.srt`. Local media files are transcribed directly. Local directories are scanned recursively for supported subtitle and media files.

Output rules:

- Without `--output`, each output is written next to the source or downloaded file with the same basename, ending in `.txt` or `.srt`.
- With `--output DIR`, all transcript files are written directly into `DIR`.
- Remote downloads use `DIR/downloads` when `--output DIR` is set. Without `--output`, downloads are written under the current directory using the `yt-dlp` filename template.
- Existing `.txt` or `.srt` files are skipped, so channel and playlist downloads can be rerun after interruption.

## Development

Run tests:

```bash
python3 -m unittest discover -s tests
```
