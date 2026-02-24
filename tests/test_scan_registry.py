"""Tests for cwac_mcp.scan_registry."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from cwac_mcp.scan_registry import ScanRecord, ScanRegistry


class TestScanRegistry:
    """Tests for the ScanRegistry class."""

    def test_register_and_get(self):
        registry = ScanRegistry()
        record = ScanRecord(
            process=None,
            config_path="test.json",
            base_urls_dir="/tmp/test",
            results_dir=None,
            status="running",
            start_time=datetime.now(),
            end_time=None,
            audit_name="test",
        )
        registry.register("test-id", record)
        assert registry.get("test-id") is record

    def test_get_nonexistent_returns_none(self):
        registry = ScanRegistry()
        assert registry.get("nonexistent") is None

    def test_list_all(self):
        registry = ScanRegistry()
        record = ScanRecord(
            process=None,
            config_path="test.json",
            base_urls_dir="/tmp/test",
            results_dir=None,
            status="running",
            start_time=datetime.now(),
            end_time=None,
            audit_name="test",
        )
        registry.register("id-1", record)
        all_scans = registry.list_all()
        assert "id-1" in all_scans

    def test_create_returns_uuid(self):
        registry = ScanRegistry()
        mock_process = MagicMock()
        scan_id = registry.create(mock_process, "config.json", "/tmp/urls", "test_audit")
        assert len(scan_id) == 36  # UUID4 format

    def test_update_status_complete(self):
        registry = ScanRegistry()
        mock_process = MagicMock()
        mock_process.poll.return_value = 0
        mock_process.stdout = None
        mock_process.stderr = None

        record = ScanRecord(
            process=mock_process,
            config_path="test.json",
            base_urls_dir="/tmp/test",
            results_dir=None,
            status="running",
            start_time=datetime.now(),
            end_time=None,
            audit_name="test",
        )
        registry.register("test-id", record)

        with patch.object(ScanRegistry, "_discover_results_dir", return_value="/results/test"):
            registry.update_status("test-id")

        assert record.status == "complete"
        assert record.end_time is not None

    def test_update_status_failed(self):
        registry = ScanRegistry()
        mock_process = MagicMock()
        mock_process.poll.return_value = 1
        mock_process.stdout = None
        mock_process.stderr = None

        record = ScanRecord(
            process=mock_process,
            config_path="test.json",
            base_urls_dir="/tmp/test",
            results_dir=None,
            status="running",
            start_time=datetime.now(),
            end_time=None,
            audit_name="test",
        )
        registry.register("test-id", record)

        with patch.object(ScanRegistry, "_discover_results_dir", return_value=None):
            registry.update_status("test-id")

        assert record.status == "failed"

    def test_update_status_still_running(self):
        registry = ScanRegistry()
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.stdout = iter([])
        mock_process.stderr = iter([])

        record = ScanRecord(
            process=mock_process,
            config_path="test.json",
            base_urls_dir="/tmp/test",
            results_dir=None,
            status="running",
            start_time=datetime.now(),
            end_time=None,
            audit_name="test",
        )
        registry.register("test-id", record)
        registry.update_status("test-id")
        assert record.status == "running"

    def test_update_status_nonexistent_is_noop(self):
        registry = ScanRegistry()
        registry.update_status("nonexistent")  # Should not raise


class TestScanRecord:
    """Tests for the ScanRecord dataclass."""

    def test_default_stdout_stderr(self):
        record = ScanRecord(
            process=None,
            config_path="test.json",
            base_urls_dir="/tmp/test",
            results_dir=None,
            status="running",
            start_time=datetime.now(),
            end_time=None,
            audit_name="test",
        )
        assert record.stdout_lines == []
        assert record.stderr_lines == []


class TestDiscoverResultsDir:
    """Tests for _discover_results_dir with dual results root."""

    def test_finds_in_cwac_results(self, tmp_path):
        """Discovers results in the CWAC results directory."""
        results_dir = tmp_path / "cwac" / "results" / "2026-02-24_10-00-00_my_scan"
        results_dir.mkdir(parents=True)

        registry = ScanRegistry()
        with patch("cwac_mcp.scan_registry.CWAC_PATH", str(tmp_path / "cwac")), \
             patch("cwac_mcp.scan_registry.PROJECT_ROOT", str(tmp_path / "project")):
            found = registry._discover_results_dir("my_scan")
        assert found is not None
        assert "my_scan" in found

    def test_finds_in_project_output(self, tmp_path):
        """Discovers results in the project output directory."""
        output_dir = tmp_path / "project" / "output" / "20260224_100000_my_scan"
        output_dir.mkdir(parents=True)

        registry = ScanRegistry()
        with patch("cwac_mcp.scan_registry.CWAC_PATH", str(tmp_path / "cwac")), \
             patch("cwac_mcp.scan_registry.PROJECT_ROOT", str(tmp_path / "project")):
            found = registry._discover_results_dir("my_scan")
        assert found is not None
        assert "my_scan" in found

    def test_prefers_most_recent(self, tmp_path):
        """Returns the most recently created matching directory."""
        import time

        cwac_results = tmp_path / "cwac" / "results"
        cwac_results.mkdir(parents=True)
        old = cwac_results / "2026-02-24_08-00-00_my_scan"
        old.mkdir()

        time.sleep(0.05)

        output_dir = tmp_path / "project" / "output"
        output_dir.mkdir(parents=True)
        new = output_dir / "20260224_100000_my_scan"
        new.mkdir()

        registry = ScanRegistry()
        with patch("cwac_mcp.scan_registry.CWAC_PATH", str(tmp_path / "cwac")), \
             patch("cwac_mcp.scan_registry.PROJECT_ROOT", str(tmp_path / "project")):
            found = registry._discover_results_dir("my_scan")
        assert found is not None
        assert "20260224_100000_my_scan" in found
