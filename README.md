# di-test — Accessibility Testing Platform

A tool that helps you find accessibility issues on websites. It combines two approaches: automated WCAG compliance scanning (using [CWAC](https://github.com/GOVTNZ/cwac)) and visual pattern detection that catches things automated tools miss — like text that *looks like* a heading but isn't marked up as one.

You don't need to be a developer to use it. Install the plugin, point it at a URL, and get a plain-language report of what it finds.

### Scanning Modes

The plugin auto-detects your environment and selects the best available mode:

| Mode | When | What you get |
|------|------|-------------|
| **Full (Visual patterns + complete CWAC suite)** | x86-64 systems with CWAC installed (dependencies auto-installed) | All audit plugins: axe-core, language, readability, broken links, SEO, and more |
| **Fallback (Visual patterns + axe-core)** | ARM64 systems or when CWAC is unavailable | axe-core accessibility scanning via Playwright — catches WCAG violations on any architecture |

You'll see which mode is active when you start a scan. No configuration needed.

## Who Is This For?

- **Accessibility advisors** running audits across government or organisational websites
- **Web content managers** checking pages for common accessibility patterns
- **Digital inclusion teams** building evidence for remediation priorities
- **Developers** integrating accessibility checks into their workflow

## Our Approach

These principles guide everything the tool does:

- **Never auto-fail WCAG** — the tool flags patterns for review, not violations. A human auditor makes the final call.
- **Explain, don't judge** — every finding includes a plain language explanation of what was detected and why it matters.
- **Deterministic first, AI second** — rules-based analysis runs first; AI interprets what it found. The AI never invents findings.
- **Auditor trust > AI cleverness** — findings include CSS selectors, XPaths, HTML snippets, and screenshots so you can independently verify everything.
- **Zero modification to CWAC** — the tool wraps CWAC without changing its source code.

---

## Quick Start

### Claude Desktop (Cowork or Code tab)

> Uses Fallback mode: Visual patterns + axe-core, no CWAC.

1. Select **+** then **Plugins** then **Add plugin**
2. Select the **By Anthropic** dropdown, then **Add marketplace from GitHub** and enter:
   ```
   https://github.com/cgbarlow/di-test/
   ```
3. Find and install **DI Accessibility Testing Platform** from the marketplace
4. Start scanning:
   - `/di-test:full-scan https://example.govt.nz` — Run a full accessibility scan (WCAG + visual patterns) and generate reports
   - `/di-test:scan https://example.govt.nz` — Run an accessibility scan
   - `/di-test:visual-scan https://example.com/page` — Run visual pattern detection
   - `/di-test:report` — Generate a report in Markdown + Word

### Claude Code (CLI)

> Mode used depends on environment, x86-64 system required for full CWAC suite.
  
1. In a Claude Code session:
   ```
   /plugin marketplace add https://github.com/cgbarlow/di-test
   /plugin install di-test@di-test-marketplace
   ```
2. Start scanning with the same commands as above.

Dependencies are installed automatically. You never need to run `pip install` or `npm install` manually.

> For manual setup without the plugin system, see [Manual Setup](docs/MANUAL-SETUP.md).

---

## Available Commands

You can use these commands, but you don't have to. You can simply ask in natural language and the AI will understand your intent and a suitable command will be used.

| Command | What it does |
|---------|-------------|
| `/di-test:full-scan` | Run both CWAC + visual scans and generate all reports |
| `/di-test:scan` | Run a CWAC accessibility scan against one or more URLs |
| `/di-test:visual-scan` | Run visual pattern detection (headings, cards) |
| `/di-test:report` | Generate a report in Markdown and Word formats |
| `/di-test:scan-status` | Check the status of a running scan |
| `/di-test:results` | Get detailed findings from a completed scan |
| `/di-test:summary` | Get a high-level summary of findings |
| `/di-test:list-scans` | List all active and historical scan results |

---

## What Does a Scan Look Like?

Here's a real example. We scanned the [FinCap Our Team page](https://www.fincap.org.nz/our-team/) and found 38 patterns to review:

- **19 team member names** styled to look like headings (large, bold, pink) but marked up as `<p>` tags instead of `<h3>`. Screen reader users can't navigate to them using heading shortcuts.
- **19 card structures** — repeated person cards that may need review for keyboard focus and screen reader behaviour.
- **1 link mismatch** — a card displaying "Katie Brannan" but linking to a different person's page.
- **1 empty heading** — a blank `<h2>` in the footer.

Every finding includes a plain-language explanation, the exact CSS selector to locate it, and a confidence score. See the [full scan report](output/accessibility-scan-report.md) and [more examples](docs/EXAMPLES.md).

---

## What It Scans

**CWAC scans** (full mode) check for WCAG compliance issues:
- Axe-core violations (missing alt text, incorrect list structure, colour contrast)
- Language readability (Flesch-Kincaid grade levels)
- Reflow issues (horizontal overflow at 320px viewport)
- Focus indicator visibility

**axe-core scans** (fallback mode) check for:
- All axe-core WCAG violations (same engine as CWAC's axe_core_audit plugin)
- Works on any architecture via Playwright

**Visual pattern scans** catch things automated tools miss:
- Text that looks like a heading but isn't marked up as one
- Card-like content groups that may need accessibility review
- Elements with heading CSS classes (e.g., `class="h3"`) on non-heading tags

For technical details, see [CWAC MCP Server](docs/CWAC-MCP.md) and [Visual Pattern Scanner](docs/VISUAL-SCANNER.md).

---

## Future Scope

- Interactive/dynamic content detection (modals, panels)
- Sticky/fixed-position content detection
- Combined reporting (visual + CWAC findings in one report)
- Persistent scan state across server restarts
- Scan cancellation support

---

## Acknowledgements

This tool was instigated by **Di Drayton**, Accessibility Subject Matter Expert, who defined the original specification for visual pattern detection ([SPEC-000-A](docs/specs/SPEC-000-A-visual-pattern-scanner.md)).

The CWAC integration wraps the [Centralised Web Accessibility Checker](https://github.com/GOVTNZ/cwac), created by the **Web Standards team** within the Digital Public Service branch of **Te Tari Taiwhenua, Department of Internal Affairs**, New Zealand Government. CWAC is licensed under GPL-3.0.

Built by [Chris Barlow](https://github.com/cgbarlow).

## Licence

This project is licensed under [CC-BY-SA-4.0](LICENSE) (Creative Commons Attribution-ShareAlike 4.0 International).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get involved, [Architecture](docs/ARCHITECTURE.md) for project structure and design decisions, and [Manual Setup](docs/MANUAL-SETUP.md) for development environment setup.
