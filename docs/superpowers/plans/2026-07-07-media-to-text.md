# Media To Text Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI that downloads subtitles or media from YouTube, Bilibili, Xiaoyuzhou, single URLs, playlists, and channels, then writes plain text transcripts.

**Architecture:** A single Python module provides CLI parsing, source collection, `yt-dlp` Python API integration with CLI fallback, subtitle cleanup, and transcription command dispatch. External downloads and transcriptions are isolated behind small functions so unit tests can mock them.

**Tech Stack:** Python standard library, optional `yt-dlp` Python package, optional `yt-dlp` CLI fallback, `yap` on macOS, `faster-whisper` on non-macOS.

---

### Task 1: Core Unit Tests

**Files:**
- Create: `tests/test_media_to_text.py`
- Create: `media_to_text.py`

- [ ] **Step 1: Write failing tests for source collection, subtitle cleanup, backend selection, and downloader fallback**

```python
import platform
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import media_to_text


class MediaToTextTests(unittest.TestCase):
    def test_collect_sources_combines_arguments_and_input_file(self):
        with TemporaryDirectory() as tmp:
            input_file = Path(tmp) / "urls.txt"
            input_file.write_text("https://example.com/a\n\n# comment\nhttps://example.com/b\n", encoding="utf-8")

            sources = media_to_text.collect_sources(["https://example.com/c"], input_file)

        self.assertEqual(sources, ["https://example.com/c", "https://example.com/a", "https://example.com/b"])

    def test_subtitle_to_text_removes_cues_tags_and_duplicate_lines(self):
        raw = """WEBVTT

00:00:01.000 --> 00:00:02.000
<c>hello</c>

00:00:02.000 --> 00:00:03.000
hello
world
"""

        self.assertEqual(media_to_text.subtitle_to_text(raw), "hello\nworld\n")

    def test_transcriber_uses_yap_on_macos(self):
        with mock.patch.object(platform, "system", return_value="Darwin"):
            command = media_to_text.build_transcription_command(Path("a.m4a"), Path("a.txt"), "base")

        self.assertEqual(command, ["yap", "transcribe", "a.m4a", "-o", "a.txt"])

    def test_downloader_falls_back_to_cli_when_python_package_missing(self):
        runner = mock.Mock(return_value=subprocess.CompletedProcess(["yt-dlp"], 0, "", ""))
        downloader = media_to_text.YtDlpDownloader(runner=runner, import_yt_dlp=lambda: None)

        result = downloader.download_subtitles("https://example.com/v", Path("out"))

        self.assertEqual(result, [])
        self.assertTrue(runner.called)
        self.assertIn("--skip-download", runner.call_args.args[0])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests/test_media_to_text.py`
Expected: FAIL because `media_to_text` does not exist yet.

### Task 2: Implement CLI and Pipeline

**Files:**
- Modify: `media_to_text.py`

- [ ] **Step 1: Implement source collection, subtitle cleanup, downloader adapter, transcription command builder, and CLI**

The implementation keeps side effects in `YtDlpDownloader` and `transcribe_media`.

- [ ] **Step 2: Run unit tests**

Run: `python3 -m unittest tests/test_media_to_text.py`
Expected: all tests pass.

### Task 3: Documentation

**Files:**
- Create: `README.md`

- [ ] **Step 1: Document installation and usage**

Include examples for URL arguments, `--input`, and channel URLs. Document `yt-dlp`, `yap`, and `faster-whisper` requirements.

- [ ] **Step 2: Run final verification**

Run: `python3 -m unittest discover -s tests`
Expected: all tests pass.

## Notes

This workspace is not a git repository, so commit steps are not applicable here.

