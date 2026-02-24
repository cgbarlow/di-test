# /di-test:scan-status — Check Scan Progress

Check the status of a running or completed CWAC scan.

## Usage

```
/di-test:scan-status
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| scan_id | No | Specific scan ID to check (defaults to most recent) |

## Examples

Check the latest scan:
```
/di-test:scan-status
```

## Related MCP Tools

| Tool | Purpose |
|------|---------|
| `cwac_scan_status` | Polls scan subprocess for progress |
