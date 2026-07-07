"""Tests for lib.github_auth — seam: get_token() public function."""

from unittest.mock import patch, MagicMock
import subprocess

import pytest

from lib.github_auth import get_token


class TestGetToken:
    """get_token() shells out to `gh auth token` and returns stripped result."""

    @patch("lib.github_auth.subprocess.run")
    def test_get_token_returns_stripped_token(self, mock_run):
        proc = MagicMock()
        proc.returncode = 0
        proc.stdout = "gho_abc123\n"
        mock_run.return_value = proc

        result = get_token()

        assert result == "gho_abc123"
        mock_run.assert_called_once_with(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
        )

    @patch("lib.github_auth.subprocess.run")
    def test_get_token_raises_when_gh_not_installed(self, mock_run):
        mock_run.side_effect = FileNotFoundError("No such file or directory: 'gh'")

        with pytest.raises(RuntimeError, match="gh CLI not installed"):
            get_token()

    @patch("lib.github_auth.subprocess.run")
    def test_get_token_raises_when_not_authenticated(self, mock_run):
        proc = MagicMock()
        proc.returncode = 1
        proc.stderr = "not logged in"
        mock_run.return_value = proc

        with pytest.raises(RuntimeError, match="gh CLI not authenticated"):
            get_token()
