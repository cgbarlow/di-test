# /di-test:visual-scan — Visual Pattern Scan

Run the visual pattern scanner against a URL using Playwright MCP to detect heading-like and card-like content that may lack proper semantic markup.

## Usage

```
/di-test:visual-scan https://example.com/page
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| URL | Yes | The URL to scan for visual accessibility patterns |
| report | No | Generate a report after scanning (default: true) |

## Examples

Full visual scan with report:
```
/di-test:visual-scan https://www.fincap.org.nz/our-team/
```

## What It Detects

- **Heading-like content**: Elements that look like headings but aren't `<h1>`-`<h6>`
- **Card-like content**: Repeated content groups functioning as navigation cards

## Related MCP Tools

| Tool | Purpose |
|------|---------|
| Playwright MCP | Browser automation for visual analysis |
