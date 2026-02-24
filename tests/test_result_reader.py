"""Tests for cwac_mcp.result_reader."""

import os

import pytest

from cwac_mcp.result_reader import (
    _count_by_field,
    _read_csv_file,
    _top_n_by_field,
    get_summary,
    read_results,
)


class TestReadResults:
    """Tests for read_results()."""

    def test_reads_all_csvs(self, tmp_results_dir):
        results = read_results(tmp_results_dir)
        assert len(results) > 0

    def test_filters_by_audit_type(self, tmp_results_dir):
        results = read_results(tmp_results_dir, audit_type="axe_core_audit")
        assert len(results) > 0
        # All results should be from axe_core_audit
        for r in results:
            assert "impact" in r or "audit_type" in r

    def test_filters_by_impact(self, tmp_results_dir):
        results = read_results(tmp_results_dir, audit_type="axe_core_audit", impact="critical")
        for r in results:
            assert r.get("impact", "").lower() == "critical"

    def test_limits_results(self, tmp_results_dir):
        results = read_results(tmp_results_dir, limit=1)
        assert len(results) <= 1

    def test_nonexistent_dir_returns_empty(self):
        results = read_results("/nonexistent/path")
        assert results == []

    def test_nonexistent_audit_type_returns_empty(self, tmp_results_dir):
        results = read_results(tmp_results_dir, audit_type="nonexistent_audit")
        assert results == []


class TestGetSummary:
    """Tests for get_summary()."""

    def test_returns_summary_dict(self, tmp_results_dir):
        summary = get_summary(tmp_results_dir)
        assert "total_issues" in summary
        assert "by_audit_type" in summary

    def test_counts_by_audit_type(self, tmp_results_dir):
        summary = get_summary(tmp_results_dir)
        assert "axe_core_audit" in summary["by_audit_type"]

    def test_nonexistent_dir_returns_zeros(self):
        summary = get_summary("/nonexistent/path")
        assert summary["total_issues"] == 0


class TestHelpers:
    """Tests for internal helper functions."""

    def test_count_by_field(self):
        rows = [
            {"impact": "critical"},
            {"impact": "serious"},
            {"impact": "critical"},
        ]
        counts = _count_by_field(rows, "impact")
        assert counts["critical"] == 2
        assert counts["serious"] == 1

    def test_top_n_by_field(self):
        rows = [
            {"id": "a"},
            {"id": "b"},
            {"id": "a"},
            {"id": "a"},
            {"id": "b"},
        ]
        top = _top_n_by_field(rows, "id", n=2)
        assert top[0]["id"] == "a"
        assert top[0]["count"] == 3

    def test_read_csv_file_nonexistent(self):
        result = _read_csv_file("/nonexistent/file.csv")
        assert result == []
