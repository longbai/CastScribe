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


if __name__ == "__main__":
    unittest.main()
