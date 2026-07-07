"""yt-dlp integration."""

from __future__ import annotations

import importlib
import subprocess
from pathlib import Path
from typing import Callable

from .subtitles import SUBTITLE_EXTENSIONS
from .transcriber import MEDIA_EXTENSIONS


DEFAULT_SUBTITLE_LANGS = ("zh-Hans", "zh-CN", "zh", "en")


class YtDlpDownloader:
    def __init__(
        self,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
        import_yt_dlp: Callable[[], object | None] | None = None,
        cookies: Path | None = None,
        cookies_from_browser: str | None = None,
        playlist_items: str | None = None,
    ) -> None:
        self.runner = runner
        self.import_yt_dlp = import_yt_dlp or self._import_yt_dlp
        self.cookies = cookies
        self.cookies_from_browser = cookies_from_browser
        self.playlist_items = playlist_items

    def download_subtitles(self, source: str, output_dir: Path) -> list[Path]:
        before = self._files(output_dir, SUBTITLE_EXTENSIONS)
        options = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": list(DEFAULT_SUBTITLE_LANGS),
            "subtitlesformat": "vtt/srt/best",
            "outtmpl": self._output_template(output_dir),
            "ignoreerrors": True,
            "noplaylist": False,
        }
        self._download(source, self._with_auth_options(options), self._with_auth_args(self._subtitle_cli_args(output_dir, source)))
        return sorted(self._files(output_dir, SUBTITLE_EXTENSIONS) - before)

    def download_audio(self, source: str, output_dir: Path) -> list[Path]:
        return self._download_media(source, output_dir, "bestaudio[ext=m4a]/bestaudio/best")

    def download_lowest_media(self, source: str, output_dir: Path) -> list[Path]:
        return self._download_media(source, output_dir, "worst")

    def _download_media(self, source: str, output_dir: Path, media_format: str) -> list[Path]:
        before = self._files(output_dir, MEDIA_EXTENSIONS)
        options = {
            "format": media_format,
            "outtmpl": self._output_template(output_dir),
            "ignoreerrors": True,
            "continuedl": True,
            "noplaylist": False,
        }
        cli_args = ["yt-dlp", "--yes-playlist", "-f", media_format, "-o", self._output_template(output_dir), source]
        self._download(source, self._with_auth_options(options), self._with_auth_args(cli_args))
        return sorted(self._files(output_dir, MEDIA_EXTENSIONS) - before)

    def _with_auth_options(self, options: dict[str, object]) -> dict[str, object]:
        options = dict(options)
        if self.cookies is not None:
            options["cookiefile"] = str(self.cookies)
        if self.cookies_from_browser is not None:
            options["cookiesfrombrowser"] = (self.cookies_from_browser, None, None, None)
        if self.playlist_items is not None:
            options["playlist_items"] = self.playlist_items
        return options

    def _with_auth_args(self, args: list[str]) -> list[str]:
        args = list(args)
        if self.cookies is not None:
            args[1:1] = ["--cookies", str(self.cookies)]
        if self.cookies_from_browser is not None:
            args[1:1] = ["--cookies-from-browser", self.cookies_from_browser]
        if self.playlist_items is not None:
            args[1:1] = ["--playlist-items", self.playlist_items]
        return args

    def _download(self, source: str, options: dict[str, object], cli_args: list[str]) -> None:
        yt_dlp_module = self.import_yt_dlp()
        if yt_dlp_module is not None:
            with yt_dlp_module.YoutubeDL(options) as ydl:
                ydl.download([source])
            return

        self.runner(cli_args, check=True, capture_output=True, text=True)

    @staticmethod
    def _import_yt_dlp() -> object | None:
        try:
            return importlib.import_module("yt_dlp")
        except ImportError:
            return None

    @staticmethod
    def _output_template(output_dir: Path) -> str:
        return str(output_dir / "%(playlist_title|single)s" / "%(title).200B [%(id)s].%(ext)s")

    @staticmethod
    def _subtitle_cli_args(output_dir: Path, source: str) -> list[str]:
        return [
            "yt-dlp",
            "--yes-playlist",
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs",
            ",".join(DEFAULT_SUBTITLE_LANGS),
            "--sub-format",
            "vtt/srt/best",
            "-o",
            YtDlpDownloader._output_template(output_dir),
            source,
        ]

    @staticmethod
    def _files(output_dir: Path, extensions: set[str]) -> set[Path]:
        if not output_dir.exists():
            return set()
        return {path for path in output_dir.rglob("*") if path.suffix.lower() in extensions}
