"""Configuration must use the project-root .env, independent of the cwd."""

import unittest
from pathlib import Path
from unittest.mock import patch

from config.settings import Settings


class SettingsTests(unittest.TestCase):
    def test_loads_only_project_root_dotenv(self):
        with patch("config.settings.load_dotenv") as load:
            Settings.from_env()
        load.assert_called_once_with(
            Path(__file__).resolve().parents[1] / ".env", override=False,
        )
