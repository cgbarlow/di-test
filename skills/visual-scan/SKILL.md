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
- **Government identity**: Official branding, contact info, copyright, and privacy links
- **CAPTCHA detection**: CAPTCHA implementations that may be accessibility barriers
- **Carousel detection**: Carousels/sliders and whether they have pause controls
- **Disclosure widgets**: Show/hide toggles and accordions with ARIA checks
- **Heading text quality**: Vague, long, duplicated, or hierarchy-skipping headings
- **Link quality**: Non-descriptive link text, new window warnings, duplicate links
- **Skip links**: Presence and functionality of skip navigation links
- **Modal dialogs**: Dialog patterns and their accessibility implementation
- **Page titles**: Missing, empty, or generic page titles
- **Print stylesheet reminder**: Reminder to check print output

## Related MCP Tools

| Tool | Purpose |
|------|---------|
| Playwright MCP | Browser automation for visual analysis |
