# Check My Website — Accessibility Pattern Scanner

A tool that scans webpages and detects visual patterns (headings, cards) that may need accessibility review. It complements CWAC scans by flagging elements that *look like* headings or cards but may lack proper semantic markup.

This tool **flags patterns, not violations**. It never auto-fails WCAG.

## What It Detects

**Heading-like content**
- Elements with class names containing h1–h6 (case-insensitive, partial match)
- Text that is visually styled as a heading — larger, bolder, isolated on its own line

**Card-like content**
- Groups of content containing an image, heading/title text, and body text wrapped in a link
- Repeated structural patterns across the page
- Elements sharing a common link destination

## Architecture

| Layer | Purpose |
|-------|---------|
| Crawler | Loads the page via Playwright |
| DOM Analyzer | Detects class-based headings (deterministic) |
| Visual Analyzer | Detects heading-like visual patterns (font size, weight, isolation) |
| Card Detector | Finds card candidate structures |
| AI Reasoning | Classifies candidates and explains findings in plain language |
| Reporter | Outputs structured JSON + screenshots |

Deterministic analysis always runs before AI. The AI interprets candidates — it does not discover elements from scratch.

## Output

Each finding includes:

- **URL** of the scanned page
- **Type** — Heading-like or Card-like
- **DOM location** — CSS selector + XPath
- **Screenshot** with highlighted region (full-page + cropped)
- **HTML snippet** with attributes
- **Reason** — plain language explanation of why it was flagged

Output is structured JSON. See the [spec](di-web-accessibility-spec.md) for the full schema.

## Test Scenarios

Test scenarios are written in Gherkin/BDD format under `tests/`:

| File | Scenarios | Covers |
|------|-----------|--------|
| `heading-detection.feature` | 9 | Class-based and visual heading detection |
| `card-detection.feature` | 8 | Card structure detection and heuristics |
| `screenshot-and-highlighting.feature` | 5 | Screenshot capture, overlays, metadata |
| `output-format.feature` | 9 | JSON output structure and field validation |
| `ai-classification.feature` | 9 | AI input/output, confidence scoring, tone |
| `page-crawl.feature` | 5 | Pipeline order, error handling, text extraction |

**45 scenarios total**, targeting [FinCap Our Team](https://www.fincap.org.nz/our-team/) as the proof-of-concept page.

These are designed to be run via the [Playwright MCP server](https://github.com/microsoft/playwright-mcp), where an LLM translates each scenario into browser automation tool calls.

## Design Principles

- **Never auto-fail WCAG** — this tool flags patterns, not violations
- **Explain, don't judge** — "This appears to function as a heading but is not marked up as one"
- **Deterministic first, AI second** — AI interprets what rules-based analysis found
- **Auditor trust > AI cleverness**
