"""CWAC MCP Server - MCP wrapper for the Centralised Web Accessibility Checker."""

import os


def _discover_cwac_path() -> str:
    """Discover the CWAC installation path.

    Discovery chain:
    1. CWAC_PATH environment variable
    2. Sibling directory (../cwac relative to this project)
    3. /workspaces/cwac (Codespace default)
    4. ~/.local/share/di-test/cwac (plugin auto-install location)

    Returns:
        Absolute path to the CWAC installation directory.
    """
    # 1. Environment variable
    env_path = os.environ.get("CWAC_PATH")
    if env_path and os.path.isdir(env_path):
        return os.path.abspath(env_path)

    # 2. Sibling directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sibling_path = os.path.join(os.path.dirname(project_root), "cwac")
    if os.path.isdir(sibling_path) and os.path.isfile(os.path.join(sibling_path, "cwac.py")):
        return os.path.abspath(sibling_path)

    # 3. Codespace default
    if os.path.isdir("/workspaces/cwac") and os.path.isfile("/workspaces/cwac/cwac.py"):
        return "/workspaces/cwac"

    # 4. Plugin auto-install location
    plugin_install = os.path.join(os.path.expanduser("~"), ".local", "share", "di-test", "cwac")
    if os.path.isdir(plugin_install) and os.path.isfile(os.path.join(plugin_install, "cwac.py")):
        return os.path.abspath(plugin_install)

    # Fallback (will fail at runtime with a clear error)
    return "/workspaces/cwac"


CWAC_PATH = _discover_cwac_path()
