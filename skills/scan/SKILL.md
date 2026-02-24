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

## Execution Steps

Follow these steps in order:

### Step 1: Start the scan

Use the `cwac_scan` MCP tool to start an accessibility scan against the URL(s) provided in `$ARGUMENTS`. This returns immediately with a scan ID.

### Step 2: Monitor progress

Poll `cwac_scan_status` until the scan completes. Show the user progress updates.

### Step 3: Present results

Once the scan completes, use `cwac_get_summary` and `cwac_get_results` to retrieve findings. Present a clear summary to the user covering:
- Total issues and severity breakdown
- Top violations by frequency
- Most affected pages

### Step 4: Offer report generation

After presenting the summary, ask the user if they would like to generate a report in Markdown and Word formats. If they say yes, use `cwac_generate_report` to generate the report and share the file paths.

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
| `cwac_scan` | Launches the scan subprocess |
| `cwac_scan_status` | Checks scan progress |
| `cwac_get_summary` | Retrieves summary of findings |
| `cwac_get_results` | Retrieves detailed findings |
| `cwac_generate_report` | Generates Markdown + Word reports |
