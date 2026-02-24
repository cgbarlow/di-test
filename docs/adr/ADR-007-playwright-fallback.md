# ADR-007: Playwright + axe-core Fallback Mode

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-02-24 |
| **Parent ADR** | ADR-001, ADR-002, ADR-006 |
| **Spec** | SPEC-007-A |

## Context

CWAC (GOVTNZ/cwac) bundles an x86-64 chromedriver binary that fails on ARM64 systems (Apple Silicon Macs, ARM-based Codespaces). This means the full CWAC suite cannot run in these environments. Rather than replacing CWAC entirely — which provides a rich set of audit plugins (language, readability, broken links, SEO, etc.) — we need an alternative that provides core accessibility scanning on any architecture.

axe-core is the industry-standard accessibility rules engine used by CWAC itself for its `axe_core_audit` plugin. Playwright provides cross-platform browser automation with architecture-appropriate browser binaries.

## Decision

Add a **fallback mode** to the scanner: when CWAC's dependencies (Selenium, chromedriver) are not available or not compatible with the host architecture, the scanner falls back to running axe-core directly via Playwright.

An environment check runs at server startup and determines the active mode:

- **Full mode (`cwac`):** All CWAC audit plugins available (axe-core, language, readability, broken links, etc.)
- **Fallback mode (`axe-only`):** axe-core accessibility scanning via Playwright — fewer audit types but works on any architecture

The fallback scanner produces CSV output in the **same column format** as CWAC's `axe_core_audit.csv`, so all downstream tools (result_reader, report_generator, templates) work identically regardless of mode.

## Alternatives Considered

### Replace CWAC entirely with Playwright + axe-core

- **Rejected.** CWAC provides language audits, readability scoring, reflow testing, SEO checks, and other plugins beyond axe-core. Replacing it would reduce capability for users on supported architectures.

### Cross-compile chromedriver for ARM64

- **Rejected.** CWAC bundles chromedriver from upstream; cross-compilation is a CWAC-side concern. We follow ADR-001's principle of zero CWAC modification.

### Use Docker to run CWAC in x86 emulation

- **Rejected.** Adds significant complexity, requires Docker installation, and emulation is slow. Not practical for a lightweight plugin.

## Rationale

- **Architecture independence:** Playwright downloads architecture-appropriate browser binaries. axe-core is pure JavaScript. The fallback works on x86-64, ARM64, and any other platform Playwright supports.
- **Same output format:** By producing CSV in CWAC's column format, we avoid any changes to result_reader, report_generator, or templates. The user experience is identical.
- **Graceful degradation:** Users on ARM systems still get axe-core scanning (the primary accessibility value). Users on x86-64 systems with CWAC get the full suite.
- **No CWAC modification:** Consistent with ADR-001 and ADR-002 — we continue to use CWAC as-is when available.
- **Clear user communication:** The environment check message tells users exactly which mode is active and what capabilities are available.

## Consequences

### Positive

- The plugin works on any architecture supported by Playwright
- Existing CWAC users see no change in behaviour
- All downstream tools work identically in both modes
- Auto-detection means zero user configuration required

### Negative

- Fallback mode provides only axe-core audits (no language, readability, broken links, etc.)
- Two code paths to maintain (CWAC runner + axe scanner)
- Playwright browser binary adds ~150MB to the installation

### Licence

- **CWAC (GPL-3.0):** No modification or distribution — used as-is when available
- **axe-core (MPL-2.0):** Permits free use; injected via Playwright (standard practice)
- **Our licence (CC-BY-SA-4.0):** Compatible — new original code
