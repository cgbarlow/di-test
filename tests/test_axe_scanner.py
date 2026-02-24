"""Tests for cwac_mcp.axe_scanner pure functions."""

import csv
import json
import os

import pytest

from cwac_mcp.axe_scanner import flatten_violations, write_csv, extract_links


class TestFlattenViolations:
    """Tests for flattening axe-core violations to CSV rows."""

    def test_single_violation_single_node(self):
        """One violation with one node produces one row."""
        violations = [
            {
                "id": "image-alt",
                "impact": "critical",
                "description": "Ensures images have alternative text",
                "help": "Images must have alternative text",
                "helpUrl": "https://dequeuniversity.com/rules/axe/4.4/image-alt",
                "tags": ["wcag2a", "wcag111", "cat.text-alternatives"],
                "nodes": [
                    {
                        "html": '<img src="hero.jpg">',
                        "target": ["img.hero"],
                    }
                ],
            }
        ]

        rows = flatten_violations(
            violations=violations,
            page_url="https://example.com/",
            page_title="Test Page",
            base_url="https://example.com",
            viewport_name="medium",
            viewport_size={"width": 1280, "height": 800},
            page_index=1,
        )

        assert len(rows) == 1
        row = rows[0]
        assert row["id"] == "image-alt"
        assert row["impact"] == "critical"
        assert row["url"] == "https://example.com/"
        assert row["audit_type"] == "AxeCoreAudit"
        assert row["target"] == "img.hero"
        assert row["html"] == '<img src="hero.jpg">'
        assert row["page_title"] == "Test Page"
        assert row["base_url"] == "https://example.com"
        assert row["organisation"] == "MCP Scan"
        assert row["sector"] == "MCP"

    def test_multiple_nodes(self):
        """One violation with multiple nodes produces multiple rows."""
        violations = [
            {
                "id": "list",
                "impact": "serious",
                "description": "Ensures lists are structured correctly",
                "help": "Lists must be structured correctly",
                "helpUrl": "https://dequeuniversity.com/rules/axe/4.4/list",
                "tags": ["wcag2a", "wcag131"],
                "nodes": [
                    {"html": "<ul><div>a</div></ul>", "target": ["ul.nav"]},
                    {"html": "<ul><div>b</div></ul>", "target": ["ul.footer"]},
                ],
            }
        ]

        rows = flatten_violations(
            violations=violations,
            page_url="https://example.com/",
            page_title="Test",
            base_url="https://example.com",
            viewport_name="medium",
            viewport_size={"width": 1280, "height": 800},
            page_index=1,
        )

        assert len(rows) == 2
        assert rows[0]["target"] == "ul.nav"
        assert rows[1]["target"] == "ul.footer"

    def test_empty_violations(self):
        """Empty violations list produces no rows."""
        rows = flatten_violations(
            violations=[],
            page_url="https://example.com/",
            page_title="Test",
            base_url="https://example.com",
            viewport_name="medium",
            viewport_size={"width": 1280, "height": 800},
            page_index=1,
        )
        assert rows == []

    def test_best_practice_tag_detection(self):
        """Correctly detects best-practice tag."""
        violations = [
            {
                "id": "region",
                "impact": "moderate",
                "description": "Content outside landmarks",
                "help": "All content should be in landmarks",
                "helpUrl": "https://example.com",
                "tags": ["best-practice", "cat.semantics"],
                "nodes": [{"html": "<div>content</div>", "target": ["div"]}],
            }
        ]

        rows = flatten_violations(
            violations=violations,
            page_url="https://example.com/",
            page_title="Test",
            base_url="https://example.com",
            viewport_name="medium",
            viewport_size={"width": 1280, "height": 800},
            page_index=1,
        )

        assert rows[0]["best-practice"] == "Yes"

    def test_non_best_practice(self):
        """Non best-practice violation marked as No."""
        violations = [
            {
                "id": "image-alt",
                "impact": "critical",
                "description": "Test",
                "help": "Test",
                "helpUrl": "https://example.com",
                "tags": ["wcag2a", "wcag111"],
                "nodes": [{"html": "<img>", "target": ["img"]}],
            }
        ]

        rows = flatten_violations(
            violations=violations,
            page_url="https://example.com/",
            page_title="Test",
            base_url="https://example.com",
            viewport_name="medium",
            viewport_size={"width": 1280, "height": 800},
            page_index=1,
        )

        assert rows[0]["best-practice"] == "No"

    def test_multiple_targets_joined(self):
        """Multiple target selectors are joined with comma."""
        violations = [
            {
                "id": "test",
                "impact": "minor",
                "description": "Test",
                "help": "Test",
                "helpUrl": "https://example.com",
                "tags": [],
                "nodes": [{"html": "<div>", "target": ["div.a", "div.b"]}],
            }
        ]

        rows = flatten_violations(
            violations=violations,
            page_url="https://example.com/",
            page_title="Test",
            base_url="https://example.com",
            viewport_name="medium",
            viewport_size={"width": 1280, "height": 800},
            page_index=1,
        )

        assert rows[0]["target"] == "div.a,div.b"

    def test_viewport_size_in_row(self):
        """Viewport size is stored as string representation."""
        violations = [
            {
                "id": "test",
                "impact": "minor",
                "description": "Test",
                "help": "Test",
                "helpUrl": "https://example.com",
                "tags": [],
                "nodes": [{"html": "<div>", "target": ["div"]}],
            }
        ]

        rows = flatten_violations(
            violations=violations,
            page_url="https://example.com/",
            page_title="Test",
            base_url="https://example.com",
            viewport_name="small",
            viewport_size={"width": 320, "height": 480},
            page_index=1,
        )

        assert "320" in rows[0]["viewport_size"]
        assert "480" in rows[0]["viewport_size"]


class TestWriteCsv:
    """Tests for writing CSV output."""

    def test_writes_correct_headers(self, tmp_path):
        """CSV file has the correct 20 column headers."""
        output_path = str(tmp_path / "axe_core_audit.csv")
        rows = [
            {
                "organisation": "MCP Scan",
                "sector": "MCP",
                "page_title": "Test",
                "base_url": "https://example.com",
                "url": "https://example.com/",
                "viewport_size": "{'width': 1280, 'height': 800}",
                "audit_id": "1_medium",
                "page_id": "1",
                "audit_type": "AxeCoreAudit",
                "issue_id": "1",
                "description": "Test description",
                "target": "img",
                "num_issues": "1",
                "help": "Test help",
                "helpUrl": "https://example.com",
                "id": "image-alt",
                "impact": "critical",
                "html": "<img>",
                "tags": "wcag2a",
                "best-practice": "No",
            }
        ]

        write_csv(rows, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)

        expected = [
            "organisation", "sector", "page_title", "base_url", "url",
            "viewport_size", "audit_id", "page_id", "audit_type", "issue_id",
            "description", "target", "num_issues", "help", "helpUrl",
            "id", "impact", "html", "tags", "best-practice",
        ]
        assert headers == expected

    def test_writes_rows(self, tmp_path):
        """CSV file contains the correct data rows."""
        output_path = str(tmp_path / "axe_core_audit.csv")
        rows = [
            {
                "organisation": "MCP Scan",
                "sector": "MCP",
                "page_title": "Test",
                "base_url": "https://example.com",
                "url": "https://example.com/",
                "viewport_size": "{'width': 1280, 'height': 800}",
                "audit_id": "1_medium",
                "page_id": "1",
                "audit_type": "AxeCoreAudit",
                "issue_id": "1",
                "description": "Images must have alt text",
                "target": "img.hero",
                "num_issues": "1",
                "help": "Images must have alternative text",
                "helpUrl": "https://example.com/rule",
                "id": "image-alt",
                "impact": "critical",
                "html": "<img src='hero.jpg'>",
                "tags": "wcag2a,wcag111",
                "best-practice": "No",
            }
        ]

        write_csv(rows, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            read_rows = list(reader)

        assert len(read_rows) == 1
        assert read_rows[0]["id"] == "image-alt"
        assert read_rows[0]["impact"] == "critical"

    def test_empty_rows(self, tmp_path):
        """Empty rows list writes only headers."""
        output_path = str(tmp_path / "axe_core_audit.csv")
        write_csv([], output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            remaining = list(reader)

        assert len(headers) == 20
        assert len(remaining) == 0


class TestExtractLinks:
    """Tests for link extraction and filtering."""

    def test_same_domain_links(self):
        """Returns only same-domain links."""
        links = extract_links(
            html='<a href="/about">About</a><a href="https://other.com">Other</a>',
            page_url="https://example.com/",
        )
        assert "https://example.com/about" in links
        assert "https://other.com" not in links

    def test_strips_fragments(self):
        """Strips URL fragments."""
        links = extract_links(
            html='<a href="/page#section">Link</a>',
            page_url="https://example.com/",
        )
        assert links == ["https://example.com/page"]

    def test_deduplicates(self):
        """Removes duplicate URLs."""
        links = extract_links(
            html='<a href="/page">Link 1</a><a href="/page">Link 2</a>',
            page_url="https://example.com/",
        )
        assert links.count("https://example.com/page") == 1

    def test_empty_html(self):
        """Returns empty list for HTML with no links."""
        links = extract_links(html="<p>No links here</p>", page_url="https://example.com/")
        assert links == []

    def test_skips_non_http_links(self):
        """Skips mailto, javascript, and tel links."""
        links = extract_links(
            html='<a href="mailto:a@b.com">Email</a><a href="javascript:void(0)">JS</a><a href="tel:123">Tel</a>',
            page_url="https://example.com/",
        )
        assert links == []
