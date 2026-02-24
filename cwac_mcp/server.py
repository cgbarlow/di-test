"""CWAC MCP Server -- exposes CWAC accessibility scanning via MCP tools.

This module defines a FastMCP server with six tools that allow an LLM to
launch CWAC accessibility scans, monitor their progress, read results,
and generate reports.

Usage:
    python -m cwac_mcp.server
    # or
    python cwac_mcp/server.py
"""

import os
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from cwac_mcp.config_builder import build_config
from cwac_mcp.cwac_runner import start_cwac, start_report_export
from cwac_mcp.result_reader import get_summary, list_scan_results, read_results
from cwac_mcp.scan_registry import ScanRegistry

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
        max_links_per_domain: Maximum number of pages to crawl per domain.
            If not set, the CWAC default is used.
        viewport_sizes: Optional viewport size overrides as a dict mapping
            size names to {width, height} dicts. For example:
            {"small": {"width": 320, "height": 480}}.

    Returns:
        A dict with "scan_id" and "status" on success, or "error" on failure.
    """
    try:
        # Build config and base_urls files on disk.
        # We need a scan_id first for the config filename, but we also need
        # the process for registry.create().  Use a temporary UUID for the
        # config filename, then register with the same id.
        import uuid

        scan_id = str(uuid.uuid4())
        config_filename, base_urls_dir = build_config(
            scan_id=scan_id,
            audit_name=audit_name,
            urls=urls,
            plugins=plugins,
            max_links_per_domain=max_links_per_domain,
            viewport_sizes=viewport_sizes,
        )

        # Launch CWAC subprocess.
        process = start_cwac(config_filename)

        # Register with the same scan_id used for config filenames.
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
        registry.register(scan_id, record)

        return {
            "scan_id": scan_id,
            "status": "running",
            "message": f"Scan started for {len(urls)} URL(s) with audit name '{audit_name}'.",
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
        summary["results_dir"] = record.results_dir

        return summary
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def cwac_list_scans() -> dict:
    """List all available CWAC scan result directories.

    Returns both actively tracked scans from this session and any
    historical result directories found on disk under the CWAC results
    folder. Useful for discovering past scans whose results can still
    be queried.

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
            "active_scans": active,
            "result_directories": result_dirs,
        }
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def cwac_generate_report(scan_id: str) -> dict:
    """Generate an HTML/JSON export report for a completed scan.

    Runs CWAC's export_report_data.py script on the scan's results
    directory to produce report files. This operation blocks until
    the report generation completes (typically a few seconds).

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

        # Extract just the folder name from the full results path.
        results_folder_name = os.path.basename(record.results_dir)

        # Run export_report_data.py synchronously (it's typically quick).
        process = start_report_export(results_folder_name)
        stdout, stderr = process.communicate(timeout=300)

        if process.returncode != 0:
            return {
                "error": "Report generation failed.",
                "return_code": process.returncode,
                "stderr": stderr.strip() if stderr else None,
                "stdout": stdout.strip() if stdout else None,
            }

        # CWAC writes reports to ./reports/{folder_name}/ (relative to CWAC_PATH).
        from cwac_mcp import CWAC_PATH

        reports_dir = os.path.join(CWAC_PATH, "reports", results_folder_name)
        report_files: list[str] = []
        if os.path.isdir(reports_dir):
            for entry in os.scandir(reports_dir):
                if entry.is_file():
                    report_files.append(entry.path)

        return {
            "scan_id": scan_id,
            "results_dir": record.results_dir,
            "report_files": sorted(report_files),
            "stdout": stdout.strip() if stdout else None,
            "message": "Report generated successfully.",
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
