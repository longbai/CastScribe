"""Format normalized transcription segments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .local import seconds_to_srt_time


@dataclass(frozen=True)
class SpeakerTurn:
    speaker: str
    text: str
    start: float | None = None
    end: float | None = None


def speaker_turns_to_text(turns: Sequence[SpeakerTurn]) -> str:
    grouped: list[SpeakerTurn] = []
    for turn in turns:
        text = turn.text.strip()
        if not text:
            continue
        if grouped and grouped[-1].speaker == turn.speaker:
            previous = grouped[-1]
            grouped[-1] = SpeakerTurn(
                previous.speaker,
                f"{previous.text.rstrip()} {text}",
                previous.start,
                turn.end if turn.end is not None else previous.end,
            )
        else:
            grouped.append(SpeakerTurn(turn.speaker, text, turn.start, turn.end))

    return "".join(f"Speaker {turn.speaker}: {turn.text}\n" for turn in grouped)


def speaker_turns_to_srt(turns: Sequence[SpeakerTurn]) -> str:
    cues: list[str] = []
    for turn in turns:
        if turn.start is None or turn.end is None:
            raise ValueError("Speaker turn timestamps are required for srt output")
        text = turn.text.strip()
        if text:
            cues.append(
                f"{len(cues) + 1}\n"
                f"{seconds_to_srt_time(turn.start)} --> {seconds_to_srt_time(turn.end)}\n"
                f"Speaker {turn.speaker}: {text}"
            )
    return "\n\n".join(cues) + ("\n" if cues else "")
