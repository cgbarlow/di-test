"""CWAC MCP Server - MCP wrapper for the Centralised Web Accessibility Checker."""

import os


def _discover_cwac_path() -> str:
    """Discover the CWAC installation path.

    Discovery chain:
    1. CWAC_PATH environment variable
    2. Sibling directory (../cwac relative to this project)
    3. Default fallback: /workspaces/cwac

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

    # 3. Default fallback
    return "/workspaces/cwac"


CWAC_PATH = _discover_cwac_path()
