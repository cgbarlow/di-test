# SPEC-005-A: Template Definitions

| Field           | Value                                        |
|-----------------|----------------------------------------------|
| **Parent ADR**  | ADR-005 (Report Template System)             |
| **Version**     | A (initial)                                  |
| **Status**      | Accepted                                     |
| **Date**        | 2026-02-24                                   |

## Overview

This specification defines the report template system used to generate Markdown and DOCX reports from CWAC scan data and visual scan findings. It covers the Jinja2 template engine configuration, the data model passed to each template, the structure of each `.md.j2` template file, the python-docx rendering pipeline for DOCX generation, the output file naming convention, and the auto-report hook that triggers report generation after scan completion.

---

## 1. Template Engine

### Jinja2 Configuration

The template engine is configured as a module-level singleton, initialised once at server startup:

```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

template_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(disabled_extensions=("md.j2",)),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)
```

### Configuration Parameters

| Parameter              | Value                        | Rationale                                                          |
|------------------------|------------------------------|--------------------------------------------------------------------|
| `loader`               | `FileSystemLoader("templates")` | Loads templates from the `templates/` directory relative to the server package root |
| `autoescape`           | Disabled for `.md.j2` files  | Markdown templates must not HTML-escape their output               |
| `trim_blocks`          | `True`                       | Removes the first newline after a block tag, preventing blank lines in output |
| `lstrip_blocks`        | `True`                       | Strips leading whitespace from block tags, enabling indented template logic without affecting output |
| `keep_trailing_newline`| `True`                       | Preserves the trailing newline at the end of the rendered file (standard for text files) |

### Template Loading

Templates are loaded by name using the `get_template` method:

```python
def render_markdown_report(template_type: str, data: dict) -> str:
    """Render a Markdown report from structured data.

    Args:
        template_type: One of 'cwac_scan_report', 'cwac_summary_report', 'visual_scan_report'.
        data: Template context dictionary (see Section 2).

    Returns:
        Rendered Markdown string.
    """
    template = template_env.get_template(f"{template_type}.md.j2")
    return template.render(**data)
```

### Custom Filters

The following custom Jinja2 filters are registered for use in templates:

| Filter          | Signature                      | Description                                                    |
|-----------------|--------------------------------|----------------------------------------------------------------|
| `severity_icon` | `value: str -> str`            | Maps impact levels to text indicators: `critical` -> `[CRITICAL]`, `serious` -> `[SERIOUS]`, `moderate` -> `[MODERATE]`, `minor` -> `[MINOR]` |
| `truncate_html` | `value: str, length: int -> str` | Truncates HTML snippets to a maximum character length, appending `...` if truncated |
| `format_duration` | `seconds: float -> str`      | Converts seconds to human-readable duration (e.g., `125.4` -> `2m 5s`) |
| `format_timestamp` | `dt: datetime -> str`       | Formats a datetime as `YYYY-MM-DD HH:MM:SS`                   |
| `pluralise`     | `count: int, singular: str, plural: str -> str` | Returns singular or plural form based on count |

Registration:

```python
template_env.filters["severity_icon"] = lambda v: f"[{v.upper()}]" if v else "[UNKNOWN]"
template_env.filters["truncate_html"] = lambda v, n=120: v[:n] + "..." if len(v) > n else v
template_env.filters["format_duration"] = format_duration
template_env.filters["format_timestamp"] = lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S")
template_env.filters["pluralise"] = lambda c, s, p: s if c == 1 else p
```

### Template Directory Structure

```
cwac-mcp-server/
  templates/
    cwac_scan_report.md.j2
    cwac_summary_report.md.j2
    visual_scan_report.md.j2
```

All templates reside in a single flat directory. There is no subdirectory hierarchy or template inheritance chain in the initial version. Shared components (e.g., report headers, severity legends) are duplicated across templates rather than extracted into partials, keeping each template self-contained and independently readable.

---

## 2. Template Data Model

Each template receives a context dictionary containing the data to render. The data model is constructed by the report generation pipeline from scan records, CSV results, and summary aggregations.

### Common Fields (All Templates)

| Field              | Type       | Description                                              |
|--------------------|------------|----------------------------------------------------------|
| `report_title`     | `str`      | Human-readable report title (e.g., "CWAC Scan Report: fincap.org.nz") |
| `audit_name`       | `str`      | The scan's audit name                                    |
| `generated_at`     | `datetime` | Timestamp of report generation                           |
| `scan_duration`    | `str`      | Human-readable scan duration (e.g., "5m 42s")            |
| `urls_scanned`     | `int`      | Total number of unique URLs included in the scan         |
| `template_type`    | `str`      | The template identifier (e.g., `cwac_scan_report`)       |

### `cwac_scan_report` Context

| Field              | Type                | Description                                              |
|--------------------|---------------------|----------------------------------------------------------|
| `total_issues`     | `int`               | Total number of issues found across all audit types      |
| `issues_by_impact` | `dict[str, int]`    | Issue counts keyed by impact level (`critical`, `serious`, `moderate`, `minor`, `unknown`) |
| `issues_by_audit`  | `dict[str, int]`    | Issue counts keyed by audit type (`axe_core_audit`, `html_validation`, etc.) |
| `top_violations`   | `list[dict]`        | Top 10 most frequent violations, each with `rule_id`, `count`, `impact`, `description` |
| `results_by_page`  | `list[dict]`        | Per-page issue breakdown, each with `url`, `issue_count`, `issues` (list of individual findings) |
| `results`          | `list[dict]`        | Flat list of all individual findings, each with `url`, `rule_id`, `impact`, `description`, `html`, `target`, `help_url` |

### `cwac_summary_report` Context

| Field                | Type              | Description                                              |
|----------------------|-------------------|----------------------------------------------------------|
| `total_issues`       | `int`             | Total number of issues                                   |
| `issues_by_impact`   | `dict[str, int]`  | Issue counts by impact level                             |
| `issues_by_audit`    | `dict[str, int]`  | Issue counts by audit type                               |
| `top_violations`     | `list[dict]`      | Top 10 most frequent violations                          |
| `pages_summary`      | `list[dict]`      | Per-page summary with `url` and `issue_count`            |
| `compliance_score`   | `float`           | Calculated compliance percentage (pages with zero critical/serious issues / total pages * 100) |
| `recommendations`    | `list[str]`       | Prioritised list of remediation recommendations          |

### `visual_scan_report` Context

| Field                | Type              | Description                                              |
|----------------------|-------------------|----------------------------------------------------------|
| `scan_url`           | `str`             | The URL that was visually scanned                        |
| `patterns_detected`  | `list[dict]`      | List of detected visual patterns, each with `pattern_type`, `element_count`, `details` |
| `heading_hierarchy`  | `list[dict]`      | Heading structure analysis with `level`, `text`, `is_valid_order` |
| `card_consistency`   | `dict`            | Card pattern analysis with `total_cards`, `consistent`, `inconsistencies` |
| `landmark_structure` | `list[dict]`      | ARIA landmark analysis with `role`, `label`, `contains` |
| `screenshots`        | `list[dict]`      | Screenshot references with `path`, `description`        |

---

## 3. Template Definitions

### 3.1 `cwac_scan_report.md.j2`

This template produces a detailed report of all findings from a single CWAC scan.

**Structure:**

```
# {{ report_title }}

**Audit:** {{ audit_name }}
**Date:** {{ generated_at | format_timestamp }}
**Duration:** {{ scan_duration }}
**URLs Scanned:** {{ urls_scanned }}

---

## Executive Summary

Total issues found: **{{ total_issues }}**

| Severity | Count |
|----------|-------|
{% for level, count in issues_by_impact.items() %}
| {{ level | severity_icon }} {{ level | capitalize }} | {{ count }} |
{% endfor %}

## Issues by Audit Type

| Audit Type | Issues |
|------------|--------|
{% for audit, count in issues_by_audit.items() %}
| {{ audit }} | {{ count }} |
{% endfor %}

## Top Violations

| # | Rule | Impact | Occurrences | Description |
|---|------|--------|-------------|-------------|
{% for v in top_violations %}
| {{ loop.index }} | `{{ v.rule_id }}` | {{ v.impact | severity_icon }} | {{ v.count }} | {{ v.description }} |
{% endfor %}

## Findings by Page

{% for page in results_by_page %}
### {{ page.url }}

{{ page.issue_count }} {{ page.issue_count | pluralise("issue", "issues") }} found.

{% for issue in page.issues %}
#### {{ issue.rule_id }} {{ issue.impact | severity_icon }}

- **Impact:** {{ issue.impact }}
- **Description:** {{ issue.description }}
- **Element:** `{{ issue.target }}`
- **HTML:** `{{ issue.html | truncate_html }}`
- **Help:** [{{ issue.rule_id }}]({{ issue.help_url }})

{% endfor %}
{% endfor %}

---

*Report generated on {{ generated_at | format_timestamp }}*
```

**Key design decisions:**

- Each page gets its own section, enabling readers to navigate directly to findings for a specific URL.
- Individual findings include the HTML snippet and CSS selector to enable developers to locate the element.
- The help URL links to Deque University's rule documentation for remediation guidance.
- The executive summary provides a scannable overview before the detailed findings.

### 3.2 `cwac_summary_report.md.j2`

This template produces a high-level summary suitable for stakeholders and governance reporting.

**Structure:**

```
# {{ report_title }}

**Audit:** {{ audit_name }}
**Date:** {{ generated_at | format_timestamp }}
**Duration:** {{ scan_duration }}
**URLs Scanned:** {{ urls_scanned }}
**Compliance Score:** {{ "%.1f" | format(compliance_score) }}%

---

## Summary Dashboard

| Metric | Value |
|--------|-------|
| Total Issues | {{ total_issues }} |
| Critical Issues | {{ issues_by_impact.get("critical", 0) }} |
| Serious Issues | {{ issues_by_impact.get("serious", 0) }} |
| Moderate Issues | {{ issues_by_impact.get("moderate", 0) }} |
| Minor Issues | {{ issues_by_impact.get("minor", 0) }} |
| Pages Scanned | {{ urls_scanned }} |
| Compliance Score | {{ "%.1f" | format(compliance_score) }}% |

## Severity Breakdown

| Severity | Count | Percentage |
|----------|-------|------------|
{% for level, count in issues_by_impact.items() %}
| {{ level | severity_icon }} {{ level | capitalize }} | {{ count }} | {{ "%.1f" | format(count / total_issues * 100 if total_issues > 0 else 0) }}% |
{% endfor %}

## Top 10 Violations

| Rule | Impact | Count | Description |
|------|--------|-------|-------------|
{% for v in top_violations %}
| `{{ v.rule_id }}` | {{ v.impact }} | {{ v.count }} | {{ v.description }} |
{% endfor %}

## Page Summary

| URL | Issues |
|-----|--------|
{% for page in pages_summary %}
| {{ page.url }} | {{ page.issue_count }} |
{% endfor %}

## Recommendations

{% for rec in recommendations %}
{{ loop.index }}. {{ rec }}
{% endfor %}

---

*Report generated on {{ generated_at | format_timestamp }}*
```

**Key design decisions:**

- The compliance score provides a single number for executive reporting.
- The severity breakdown includes percentages to communicate relative distribution.
- Recommendations are prioritised, with the most impactful items first.
- No code snippets or HTML elements -- this report is intended for non-technical readers.

### 3.3 `visual_scan_report.md.j2`

This template produces a report of visual pattern scanning findings from Playwright-based analysis.

**Structure:**

```
# {{ report_title }}

**URL:** {{ scan_url }}
**Date:** {{ generated_at | format_timestamp }}
**Duration:** {{ scan_duration }}

---

## Patterns Detected

{% for pattern in patterns_detected %}
### {{ pattern.pattern_type | replace("_", " ") | title }}

- **Elements found:** {{ pattern.element_count }}
- **Details:** {{ pattern.details }}

{% endfor %}

## Heading Hierarchy

| Level | Text | Valid Order |
|-------|------|-------------|
{% for h in heading_hierarchy %}
| H{{ h.level }} | {{ h.text }} | {{ "Yes" if h.is_valid_order else "**No**" }} |
{% endfor %}

{% if card_consistency %}
## Card Consistency

- **Total cards:** {{ card_consistency.total_cards }}
- **Consistent structure:** {{ "Yes" if card_consistency.consistent else "**No**" }}

{% if not card_consistency.consistent %}
### Inconsistencies

{% for issue in card_consistency.inconsistencies %}
- {{ issue }}
{% endfor %}
{% endif %}
{% endif %}

## Landmark Structure

| Role | Label | Contains |
|------|-------|----------|
{% for lm in landmark_structure %}
| `{{ lm.role }}` | {{ lm.label or "(none)" }} | {{ lm.contains | join(", ") }} |
{% endfor %}

{% if screenshots %}
## Screenshots

{% for shot in screenshots %}
### {{ shot.description }}

![{{ shot.description }}]({{ shot.path }})

{% endfor %}
{% endif %}

---

*Report generated on {{ generated_at | format_timestamp }}*
```

**Key design decisions:**

- Visual patterns are listed generically so new pattern types can be added without template changes.
- Heading hierarchy validation flags out-of-order headings (e.g., H1 followed by H3) which is a common WCAG issue.
- Card consistency analysis identifies structural inconsistencies that cause navigation confusion for screen reader users.
- Screenshots are optional; they are included when the visual scan captures them.

---

## 4. DOCX Generation

### Overview

DOCX files are generated directly from structured data using python-docx. Each report type has a dedicated builder function that constructs the document programmatically. The builders receive the same data context as the Jinja2 templates, ensuring content parity between Markdown and DOCX outputs.

### Architecture

```python
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

DOCX_BUILDERS = {
    "cwac_scan_report": build_cwac_scan_docx,
    "cwac_summary_report": build_cwac_summary_docx,
    "visual_scan_report": build_visual_scan_docx,
}

def generate_docx_report(template_type: str, data: dict, output_path: str) -> str:
    """Generate a DOCX report from structured data.

    Args:
        template_type: One of the registered template types.
        data: Template context dictionary (same as Jinja2 context).
        output_path: Absolute path for the output .docx file.

    Returns:
        The output_path on success.

    Raises:
        ValueError: If template_type is not recognised.
    """
    builder = DOCX_BUILDERS.get(template_type)
    if not builder:
        raise ValueError(f"Unknown template type: {template_type}")
    return builder(data, output_path)
```

### Common DOCX Styling

All DOCX builders share a common set of style constants and helper functions:

```python
# Style constants
FONT_NAME = "Calibri"
HEADING_COLOR = RGBColor(0x1A, 0x1A, 0x2E)  # Dark navy
TABLE_HEADER_BG = RGBColor(0x2C, 0x3E, 0x50)  # Dark blue-grey
TABLE_HEADER_TEXT = RGBColor(0xFF, 0xFF, 0xFF)  # White
SEVERITY_COLORS = {
    "critical": RGBColor(0xC0, 0x39, 0x2B),  # Red
    "serious":  RGBColor(0xE6, 0x7E, 0x22),  # Orange
    "moderate": RGBColor(0xF3, 0x9C, 0x12),  # Amber
    "minor":    RGBColor(0x27, 0xAE, 0x60),  # Green
}

def add_styled_table(doc: Document, headers: list[str], rows: list[list[str]]) -> None:
    """Add a styled table with coloured header row."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"

    # Header row
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        run = cell.paragraphs[0].runs[0]
        run.font.bold = True
        run.font.color.rgb = TABLE_HEADER_TEXT
        run.font.size = Pt(10)

    # Data rows
    for row_idx, row_data in enumerate(rows):
        for col_idx, cell_text in enumerate(row_data):
            table.rows[row_idx + 1].cells[col_idx].text = str(cell_text)
```

### Builder: `build_cwac_scan_docx`

The CWAC scan report DOCX builder follows this structure:

1. **Title page.** Report title as Heading 0, audit metadata as a summary paragraph.
2. **Executive summary.** Total issues, severity breakdown table.
3. **Issues by audit type.** Table mapping audit types to issue counts.
4. **Top violations.** Numbered table of the 10 most frequent violations.
5. **Findings by page.** For each scanned URL: a Heading 2 with the URL, followed by individual findings as styled paragraphs with rule ID, impact, description, element, and help URL.
6. **Footer.** Generation timestamp.

### Builder: `build_cwac_summary_docx`

The summary report DOCX builder follows this structure:

1. **Title page.** Report title, compliance score as a prominent heading.
2. **Summary dashboard.** Key metrics table.
3. **Severity breakdown.** Table with counts and percentages.
4. **Top violations.** Numbered table.
5. **Page summary.** Table listing each URL and its issue count.
6. **Recommendations.** Numbered list of prioritised recommendations.
7. **Footer.** Generation timestamp.

### Builder: `build_visual_scan_docx`

The visual scan report DOCX builder follows this structure:

1. **Title page.** Report title, scanned URL, scan date.
2. **Patterns detected.** For each pattern: heading, element count, details paragraph.
3. **Heading hierarchy.** Table with level, text, and validity columns.
4. **Card consistency.** Summary paragraph, inconsistencies as a bulleted list (if any).
5. **Landmark structure.** Table with role, label, and contents columns.
6. **Screenshots.** Embedded images using `doc.add_picture()` with captions (if screenshots are available on disk).
7. **Footer.** Generation timestamp.

### Error Handling

| Condition                         | Behaviour                                                     |
|-----------------------------------|---------------------------------------------------------------|
| Output directory does not exist   | Created automatically via `os.makedirs(exist_ok=True)`        |
| python-docx not installed         | `ImportError` raised at module import; server fails to start  |
| Invalid data in context           | `KeyError` or `TypeError` raised; caught by caller, logged    |
| Disk write failure                | `OSError` raised; caught by caller, error returned to MCP client |
| Screenshot file not found         | Warning logged; screenshot omitted from DOCX output           |

---

## 5. Output File Naming

### Convention

All generated reports are saved to the `./output/` directory relative to the project root. The filename follows a deterministic pattern:

```
{audit_name}_{timestamp}_report.{ext}
```

### Components

| Component      | Format              | Example                   | Source                          |
|----------------|---------------------|---------------------------|---------------------------------|
| `audit_name`   | Lowercase, underscores | `fincap_homepage`         | `ScanRecord.audit_name`, sanitised |
| `timestamp`    | `YYYYMMDD_HHMMSS`   | `20260224_143542`         | Report generation time          |
| `_report`      | Literal suffix       | `_report`                 | Fixed                           |
| `.ext`         | `md` or `docx`       | `.md`, `.docx`            | Output format                   |

### Filename Sanitisation

The `audit_name` is sanitised before use in filenames:

```python
import re

def sanitise_filename(name: str) -> str:
    """Sanitise a string for use as a filename component.

    - Converts to lowercase.
    - Replaces spaces and hyphens with underscores.
    - Removes any characters that are not alphanumeric or underscores.
    - Collapses multiple underscores to a single one.
    - Strips leading and trailing underscores.
    """
    name = name.lower()
    name = re.sub(r"[\s\-]+", "_", name)
    name = re.sub(r"[^\w]", "", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")
```

### Full Path Construction

```python
from datetime import datetime
import os

def build_output_path(audit_name: str, ext: str) -> str:
    """Construct the full output file path for a report.

    Args:
        audit_name: The scan's audit name (will be sanitised).
        ext: File extension ('md' or 'docx').

    Returns:
        Absolute path to the output file.
    """
    safe_name = sanitise_filename(audit_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_name}_{timestamp}_report.{ext}"
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, filename)
```

### Examples

| Audit Name             | Timestamp         | Markdown Path                                              | DOCX Path                                                  |
|------------------------|-------------------|------------------------------------------------------------|------------------------------------------------------------|
| `fincap_homepage`      | `20260224_143542`  | `./output/fincap_homepage_20260224_143542_report.md`       | `./output/fincap_homepage_20260224_143542_report.docx`     |
| `GovtNZ Full Audit`   | `20260224_160000`  | `./output/govtnz_full_audit_20260224_160000_report.md`     | `./output/govtnz_full_audit_20260224_160000_report.docx`   |
| `test-scan-2`         | `20260224_091500`  | `./output/test_scan_2_20260224_091500_report.md`           | `./output/test_scan_2_20260224_091500_report.docx`         |

### Output Directory Management

- The `./output/` directory is created automatically on first report generation.
- The directory should be added to `.gitignore` to prevent committing generated reports.
- There is no automatic cleanup or rotation. Accumulated reports must be managed manually by the user.

---

## 6. Auto-Report Hook

### Trigger Mechanism

The auto-report hook is invoked when a scan transitions from `running` to `complete` in the scan registry. This transition is detected during `cwac_scan_status` polling or internal process monitoring.

### Hook Integration Point

The hook is called from the status transition logic in the scan registry (see SPEC-003-A, Section 3):

```python
def update_scan_status(scan_record: ScanRecord) -> None:
    """Check subprocess state and update scan record if needed."""
    if scan_record.status != ScanStatus.RUNNING:
        return

    return_code = scan_record.process.poll()

    if return_code is None:
        # Still running
        new_output = read_available_output(scan_record.process.stdout)
        scan_record.stdout += new_output
        return

    # Process has exited
    scan_record.end_time = datetime.now()

    if return_code == 0:
        scan_record.status = ScanStatus.COMPLETE
        scan_record.stdout += scan_record.process.stdout.read()
        scan_record.results_dir = find_results_dir(scan_record)
        trigger_cleanup(scan_record)

        # AUTO-REPORT HOOK
        try:
            report_paths = generate_reports(scan_record)
            scan_record.report_paths = report_paths
        except Exception as e:
            logger.warning(f"Auto-report generation failed: {e}")
            # Non-fatal: scan completion is not affected by report failure
    else:
        scan_record.status = ScanStatus.FAILED
        scan_record.stdout += scan_record.process.stdout.read()
        scan_record.stderr = scan_record.process.stderr.read()
        trigger_cleanup(scan_record)
```

### Report Generation Pipeline

```python
def generate_reports(scan_record: ScanRecord) -> dict[str, str]:
    """Generate all reports for a completed scan.

    Args:
        scan_record: A completed ScanRecord with results_dir populated.

    Returns:
        Dictionary mapping format ('md', 'docx') to absolute file paths.
    """
    # 1. Parse results into template data model
    data = build_template_data(scan_record)

    # 2. Determine template type
    template_type = "cwac_scan_report"  # Default for CWAC scans

    # 3. Generate Markdown report
    md_content = render_markdown_report(template_type, data)
    md_path = build_output_path(scan_record.audit_name, "md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # 4. Generate DOCX report
    docx_path = build_output_path(scan_record.audit_name, "docx")
    generate_docx_report(template_type, data, docx_path)

    return {"md": md_path, "docx": docx_path}
```

### Data Construction

The `build_template_data` function reads scan results and constructs the template context:

```python
def build_template_data(scan_record: ScanRecord) -> dict:
    """Build the template data model from a completed scan's results.

    Reads CSV files from the results directory, aggregates them,
    and constructs the context dictionary expected by templates.
    """
    results = parse_csv_results(scan_record.results_dir)
    summary = aggregate_results(results)

    return {
        "report_title": f"CWAC Scan Report: {scan_record.audit_name}",
        "audit_name": scan_record.audit_name,
        "generated_at": datetime.now(),
        "scan_duration": format_duration(
            (scan_record.end_time - scan_record.start_time).total_seconds()
        ),
        "urls_scanned": summary["urls_scanned"],
        "template_type": "cwac_scan_report",
        "total_issues": summary["total_issues"],
        "issues_by_impact": summary["issues_by_impact"],
        "issues_by_audit": summary["issues_by_audit"],
        "top_violations": summary["top_violations"],
        "results_by_page": summary["results_by_page"],
        "results": results,
    }
```

### Hook Behaviour

| Aspect                  | Behaviour                                                        |
|-------------------------|------------------------------------------------------------------|
| **Trigger condition**   | Scan status transitions to `COMPLETE` (exit code 0)              |
| **Failure handling**    | Non-fatal. Exceptions are logged; scan completion is unaffected  |
| **Reports generated**   | Both Markdown and DOCX for the `cwac_scan_report` template type  |
| **Path storage**        | Report file paths are stored in `scan_record.report_paths`       |
| **User notification**   | Report paths are included in the `cwac_scan_status` response when the scan is complete |
| **Failed scans**        | No reports are generated for failed scans                        |
| **Duplicate prevention**| If `scan_record.report_paths` is already populated, the hook does not re-generate |

### ScanRecord Extension

The `ScanRecord` dataclass is extended with a `report_paths` field to store generated report locations:

```python
@dataclass
class ScanRecord:
    # ... existing fields ...

    report_paths: dict[str, str] = field(default_factory=dict)
    """Paths to generated report files. Keys: 'md', 'docx'. Values: absolute file paths.
    Empty dict until auto-report hook runs successfully."""
```

### Status Response Extension

When a scan is complete and reports have been generated, the `cwac_scan_status` response includes the report paths:

```json
{
  "scan_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "complete",
  "elapsed_time": "5m 42s",
  "results_dir": "/workspaces/cwac/results/scan_2026-02-24_20260224_143542/",
  "exit_code": 0,
  "report_paths": {
    "md": "/workspaces/di-test/output/scan_2026_02_24_20260224_143542_report.md",
    "docx": "/workspaces/di-test/output/scan_2026_02_24_20260224_143542_report.docx"
  }
}
```

---

## Related Specifications

| Spec ID    | Relationship  | Title                      |
|------------|--------------|----------------------------|
| SPEC-001-A | Relates to   | MCP Tool Definitions       |
| SPEC-003-A | Extends      | Scan Registry Design       |

## Changelog

| Version | Date       | Author        | Changes                          |
|---------|------------|---------------|----------------------------------|
| A       | 2026-02-24 | Chris Barlow  | Initial specification            |
