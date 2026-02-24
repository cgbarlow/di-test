# Contributing to di-test

Thanks for your interest in contributing to di-test. This guide covers the project structure, architecture, development setup, and documentation conventions.

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js v18+
- [CWAC](https://github.com/GOVTNZ/cwac) installed at a discoverable location

### Manual Setup

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

### Running Tests

```bash
pytest tests/
```

The test suite includes 68 pytest tests across 7 test files covering report generation, templates, plugin manifest, config builder, result reader, and scan registry.

## Project Structure

```
di-test/
├── .claude-plugin/
│   └── plugin.json                        # Claude Code plugin manifest
├── .mcp.json                              # MCP server configuration (Playwright + CWAC)
├── marketplace.json                       # Plugin marketplace listing
├── cwac_mcp/                              # CWAC MCP server
│   ├── __init__.py                        # Package init, CWAC_PATH + PROJECT_ROOT discovery
│   ├── server.py                          # FastMCP server with 6 tools, dual-mode routing
│   ├── environment_check.py               # Detect scan mode (cwac vs axe-only)
│   ├── cwac_runner.py                     # Subprocess execution of CWAC
│   ├── axe_scanner.py                     # Standalone Playwright + axe-core scanner
│   ├── scanner_runner.py                  # Subprocess launcher for axe_scanner
│   ├── config_builder.py                  # Builds CWAC + axe-core configs from tool params
│   ├── result_reader.py                   # Reads/parses result CSVs (both modes)
│   ├── scan_registry.py                   # Tracks active/completed scans in memory
│   ├── report_generator.py               # Markdown + DOCX report generation
│   └── requirements.txt                   # Python dependencies (incl. playwright)
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
│   ├── fixtures/                          # HTML test fixtures
│   │   ├── violations.html                # Page with known a11y violations
│   │   └── no_violations.html             # Clean accessible page
│   ├── conftest.py                        # Shared pytest fixtures
│   ├── test_environment_check.py          # Environment detection tests
│   ├── test_axe_scanner.py                # axe-core scanner pure function tests
│   ├── test_config_builder.py             # Config builder tests (both modes)
│   ├── test_result_reader.py              # Result reader tests
│   ├── test_scan_registry.py              # Scan registry tests (dual results root)
│   ├── test_plugin_manifest.py            # Plugin manifest validation
│   ├── test_report_generator.py           # Report generator tests
│   └── test_report_templates.py           # Template rendering tests
├── docs/
│   ├── CWAC-MCP.md                        # CWAC MCP server technical reference
│   ├── VISUAL-SCANNER.md                  # Visual scanner technical reference
│   ├── EXAMPLES.md                        # Example scan results
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

## Architecture

The platform combines two MCP servers with dual-mode scanning:

| Server | What it does | How it works |
|--------|-------------|--------------|
| **Playwright MCP** | Visual pattern detection — finds elements that *look like* headings or cards but may lack semantic markup | LLM-driven browser automation using Gherkin test scenarios |
| **CWAC MCP** | WCAG compliance scanning — runs axe-core, language, reflow, and other accessibility audits | Subprocess wrapper around [GOVTNZ/cwac](https://github.com/GOVTNZ/cwac) |

### Dual-Mode Scanner

The CWAC MCP server supports two scanning modes, selected automatically at startup:

| Mode | Engine | Available when | Audit types |
|------|--------|---------------|-------------|
| **Full (`cwac`)** | CWAC subprocess | CWAC + chromedriver + selenium available | All CWAC plugins (axe-core, language, readability, etc.) |
| **Fallback (`axe-only`)** | Playwright + axe-core | Playwright + axe-core available, CWAC unavailable | axe-core only |

The fallback scanner produces CSV output in the same column format as CWAC, so all downstream tools (result_reader, report_generator, templates) work identically regardless of mode.

For detailed technical documentation:
- [CWAC MCP Server](docs/CWAC-MCP.md) — architecture, tools, plugins, scan lifecycle, fallback mode
- [Visual Pattern Scanner](docs/VISUAL-SCANNER.md) — analysis pipeline, detection methods, output format

## Architecture Decision Records (ADRs)

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
| [ADR-007](docs/adr/ADR-007-playwright-fallback.md) | Playwright + axe-core fallback mode | Architecture independence + graceful degradation; fewer audit types in fallback |

## Technical Specifications

| Spec | Covers | Parent ADR |
|------|--------|-----------|
| [SPEC-000-A](docs/specs/SPEC-000-A-visual-pattern-scanner.md) | Visual pattern detection: heading-like and card-like content analysis pipeline | ADR-000 |
| [SPEC-001-A](docs/specs/SPEC-001-A-mcp-tool-definitions.md) | All 6 MCP tool definitions with parameters, return values, and behaviour | ADR-001 |
| [SPEC-002-A](docs/specs/SPEC-002-A-subprocess-execution-model.md) | Subprocess invocation, config generation, process monitoring, cleanup | ADR-002 |
| [SPEC-003-A](docs/specs/SPEC-003-A-scan-registry-design.md) | Scan registry data structure, state transitions, thread safety | ADR-003 |
| [SPEC-004-A](docs/specs/SPEC-004-A-manifest-and-skills.md) | Plugin manifest schema, skill definitions, marketplace config | ADR-004 |
| [SPEC-005-A](docs/specs/SPEC-005-A-template-definitions.md) | Report templates, Jinja2 rendering, DOCX generation, auto-report | ADR-005 |
| [SPEC-006-A](docs/specs/SPEC-006-A-installation-pipeline.md) | SessionStart hook, install script, CWAC_PATH discovery, verification | ADR-006 |
| [SPEC-007-A](docs/specs/SPEC-007-A-axe-scanner.md) | axe-core scanner design, CSV mapping, environment check | ADR-007 |
