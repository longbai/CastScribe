import unittest
from pathlib import Path


class PrivacyIgnoreTests(unittest.TestCase):
    def test_gitignore_blocks_cloud_credential_files(self):
        gitignore = Path(".gitignore").read_text(encoding="utf-8")

        for pattern in [
            ".env",
            "*token*",
            "*secret*",
            "*.pem",
            "*.key",
            "*service-account*.json",
            "*credentials*.json",
            "azure*.json",
            "gcloud*.json",
        ]:
            self.assertIn(pattern, gitignore)


if __name__ == "__main__":
    unittest.main()
