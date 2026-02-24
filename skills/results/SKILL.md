# /di-test:results — Get Scan Results

Retrieve detailed accessibility findings from a completed scan.

## Usage

```
/di-test:results
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| scan_id | No | Specific scan ID (defaults to most recent) |
| audit_type | No | Filter by audit type (e.g., "axe_core_audit") |
| impact | No | Filter by impact level (critical, serious, moderate, minor) |
| limit | No | Maximum number of results to return |

## Examples

Get all results:
```
/di-test:results
```

Get critical issues only:
```
/di-test:results --impact critical
```

## Related MCP Tools

| Tool | Purpose |
|------|---------|
| `cwac_get_results` | Reads and filters CWAC result CSVs |
