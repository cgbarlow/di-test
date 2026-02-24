# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-02-24

### Added

- **MSD scan report** — Added CWAC scan results for msd.govt.nz (50 pages, 3 critical + 24 serious axe-core issues) to README.
- **ADR-000** — Architecture Decision Record for the visual pattern scanner (predates CWAC work).
- **SPEC-000-A** — Technical specification for visual pattern detection pipeline, reformatted from original `di-web-accessibility-spec.md`.

### Changed

- **`di-web-accessibility-spec.md`** — Renamed and reformatted to `docs/specs/SPEC-000-A-visual-pattern-scanner.md` with metadata table, numbered sections, and SPEC template structure.
- **`README.md`** — Added CWAC Scan Reports section with MSD results, updated project structure and documentation tables to include ADR-000 and SPEC-000-A.

## [0.1.0] - 2026-02-24

### Added

- **CWAC MCP Server** — New MCP server wrapping the [GOVTNZ/cwac](https://github.com/GOVTNZ/cwac) accessibility checker, enabling Claude Code to run WCAG compliance scans directly via MCP tools.
  - `cwac_scan` — Start an accessibility scan against one or more URLs with configurable plugins, crawl depth, and viewport sizes.
  - `cwac_scan_status` — Check the status of a running or completed scan.
  - `cwac_get_results` — Retrieve detailed scan results with optional filtering by audit type, impact level, and row limit.
  - `cwac_get_summary` — Get aggregated summary with issue counts by audit type, axe impact breakdown, and top violations.
  - `cwac_list_scans` — List all active and historical scan result directories.
  - `cwac_generate_report` — Generate leaderboard CSV reports from scan results.
- **Subprocess execution model** — CWAC runs as a subprocess with `cwd=/workspaces/cwac`, requiring zero modifications to CWAC source code.
- **Scan lifecycle management** — Non-blocking async scan model with in-memory scan registry for tracking process state, results paths, and captured output.
- **Config builder** — Generates CWAC config JSON and base URLs CSV files from MCP tool parameters, with audit name sanitisation matching CWAC's own logic.
- **Result reader** — Parses CWAC's CSV output files using stdlib `csv` module with filtering and aggregation support.
- **Architecture Decision Records (ADRs)** — 3 ADRs documenting key decisions using the WH(Y) format:
  - ADR-001: CWAC MCP integration approach (MCP server vs REST API vs shell scripts)
  - ADR-002: Subprocess vs direct import (subprocess wrapper vs Python import vs CWAC fork)
  - ADR-003: Scan lifecycle management (async model vs blocking scans vs job queues)
- **Technical Specifications** — 3 SPECs detailing implementation design:
  - SPEC-001-A: MCP tool definitions (all 6 tools with parameters, return values, behaviour)
  - SPEC-002-A: Subprocess execution model (invocation, config generation, monitoring, cleanup)
  - SPEC-003-A: Scan registry design (data structure, state transitions, thread safety)

### Changed

- **`.mcp.json`** — Added `cwac` server entry alongside the existing `playwright` server.
- **`.gitignore`** — Added `__pycache__/` and `*.pyc` patterns.
- **`README.md`** — Comprehensive rewrite covering both MCP servers (Playwright + CWAC), updated project structure, CWAC architecture diagram, usage examples for both tools, plugin reference, scan lifecycle documentation, and links to all ADRs and SPECs.
