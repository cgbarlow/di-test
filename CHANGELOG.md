# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-02-24

### Added

- **Playwright + axe-core fallback mode** — When CWAC's chromedriver is unavailable or incompatible with the host architecture (e.g. ARM64), the scanner automatically falls back to running axe-core directly via Playwright. This enables accessibility scanning on any architecture, including Apple Silicon Macs and ARM-based Codespaces.
- **Environment detection** — New `environment_check.py` module auto-detects whether CWAC (full suite) or axe-only (fallback) mode should be used. The active mode is reported in all scan responses.
- **`axe_scanner.py`** — Standalone Playwright + axe-core scanner that injects axe-core JS into pages, collects violations, crawls same-domain links, and writes CSV output in the same column format as CWAC.
- **`scanner_runner.py`** — Subprocess launcher for the fallback scanner, analogous to `cwac_runner.py`.
- **ADR-007** — Architecture Decision Record for the Playwright fallback mode.
- **SPEC-007-A** — Technical specification for the axe-core scanner design.
- **New test suites** — `test_environment_check.py`, `test_axe_scanner.py`, HTML test fixtures.

### Changed

- **`cwac_mcp/__init__.py`** — Added `PROJECT_ROOT` and `RESULTS_ROOT` exports alongside `CWAC_PATH`.
- **`cwac_mcp/server.py`** — Routes `cwac_scan` to CWAC or axe-core based on detected mode. All tool responses include `scan_mode`. Report generation works in both modes.
- **`cwac_mcp/config_builder.py`** — Added `build_axe_config()` for fallback mode (self-contained JSON, no CWAC directories).
- **`cwac_mcp/result_reader.py`** — `list_scan_results()` searches both CWAC `results/` and project `output/` directories.
- **`cwac_mcp/scan_registry.py`** — `_discover_results_dir()` searches both CWAC and project output directories.
- **`cwac_mcp/requirements.txt`** — Added `playwright` dependency.
- **`package.json`** — Added `axe-core` dependency, version bumped to 0.3.0.
- **`scripts/install-deps.sh`** — CWAC installation is now optional (warns instead of failing). Added Playwright browser install. Clear messages about available mode.
- **README.md** — Updated to reflect dual-mode reality (full CWAC on x86-64, axe-only fallback on ARM64). References new Manual Setup and Architecture docs.
- **CONTRIBUTING.md** — Slimmed down; manual setup moved to `docs/MANUAL-SETUP.md`, architecture moved to `docs/ARCHITECTURE.md`.
- **docs/ARCHITECTURE.md** — New file: architecture overview, dual-mode scanner, project structure, ADR and SPEC tables.
- **docs/MANUAL-SETUP.md** — New file: development setup instructions without the plugin system.
- **docs/CWAC-MCP.md** — Added fallback mode documentation.

## [0.2.4] - 2026-02-24

### Added

- **`/di-test:full-scan`** — Combined scan command that runs both CWAC compliance scan and visual pattern scan in parallel, then generates reports for both and presents a combined summary.

## [0.2.3] - 2026-02-24

### Fixed

- **CWAC auto-install** — SessionStart hook now clones CWAC from GitHub to `~/.local/share/di-test/cwac/` if not found, and installs its Python deps, Node deps, and Chrome automatically. Plugin users no longer need to manually install CWAC.
- **CWAC discovery chain** — Added `~/.local/share/di-test/cwac/` as step 4 in the discovery chain (after env var, sibling dir, and `/workspaces/cwac`).

## [0.2.2] - 2026-02-24

### Fixed

- **Plugin structure** — Moved `marketplace.json` into `.claude-plugin/` with proper marketplace schema (plugins array, owner, source URL). Previously at repo root with flat format.
- **hooks.json format** — Corrected from array-with-event-fields to the plugin system's expected schema (event names as object keys with nested hooks arrays).
- **MCP server path** — Replaced hardcoded `/workspaces/di-test/` path in `.mcp.json` with `${CLAUDE_PLUGIN_ROOT}` so CWAC server resolves correctly when installed from plugin cache.
- **plugin.json simplified** — Removed explicit skills, hooks, mcpServers declarations. Plugin system auto-discovers from `skills/`, `hooks/hooks.json`, and `.mcp.json`.

## [0.2.1] - 2026-02-24

### Added

- **LICENSE** — Added CC-BY-SA-4.0 licence file.
- **CONTRIBUTING.md** — Developer guide with project structure, architecture overview, ADR/SPEC tables, and development setup. Technical content previously in README relocated here.
- **docs/CWAC-MCP.md** — CWAC MCP server technical reference (architecture, tools, plugins, scan lifecycle).
- **docs/VISUAL-SCANNER.md** — Visual pattern scanner technical reference (pipeline, detection methods, output format, test scenarios).
- **docs/EXAMPLES.md** — Example scan results (FinCap visual scan, MSD CWAC scan) with sample output.
- **Acknowledgements** — Credited Di Drayton as instigator and accessibility SME, and the DIA Web Standards team as CWAC creators.

### Changed

- **README.md** — Major restructure for non-technical audiences (accessibility staff, web content managers). Reduced from 444 to ~130 lines. Added "Who Is This For?" and "Our Approach" sections. Moved technical content (architecture, MCP tools, project structure, ADR/SPEC tables) to CONTRIBUTING.md and docs/. Added licence and contributing sections.
- **Version alignment** — `plugin.json`, `marketplace.json`, and `package.json` all now report 0.2.1 (previously `package.json` was 1.0.0 while plugin was 0.2.0).

## [0.2.0] - 2026-02-24

### Added

- **Claude Code Plugin** — di-test is now a distributable Claude Code plugin with marketplace support.
  - Plugin manifest at `.claude-plugin/plugin.json` with 7 skills, hooks, and MCP server config.
  - Marketplace listing at `marketplace.json` for same-repo installation.
  - 7 skills: `/di-test:scan`, `/di-test:scan-status`, `/di-test:results`, `/di-test:summary`, `/di-test:report`, `/di-test:list-scans`, `/di-test:visual-scan`.
  - SessionStart hook for automatic dependency installation via `scripts/install-deps.sh`.
- **Report Template System** — Auto-generated reports in Markdown and DOCX formats.
  - `cwac_mcp/report_generator.py` — Jinja2-based markdown + python-docx DOCX generation.
  - 3 Jinja2 templates: `cwac_scan_report.md.j2`, `cwac_summary_report.md.j2`, `visual_scan_report.md.j2`.
  - Reports auto-save to `./output/` as `{audit_name}_{timestamp}_report.{md,docx}`.
- **CWAC_PATH Discovery** — Configurable CWAC path with env var → sibling dir → fallback chain.
- **Test Suite** — 68 pytest tests across 7 test files covering report generation, templates, plugin manifest, config builder, result reader, and scan registry.
- **Architecture Decision Records** — 3 new ADRs for v0.2:
  - ADR-004: Plugin architecture (same-repo marketplace model)
  - ADR-005: Report template system (Jinja2 + python-docx)
  - ADR-006: Dependency management (SessionStart hook + CWAC_PATH discovery)
- **Technical Specifications** — 3 new SPECs for v0.2:
  - SPEC-004-A: Plugin manifest and skill definitions
  - SPEC-005-A: Report template definitions and rendering pipeline
  - SPEC-006-A: Installation pipeline and dependency verification

### Changed

- **`cwac_mcp/__init__.py`** — CWAC_PATH now uses a discovery chain instead of a hardcoded path.
- **`cwac_mcp/requirements.txt`** — Added `python-docx` and `jinja2` dependencies.
- **`README.md`** — Added Quick Start sections for Claude Desktop, Claude Code CLI, and manual setup; updated project structure; added commands table.

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
