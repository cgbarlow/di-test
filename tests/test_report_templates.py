"""Tests for report template rendering."""

import os

import pytest


class TestTemplateFiles:
    """Tests that template files exist and are valid Jinja2."""

    TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

    def test_cwac_scan_template_exists(self):
        path = os.path.join(self.TEMPLATE_DIR, "cwac_scan_report.md.j2")
        assert os.path.isfile(path), f"Template not found: {path}"

    def test_cwac_summary_template_exists(self):
        path = os.path.join(self.TEMPLATE_DIR, "cwac_summary_report.md.j2")
        assert os.path.isfile(path), f"Template not found: {path}"

    def test_visual_scan_template_exists(self):
        path = os.path.join(self.TEMPLATE_DIR, "visual_scan_report.md.j2")
        assert os.path.isfile(path), f"Template not found: {path}"

    def test_templates_are_valid_jinja2(self):
        from jinja2 import Environment, FileSystemLoader

        env = Environment(loader=FileSystemLoader(self.TEMPLATE_DIR))
        for name in ["cwac_scan_report.md.j2", "cwac_summary_report.md.j2", "visual_scan_report.md.j2"]:
            template = env.get_template(name)
            assert template is not None


class TestCwacScanTemplate:
    """Tests for the CWAC scan report template rendering."""

    def test_renders_with_full_context(self, sample_report_context):
        from cwac_mcp.report_generator import generate_markdown_report

        md = generate_markdown_report("cwac_scan_report", sample_report_context)
        assert isinstance(md, str)
        assert len(md) > 100

    def test_contains_summary_section(self, sample_report_context):
        from cwac_mcp.report_generator import generate_markdown_report

        md = generate_markdown_report("cwac_scan_report", sample_report_context)
        assert "summary" in md.lower() or "overview" in md.lower()

    def test_contains_findings_section(self, sample_report_context):
        from cwac_mcp.report_generator import generate_markdown_report

        md = generate_markdown_report("cwac_scan_report", sample_report_context)
        assert "image-alt" in md or "finding" in md.lower()


class TestVisualScanTemplate:
    """Tests for the visual scan report template rendering."""

    def test_renders_heading_findings(self, sample_visual_findings):
        from cwac_mcp.report_generator import generate_markdown_report

        context = {
            "url": "https://example.com/team/",
            "scan_date": "2026-02-24",
            "findings": sample_visual_findings,
            "total_findings": len(sample_visual_findings),
            "generated_at": "2026-02-24T10:00:00",
        }
        md = generate_markdown_report("visual_scan_report", context)
        assert "Heading-like content" in md
        assert "p.h3" in md or "Jane Smith" in md

    def test_renders_empty_findings(self):
        from cwac_mcp.report_generator import generate_markdown_report

        context = {
            "url": "https://example.com/",
            "scan_date": "2026-02-24",
            "findings": [],
            "total_findings": 0,
            "generated_at": "2026-02-24T10:00:00",
        }
        md = generate_markdown_report("visual_scan_report", context)
        assert isinstance(md, str)
