# CastScribe

CastScribe downloads subtitles or media from YouTube, Bilibili, Xiaoyuzhou, Apple Podcasts, playlists, feeds, and channel URLs, then writes transcript files.

It first tries subtitles. If subtitles are unavailable, it downloads audio. If audio-only download is unavailable, it downloads the lowest quality combined audio/video format and transcribes that.

## Operating Systems

CastScribe can download media and convert existing subtitles on any system that supports Python and `yt-dlp`.

Local speech transcription depends on the operating system:

- macOS 26 or later: local transcription uses Apple's `yap` command.
- macOS before 26: use a cloud backend, or use `faster-whisper` by running on another supported Python environment.
- Linux and Windows: local transcription uses `faster-whisper`.

Cloud transcription backends are available on macOS, Linux, and Windows when the matching cloud SDK and credentials are configured.

## Requirements

- Python 3.10+
- `yt-dlp` Python package, installed automatically when installing this project
- Or `yt-dlp` CLI available on `PATH`
- optional cloud transcription SDKs: `castscribe[azure]`, `castscribe[aws]`, `castscribe[google]`, or `castscribe[cloud]`

## Local Transcription Setup

CastScribe first tries downloaded subtitles. These local transcription requirements apply only when no subtitle is available and CastScribe must transcribe audio.

### macOS 26 or Later

CastScribe uses [`yap`](https://github.com/finnvoor/yap) for the default local backend.

Install `yap` with Homebrew:

```bash
brew install yap
```

Or install it with Mint:

```bash
mint install finnvoor/yap
```

Enable Dictation and install the language assets before long runs:

1. Open System Settings.
2. Go to Keyboard.
3. Enable Dictation.
4. Add the language you plan to use, for example English -> United States.

`yap` does not provide speaker diarization. Use `--backend google`, `--backend azure`, or `--backend aws` when you need speaker labels.

### Linux, Windows, or Non-yap Environments

CastScribe uses [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) for the default local backend outside `yap` environments.

Install it through CastScribe's Whisper extra:

```bash
python3 -m pip install -e '.[whisper]'
```

Or install `faster-whisper` directly:

```bash
python3 -m pip install faster-whisper
```

The `--model` value is passed to `faster-whisper`; common choices are `tiny`, `base`, `small`, `medium`, and `large-v3`.

## Install

Install from GitHub:

```bash
python3 -m pip install "castscribe @ git+https://github.com/longbai/CastScribe.git"
```

Or install from a local checkout:

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

## Cloud Transcription

CastScribe only calls a transcription backend when it cannot use downloaded subtitles. The default backend is local.

Install optional cloud SDKs:

```bash
python3 -m pip install -e '.[azure]'
python3 -m pip install -e '.[aws]'
python3 -m pip install -e '.[google]'
python3 -m pip install -e '.[cloud]'
```

Azure Speech uses environment variables named `SPEECH_KEY` and `ENDPOINT`:

```bash
castscribe --backend azure --language en-US ./meeting.wav
```

AWS Transcribe uses the normal `boto3` credential chain. The first version expects the media file to already be available in S3:

```bash
castscribe \
  --backend aws \
  --cloud-region us-west-2 \
  --cloud-uri s3://your-bucket/path/audio.mp3 \
  --language en-US \
  ./audio.mp3
```

Google Cloud Speech-to-Text uses Application Default Credentials:

```bash
castscribe --backend google --language en-US --min-speakers 2 --max-speakers 6 ./meeting.wav
```

Tencent Cloud and Alibaba Cloud are selectable but not implemented yet:

```bash
castscribe --backend tencent ./meeting.wav
castscribe --backend aliyun ./meeting.wav
```

Cloud credentials must not be committed to the repository. Do not pass access keys on the command line; use the provider's environment variables or default credential chain.

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

Build a wheel and source distribution:

```bash
python3 -m pip install -e '.[build]'
python3 -m build
python3 -m twine check dist/*
```

Install the built wheel locally:

```bash
python3 -m pip install dist/castscribe-*.whl
```
