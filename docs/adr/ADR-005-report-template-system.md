# ADR-005: Report Template System

| Field    | Value                                        |
|----------|----------------------------------------------|
| **ID**   | ADR-005                                      |
| **Status** | Accepted                                   |
| **Date** | 2026-02-24                                   |
| **Author** | Chris Barlow                               |

## WH(Y) Decision Statement

**In the context of** generating human-readable accessibility reports from CWAC scan data and visual scan findings,

**facing** the need for consistent, branded, and distributable report outputs in both Markdown and DOCX formats,

**we decided for** a Jinja2-based Markdown template system with direct DOCX generation via python-docx, auto-saving to `./output/` with structured filenames,

**and neglected** pandoc-based conversion, HTML-to-DOCX pipelines, LaTeX templates, and manual report creation,

**to achieve** zero-dependency report generation (no pandoc install required), consistent output structure across report types, and automatic report production after scan completion,

**accepting that** template customisation requires editing `.md.j2` files directly and DOCX styling is limited to what python-docx supports natively.

## Context

The CWAC MCP server and visual pattern scanner produce structured data (CSV results, JSON summaries, scan metadata) that must be transformed into distributable reports. These reports serve multiple audiences:

- **Developers** need actionable issue lists with code snippets and remediation guidance.
- **Project managers** need summary dashboards with issue counts and severity breakdowns.
- **Stakeholders** need high-level compliance summaries suitable for inclusion in governance documentation.

The reports must be available in two formats:

1. **Markdown** -- for inline display in Claude Code conversations, version control, and rendering on GitHub or documentation sites.
2. **DOCX** -- for email distribution, printing, and inclusion in formal audit deliverables where recipients may not have Markdown rendering tools.

Three distinct report types are required:

| Report Type            | Purpose                                                         | Primary Data Source       |
|------------------------|-----------------------------------------------------------------|---------------------------|
| `cwac_scan_report`     | Detailed findings from a single CWAC scan                       | CWAC CSV results + summary |
| `cwac_summary_report`  | Aggregated summary across multiple scans or a single scan       | CWAC summary JSON          |
| `visual_scan_report`   | Findings from Playwright-based visual pattern scanning          | Visual scan output JSON    |

Reports are auto-generated after scan completion and saved to `./output/` with filenames following the pattern `{audit_name}_{timestamp}_report.{md,docx}`. This ensures every scan produces a retrievable report without requiring the user to explicitly request one.

## Decision

We will implement a template-based report generation system with the following architecture:

### Template Engine

All Markdown reports are rendered using **Jinja2** templates. Templates are stored as `.md.j2` files in the `templates/` directory within the MCP server package:

```
cwac-mcp-server/
  templates/
    cwac_scan_report.md.j2
    cwac_summary_report.md.j2
    visual_scan_report.md.j2
```

Jinja2 was chosen because:

- It is already a transitive dependency of the MCP SDK (via `starlette` and other packages), adding no new dependencies.
- Its template syntax is well-documented and widely understood.
- It supports template inheritance, macros, and filters -- enabling shared report components (headers, footers, severity badges).
- It cleanly separates report structure (template) from report data (context dictionary), making templates testable independently of scan logic.

### DOCX Generation

DOCX files are generated directly from structured data using **python-docx**, not by converting Markdown output. This is a deliberate design choice:

```python
from docx import Document
from docx.shared import Inches, Pt, RGBColor

def generate_docx(report_data: dict, template_type: str, output_path: str) -> str:
    doc = Document()
    # Build document programmatically from report_data
    doc.add_heading(report_data["title"], level=0)
    doc.add_paragraph(report_data["summary"])
    # ... tables, styled paragraphs, etc.
    doc.save(output_path)
    return output_path
```

Each report type has a corresponding DOCX builder function that constructs the document using python-docx's API. The builders receive the same data context as the Jinja2 templates, ensuring content parity between Markdown and DOCX outputs.

### Output File Naming

All reports are saved to `./output/` relative to the project root, with filenames following a consistent pattern:

```
./output/{audit_name}_{timestamp}_report.md
./output/{audit_name}_{timestamp}_report.docx
```

Where:

- `{audit_name}` is the human-readable scan name (e.g., `fincap_homepage`, `govtnz_full_audit`).
- `{timestamp}` is an ISO-8601-derived string in the format `YYYYMMDD_HHMMSS`.

Examples:

```
./output/fincap_homepage_20260224_143542_report.md
./output/fincap_homepage_20260224_143542_report.docx
./output/govtnz_full_audit_20260224_160000_report.md
./output/govtnz_full_audit_20260224_160000_report.docx
```

The `./output/` directory is created automatically if it does not exist. It is included in `.gitignore` to prevent committing generated reports to version control.

### Auto-Report Hook

After a scan transitions to the `complete` state (detected by `cwac_scan_status` or an internal completion callback), the report generation pipeline is triggered automatically:

1. The scan registry detects process completion (exit code 0).
2. The scan record's results directory is located.
3. Results are parsed and aggregated into the template data model.
4. Both Markdown and DOCX reports are generated and saved to `./output/`.
5. The report file paths are recorded in the scan record for later retrieval.

This ensures that every successful scan produces a report without requiring the user to invoke a separate report generation tool. The user is informed of the report paths in the scan completion response.

### Template Types

| Template                    | File                            | Content                                          |
|-----------------------------|---------------------------------|--------------------------------------------------|
| `cwac_scan_report`          | `cwac_scan_report.md.j2`       | Full scan findings: issues by page, severity, rule; code snippets; remediation links |
| `cwac_summary_report`       | `cwac_summary_report.md.j2`    | High-level dashboard: total issues, severity breakdown, top violations, pages scanned |
| `visual_scan_report`        | `visual_scan_report.md.j2`     | Visual pattern findings: heading hierarchy, card consistency, landmark structure      |

## Alternatives Considered

### Alternative 1: Pandoc-based conversion

Converting Jinja2-rendered Markdown to DOCX using pandoc:

```bash
pandoc report.md -o report.docx --reference-doc=template.docx
```

**Why it was rejected:**

- Pandoc is a large external dependency (~200 MB installed) that must be present on the host system. It is not a Python package and cannot be installed via pip.
- In containerised development environments (like Codespaces), pandoc may not be pre-installed and adding it increases image size and build time.
- Pandoc's Markdown-to-DOCX conversion produces adequate but not highly customisable output. Fine-grained control over table styling, heading fonts, and colour schemes requires a reference document that is itself difficult to maintain.
- The conversion adds a subprocess call, introducing a potential failure point and making the pipeline harder to test in CI.
- Error messages from pandoc are opaque and difficult to surface meaningfully to the user through MCP.

### Alternative 2: HTML-to-DOCX pipeline

Rendering Markdown to HTML (via `markdown` or `mistune`), then converting HTML to DOCX (via `htmldocx` or `mammoth`):

```python
import markdown
from htmldocx import HtmlToDocx

html = markdown.markdown(rendered_md)
parser = HtmlToDocx()
parser.parse_html_string(html)
parser.save("report.docx")
```

**Why it was rejected:**

- Introduces two conversion steps (Markdown to HTML to DOCX), each with potential for formatting loss or unexpected behaviour.
- The `htmldocx` library has limited table support and struggles with complex Markdown structures (nested lists, code blocks within tables).
- Debugging formatting issues requires understanding three different format representations (Markdown, HTML, DOCX).
- The intermediate HTML step adds complexity without adding value, since the data is already structured and can be mapped directly to DOCX elements.

### Alternative 3: LaTeX templates

Using Jinja2 templates that produce LaTeX, then compiling to PDF via `pdflatex` or `xelatex`:

**Why it was rejected:**

- LaTeX is an even larger dependency than pandoc and is not commonly available in development containers.
- The primary requirement is DOCX output, not PDF. LaTeX excels at PDF but does not produce DOCX natively.
- LaTeX template syntax is significantly more complex than Markdown, raising the barrier for template customisation.
- Compilation errors in LaTeX are notoriously difficult to debug.

### Alternative 4: Manual report creation

Having Claude Code generate reports on-the-fly by formatting scan data into Markdown within the conversation:

**Why it was rejected:**

- No consistency: every report would be structured differently depending on the LLM's output.
- No DOCX output: Claude Code cannot generate binary files.
- No persistence: reports exist only in the conversation history and are lost when the session ends.
- High token usage: every report generation consumes significant tokens for formatting that could be handled by a template.
- No automation: the user must explicitly ask for a report after every scan.

## Consequences

### Positive

- **Zero external dependencies for DOCX.** python-docx is a pure Python package installed via pip. No system-level tools (pandoc, LaTeX) are required.
- **Consistent output.** Every report of a given type has identical structure, making reports comparable across scans.
- **Automatic generation.** Reports are produced immediately after scan completion without user intervention.
- **Dual format.** Both Markdown (for developers and version control) and DOCX (for stakeholders and formal deliverables) are generated from the same data.
- **Testable templates.** Jinja2 templates can be unit tested by rendering them with mock data and asserting on the output structure.
- **Extensible.** New report types can be added by creating a new `.md.j2` template and a corresponding DOCX builder function.

### Negative

- **DOCX styling limitations.** python-docx supports basic document formatting (headings, tables, paragraphs, bold/italic) but lacks support for advanced features like embedded charts, complex page layouts, or conditional formatting. Reports that require rich visual design may need a different approach.
- **Dual maintenance.** The Markdown template and DOCX builder for each report type must be kept in sync manually. A change to the report structure requires updating both.
- **Template learning curve.** Contributors must understand Jinja2 syntax to modify report templates. While Jinja2 is well-documented, it is an additional technology in the stack.
- **Output directory management.** The `./output/` directory will accumulate reports over time. There is no automatic cleanup; users must manage disk usage manually.

## Dependencies

| Relationship  | Target   | Description                                                |
|---------------|----------|------------------------------------------------------------|
| DEPENDS_ON    | ADR-001  | Report generation is triggered through MCP tool invocation |
| DEPENDS_ON    | ADR-003  | Auto-report hook relies on scan lifecycle state transitions |

## Referenced Specification

| Spec ID    | Title                  | Version |
|------------|------------------------|---------|
| SPEC-005-A | Template Definitions   | A       |

## Status History

| Date       | Status   | Changed By    | Notes                     |
|------------|----------|---------------|---------------------------|
| 2026-02-24 | Accepted | Chris Barlow  | Initial decision recorded |

## Governance

This ADR was authored following the WH(Y) decision format from [cgbarlow/adr](https://github.com/cgbarlow/adr). Changes to this decision require a new ADR that supersedes this one.
