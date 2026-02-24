"""Tests for cwac_mcp.environment_check."""

import os
from unittest.mock import patch, MagicMock

import pytest

from cwac_mcp.environment_check import check_environment, _check_chromedriver, _check_importable


class TestCheckImportable:
    """Tests for the _check_importable helper."""

    def test_importable_module(self):
        assert _check_importable("os") is True

    def test_non_importable_module(self):
        assert _check_importable("nonexistent_module_xyz") is False


class TestCheckChromedriver:
    """Tests for chromedriver architecture detection."""

    def test_returns_false_when_cwac_path_none(self):
        assert _check_chromedriver(None) is False

    def test_returns_false_when_dir_missing(self, tmp_path):
        assert _check_chromedriver(str(tmp_path / "nonexistent")) is False

    def test_returns_false_when_no_chromedriver(self, tmp_path):
        """CWAC dir exists but no chromedriver binary."""
        assert _check_chromedriver(str(tmp_path)) is False


class TestCheckEnvironment:
    """Tests for the main check_environment function."""

    def test_cwac_mode_when_all_deps_available(self):
        """Returns cwac mode when CWAC + chromedriver + selenium are available."""
        with patch("cwac_mcp.environment_check._discover_cwac_path", return_value="/fake/cwac"), \
             patch("cwac_mcp.environment_check.os.path.isfile", return_value=True), \
             patch("cwac_mcp.environment_check._check_chromedriver", return_value=True), \
             patch("cwac_mcp.environment_check._check_importable", side_effect=lambda mod: True), \
             patch("cwac_mcp.environment_check._check_axe_core", return_value=True):
            result = check_environment()
            assert result["mode"] == "cwac"
            assert result["cwac_available"] is True
            assert result["chromedriver_ok"] is True

    def test_axe_only_mode_when_cwac_unavailable(self):
        """Returns axe-only mode when CWAC is unavailable but Playwright + axe-core are."""
        def mock_importable(mod):
            if mod == "selenium":
                return False
            if mod == "playwright":
                return True
            return True

        with patch("cwac_mcp.environment_check._discover_cwac_path", return_value=None), \
             patch("cwac_mcp.environment_check._check_chromedriver", return_value=False), \
             patch("cwac_mcp.environment_check._check_importable", side_effect=mock_importable), \
             patch("cwac_mcp.environment_check._check_axe_core", return_value=True):
            result = check_environment()
            assert result["mode"] == "axe-only"
            assert result["cwac_available"] is False
            assert result["playwright_available"] is True
            assert result["axe_core_available"] is True

    def test_axe_only_when_chromedriver_wrong_arch(self):
        """Returns axe-only mode when chromedriver exists but wrong architecture."""
        def mock_importable(mod):
            if mod == "selenium":
                return True
            if mod == "playwright":
                return True
            return True

        with patch("cwac_mcp.environment_check._discover_cwac_path", return_value="/fake/cwac"), \
             patch("cwac_mcp.environment_check._check_chromedriver", return_value=False), \
             patch("cwac_mcp.environment_check._check_importable", side_effect=mock_importable), \
             patch("cwac_mcp.environment_check._check_axe_core", return_value=True):
            result = check_environment()
            assert result["mode"] == "axe-only"
            assert result["chromedriver_ok"] is False

    def test_message_present(self):
        """Result always includes a human-readable message."""
        with patch("cwac_mcp.environment_check._discover_cwac_path", return_value=None), \
             patch("cwac_mcp.environment_check._check_chromedriver", return_value=False), \
             patch("cwac_mcp.environment_check._check_importable", return_value=True), \
             patch("cwac_mcp.environment_check._check_axe_core", return_value=True):
            result = check_environment()
            assert "message" in result
            assert isinstance(result["message"], str)
            assert len(result["message"]) > 0

    def test_returns_cwac_path_when_available(self):
        """Result includes cwac_path when CWAC is found."""
        with patch("cwac_mcp.environment_check._discover_cwac_path", return_value="/fake/cwac"), \
             patch("cwac_mcp.environment_check.os.path.isfile", return_value=True), \
             patch("cwac_mcp.environment_check._check_chromedriver", return_value=True), \
             patch("cwac_mcp.environment_check._check_importable", return_value=True), \
             patch("cwac_mcp.environment_check._check_axe_core", return_value=True):
            result = check_environment()
            assert result["cwac_path"] == "/fake/cwac"

    def test_no_mode_available_returns_error(self):
        """Returns error mode when neither CWAC nor Playwright is available."""
        with patch("cwac_mcp.environment_check._discover_cwac_path", return_value=None), \
             patch("cwac_mcp.environment_check._check_chromedriver", return_value=False), \
             patch("cwac_mcp.environment_check._check_importable", return_value=False), \
             patch("cwac_mcp.environment_check._check_axe_core", return_value=False):
            result = check_environment()
            assert result["mode"] == "unavailable"
            assert "message" in result
