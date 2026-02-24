"""Subprocess execution wrapper for CWAC."""

import subprocess
import sys
from cwac_mcp import CWAC_PATH


def start_cwac(config_filename: str) -> subprocess.Popen:
    """Start CWAC as a subprocess.

    Args:
        config_filename: Just the filename (e.g. "mcp_abc123.json"), not full path.

    Returns:
        Popen process handle.
    """
    process = subprocess.Popen(
        [sys.executable, "cwac.py", config_filename],
        cwd=CWAC_PATH,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return process


def start_report_export(results_folder_name: str) -> subprocess.Popen:
    """Run export_report_data.py as a subprocess.

    Args:
        results_folder_name: The name of the results folder (not full path).

    Returns:
        Popen process handle.
    """
    process = subprocess.Popen(
        [sys.executable, "export_report_data.py", results_folder_name],
        cwd=CWAC_PATH,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return process
