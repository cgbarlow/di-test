# di-test — Accessibility Testing Platform

A comprehensive accessibility testing platform combining visual pattern detection with WCAG compliance scanning. It integrates two complementary approaches via MCP (Model Context Protocol) servers, giving Claude Code (or any MCP-compatible LLM) the ability to run both visual heuristic analysis and full CWAC accessibility audits from a single conversational interface.

## Two MCP Servers, Two Approaches

| Server | What it does | How it works |
|--------|-------------|--------------|
| **Playwright MCP** | Visual pattern detection — finds elements that *look like* headings or cards but may lack semantic markup | LLM-driven browser automation using Gherkin test scenarios |
| **CWAC MCP** | WCAG compliance scanning — runs axe-core, language, reflow, and other accessibility audits | Subprocess wrapper around [GOVTNZ/cwac](https://github.com/GOVTNZ/cwac) |

Together they provide a complete accessibility audit workflow: CWAC finds WCAG violations, while the visual pattern scanner catches elements that pass automated checks but may still confuse users.

---

## Quick Start

### Claude Cowork and Claude Code Desktop

1. From either the **Cowork** or **Code** tab in Claude Desktop, select **+** → **Plugins** → **Add plugin**
2. **Add marketplace** — Select the **By Anthropic** dropdown, then select **Add marketplace from GitHub** and enter:
   ```
   cgbarlow/di-test/
   ```
3. **Install plugin** — find and install **DI Accessibility Testing Platform** from the marketplace
4. **Start scanning** — the plugin installs dependencies automatically on first session. Then:
   - `/di-test:scan https://example.govt.nz` — Run a CWAC accessibility scan
   - `/di-test:visual-scan https://example.com/page` — Run visual pattern detection
   - `/di-test:report` — Generate a report in Markdown + DOCX

### Claude Code CLI

1. **Install Claude Code** ([full guide](https://code.claude.com/docs/en/quickstart)):
   ```bash
   curl -fsSL https://claude.ai/install.sh | bash
   ```
2. **Add the marketplace** — in a Claude Code session:
   ```
   /plugin marketplace add cgbarlow/di-test
   ```
3. **Install the plugin:**
   ```
   /plugin install di-test@di-test-marketplace
   ```
4. **Start scanning:**
   - `/di-test:scan https://example.govt.nz` — Run a CWAC accessibility scan
   - `/di-test:visual-scan https://example.com/page` — Run visual pattern detection
   - `/di-test:report` — Generate a report in Markdown + DOCX

Dependencies are installed automatically via the SessionStart hook. You never need to run `pip install` or `npm install` manually.

### Manual Setup (without plugin)

If you prefer to run without the plugin system:

1. Clone the repository:
   ```bash
   git clone https://github.com/cgbarlow/di-test.git
   cd di-test
   ```
2. Install dependencies:
   ```bash
   pip install -r cwac_mcp/requirements.txt
   npm install
   npx playwright install --with-deps chromium
   ```
3. Install [CWAC](https://github.com/GOVTNZ/cwac) as a sibling directory or set `CWAC_PATH`
4. Both MCP servers are configured in `.mcp.json`. Claude Code will discover them automatically.

### Prerequisites

- Python 3.10+
- Node.js v18+
- [CWAC](https://github.com/GOVTNZ/cwac) installed at a discoverable location (for CWAC MCP tools)

### Available Commands

| Command | What it does |
|---------|-------------|
| `/di-test:scan` | Start a CWAC accessibility scan against one or more URLs |
| `/di-test:scan-status` | Check the status of a running scan |
| `/di-test:results` | Get detailed findings from a completed scan |
| `/di-test:summary` | Get a high-level summary of findings |
| `/di-test:report` | Generate a report in Markdown and DOCX formats |
| `/di-test:list-scans` | List all active and historical scan results |
| `/di-test:visual-scan` | Run the visual pattern scanner via Playwright MCP |

---

## CWAC MCP Server

The CWAC MCP server wraps the [Centralised Web Accessibility Checker](https://github.com/GOVTNZ/cwac) as an MCP server, exposing 6 tools for scan lifecycle management.

### Architecture

```
Claude Code
    │
    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  CWAC MCP    │────▶│  Subprocess  │────▶│    CWAC      │
│  Server      │     │  Runner      │     │  (cwac.py)   │
│  (FastMCP)   │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
    │                                          │
    ▼                                          ▼
┌──────────────┐                        ┌──────────────┐
│ Scan Registry│                        │  Results CSV │
│ (in-memory)  │                        │  files       │
└──────────────┘                        └──────────────┘
    │                                          │
    ▼                                          ▼
┌──────────────┐                        ┌──────────────┐
│Config Builder│                        │Result Reader │
│ (temp JSON)  │                        │ (CSV parser) │
└──────────────┘                        └──────────────┘
```

The server runs CWAC as a **subprocess** with `cwd=/workspaces/cwac` rather than importing it directly. This avoids modifying CWAC's source code and handles its reliance on relative paths (`./config/`, `./base_urls/`, `./results/`). See [ADR-002](docs/adr/ADR-002-subprocess-vs-direct-import.md) for the full rationale.

### MCP Tools

| Tool | Description |
|------|-------------|
| `cwac_scan` | Start a CWAC accessibility scan. Accepts URLs, audit name, plugin toggles, crawl depth, and viewport sizes. Returns a scan ID for tracking. |
| `cwac_scan_status` | Check scan status (running/complete/failed), elapsed time, and recent output. |
| `cwac_get_results` | Retrieve scan results with optional filters by audit type, impact level, and row limit. |
| `cwac_get_summary` | Get aggregated summary: total issues, breakdown by audit type, axe impact distribution, top violations. |
| `cwac_list_scans` | List all active and historical scan result directories. |
| `cwac_generate_report` | Run CWAC's report exporter to generate leaderboard CSVs from scan results. |

### CWAC MCP Usage Examples

**Run a basic accessibility scan:**
```
Scan https://www.example.govt.nz for accessibility issues using CWAC
```

**Scan multiple URLs with specific settings:**
```
Run a CWAC scan on these URLs with max 10 pages per domain:
- https://www.site1.govt.nz
- https://www.site2.govt.nz
```

**Check scan progress:**
```
What's the status of the CWAC scan?
```

**Get a summary of findings:**
```
Show me a summary of the CWAC scan results
```

**Filter results by severity:**
```
Show me only the critical axe-core issues from the scan
```

**Generate a report:**
```
Generate a leaderboard report from the CWAC scan results
```

### Scan Lifecycle

1. **Initiate** — `cwac_scan` builds config, writes base URLs CSV, launches CWAC subprocess
2. **Monitor** — `cwac_scan_status` polls the subprocess for progress
3. **Retrieve** — `cwac_get_results` or `cwac_get_summary` reads result CSVs
4. **Report** — `cwac_generate_report` runs the export pipeline

Scans are non-blocking: `cwac_scan` returns immediately with a scan ID, and you can check status while the scan runs. See [ADR-003](docs/adr/ADR-003-scan-lifecycle-management.md) for the lifecycle design.

### Available Plugins

| Plugin | Key | Default |
|--------|-----|---------|
| Axe-core audit | `axe_core_audit` | Enabled |
| Language audit | `language_audit` | Enabled |
| Reflow audit | `reflow_audit` | Enabled |
| Focus indicator audit | `focus_indicator_audit` | Disabled |
| Screenshot audit | `screenshot_audit` | Disabled |
| Element audit | `element_audit` | Disabled |

---

## Visual Pattern Scanner (Playwright MCP)

The visual pattern scanner detects elements that *look like* headings or cards but may lack proper semantic markup. It uses LLM-driven browser automation with Gherkin test scenarios.

This tool **flags patterns, not violations**. It never auto-fails WCAG.

### Running a Visual Scan

```
Run the tests against https://www.fincap.org.nz/our-team/ using Playwright MCP
```

This runs a 6-layer analysis pipeline:

1. **DOM Analyzer** — Class-based heading detection (deterministic)
2. **Visual Analyzer** — Heading-like visual patterns (rules-based)
3. **Card Detector** — Card candidate structure detection (heuristic)
4. **AI Reasoning** — Classification + plain language explanation
5. **Screenshot Capture** — Full-page + cropped + highlight overlays
6. **Reporter** — Structured JSON + report compilation

### Visual Scanner Usage Examples

**Full scan with report:**
```
Scan https://www.fincap.org.nz/our-team/ using Playwright MCP and generate a detailed report
```

**Heading-only check:**
```
Check https://example.com for elements that look like headings but aren't marked up as headings
```

**Card pattern detection:**
```
Scan https://example.com/team/ for card-like content structures using Playwright MCP
```

### What It Detects

**Heading-like content:**

| Method | What it finds |
|--------|--------------|
| Class-based (DOM) | Elements with class names containing h1-h6 |
| Visual analysis | Text visually styled as a heading (larger, bolder, isolated, spaced) |
| Non-semantic tags | Elements that look like headings but use `<div>`, `<span>`, `<p>` |

**Card-like content:**

| Method | What it finds |
|--------|--------------|
| Link-wrapped groups | An `<a>` wrapping an image + heading + body text |
| Shared destinations | Multiple elements linking to the same URL within a container |
| Repeated patterns | Groups with matching DOM structure and CSS classes |
| Structural heuristics | Shared parent containers, vertical alignment, bounding box adjacency |

### Example Report

A complete scan has been run against the [FinCap Our Team page](https://www.fincap.org.nz/our-team/) as a proof of concept:

| File | Description |
|------|-------------|
| [Scan Report (Markdown)](output/accessibility-scan-report.md) | Detailed findings with analysis and recommendations |
| [Scan Report (Word)](output/accessibility-scan-report.docx) | Same report in .docx format |
| [Findings JSON](output/findings.json) | Structured JSON output with all 38 findings |
| [Full Page Screenshot](output/screenshots/our-team-full.png) | Full-page capture |
| [Highlighted Screenshot](output/screenshots/our-team-highlighted.png) | Red overlays on flagged elements |

Key findings: 19 heading-like candidates (team member names using `<p class="h3">` instead of `<h3>`), 19 card-like candidates (repeated `<article>` structures), a link mismatch, and an empty `<h2>`.

---

## CWAC Scan Reports

### MSD (Ministry of Social Development) — msd.govt.nz

A CWAC scan was run against [msd.govt.nz](https://msd.govt.nz) on 2026-02-24, crawling 50 pages with axe-core, language, and reflow audits enabled.

| Metric | Value |
|--------|-------|
| Pages scanned | 50 |
| Axe-core issues | 27 (3 critical, 24 serious) |
| Language audit | All pages analysed (Flesch-Kincaid grade levels recorded) |
| Reflow audit | 0 overflow issues |

**Top axe-core findings:**

| Impact | Rule | Description | Count |
|--------|------|-------------|-------|
| Critical | `image-alt` | `<img>` elements missing alternative text | 3 |
| Serious | `list` | Lists not structured correctly | 24 |

**Scan result files:**

| File | Description |
|------|-------------|
| [Axe-Core Audit](output/msd-govt-nz-2026-02-24/axe_core_audit.csv) | All axe-core findings across 50 pages |
| [Language Audit](output/msd-govt-nz-2026-02-24/language_audit.csv) | Flesch-Kincaid and SMOG readability scores |
| [Reflow Audit](output/msd-govt-nz-2026-02-24/reflow_audit.csv) | Horizontal overflow checks at 320px |
| [Pages Scanned](output/msd-govt-nz-2026-02-24/pages_scanned.csv) | List of all 50 pages crawled |

### FinCap — fincap.org.nz

See the [FinCap scan report](output/accessibility-scan-report.md) above for the visual pattern scan of the Our Team page.

### Output Format

Each finding includes:

| Field | Description |
|-------|-------------|
| `url` | URL of the scanned page |
| `type` | `"Heading-like content"` or `"Card-like content"` |
| `reason` | Plain language explanation of why it was flagged |
| `location.cssSelector` | CSS selector that uniquely locates the element |
| `location.xpath` | XPath expression that locates the element |
| `visual.fontSize` | Computed font size (heading-like only) |
| `visual.fontWeight` | Computed font weight (heading-like only) |
| `screenshot` | File path to the saved screenshot |
| `htmlSnippet` | The element's outer HTML including attributes |
| `confidence` | AI confidence score (0-1) |

### Test Scenarios

| File | Scenarios | Covers |
|------|-----------|--------|
| `page-crawl.feature` | 5 | Page load, text extraction, pipeline order, error handling |
| `heading-detection.feature` | 9 | Class-based and visual heading detection |
| `card-detection.feature` | 8 | Card structure detection and heuristics |
| `screenshot-and-highlighting.feature` | 5 | Screenshot capture, overlays, metadata |
| `output-format.feature` | 9 | JSON output structure and field validation |
| `ai-classification.feature` | 9 | AI input/output, confidence scoring, tone |

**45 scenarios total** | 43 pass, 2 skipped (edge-case conditions)

---

## Project Structure

```
di-test/
├── .claude-plugin/
│   └── plugin.json                        # Claude Code plugin manifest
├── .mcp.json                              # MCP server configuration (Playwright + CWAC)
├── marketplace.json                       # Plugin marketplace listing
├── cwac_mcp/                              # CWAC MCP server
│   ├── __init__.py                        # Package init, CWAC_PATH discovery
│   ├── server.py                          # FastMCP server with 6 tool definitions
│   ├── cwac_runner.py                     # Subprocess execution of CWAC
│   ├── config_builder.py                  # Builds CWAC config JSON from tool params
│   ├── result_reader.py                   # Reads/parses CWAC result CSVs
│   ├── scan_registry.py                   # Tracks active/completed scans in memory
│   ├── report_generator.py               # Markdown + DOCX report generation
│   └── requirements.txt                   # Python dependencies
├── skills/                                # Plugin skill definitions
│   ├── scan/SKILL.md                      # /di-test:scan
│   ├── scan-status/SKILL.md               # /di-test:scan-status
│   ├── results/SKILL.md                   # /di-test:results
│   ├── summary/SKILL.md                   # /di-test:summary
│   ├── report/SKILL.md                    # /di-test:report
│   ├── list-scans/SKILL.md                # /di-test:list-scans
│   └── visual-scan/SKILL.md               # /di-test:visual-scan
├── hooks/
│   └── hooks.json                         # SessionStart hook configuration
├── scripts/
│   └── install-deps.sh                    # Dependency installation (idempotent)
├── templates/                             # Jinja2 report templates
│   ├── cwac_scan_report.md.j2             # Detailed CWAC scan report
│   ├── cwac_summary_report.md.j2          # Summary report
│   └── visual_scan_report.md.j2           # Visual pattern scan report
├── tests/                                 # Test suites
│   ├── *.feature                          # Gherkin scenarios (visual scanner)
│   ├── conftest.py                        # Shared pytest fixtures
│   ├── test_config_builder.py             # Config builder tests
│   ├── test_result_reader.py              # Result reader tests
│   ├── test_scan_registry.py              # Scan registry tests
│   ├── test_plugin_manifest.py            # Plugin manifest validation
│   ├── test_report_generator.py           # Report generator tests
│   └── test_report_templates.py           # Template rendering tests
├── docs/
│   ├── adr/                               # Architecture Decision Records
│   │   ├── ADR-000 through ADR-006
│   └── specs/                             # Technical Specifications
│       ├── SPEC-000-A through SPEC-006-A
└── output/                                # Generated scan output
    ├── accessibility-scan-report.md
    ├── accessibility-scan-report.docx
    ├── findings.json
    └── screenshots/
```

## Documentation

### Architecture Decision Records (ADRs)

All architectural decisions are documented using the WH(Y) ADR format:

| ADR | Decision | Key Trade-off |
|-----|----------|---------------|
| [ADR-000](docs/adr/ADR-000-visual-pattern-scanner.md) | LLM-driven visual pattern detection via Playwright MCP | Catches non-semantic patterns automated tools miss; AI-dependent, flags not violations |
| [ADR-001](docs/adr/ADR-001-cwac-mcp-integration-approach.md) | MCP server wrapper for CWAC integration | MCP provides structured tools + Claude Code integration; requires additional server process |
| [ADR-002](docs/adr/ADR-002-subprocess-vs-direct-import.md) | Subprocess execution instead of direct Python import | Zero CWAC modifications + update compatibility; subprocess overhead + temp file management |
| [ADR-003](docs/adr/ADR-003-scan-lifecycle-management.md) | Async scan model with in-memory registry | Non-blocking scans + concurrent support; state lost on server restart |
| [ADR-004](docs/adr/ADR-004-plugin-architecture.md) | Same-repo Claude Code plugin with marketplace | Zero-friction install + skill discoverability; requires repo access |
| [ADR-005](docs/adr/ADR-005-report-template-system.md) | Jinja2 + python-docx dual-format reports | Markdown + DOCX from structured data, no pandoc; python-docx adds dependency |
| [ADR-006](docs/adr/ADR-006-dependency-management.md) | SessionStart hook with CWAC_PATH discovery chain | Auto-install + portable paths; startup latency on first session |

### Technical Specifications

| Spec | Covers | Parent ADR |
|------|--------|-----------|
| [SPEC-000-A](docs/specs/SPEC-000-A-visual-pattern-scanner.md) | Visual pattern detection: heading-like and card-like content analysis pipeline | ADR-000 |
| [SPEC-001-A](docs/specs/SPEC-001-A-mcp-tool-definitions.md) | All 6 MCP tool definitions with parameters, return values, and behaviour | ADR-001 |
| [SPEC-002-A](docs/specs/SPEC-002-A-subprocess-execution-model.md) | Subprocess invocation, config generation, process monitoring, cleanup | ADR-002 |
| [SPEC-003-A](docs/specs/SPEC-003-A-scan-registry-design.md) | Scan registry data structure, state transitions, thread safety | ADR-003 |
| [SPEC-004-A](docs/specs/SPEC-004-A-manifest-and-skills.md) | Plugin manifest schema, skill definitions, marketplace config | ADR-004 |
| [SPEC-005-A](docs/specs/SPEC-005-A-template-definitions.md) | Report templates, Jinja2 rendering, DOCX generation, auto-report | ADR-005 |
| [SPEC-006-A](docs/specs/SPEC-006-A-installation-pipeline.md) | SessionStart hook, install script, CWAC_PATH discovery, verification | ADR-006 |

## Design Principles

- **Never auto-fail WCAG** — the visual scanner flags patterns, not violations
- **Explain, don't judge** — findings include plain language explanations
- **Deterministic first, AI second** — AI interprets what rules-based analysis found
- **Auditor trust > AI cleverness** — findings include selectors, XPaths, HTML snippets, and screenshots
- **Zero modification to CWAC** — the MCP server wraps CWAC without changing its source

## How It Works (Under the Hood)

### Playwright MCP (Visual Scanner)

1. You prompt Claude Code with a scan request
2. The LLM reads the Gherkin test scenarios in `tests/`
3. Playwright MCP provides browser automation tools
4. The LLM executes each scenario step via Playwright MCP tool calls
5. AI classification interprets the deterministic findings
6. Output is saved as JSON, screenshots, and reports

### CWAC MCP

1. You prompt Claude Code to run a CWAC scan
2. The MCP server generates a config JSON and base URLs CSV
3. CWAC runs as a subprocess in its own directory
4. The scan registry tracks progress via subprocess polling
5. Results are read from CWAC's CSV output files
6. Summaries and reports are generated on demand

## Future Scope

- Interactive/dynamic content detection (modals, panels)
- Sticky/fixed-position content detection
- Persistent scan state across server restarts
- Scan cancellation support
- Web UI report viewer
- Combined reporting (visual + CWAC findings in one report)
