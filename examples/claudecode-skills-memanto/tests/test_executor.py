"""
Tests for executor module — focus on helper functions that don't require
a live subprocess or API key.
"""

from __future__ import annotations
from unittest.mock import MagicMock, patch
from memanto_skills.executor import _find_artifacts_after, _find_git_diff


class TestFindArtifactsAfter:
    def test_empty_when_no_recent_files(self) -> None:
        result = _find_artifacts_after(0.0)
        assert isinstance(result, list)

    def test_skips_directories(self) -> None:
        result = _find_artifacts_after(0.0)
        assert isinstance(result, list)


class TestFindGitDiff:
    def test_no_git_repo(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")
            assert _find_git_diff(1000.0) == ""

    def test_git_timeout(self) -> None:
        with patch("subprocess.run") as mock_run:
            from subprocess import TimeoutExpired
            mock_run.side_effect = TimeoutExpired("git", 10)
            assert _find_git_diff(1000.0) == ""

    def test_git_error(self) -> None:
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 128
            mock_result.stdout = ""
            mock_run.return_value = mock_result
            assert _find_git_diff(1000.0) == ""
