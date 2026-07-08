import re
import unittest
from pathlib import Path


class PackagingMetadataTests(unittest.TestCase):
    def test_pyproject_has_publishable_metadata(self):
        pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

        self.assertRegex(pyproject, r'(?m)^name = "castscribe"$')
        self.assertRegex(pyproject, r'(?m)^license = "MIT"$')
        self.assertIn("[project.urls]", pyproject)
        self.assertRegex(pyproject, r'(?m)^Homepage = "https://github.com/longbai/CastScribe"$')
        self.assertRegex(pyproject, r'(?m)^Repository = "https://github.com/longbai/CastScribe"$')
        self.assertRegex(pyproject, r'(?m)^Issues = "https://github.com/longbai/CastScribe/issues"$')

    def test_pyproject_has_build_and_dev_extras(self):
        pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

        build_extra = self.extract_extra(pyproject, "build")
        dev_extra = self.extract_extra(pyproject, "dev")

        self.assertIn('"build"', build_extra)
        self.assertIn('"twine"', build_extra)
        self.assertIn('"build"', dev_extra)
        self.assertIn('"twine"', dev_extra)

    @staticmethod
    def extract_extra(pyproject: str, name: str) -> str:
        match = re.search(rf"(?ms)^{name} = \[(.*?)\]\n", pyproject)
        if match is None:
            raise AssertionError(f"Missing optional dependency group: {name}")
        return match.group(1)


if __name__ == "__main__":
    unittest.main()
