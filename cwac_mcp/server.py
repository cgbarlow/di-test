"""CWAC MCP Server -- exposes CWAC accessibility scanning via MCP tools.

This module defines a FastMCP server with six tools that allow an LLM to
launch CWAC accessibility scans, monitor their progress, read results,
and generate reports.

Supports two modes:
- "cwac" (full suite): Uses CWAC subprocess for all audit plugins
- "axe-only" (fallback): Uses Playwright + axe-core when CWAC is unavailable

Usage:
    python -m cwac_mcp.server
    # or
    python cwac_mcp/server.py
"""

import os
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from cwac_mcp.config_builder import build_config, build_axe_config
from cwac_mcp.cwac_runner import start_cwac, start_report_export
from cwac_mcp.environment_check import check_environment
from cwac_mcp.result_reader import get_summary, list_scan_results, read_results
from cwac_mcp.scan_registry import ScanRegistry

# ---------------------------------------------------------------------------
# Environment detection
# ---------------------------------------------------------------------------

_env = check_environment()
SCAN_MODE = _env["mode"]

# ---------------------------------------------------------------------------
# Global instances
# ---------------------------------------------------------------------------

mcp = FastMCP("cwac")
registry = ScanRegistry()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def cwac_scan(
    urls: list[str],
    audit_name: str = "mcp_scan",
    plugins: dict[str, bool] | None = None,
    max_links_per_domain: int | None = None,
    viewport_sizes: dict[str, dict[str, int]] | None = None,
) -> dict:
    """Launch a CWAC accessibility scan against one or more URLs.

    This starts an asynchronous scan subprocess. Use cwac_scan_status to
    monitor progress, and cwac_get_results or cwac_get_summary to retrieve
    findings once the scan completes.

    Args:
        urls: One or more URLs to scan for accessibility issues. Each URL
            will be crawled up to max_links_per_domain pages deep.
        audit_name: A human-readable name for this audit. Used to identify
            the results directory. Defaults to "mcp_scan".
        plugins: Optional dict mapping plugin keys to enabled/disabled.
            For example: {"axe_core_audit": true, "language_audit": false}.
            Only the listed plugins are toggled; others keep their defaults.
            Available plugin keys include: axe_core_audit, language_audit,
            readability_audit, broken_link_audit, spell_check_audit,
            seo_audit, meta_audit, link_text_audit, colour_contrast_audit.
            Note: In axe-only fallback mode, plugin toggles are ignored
            (only axe-core runs).
        max_links_per_domain: Maximum number of pages to crawl per domain.
            If not set, the CWAC default is used.
        viewport_sizes: Optional viewport size overrides as a dict mapping
            size names to {width, height} dicts. For example:
            {"small": {"width": 320, "height": 480}}.

    Returns:
        A dict with "scan_id" and "status" on success, or "error" on failure.
    """
    try:
        import uuid

        scan_id = str(uuid.uuid4())

        if SCAN_MODE == "cwac":
            # Full CWAC mode: build CWAC config and launch CWAC subprocess.
            config_filename, base_urls_dir = build_config(
                scan_id=scan_id,
                audit_name=audit_name,
                urls=urls,
                plugins=plugins,
                max_links_per_domain=max_links_per_domain,
                viewport_sizes=viewport_sizes,
            )
            process = start_cwac(config_filename)

            from cwac_mcp.scan_registry import ScanRecord

            record = ScanRecord(
                process=process,
                config_path=config_filename,
                base_urls_dir=base_urls_dir,
                results_dir=None,
                status="running",
                start_time=datetime.now(),
                end_time=None,
                audit_name=audit_name,
            )
        else:
            # Fallback axe-only mode: build axe config and launch scanner.
            from cwac_mcp.scanner_runner import start_scanner

            config_path, output_dir = build_axe_config(
                scan_id=scan_id,
                audit_name=audit_name,
                urls=urls,
                max_links_per_domain=max_links_per_domain,
                viewport_sizes=viewport_sizes,
            )
            process = start_scanner(config_path)

            from cwac_mcp.scan_registry import ScanRecord

            record = ScanRecord(
                process=process,
                config_path=config_path,
                base_urls_dir="",  # No base_urls dir in fallback mode
                results_dir=output_dir,  # Known upfront in fallback mode
                status="running",
                start_time=datetime.now(),
                end_time=None,
                audit_name=audit_name,
            )

        registry.register(scan_id, record)

        return {
            "scan_id": scan_id,
            "status": "running",
            "scan_mode": SCAN_MODE,
            "message": f"Scan started for {len(urls)} URL(s) with audit name '{audit_name}' ({SCAN_MODE} mode).",
        }
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def cwac_scan_status(scan_id: str) -> dict:
    """Check the current status of a CWAC scan.

    Polls the subprocess to determine whether the scan is still running,
    has completed successfully, or has failed. Returns timing information
    and the most recent stdout lines for progress monitoring.

    Args:
        scan_id: The unique identifier returned by cwac_scan.

    Returns:
        A dict containing status, elapsed time, and recent output lines.
        Returns an error dict if the scan_id is not found.
    """
    try:
        registry.update_status(scan_id)
        record = registry.get(scan_id)

        if record is None:
            return {"error": f"Scan '{scan_id}' not found."}

        now = datetime.now()
        elapsed = (record.end_time or now) - record.start_time
        elapsed_seconds = int(elapsed.total_seconds())

        result: dict = {
            "scan_id": scan_id,
            "status": record.status,
            "scan_mode": SCAN_MODE,
            "elapsed_seconds": elapsed_seconds,
            "start_time": record.start_time.isoformat(),
        }

        if record.end_time:
            result["end_time"] = record.end_time.isoformat()

        if record.results_dir:
            result["results_dir"] = record.results_dir

        # Include the last 20 stdout lines for progress visibility.
        if record.stdout_lines:
            result["recent_output"] = record.stdout_lines[-20:]

        # Include stderr if the scan failed.
        if record.status == "failed" and record.stderr_lines:
            result["error_output"] = record.stderr_lines[-20:]

        return result
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def cwac_get_results(
    scan_id: str,
    audit_type: str | None = None,
    impact: str | None = None,
    limit: int | None = None,
) -> dict:
    """Retrieve detailed accessibility findings from a completed scan.

    Returns individual issue rows from CWAC's result CSVs. You can filter
    by audit type, impact level, and limit the number of rows returned.

    Args:
        scan_id: The unique identifier returned by cwac_scan.
        audit_type: Filter results to a specific audit type. For example:
            "axe_core_audit", "language_audit", "readability_audit",
            "broken_link_audit", "spell_check_audit", "seo_audit",
            "meta_audit", "link_text_audit", "colour_contrast_audit".
            If not provided, results from all audit types are returned.
        impact: Filter axe-core results by impact level. One of:
            "critical", "serious", "moderate", "minor".
            Only applies to audit types that have an impact column.
        limit: Maximum number of result rows to return. Useful for
            getting a sample without overwhelming context.

    Returns:
        A dict with "results" (list of issue dicts) and "count" on success.
        Returns an error dict if the scan is not found or not yet complete.
    """
    try:
        record = registry.get(scan_id)
        if record is None:
            return {"error": f"Scan '{scan_id}' not found."}

        # Refresh status in case the scan just finished.
        registry.update_status(scan_id)
        record = registry.get(scan_id)

        if record.status == "running":
            return {
                "error": "Scan is still running. Use cwac_scan_status to monitor progress.",
                "status": "running",
            }

        if record.status == "failed":
            return {
                "error": "Scan failed. Check cwac_scan_status for error details.",
                "status": "failed",
            }

        if not record.results_dir:
            return {"error": "Scan completed but no results directory was found."}

        results = read_results(
            results_dir=record.results_dir,
            audit_type=audit_type,
            impact=impact,
            limit=limit,
        )

        return {
            "scan_id": scan_id,
            "scan_mode": SCAN_MODE,
            "results_dir": record.results_dir,
            "count": len(results),
            "results": results,
        }
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def cwac_get_summary(scan_id: str) -> dict:
    """Get a high-level summary of accessibility findings from a completed scan.

    Returns aggregated counts by audit type, axe-core impact breakdown,
    and top violations. This is useful for getting an overview before
    diving into detailed results with cwac_get_results.

    Args:
        scan_id: The unique identifier returned by cwac_scan.

    Returns:
        A dict with total issue counts, per-audit-type breakdowns,
        and axe impact distribution. Returns an error dict if the scan
        is not found or not yet complete.
    """
    try:
        record = registry.get(scan_id)
        if record is None:
            return {"error": f"Scan '{scan_id}' not found."}

        # Refresh status in case the scan just finished.
        registry.update_status(scan_id)
        record = registry.get(scan_id)

        if record.status == "running":
            return {
                "error": "Scan is still running. Use cwac_scan_status to monitor progress.",
                "status": "running",
            }

        if record.status == "failed":
            return {
                "error": "Scan failed. Check cwac_scan_status for error details.",
                "status": "failed",
            }

        if not record.results_dir:
            return {"error": "Scan completed but no results directory was found."}

        summary = get_summary(record.results_dir)
        summary["scan_id"] = scan_id
        summary["scan_mode"] = SCAN_MODE
        summary["results_dir"] = record.results_dir

        return summary
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def cwac_list_scans() -> dict:
    """List all available CWAC scan result directories.

    Returns both actively tracked scans from this session and any
    historical result directories found on disk under the CWAC results
    folder and the project output folder. Useful for discovering past
    scans whose results can still be queried.

    Returns:
        A dict with "active_scans" (scans tracked in this session)
        and "result_directories" (all result folders on disk).
    """
    try:
        # Active scans from this session's registry.
        active: list[dict] = []
        for scan_id, record in registry.list_all().items():
            registry.update_status(scan_id)
            record = registry.get(scan_id)
            active.append({
                "scan_id": scan_id,
                "audit_name": record.audit_name,
                "status": record.status,
                "start_time": record.start_time.isoformat(),
                "end_time": record.end_time.isoformat() if record.end_time else None,
                "results_dir": record.results_dir,
            })

        # All result directories on disk.
        result_dirs = list_scan_results()

        return {
            "scan_mode": SCAN_MODE,
            "active_scans": active,
            "result_directories": result_dirs,
        }
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def cwac_generate_report(scan_id: str) -> dict:
    """Generate a report for a completed scan.

    In CWAC mode, runs CWAC's export_report_data.py script. In axe-only
    fallback mode, generates a Markdown + DOCX report from the CSV results.

    Args:
        scan_id: The unique identifier returned by cwac_scan.

    Returns:
        A dict with the report output and paths on success.
        Returns an error dict if the scan is not found, not complete,
        or if report generation fails.
    """
    try:
        record = registry.get(scan_id)
        if record is None:
            return {"error": f"Scan '{scan_id}' not found."}

        # Refresh status in case the scan just finished.
        registry.update_status(scan_id)
        record = registry.get(scan_id)

        if record.status == "running":
            return {
                "error": "Scan is still running. Wait for it to complete before generating a report.",
                "status": "running",
            }

        if record.status == "failed":
            return {
                "error": "Scan failed. Cannot generate a report for a failed scan.",
                "status": "failed",
            }

        if not record.results_dir:
            return {"error": "Scan completed but no results directory was found."}

        if SCAN_MODE == "cwac":
            # CWAC mode: use CWAC's export script.
            results_folder_name = os.path.basename(record.results_dir)
            process = start_report_export(results_folder_name)
            stdout, stderr = process.communicate(timeout=300)

            if process.returncode != 0:
                return {
                    "error": "Report generation failed.",
                    "return_code": process.returncode,
                    "stderr": stderr.strip() if stderr else None,
                    "stdout": stdout.strip() if stdout else None,
                }

            from cwac_mcp import CWAC_PATH

            reports_dir = os.path.join(CWAC_PATH, "reports", results_folder_name)
            report_files: list[str] = []
            if os.path.isdir(reports_dir):
                for entry in os.scandir(reports_dir):
                    if entry.is_file():
                        report_files.append(entry.path)

            return {
                "scan_id": scan_id,
                "scan_mode": SCAN_MODE,
                "results_dir": record.results_dir,
                "report_files": sorted(report_files),
                "stdout": stdout.strip() if stdout else None,
                "message": "Report generated successfully.",
            }
        else:
            # Fallback mode: generate reports from CSV using report_generator.
            from cwac_mcp.report_generator import generate_reports

            summary = get_summary(record.results_dir)
            results = read_results(record.results_dir)

            context = {
                "audit_name": record.audit_name,
                "scan_date": record.start_time.isoformat(),
                "base_url": results[0]["base_url"] if results else "Unknown",
                "pages_scanned": len(set(r.get("url", "") for r in results)),
                "total_issues": summary.get("total_issues", 0),
                "summary": summary,
                "results": results,
                "generated_at": datetime.now().isoformat(),
                "scan_mode": SCAN_MODE,
            }

            output_dir = record.results_dir
            reports = generate_reports(
                template_name="cwac_scan_report",
                context=context,
                output_dir=output_dir,
                audit_name=record.audit_name,
            )

            report_files = [v for v in reports.values() if v]

            return {
                "scan_id": scan_id,
                "scan_mode": SCAN_MODE,
                "results_dir": record.results_dir,
                "report_files": report_files,
                "message": "Report generated successfully (axe-only mode).",
            }
    except TimeoutError:
        return {"error": "Report generation timed out after 300 seconds."}
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
