"""Subtitle cleanup and conversion helpers."""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path
from typing import Sequence


SUBTITLE_EXTENSIONS = {".vtt", ".srt", ".ass", ".json3"}


def subtitle_to_text(raw: str) -> str:
    lines: list[str] = []
    previous = ""

    for line in raw.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        if cleaned in {"WEBVTT", "Kind: captions", "Language: en"}:
            continue
        if "-->" in cleaned:
            continue
        if re.fullmatch(r"\d+", cleaned):
            continue
        if cleaned.startswith(("NOTE", "STYLE", "REGION")):
            continue

        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        cleaned = re.sub(r"\{\\[^}]+\}", "", cleaned)
        cleaned = html.unescape(cleaned).strip()
        if cleaned and cleaned != previous:
            lines.append(cleaned)
            previous = cleaned

    return "\n".join(lines) + ("\n" if lines else "")


def subtitle_file_to_output(subtitle_path: Path, output_path: Path, output_format: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "srt":
        if subtitle_path.suffix.lower() == ".srt":
            shutil.copyfile(subtitle_path, output_path)
        else:
            output_path.write_text(
                subtitle_to_srt(subtitle_path.read_text(encoding="utf-8", errors="ignore")),
                encoding="utf-8",
            )
        return

    output_path.write_text(
        subtitle_to_text(subtitle_path.read_text(encoding="utf-8", errors="ignore")),
        encoding="utf-8",
    )


def subtitle_file_to_text(subtitle_path: Path, text_path: Path) -> None:
    subtitle_file_to_output(subtitle_path, text_path, "txt")


def subtitle_to_srt(raw: str) -> str:
    cues: list[str] = []
    current: list[str] = []
    current_time = ""

    for line in raw.splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned == "WEBVTT" or cleaned.startswith(("NOTE", "STYLE", "REGION")):
            continue
        if re.fullmatch(r"\d+", cleaned):
            continue
        if "-->" in cleaned:
            if current_time and current:
                cues.append(format_srt_cue(len(cues) + 1, current_time, current))
            current_time = cleaned.replace(".", ",")
            current = []
            continue
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        cleaned = html.unescape(cleaned).strip()
        if cleaned:
            current.append(cleaned)

    if current_time and current:
        cues.append(format_srt_cue(len(cues) + 1, current_time, current))

    return "\n\n".join(cues) + ("\n" if cues else "")


def format_srt_cue(index: int, timing: str, lines: Sequence[str]) -> str:
    return f"{index}\n{timing}\n" + "\n".join(lines)
