"""Shared pytest fixtures for di-test."""

import json
import os
import tempfile
import shutil
from datetime import datetime

import pytest


@pytest.fixture
def sample_axe_results():
    """Sample axe-core result rows as list of dicts."""
    return [
        {
            "organisation": "Test Org",
            "sector": "Government",
            "page_title": "Test Page",
            "base_url": "https://example.govt.nz",
            "url": "https://example.govt.nz/",
            "viewport_size": "{'width': 1280, 'height': 800}",
            "audit_id": "1_medium",
            "page_id": "1",
            "audit_type": "AxeCoreAudit",
            "issue_id": "1",
            "description": "Ensures images have alternative text",
            "target": "img.hero",
            "num_issues": "1",
            "help": "Images must have alternative text",
            "helpUrl": "https://dequeuniversity.com/rules/axe/4.4/image-alt",
            "id": "image-alt",
            "impact": "critical",
            "html": '<img src="hero.jpg" class="hero">',
            "tags": "wcag2a,wcag111",
            "best-practice": "No",
        },
        {
            "organisation": "Test Org",
            "sector": "Government",
            "page_title": "Test Page",
            "base_url": "https://example.govt.nz",
            "url": "https://example.govt.nz/about",
            "viewport_size": "{'width': 1280, 'height': 800}",
            "audit_id": "2_medium",
            "page_id": "2",
            "audit_type": "AxeCoreAudit",
            "issue_id": "2",
            "description": "Ensures lists are structured correctly",
            "target": "ul.nav",
            "num_issues": "1",
            "help": "Lists must be structured correctly",
            "helpUrl": "https://dequeuniversity.com/rules/axe/4.4/list",
            "id": "list",
            "impact": "serious",
            "html": "<ul class='nav'><div>item</div></ul>",
            "tags": "wcag2a,wcag131",
            "best-practice": "No",
        },
    ]


@pytest.fixture
def sample_language_results():
    """Sample language audit result rows."""
    return [
        {
            "organisation": "Test Org",
            "sector": "Government",
            "page_title": "Test Page",
            "base_url": "https://example.govt.nz",
            "url": "https://example.govt.nz/",
            "viewport_size": "{'width': 1280, 'height': 800}",
            "audit_id": "1_medium",
            "page_id": "1",
            "flesch_kincaid_gl": "9.5",
            "num_sentences": "25",
            "words_per_sentence": "15.2",
            "syllables_per_word": "1.6",
            "smog_gl": "11.3",
            "helpUrl": "https://www.digital.govt.nz/standards-and-guidance/design-and-ux/content-design-guidance/writing-style/plain-language/",
        },
    ]


@pytest.fixture
def sample_scan_summary():
    """Sample summary dict as returned by get_summary()."""
    return {
        "total_issues": 27,
        "by_audit_type": {
            "axe_core_audit": 27,
            "language_audit": 50,
            "reflow_audit": 0,
        },
        "axe_impact_breakdown": {
            "critical": 3,
            "serious": 24,
        },
        "top_violations": [
            {"id": "list", "count": 24},
            {"id": "image-alt", "count": 3},
        ],
    }


@pytest.fixture
def sample_visual_findings():
    """Sample visual pattern scanner findings."""
    return [
        {
            "url": "https://example.com/team/",
            "type": "Heading-like content",
            "reason": "Text is visually styled as a heading but not marked up as one",
            "location": {
                "cssSelector": "p.h3",
                "xpath": "//p[@class='h3']",
            },
            "visual": {
                "fontSize": "28px",
                "fontWeight": "700",
            },
            "screenshot": "screenshots/team-item1.png",
            "htmlSnippet": '<p class="h3">Jane Smith</p>',
            "confidence": 0.92,
        },
    ]


@pytest.fixture
def tmp_results_dir(tmp_path):
    """Create a temporary results directory with sample CSV files."""
    results_dir = tmp_path / "2026-02-24_10-00-00_test_scan"
    results_dir.mkdir()

    # axe_core_audit.csv
    axe_csv = results_dir / "axe_core_audit.csv"
    axe_csv.write_text(
        "organisation,sector,page_title,base_url,url,viewport_size,audit_id,page_id,audit_type,issue_id,description,target,num_issues,help,helpUrl,id,impact,html,tags,best-practice\n"
        'Test Org,Government,Test Page,https://example.govt.nz,https://example.govt.nz/,"{\'width\': 1280, \'height\': 800}",1_medium,1,AxeCoreAudit,1,Images must have alt text,img.hero,1,Images must have alternative text,https://dequeuniversity.com/rules/axe/4.4/image-alt,image-alt,critical,"<img src=""hero.jpg"">","wcag2a,wcag111",No\n',
        encoding="utf-8",
    )

    # language_audit.csv
    lang_csv = results_dir / "language_audit.csv"
    lang_csv.write_text(
        "organisation,sector,page_title,base_url,url,viewport_size,audit_id,page_id,flesch_kincaid_gl,num_sentences,words_per_sentence,syllables_per_word,smog_gl,helpUrl\n"
        "Test Org,Government,Test Page,https://example.govt.nz,https://example.govt.nz/,\"{'width': 1280, 'height': 800}\",1_medium,1,9.5,25,15.2,1.6,11.3,https://example.com\n",
        encoding="utf-8",
    )

    # pages_scanned.csv
    pages_csv = results_dir / "pages_scanned.csv"
    pages_csv.write_text(
        "organisation,base_url,number_of_pages,sector\n"
        "Test Org,https://example.govt.nz,5,Government\n",
        encoding="utf-8",
    )

    return str(results_dir)


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create a temporary output directory for report files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return str(output_dir)


@pytest.fixture
def sample_report_context(sample_axe_results, sample_scan_summary):
    """Complete template context for a CWAC scan report."""
    return {
        "audit_name": "test_scan",
        "scan_date": "2026-02-24T10:00:00",
        "base_url": "https://example.govt.nz",
        "pages_scanned": 5,
        "total_issues": 27,
        "summary": sample_scan_summary,
        "results": sample_axe_results,
        "generated_at": datetime.now().isoformat(),
    }
