# Visual Pattern Scanner — Technical Reference

The visual pattern scanner detects elements that *look like* headings or cards but may lack proper semantic markup. It uses LLM-driven browser automation with Gherkin test scenarios via Playwright MCP.

This tool **flags patterns, not violations**. It never auto-fails WCAG.

## Analysis Pipeline

The scanner runs a 6-layer analysis pipeline:

1. **DOM Analyzer** — Class-based heading detection (deterministic)
2. **Visual Analyzer** — Heading-like visual patterns (rules-based)
3. **Card Detector** — Card candidate structure detection (heuristic)
4. **AI Reasoning** — Classification + plain language explanation
5. **Screenshot Capture** — Full-page + cropped + highlight overlays
6. **Reporter** — Structured JSON + report compilation

## What It Detects

### Heading-like Content

| Method | What it finds |
|--------|--------------|
| Class-based (DOM) | Elements with class names containing h1-h6 |
| Visual analysis | Text visually styled as a heading (larger, bolder, isolated, spaced) |
| Non-semantic tags | Elements that look like headings but use `<div>`, `<span>`, `<p>` |

### Card-like Content

| Method | What it finds |
|--------|--------------|
| Link-wrapped groups | An `<a>` wrapping an image + heading + body text |
| Shared destinations | Multiple elements linking to the same URL within a container |
| Repeated patterns | Groups with matching DOM structure and CSS classes |
| Structural heuristics | Shared parent containers, vertical alignment, bounding box adjacency |

## How It Works

1. You prompt Claude Code with a scan request
2. The LLM reads the Gherkin test scenarios in `tests/`
3. Playwright MCP provides browser automation tools
4. The LLM executes each scenario step via Playwright MCP tool calls
5. AI classification interprets the deterministic findings
6. Output is saved as JSON, screenshots, and reports

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
| `confidence` | AI confidence score (0-1) |

## Test Scenarios

| File | Scenarios | Covers |
|------|-----------|--------|
| `page-crawl.feature` | 5 | Page load, text extraction, pipeline order, error handling |
| `heading-detection.feature` | 9 | Class-based and visual heading detection |
| `card-detection.feature` | 8 | Card structure detection and heuristics |
| `screenshot-and-highlighting.feature` | 5 | Screenshot capture, overlays, metadata |
| `output-format.feature` | 9 | JSON output structure and field validation |
| `ai-classification.feature` | 9 | AI input/output, confidence scoring, tone |

**45 scenarios total** | 43 pass, 2 skipped (edge-case conditions)
