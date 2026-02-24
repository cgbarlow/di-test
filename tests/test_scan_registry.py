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
