"""In-memory registry for tracking active and completed CWAC scans.

Each scan is identified by a UUID and tracked via a ScanRecord dataclass
that holds the subprocess handle, file paths, status, and captured output.
The registry provides methods to create, query, update, and clean up scans.
"""

import os
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from subprocess import Popen
from typing import Optional

from cwac_mcp import CWAC_PATH, PROJECT_ROOT


@dataclass
class ScanRecord:
    """Represents the state and metadata of a single CWAC scan."""

    process: Optional[Popen]
    config_path: str
    base_urls_dir: str
    results_dir: Optional[str]
    status: str  # "running", "complete", or "failed"
    start_time: datetime
    end_time: Optional[datetime]
    audit_name: str
    stdout_lines: list[str] = field(default_factory=list)
    stderr_lines: list[str] = field(default_factory=list)


class ScanRegistry:
    """Thread-safe in-memory registry mapping scan IDs to ScanRecords.

    Usage:
        registry = ScanRegistry()
        scan_id = registry.create(process, config_path, base_urls_dir, audit_name)
        registry.update_status(scan_id)
        record = registry.get(scan_id)
    """

    def __init__(self) -> None:
        self._scans: dict[str, ScanRecord] = {}

    def create(
        self,
        process: Popen,
        config_path: str,
        base_urls_dir: str,
        audit_name: str,
    ) -> str:
        """Register a new scan and return its unique ID.

        Args:
            process: The subprocess.Popen handle running CWAC.
            config_path: Path to the config JSON file used for this scan.
            base_urls_dir: Path to the temporary base_urls directory.
            audit_name: The audit_name value written into the config
                (before CWAC prepends its timestamp).

        Returns:
            A UUID4 string identifying this scan.
        """
        scan_id = str(uuid.uuid4())
        record = ScanRecord(
            process=process,
            config_path=config_path,
            base_urls_dir=base_urls_dir,
            results_dir=None,
            status="running",
            start_time=datetime.now(),
            end_time=None,
            audit_name=audit_name,
        )
        self._scans[scan_id] = record
        return scan_id

    def get(self, scan_id: str) -> Optional[ScanRecord]:
        """Retrieve a scan record by ID, or None if not found.

        Args:
            scan_id: The UUID of the scan to look up.

        Returns:
            The ScanRecord if it exists, otherwise None.
        """
        return self._scans.get(scan_id)

    def update_status(self, scan_id: str) -> None:
        """Poll the subprocess and update the scan's status accordingly.

        If the process has terminated (poll() returns a value), the status
        is set to "complete" (return code 0) or "failed" (non-zero).
        Any remaining stdout/stderr is captured.

        When the scan completes, the results directory is discovered by
        scanning /workspaces/cwac/results/ for directories whose name ends
        with the audit_name (CWAC prepends a timestamp like
        ``2026-02-24_14-30-00_audit_name``).

        Args:
            scan_id: The UUID of the scan to update.
        """
        record = self._scans.get(scan_id)
        if record is None:
            return

        # Nothing to do if the scan already finished.
        if record.status in ("complete", "failed"):
            return

        process = record.process
        if process is None:
            return

        return_code = process.poll()
        if return_code is None:
            # Still running -- capture any new output available so far.
            self._capture_output(record)
            return

        # Process has terminated.
        self._capture_output(record)
        record.end_time = datetime.now()

        if return_code == 0:
            record.status = "complete"
        else:
            record.status = "failed"

        # Discover the results directory.
        record.results_dir = self._discover_results_dir(record.audit_name)

    def register(self, scan_id: str, record: ScanRecord) -> None:
        """Register a scan with a specific ID.

        Used when the scan_id must match a previously generated value
        (e.g. the config filename includes the scan_id).

        Args:
            scan_id: The UUID to use as the registry key.
            record: The ScanRecord to store.
        """
        self._scans[scan_id] = record

    def list_all(self) -> dict[str, ScanRecord]:
        """Return a shallow copy of the entire scan registry.

        Returns:
            A dict mapping scan IDs to their ScanRecords.
        """
        return dict(self._scans)

    def cleanup(self, scan_id: str) -> None:
        """Remove temporary files created for a scan.

        Deletes the config file written to /workspaces/cwac/config/ and the
        base_urls subdirectory created for this scan. The scan record itself
        is *not* removed from the registry so its metadata remains queryable.

        Args:
            scan_id: The UUID of the scan whose temp files should be removed.
        """
        record = self._scans.get(scan_id)
        if record is None:
            return

        # Remove the temporary config file.
        config_full_path = os.path.join(CWAC_PATH, "config", record.config_path)
        if os.path.isfile(config_full_path):
            os.remove(config_full_path)

        # Remove the temporary base_urls directory.
        if os.path.isdir(record.base_urls_dir):
            shutil.rmtree(record.base_urls_dir)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _capture_output(record: ScanRecord) -> None:
        """Read any available stdout/stderr from the process without blocking.

        Args:
            record: The scan record whose process output should be captured.
        """
        process = record.process
        if process is None:
            return

        if process.stdout is not None:
            try:
                for line in process.stdout:
                    text = line if isinstance(line, str) else line.decode("utf-8", errors="replace")
                    record.stdout_lines.append(text.rstrip("\n"))
            except (ValueError, OSError):
                # Stream may already be closed.
                pass

        if process.stderr is not None:
            try:
                for line in process.stderr:
                    text = line if isinstance(line, str) else line.decode("utf-8", errors="replace")
                    record.stderr_lines.append(text.rstrip("\n"))
            except (ValueError, OSError):
                pass

    @staticmethod
    def _discover_results_dir(audit_name: str) -> Optional[str]:
        """Find the results directory that matches *audit_name*.

        Searches both CWAC results (``{CWAC_PATH}/results/``) and fallback
        output (``{PROJECT_ROOT}/output/``) for directories whose name ends
        with ``_{audit_name}``. Returns the most recently created match.

        Args:
            audit_name: The raw audit_name (without the timestamp prefix).

        Returns:
            The full path to the matching results directory, or None if no
            match is found.
        """
        suffix = f"_{audit_name}"
        candidates: list[tuple[float, str]] = []

        # Search both CWAC results and project output directories.
        results_roots = [
            os.path.join(CWAC_PATH, "results"),
            os.path.join(PROJECT_ROOT, "output"),
        ]

        for results_root in results_roots:
            if not os.path.isdir(results_root):
                continue
            try:
                for entry in os.scandir(results_root):
                    if entry.is_dir() and entry.name.endswith(suffix):
                        candidates.append((entry.stat().st_ctime, entry.path))
            except OSError:
                continue

        if not candidates:
            return None

        # Return the most recently created match.
        candidates.sort(key=lambda c: c[0], reverse=True)
        return candidates[0][1]
