# /di-test:report — Generate Report

Generate a formatted accessibility report in Markdown and DOCX formats.

## Usage

```
/di-test:report
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| scan_id | No | Specific scan ID (defaults to most recent) |
| format | No | Output format: "both" (default), "md", "docx" |
| template | No | Template: "cwac_scan_report" (default), "cwac_summary_report" |

## Examples

Generate both formats:
```
/di-test:report
```

Generate markdown only:
```
/di-test:report --format md
```

## Output

Reports are saved to `./output/` with filenames:
- `{audit_name}_{timestamp}_report.md`
- `{audit_name}_{timestamp}_report.docx`

## Related MCP Tools

| Tool | Purpose |
|------|---------|
| `cwac_get_results` | Reads results for report content |
| `cwac_get_summary` | Provides summary data for reports |
