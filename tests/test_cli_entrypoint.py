import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import media_to_text
from castscribe import cli


class CliEntrypointTests(unittest.TestCase):
    def test_castscribe_main_returns_usage_error_without_sources(self):
        self.assertEqual(cli.main([]), 2)

    def test_legacy_script_exports_same_main_function(self):
        self.assertIs(media_to_text.main, cli.main)

    def test_parse_args_accepts_cloud_backend_options(self):
        args = cli.parse_args(
            [
                "--backend",
                "google",
                "--language",
                "en-US",
                "--min-speakers",
                "2",
                "--max-speakers",
                "6",
                "--speaker-count",
                "3",
                "--cloud-uri",
                "s3://bucket/audio.mp3",
                "--cloud-output-uri",
                "s3://bucket/out/",
                "--cloud-region",
                "us-west-2",
                "--poll-interval",
                "1.5",
                "--timeout",
                "30",
                "https://example.com/v",
            ]
        )

        self.assertEqual(args.backend, "google")
        self.assertEqual(args.language, "en-US")
        self.assertEqual(args.min_speakers, 2)
        self.assertEqual(args.max_speakers, 6)
        self.assertEqual(args.speaker_count, 3)
        self.assertEqual(args.cloud_uri, "s3://bucket/audio.mp3")
        self.assertEqual(args.cloud_output_uri, "s3://bucket/out/")
        self.assertEqual(args.cloud_region, "us-west-2")
        self.assertEqual(args.poll_interval, 1.5)
        self.assertEqual(args.timeout, 30)


if __name__ == "__main__":
    unittest.main()
