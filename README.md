# Check My Website — Accessibility Pattern Scanner

A tool that scans webpages and detects visual patterns (headings, cards) that may need accessibility review. It complements CWAC scans by flagging elements that *look like* headings or cards but may lack proper semantic markup.

This tool **flags patterns, not violations**. It never auto-fails WCAG.

## Quick Start

### Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (or any LLM client that supports MCP)
- Node.js (v18+)
- A Chromium browser (installed automatically on first run)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/cgbarlow/di-test.git
   cd di-test
   ```

2. Install dependencies:
   ```bash
   npm install
   npx playwright install --with-deps chromium
   ```

3. The Playwright MCP server is already configured in `.mcp.json`. Claude Code will pick it up automatically.

### Running a Scan

Open Claude Code in the project directory and prompt it to run the tests against your target page. The Gherkin test scenarios in `tests/` define the full analysis pipeline.

**Basic scan:**
```
Run the tests against https://www.fincap.org.nz/our-team/ using Playwright MCP
```

**Scan a different page:**
```
Run the heading detection and card detection tests against https://example.com/team/ using Playwright MCP
```

**Run a single feature:**
```
Run just the heading-detection.feature tests against https://www.fincap.org.nz/our-team/
```

The LLM translates each Gherkin scenario into Playwright MCP browser automation tool calls, executing the 6-layer analysis pipeline against the live page.

## Usage Examples

### Example 1: Full scan with report

```
Scan https://www.fincap.org.nz/our-team/ using Playwright MCP and generate a detailed report
```

This will:
1. Navigate to the page and verify it loads
2. Extract all text nodes with computed styles
3. Run DOM analysis (class-based heading detection)
4. Run visual analysis (font size, weight, isolation, spacing)
5. Run card detection (structure, repeated patterns, shared links)
6. Classify each candidate with AI (confidence scores, plain language explanations)
7. Capture screenshots with highlight overlays
8. Produce structured JSON output and a markdown/docx report

### Example 2: Heading-only check

```
Check https://example.com for elements that look like headings but aren't marked up as headings
```

### Example 3: Card pattern detection

```
Scan https://example.com/team/ for card-like content structures using Playwright MCP
```

### Example 4: Generate a report after scanning

```
Create a detailed report based on your findings
```

```
Convert the report to docx
```

## Example Report

A complete scan has been run against the [FinCap Our Team page](https://www.fincap.org.nz/our-team/) as a proof of concept. The full output is available in this repository:

| File | Description |
|------|-------------|
| [Scan Report (Markdown)](output/accessibility-scan-report.md) | Detailed findings report with analysis, tables, and recommendations |
| [Scan Report (Word)](output/accessibility-scan-report.docx) | Same report in .docx format for stakeholder distribution |
| [Findings JSON](output/findings.json) | Structured JSON output with all 38 findings |
| [Full Page Screenshot](output/screenshots/our-team-full.png) | Full-page capture of the target page |
| [Highlighted Screenshot](output/screenshots/our-team-highlighted.png) | Full-page with red overlays on flagged elements |
| [Cropped: Fleur Howard](output/screenshots/our-team-item0.png) | Example cropped card screenshot |
| [Cropped: Jake Lilley](output/screenshots/our-team-item1.png) | Example cropped card screenshot |
| [Cropped: Iuni Perez](output/screenshots/our-team-item2.png) | Example cropped card screenshot |

### Key findings from the example scan

- **19 heading-like candidates** — All team member names use `<p class="h3 card-title">` instead of semantic `<h3>` tags. They score 5/5 on visual heading signals (larger font, heavier weight, isolated line, vertical spacing, precedes content).
- **19 card-like candidates** — Repeated `<article>` structures each containing image + name + title + description + link, using `stretched-link` for full-card click behaviour.
- **Link mismatch** — Katie Brannan's card links to `/people/bella-tioro/` (possible content error).
- **Empty heading** — An empty `<h2>` in the footer social media section.

### Example JSON output

Each finding follows this structure:

```json
{
  "url": "https://www.fincap.org.nz/our-team/",
  "type": "Heading-like content",
  "reason": "This appears to function as a heading but is not marked up as one. The element uses a <p> tag with class 'h3' and has visual characteristics of a heading: larger font size (30px vs 18px body), heavier weight (500 vs 400), isolated on its own line, with vertical margin separation.",
  "location": {
    "cssSelector": "section:nth-of-type(2) article:nth-child(1) p.h3.card-title",
    "xpath": "/html/body/main/section[2]/div/div[2]/div[1]/article/div[2]/p[1]"
  },
  "visual": {
    "fontSize": "30px",
    "fontWeight": "500"
  },
  "screenshot": "our-team-item0.png",
  "htmlSnippet": "<p class=\"h3 card-title mb-4\">Fleur Howard</p>",
  "confidence": 0.95
}
```

## What It Detects

### Heading-like content

| Method | What it finds |
|--------|--------------|
| **Class-based (DOM)** | Elements with class names containing h1–h6 (case-insensitive, partial match) |
| **Visual analysis** | Text that is visually styled as a heading — larger, bolder, isolated on its own line, with vertical spacing, appearing before content blocks |
| **Non-semantic tags** | Elements that look like headings but use `<div>`, `<span>`, `<p>`, or other non-heading tags |

### Card-like content

| Method | What it finds |
|--------|--------------|
| **Link-wrapped groups** | An `<a>` wrapping an image + heading + body text |
| **Shared destinations** | Multiple elements linking to the same URL within a container |
| **Repeated patterns** | Groups with matching DOM structure and CSS classes across the page |
| **Structural heuristics** | Shared parent containers, vertical alignment, bounding box adjacency |

## Architecture

The tool runs a 6-layer analysis pipeline. Deterministic analysis always runs before AI — the AI interprets candidates, it does not discover elements from scratch.

```
Page Load
  │
  ▼
┌─────────────────┐
│  DOM Analyzer    │  Layer 1 — Class-based heading detection (deterministic)
└────────┬────────┘
         ▼
┌─────────────────┐
│ Visual Analyzer  │  Layer 2 — Heading-like visual patterns (rules-based)
└────────┬────────┘
         ▼
┌─────────────────┐
│  Card Detector   │  Layer 3 — Card candidate structure detection (heuristic)
└────────┬────────┘
         ▼
┌─────────────────┐
│  AI Reasoning    │  Layer 4 — Classification + plain language explanation
└────────┬────────┘
         ▼
┌─────────────────┐
│Screenshot Capture│  Layer 5 — Full-page + cropped + highlight overlays
└────────┬────────┘
         ▼
┌─────────────────┐
│    Reporter      │  Layer 6 — Structured JSON + report compilation
└─────────────────┘
```

| Layer | Type | Purpose |
|-------|------|---------|
| DOM Analyzer | Deterministic | Detects class-based headings (h1–h6 in class names) |
| Visual Analyzer | Rules-based | Detects heading-like visual patterns (font size, weight, isolation, spacing) |
| Card Detector | Heuristic | Finds card candidate structures (link groups, repeated patterns, shared containers) |
| AI Reasoning | LLM | Classifies candidates with confidence scores; explains findings in plain language |
| Screenshot Capture | Automation | Captures full-page and cropped screenshots with highlight overlays |
| Reporter | Output | Compiles structured JSON output and reports |

## Output Format

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
| `confidence` | AI confidence score (0–1) |

See the [full specification](di-web-accessibility-spec.md) for the complete schema and detection rules.

## Test Scenarios

Test scenarios are written in Gherkin/BDD format under `tests/`. They define the expected behaviour of each pipeline layer and are executed by the LLM via Playwright MCP browser automation.

| File | Scenarios | Covers |
|------|-----------|--------|
| `page-crawl.feature` | 5 | Page load, text extraction, pipeline order, error handling |
| `heading-detection.feature` | 9 | Class-based and visual heading detection |
| `card-detection.feature` | 8 | Card structure detection and heuristics |
| `screenshot-and-highlighting.feature` | 5 | Screenshot capture, overlays, metadata |
| `output-format.feature` | 9 | JSON output structure and field validation |
| `ai-classification.feature` | 9 | AI input/output, confidence scoring, tone |

**45 scenarios total**, targeting [FinCap Our Team](https://www.fincap.org.nz/our-team/) as the proof-of-concept page.

### Test Results (PoC Run)

| Feature | Pass | Skip | Fail |
|---------|------|------|------|
| Page Crawl & Pipeline | 3 | 2 | 0 |
| Heading Detection | 9 | 0 | 0 |
| Card Detection | 8 | 0 | 0 |
| Screenshot & Highlighting | 5 | 0 | 0 |
| Output Format | 9 | 0 | 0 |
| AI Classification | 9 | 0 | 0 |
| **Total** | **43** | **2** | **0** |

The 2 skipped scenarios require edge-case conditions (unreachable URL, page with zero findings) that don't apply to the live target page.

## How It Works (Under the Hood)

This tool uses the [Playwright MCP server](https://github.com/microsoft/playwright-mcp) to give an LLM direct browser control. The workflow is:

1. **You prompt** Claude Code (or another MCP-capable LLM) with a scan request
2. **The LLM reads** the Gherkin test scenarios in `tests/` to understand what to test
3. **Playwright MCP** provides browser automation tools (navigate, evaluate JS, take screenshots)
4. **The LLM executes** each scenario step by calling Playwright MCP tools — running JavaScript in the page to analyse DOM structure, computed styles, and visual patterns
5. **AI classification** happens naturally as the LLM interprets the deterministic findings
6. **Output** is saved as JSON, screenshots, and optionally a markdown/docx report

No traditional test runner is needed. The Gherkin files serve as executable specifications that the LLM interprets and runs directly.

## Design Principles

- **Never auto-fail WCAG** — this tool flags patterns, not violations
- **Explain, don't judge** — "This appears to function as a heading but is not marked up as one"
- **Deterministic first, AI second** — AI interprets what rules-based analysis found, it does not discover elements from scratch
- **Auditor trust > AI cleverness** — findings include selectors, XPaths, HTML snippets, and screenshots so auditors can independently verify

## Project Structure

```
di-test/
├── .mcp.json                              # Playwright MCP server configuration
├── di-web-accessibility-spec.md           # Detailed specification document
├── tests/
│   ├── page-crawl.feature                 # Page load and pipeline tests
│   ├── heading-detection.feature          # Heading detection tests
│   ├── card-detection.feature             # Card detection tests
│   ├── screenshot-and-highlighting.feature # Screenshot tests
│   ├── output-format.feature              # JSON output tests
│   └── ai-classification.feature          # AI classification tests
└── output/                                # Generated scan output
    ├── accessibility-scan-report.md       # Example report (Markdown)
    ├── accessibility-scan-report.docx     # Example report (Word)
    ├── findings.json                      # Example JSON findings
    └── screenshots/                       # Example screenshots
        ├── our-team-full.png
        ├── our-team-highlighted.png
        ├── our-team-item0.png
        ├── our-team-item1.png
        └── our-team-item2.png
```

## Future Scope

- Interactive/dynamic content detection (right-side panels, modals)
- Sticky/fixed-position content detection
- CSV export for spreadsheet workflows
- Web UI report viewer
- Integration with CWAC scan IDs
- Multi-page crawling
