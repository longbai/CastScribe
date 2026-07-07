import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from castscribe.transcription.formatting import SpeakerTurn, speaker_turns_to_text, speaker_turns_to_srt
from castscribe.transcription.options import TranscriptionOptions


class TranscriptionCoreTests(unittest.TestCase):
    def test_transcription_options_defaults_to_local_backend(self):
        options = TranscriptionOptions()

        self.assertEqual(options.backend, "local")
        self.assertEqual(options.output_format, "txt")
        self.assertEqual(options.min_speakers, 2)
        self.assertEqual(options.max_speakers, 10)

    def test_transcription_options_rejects_unknown_backend(self):
        with self.assertRaisesRegex(ValueError, "Unsupported transcription backend"):
            TranscriptionOptions(backend="unknown")

    def test_transcription_options_rejects_invalid_speaker_range(self):
        with self.assertRaisesRegex(ValueError, "min_speakers"):
            TranscriptionOptions(min_speakers=4, max_speakers=2)

    def test_speaker_turns_to_text_groups_consecutive_speaker_lines(self):
        turns = [
            SpeakerTurn("1", "hello"),
            SpeakerTurn("1", "again"),
            SpeakerTurn("2", "reply"),
        ]

        self.assertEqual(speaker_turns_to_text(turns), "Speaker 1: hello again\nSpeaker 2: reply\n")

    def test_speaker_turns_to_srt_requires_timestamps(self):
        turns = [SpeakerTurn("1", "hello")]

        with self.assertRaisesRegex(ValueError, "timestamps"):
            speaker_turns_to_srt(turns)


if __name__ == "__main__":
    unittest.main()
