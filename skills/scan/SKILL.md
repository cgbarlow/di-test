# /di-test:scan — Start Accessibility Scan

Start a CWAC accessibility scan against one or more URLs.

## Usage

```
/di-test:scan https://example.govt.nz
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| URLs | Yes | One or more URLs to scan |
| audit_name | No | Human-readable name for the audit (default: "mcp_scan") |
| plugins | No | Enable/disable specific audit plugins |
| max_links | No | Maximum pages to crawl per domain |

## Examples

Scan a single site:
```
/di-test:scan https://www.example.govt.nz
```

Scan with custom settings:
```
/di-test:scan https://www.example.govt.nz --name "Q1 Audit" --max-links 20
```

## Related MCP Tools

| Tool | Purpose |
|------|---------|
| `cwac_scan` | Launches the CWAC subprocess scan |
