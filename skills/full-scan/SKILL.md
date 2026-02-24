# /di-test:full-scan — Combined Accessibility Scan

Run both a CWAC compliance scan and a visual pattern scan against a URL, then generate reports for both.

## Usage

```
/di-test:full-scan https://example.govt.nz
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| URL | Yes | The URL to scan |
| max_links | No | Maximum pages to crawl per domain (CWAC only, default: 10) |

## What It Does

This command runs two scans in parallel and generates a combined summary:

1. **CWAC scan** — WCAG compliance checking (axe-core violations, language readability, reflow issues)
2. **Visual pattern scan** — Detects heading-like and card-like content that may lack semantic markup
3. **Reports** — Generates reports for both scans in Markdown and Word formats

## Execution Steps

Follow these steps in order:

### Step 1: Start the CWAC scan (non-blocking)

Use the `cwac_scan` MCP tool to start a CWAC accessibility scan against the URL provided in `$ARGUMENTS`. This returns immediately with a scan ID. Use default settings unless the user specified otherwise.

### Step 2: Run the visual pattern scan

While the CWAC scan runs in the background, run the visual pattern scan using Playwright MCP. Follow the Gherkin test scenarios in `tests/` to execute the 6-layer analysis pipeline (DOM analysis, visual analysis, card detection, AI classification, screenshots, reporting). Save output to `./output/`.

### Step 3: Check CWAC scan completion

Use `cwac_scan_status` to check whether the CWAC scan has finished. If still running, wait and check again. Once complete, retrieve results using `cwac_get_summary` and `cwac_get_results`.

### Step 4: Generate reports

Generate reports for both scans:
- Use `cwac_generate_report` for the CWAC scan report (Markdown + Word)
- The visual scan report should already be generated from Step 2

### Step 5: Present combined summary

Present a single combined summary to the user covering:
- **CWAC findings** — Total issues, critical/serious counts, top violations
- **Visual pattern findings** — Heading-like and card-like candidates found
- **Report locations** — Paths to all generated report files

## Examples

Full scan of a single page:
```
/di-test:full-scan https://www.example.govt.nz
```

Full scan with deeper crawl:
```
/di-test:full-scan https://www.example.govt.nz --max-links 50
```
