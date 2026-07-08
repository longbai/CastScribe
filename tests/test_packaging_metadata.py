import tomllib
import unittest
from pathlib import Path


class PackagingMetadataTests(unittest.TestCase):
    def test_pyproject_has_publishable_metadata(self):
        metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
        project = metadata["project"]

        self.assertEqual(project["name"], "castscribe")
        self.assertIn("license", project)
        self.assertIn("urls", project)
        self.assertIn("Homepage", project["urls"])
        self.assertIn("Repository", project["urls"])
        self.assertIn("Issues", project["urls"])

    def test_pyproject_has_build_and_dev_extras(self):
        metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
        extras = metadata["project"]["optional-dependencies"]

        self.assertIn("build", extras)
        self.assertIn("dev", extras)
        self.assertIn("build", extras["build"])
        self.assertIn("twine", extras["build"])


if __name__ == "__main__":
    unittest.main()
