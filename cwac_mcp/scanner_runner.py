"""Subprocess launcher for axe_scanner.py (fallback mode).

Analogous to cwac_runner.py but launches the Playwright-based axe-core
scanner instead of CWAC.
"""

import subprocess
import sys


def start_scanner(config_path: str) -> subprocess.Popen:
    """Launch axe_scanner.py as a subprocess.

    Args:
        config_path: Absolute path to the config JSON file.

    Returns:
        Popen process handle.
    """
    process = subprocess.Popen(
        [sys.executable, "-m", "cwac_mcp.axe_scanner", config_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return process
