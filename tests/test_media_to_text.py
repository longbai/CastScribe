import platform
import subprocess
import unittest
import locale
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from castscribe import downloader as castscribe_downloader
from castscribe import pipeline, sources, subtitles, transcriber
from castscribe.transcription.options import TranscriptionOptions


class MediaToTextTests(unittest.TestCase):
    def test_collect_sources_combines_arguments_and_input_file(self):
        with TemporaryDirectory() as tmp:
            input_file = Path(tmp) / "urls.txt"
            input_file.write_text(
                "https://example.com/a\n\n# comment\nhttps://example.com/b\n",
                encoding="utf-8",
            )

            result = sources.collect_sources(["https://example.com/c"], input_file)

        self.assertEqual(
            result,
            ["https://example.com/c", "https://example.com/a", "https://example.com/b"],
        )

    def test_subtitle_to_text_removes_cues_tags_and_duplicate_lines(self):
        raw = """WEBVTT

00:00:01.000 --> 00:00:02.000
<c>hello</c>

00:00:02.000 --> 00:00:03.000
hello
world
"""

        self.assertEqual(subtitles.subtitle_to_text(raw), "hello\nworld\n")

    def test_transcriber_uses_yap_on_macos(self):
        with mock.patch.object(platform, "system", return_value="Darwin"):
            command = transcriber.build_transcription_command(
                Path("a.m4a"),
                Path("a.txt"),
                "base",
                "txt",
                "en_US",
            )

        self.assertEqual(command, ["yap", "transcribe", "a.m4a", "--locale", "en_US", "--txt", "-o", "a.txt"])

    def test_transcriber_normalizes_unsupported_en_cn_locale_for_yap(self):
        with (
            mock.patch.object(platform, "system", return_value="Darwin"),
            mock.patch.object(locale, "getlocale", return_value=("en_CN", "UTF-8")),
        ):
            command = transcriber.build_transcription_command(
                Path("a.m4a"),
                Path("a.txt"),
                "base",
                "txt",
                None,
            )

        self.assertEqual(command, ["yap", "transcribe", "a.m4a", "--locale", "zh_CN", "--txt", "-o", "a.txt"])

    def test_transcriber_can_use_yap_srt_output(self):
        with mock.patch.object(platform, "system", return_value="Darwin"):
            command = transcriber.build_transcription_command(
                Path("a.m4a"),
                Path("a.srt"),
                "base",
                "srt",
                "zh_TW",
            )

        self.assertEqual(command, ["yap", "transcribe", "a.m4a", "--locale", "zh_TW", "--srt", "-o", "a.srt"])

    def test_transcriber_retries_yap_with_zh_cn_when_auto_locale_fails(self):
        calls = []

        def fake_run(command, check, text):
            calls.append(command)
            if len(calls) == 1:
                raise subprocess.CalledProcessError(1, command)
            return subprocess.CompletedProcess(command, 0)

        with (
            mock.patch.object(platform, "system", return_value="Darwin"),
            mock.patch.object(locale, "getlocale", return_value=("en_US", "UTF-8")),
            mock.patch.object(subprocess, "run", side_effect=fake_run),
        ):
            transcriber.transcribe_media(Path("a.mp4"), Path("a.txt"), "base", "txt")

        self.assertEqual(calls[0][4], "en_US")
        self.assertEqual(calls[1][4], "zh_CN")

    def test_downloader_falls_back_to_cli_when_python_package_missing(self):
        runner = mock.Mock(return_value=subprocess.CompletedProcess(["yt-dlp"], 0, "", ""))
        downloader = castscribe_downloader.YtDlpDownloader(
            runner=runner,
            import_yt_dlp=lambda: None,
        )

        result = downloader.download_subtitles("https://example.com/v", Path("out"))

        self.assertEqual(result, [])
        self.assertTrue(runner.called)
        self.assertIn("--skip-download", runner.call_args.args[0])

    def test_downloader_explicitly_allows_playlists_for_cli_fallback(self):
        runner = mock.Mock(return_value=subprocess.CompletedProcess(["yt-dlp"], 0, "", ""))
        downloader = castscribe_downloader.YtDlpDownloader(
            runner=runner,
            import_yt_dlp=lambda: None,
        )

        downloader.download_subtitles("https://www.youtube.com/playlist?list=abc", Path("out"))
        subtitle_args = runner.call_args.args[0]
        downloader.download_audio("https://www.youtube.com/playlist?list=abc", Path("out"))
        audio_args = runner.call_args.args[0]

        self.assertIn("--yes-playlist", subtitle_args)
        self.assertIn("--yes-playlist", audio_args)
        self.assertIn("bestaudio[ext=m4a]/bestaudio/best", audio_args)

    def test_downloader_passes_cookie_options_to_cli_fallback(self):
        runner = mock.Mock(return_value=subprocess.CompletedProcess(["yt-dlp"], 0, "", ""))
        downloader = castscribe_downloader.YtDlpDownloader(
            runner=runner,
            import_yt_dlp=lambda: None,
            cookies=Path("cookies.txt"),
            cookies_from_browser="chrome",
        )

        downloader.download_subtitles("https://www.youtube.com/watch?v=abc", Path("out"))
        args = runner.call_args.args[0]

        self.assertIn("--cookies", args)
        self.assertIn("cookies.txt", args)
        self.assertIn("--cookies-from-browser", args)
        self.assertIn("chrome", args)

    def test_downloader_explicitly_allows_playlists_for_python_api(self):
        captured_options = []

        class FakeYoutubeDL:
            def __init__(self, options):
                captured_options.append(options)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def download(self, sources):
                return None

        fake_module = mock.Mock(YoutubeDL=FakeYoutubeDL)
        downloader = castscribe_downloader.YtDlpDownloader(import_yt_dlp=lambda: fake_module)

        downloader.download_subtitles("https://www.youtube.com/playlist?list=abc", Path("out"))
        downloader.download_audio("https://www.youtube.com/playlist?list=abc", Path("out"))

        self.assertFalse(captured_options[0]["noplaylist"])
        self.assertFalse(captured_options[1]["noplaylist"])

    def test_downloader_passes_cookie_options_to_python_api(self):
        captured_options = []

        class FakeYoutubeDL:
            def __init__(self, options):
                captured_options.append(options)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def download(self, sources):
                return None

        fake_module = mock.Mock(YoutubeDL=FakeYoutubeDL)
        downloader = castscribe_downloader.YtDlpDownloader(
            import_yt_dlp=lambda: fake_module,
            cookies=Path("cookies.txt"),
            cookies_from_browser="chrome",
        )

        downloader.download_subtitles("https://www.youtube.com/watch?v=abc", Path("out"))

        self.assertEqual(captured_options[0]["cookiefile"], "cookies.txt")
        self.assertEqual(captured_options[0]["cookiesfrombrowser"], ("chrome", None, None, None))

    def test_process_source_uses_lowest_media_when_audio_produces_no_files(self):
        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "downloads" / "single" / "video [id].mp4"
            media.parent.mkdir(parents=True)
            media.write_text("fake media", encoding="utf-8")
            downloader = mock.Mock()
            downloader.download_subtitles.return_value = []
            downloader.download_audio.return_value = []
            downloader.download_lowest_media.return_value = [media]

            options = TranscriptionOptions(backend="google", language="en-US")
            with mock.patch.object(pipeline, "transcribe_media") as transcribe:
                pipeline.process_source(
                    "https://example.com/v",
                    Path(tmp),
                    downloader,
                    "base",
                    keep_subtitles=True,
                    transcription_options=options,
                )

        downloader.download_lowest_media.assert_called_once()
        transcribe.assert_called_once()
        self.assertEqual(transcribe.call_args.args[2], options)

    def test_apple_podcast_show_url_resolves_to_feed_url_before_download(self):
        payload = {
            "resultCount": 1,
            "results": [
                {
                    "collectionId": 1666678354,
                    "feedUrl": "https://feeds.simplecast.com/ob9OSBIN",
                }
            ],
        }
        opener = mock.Mock(return_value=json.dumps(payload).encode("utf-8"))
        downloader = mock.Mock()
        downloader.download_subtitles.return_value = []
        downloader.download_audio.return_value = []
        downloader.download_lowest_media.return_value = []

        pipeline.process_source(
            "https://podcasts.apple.com/cn/podcast/the-economics-of-everyday-things/id1666678354",
            Path("out"),
            downloader,
            "base",
            keep_subtitles=True,
            url_opener=opener,
        )

        downloader.download_subtitles.assert_called_once()
        self.assertEqual(downloader.download_subtitles.call_args.args[0], "https://feeds.simplecast.com/ob9OSBIN")

    def test_downloader_passes_playlist_item_limit_to_cli_fallback(self):
        runner = mock.Mock(return_value=subprocess.CompletedProcess(["yt-dlp"], 0, "", ""))
        downloader = castscribe_downloader.YtDlpDownloader(
            runner=runner,
            import_yt_dlp=lambda: None,
            playlist_items="1:2",
        )

        downloader.download_audio("https://feeds.example.com/show", Path("out"))
        args = runner.call_args.args[0]

        self.assertIn("--playlist-items", args)
        self.assertIn("1:2", args)

    def test_downloader_passes_playlist_item_limit_to_python_api(self):
        captured_options = []

        class FakeYoutubeDL:
            def __init__(self, options):
                captured_options.append(options)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def download(self, sources):
                return None

        fake_module = mock.Mock(YoutubeDL=FakeYoutubeDL)
        downloader = castscribe_downloader.YtDlpDownloader(
            import_yt_dlp=lambda: fake_module,
            playlist_items="1:2",
        )

        downloader.download_audio("https://feeds.example.com/show", Path("out"))

        self.assertEqual(captured_options[0]["playlist_items"], "1:2")

    def test_file_url_subtitle_is_processed_without_downloader(self):
        with TemporaryDirectory() as tmp:
            subtitle = Path(tmp) / "clip.vtt"
            subtitle.write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nhello\n", encoding="utf-8")
            downloader = mock.Mock()

            pipeline.process_source(
                subtitle.as_uri(),
                None,
                downloader,
                "base",
                keep_subtitles=True,
            )

            text_path = subtitle.with_suffix(".txt")
            text = text_path.read_text(encoding="utf-8")

        downloader.download_subtitles.assert_not_called()
        self.assertEqual(text, "hello\n")

    def test_output_directory_puts_local_transcript_inside_that_directory(self):
        with TemporaryDirectory() as tmp:
            subtitle = Path(tmp) / "clip.vtt"
            subtitle.write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nhello\n", encoding="utf-8")
            output = Path(tmp) / "out"

            pipeline.process_source(
                str(subtitle),
                output,
                mock.Mock(),
                "base",
                keep_subtitles=True,
            )

            text = (output / "clip.txt").read_text(encoding="utf-8")

        self.assertEqual(text, "hello\n")

    def test_local_directory_recursively_transcribes_media_files(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "input"
            nested = root / "nested"
            nested.mkdir(parents=True)
            media = nested / "episode.mp3"
            media.write_text("fake media", encoding="utf-8")
            (nested / "notes.txt").write_text("ignore me", encoding="utf-8")
            output = Path(tmp) / "out"
            downloader = mock.Mock()

            with mock.patch.object(pipeline, "transcribe_media") as transcribe:
                pipeline.process_source(
                    str(root),
                    output,
                    downloader,
                    "base",
                    keep_subtitles=True,
                )

        downloader.download_subtitles.assert_not_called()
        transcribe.assert_called_once()
        self.assertEqual(transcribe.call_args.args[0], media)

    def test_output_format_srt_uses_srt_extension_for_local_subtitle(self):
        with TemporaryDirectory() as tmp:
            subtitle = Path(tmp) / "clip.srt"
            subtitle.write_text("1\n00:00:00,000 --> 00:00:01,000\nhello\n", encoding="utf-8")
            output = Path(tmp) / "out"

            pipeline.process_source(
                str(subtitle),
                output,
                mock.Mock(),
                "base",
                keep_subtitles=True,
                output_format="srt",
            )

            text = (output / "clip.srt").read_text(encoding="utf-8")

        self.assertIn("hello", text)


if __name__ == "__main__":
    unittest.main()
