"""Tests for cwac_mcp.config_builder."""

import json
import os
from unittest.mock import mock_open, patch

import pytest

from cwac_mcp.config_builder import _sanitize_audit_name


class TestSanitizeAuditName:
    """Tests for the _sanitize_audit_name helper."""

    def test_strips_whitespace(self):
        assert _sanitize_audit_name("  hello  ") == "hello"

    def test_replaces_special_chars(self):
        assert _sanitize_audit_name("my scan!@#$%") == "my_scan_"

    def test_collapses_underscores(self):
        assert _sanitize_audit_name("a___b") == "a_b"

    def test_truncates_to_50(self):
        result = _sanitize_audit_name("a" * 100)
        assert len(result) == 50

    def test_preserves_valid_chars(self):
        assert _sanitize_audit_name("my-scan_v1.0") == "my-scan_v1.0"

    def test_empty_after_sanitize_raises_in_build(self):
        # Sanitizing just special chars should produce underscores
        result = _sanitize_audit_name("!@#")
        # The result should be non-empty (underscores remain)
        assert len(result) > 0


class TestBuildConfig:
    """Tests for build_config (integration tests requiring CWAC path)."""

    @pytest.fixture
    def mock_cwac_env(self, tmp_path):
        """Set up a mock CWAC directory structure."""
        cwac_dir = tmp_path / "cwac"
        config_dir = cwac_dir / "config"
        config_dir.mkdir(parents=True)
        base_urls_dir = cwac_dir / "base_urls" / "visit"
        base_urls_dir.mkdir(parents=True)

        # Create a minimal default config
        default_config = {
            "audit_name": "default",
            "audit_plugins": {
                "axe_core_audit": {"enabled": True},
                "language_audit": {"enabled": True},
            },
            "max_links_per_domain": 50,
            "viewport_sizes": {
                "small": {"width": 320, "height": 450},
                "medium": {"width": 1280, "height": 800},
            },
            "base_urls_visit_path": "./base_urls/visit/",
        }
        (config_dir / "config_default.json").write_text(json.dumps(default_config))

        return str(cwac_dir)

    def test_build_config_creates_files(self, mock_cwac_env):
        """Test that build_config creates config and base_urls files."""
        with patch("cwac_mcp.config_builder.CWAC_PATH", mock_cwac_env), \
             patch("cwac_mcp.config_builder._DEFAULT_CONFIG", os.path.join(mock_cwac_env, "config", "config_default.json")), \
             patch("cwac_mcp.config_builder._CONFIG_DIR", os.path.join(mock_cwac_env, "config")), \
             patch("cwac_mcp.config_builder._BASE_URLS_VISIT_DIR", os.path.join(mock_cwac_env, "base_urls", "visit")):
            from cwac_mcp.config_builder import build_config

            config_filename, base_urls_dir = build_config(
                scan_id="test-uuid",
                audit_name="my_scan",
                urls=["https://example.com"],
            )

            assert config_filename == "mcp_test-uuid.json"
            assert os.path.isdir(base_urls_dir)

            # Check config was written
            config_path = os.path.join(mock_cwac_env, "config", config_filename)
            assert os.path.isfile(config_path)

            with open(config_path) as f:
                config = json.load(f)
            assert config["audit_name"] == "my_scan"

    def test_build_config_writes_urls_csv(self, mock_cwac_env):
        """Test that URLs are written to a CSV file."""
        with patch("cwac_mcp.config_builder.CWAC_PATH", mock_cwac_env), \
             patch("cwac_mcp.config_builder._DEFAULT_CONFIG", os.path.join(mock_cwac_env, "config", "config_default.json")), \
             patch("cwac_mcp.config_builder._CONFIG_DIR", os.path.join(mock_cwac_env, "config")), \
             patch("cwac_mcp.config_builder._BASE_URLS_VISIT_DIR", os.path.join(mock_cwac_env, "base_urls", "visit")):
            from cwac_mcp.config_builder import build_config

            _, base_urls_dir = build_config(
                scan_id="test-uuid-2",
                audit_name="csv_test",
                urls=["https://example.com", "https://example.org"],
            )

            csv_path = os.path.join(base_urls_dir, "urls.csv")
            assert os.path.isfile(csv_path)

            with open(csv_path) as f:
                content = f.read()
            assert "https://example.com" in content
            assert "https://example.org" in content

    def test_build_config_empty_urls_raises(self, mock_cwac_env):
        """Test that empty URLs list raises ValueError."""
        with patch("cwac_mcp.config_builder.CWAC_PATH", mock_cwac_env), \
             patch("cwac_mcp.config_builder._DEFAULT_CONFIG", os.path.join(mock_cwac_env, "config", "config_default.json")), \
             patch("cwac_mcp.config_builder._CONFIG_DIR", os.path.join(mock_cwac_env, "config")), \
             patch("cwac_mcp.config_builder._BASE_URLS_VISIT_DIR", os.path.join(mock_cwac_env, "base_urls", "visit")):
            from cwac_mcp.config_builder import build_config

            with pytest.raises(ValueError, match="URL"):
                build_config(
                    scan_id="test-uuid-3",
                    audit_name="empty_test",
                    urls=[],
                )

    def test_build_config_toggles_plugins(self, mock_cwac_env):
        """Test that plugin toggles are applied."""
        with patch("cwac_mcp.config_builder.CWAC_PATH", mock_cwac_env), \
             patch("cwac_mcp.config_builder._DEFAULT_CONFIG", os.path.join(mock_cwac_env, "config", "config_default.json")), \
             patch("cwac_mcp.config_builder._CONFIG_DIR", os.path.join(mock_cwac_env, "config")), \
             patch("cwac_mcp.config_builder._BASE_URLS_VISIT_DIR", os.path.join(mock_cwac_env, "base_urls", "visit")):
            from cwac_mcp.config_builder import build_config

            config_filename, _ = build_config(
                scan_id="test-uuid-4",
                audit_name="plugin_test",
                urls=["https://example.com"],
                plugins={"language_audit": False},
            )

            config_path = os.path.join(mock_cwac_env, "config", config_filename)
            with open(config_path) as f:
                config = json.load(f)
            assert config["audit_plugins"]["language_audit"]["enabled"] is False
            assert config["audit_plugins"]["axe_core_audit"]["enabled"] is True
