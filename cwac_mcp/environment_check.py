"""Detect scan mode at startup: 'cwac' (full suite) or 'axe-only' (fallback).

The environment check determines which scanning engine is available by probing
for CWAC dependencies (chromedriver, selenium) and fallback dependencies
(Playwright, axe-core). The result is used by server.py to route scan requests.
"""

import importlib
import os
import platform
import struct
import subprocess

from cwac_mcp import _discover_cwac_path


def check_environment() -> dict:
    """Detect the available scan mode.

    Returns:
        A dict with:
            mode: "cwac", "axe-only", or "unavailable"
            cwac_available: bool
            cwac_path: str or None
            chromedriver_ok: bool
            playwright_available: bool
            axe_core_available: bool
            message: str (human-readable summary)
    """
    cwac_path = _discover_cwac_path()
    cwac_exists = cwac_path is not None and os.path.isfile(os.path.join(cwac_path, "cwac.py"))

    chromedriver_ok = _check_chromedriver(cwac_path) if cwac_exists else False
    selenium_ok = _check_importable("selenium")
    playwright_ok = _check_importable("playwright")
    axe_core_ok = _check_axe_core()

    cwac_available = cwac_exists and chromedriver_ok and selenium_ok

    result = {
        "cwac_available": cwac_available,
        "cwac_path": cwac_path if cwac_exists else None,
        "chromedriver_ok": chromedriver_ok,
        "playwright_available": playwright_ok,
        "axe_core_available": axe_core_ok,
    }

    if cwac_available:
        result["mode"] = "cwac"
        result["message"] = (
            f"Full mode (CWAC): All audit plugins available. "
            f"CWAC found at {cwac_path}."
        )
    elif playwright_ok and axe_core_ok:
        result["mode"] = "axe-only"
        reasons = []
        if not cwac_exists:
            reasons.append("CWAC not found")
        elif not chromedriver_ok:
            reasons.append("chromedriver incompatible with this architecture")
        elif not selenium_ok:
            reasons.append("selenium not installed")
        reason_str = "; ".join(reasons) if reasons else "CWAC unavailable"
        result["message"] = (
            f"Fallback mode (axe-core only): {reason_str}. "
            f"Running axe-core accessibility scanning via Playwright."
        )
    else:
        result["mode"] = "unavailable"
        missing = []
        if not cwac_available:
            missing.append("CWAC (full suite)")
        if not playwright_ok:
            missing.append("Playwright")
        if not axe_core_ok:
            missing.append("axe-core")
        result["message"] = (
            f"No scanning mode available. Missing: {', '.join(missing)}. "
            f"Run scripts/install-deps.sh to install dependencies."
        )

    return result


def _check_chromedriver(cwac_path: str | None) -> bool:
    """Check if chromedriver exists and matches the host architecture.

    Args:
        cwac_path: Path to the CWAC installation directory.

    Returns:
        True if chromedriver is found and compatible with the host architecture.
    """
    if cwac_path is None or not os.path.isdir(cwac_path):
        return False

    # CWAC stores chromedriver in node_modules or alongside its files.
    # Check common locations.
    chromedriver_paths = [
        os.path.join(cwac_path, "node_modules", "chromedriver", "lib", "chromedriver", "chromedriver"),
        os.path.join(cwac_path, "chromedriver"),
    ]

    chromedriver = None
    for path in chromedriver_paths:
        if os.path.isfile(path):
            chromedriver = path
            break

    if chromedriver is None:
        return False

    # Check architecture compatibility.
    host_machine = platform.machine().lower()

    try:
        with open(chromedriver, "rb") as f:
            magic = f.read(4)

        # ELF binary (Linux)
        if magic == b"\x7fELF":
            with open(chromedriver, "rb") as f:
                f.seek(18)  # e_machine offset in ELF header
                e_machine = struct.unpack("<H", f.read(2))[0]
            # 62 = x86-64, 183 = AArch64
            if host_machine in ("x86_64", "amd64"):
                return e_machine == 62
            elif host_machine in ("aarch64", "arm64"):
                return e_machine == 183
            return False

        # Mach-O binary (macOS)
        if magic in (b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe"):
            with open(chromedriver, "rb") as f:
                f.seek(4)  # cputype offset
                cputype = struct.unpack("<I", f.read(4))[0]
            # 0x01000007 = x86_64, 0x0100000c = ARM64
            if host_machine in ("x86_64", "amd64"):
                return cputype == 0x01000007
            elif host_machine in ("aarch64", "arm64"):
                return cputype == 0x0100000C
            return False

    except (OSError, struct.error):
        pass

    # Fallback: try running `file` command
    try:
        output = subprocess.check_output(
            ["file", chromedriver], text=True, timeout=5
        )
        if host_machine in ("x86_64", "amd64"):
            return "x86-64" in output or "x86_64" in output
        elif host_machine in ("aarch64", "arm64"):
            return "aarch64" in output or "arm64" in output
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    return False


def _check_importable(module_name: str) -> bool:
    """Check if a Python module can be imported.

    Args:
        module_name: The module name to check.

    Returns:
        True if the module is importable.
    """
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def _check_axe_core() -> bool:
    """Check if axe-core JS is available in node_modules.

    Returns:
        True if axe.min.js exists in the expected location.
    """
    from cwac_mcp import PROJECT_ROOT
    axe_path = os.path.join(PROJECT_ROOT, "node_modules", "axe-core", "axe.min.js")
    return os.path.isfile(axe_path)
