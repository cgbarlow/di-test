"""Builds CWAC configuration files from MCP tool parameters.

This module reads the default CWAC config, applies overrides requested by the
caller (audit name, plugin toggles, viewport sizes, etc.), writes a new config
JSON into /workspaces/cwac/config/, prepares a base_urls CSV, and returns the
paths so a scan can be launched.
"""

import json
import os
import re
from datetime import datetime
from typing import Optional

from cwac_mcp import CWAC_PATH, PROJECT_ROOT

# Paths relative to CWAC_PATH.
_DEFAULT_CONFIG = os.path.join(CWAC_PATH, "config", "config_default.json")
_CONFIG_DIR = os.path.join(CWAC_PATH, "config")
_BASE_URLS_VISIT_DIR = os.path.join(CWAC_PATH, "base_urls", "visit")


def _sanitize_audit_name(name: str) -> str:
    """Sanitize an audit name for use in filenames and folder names.

    Mirrors the logic in CWAC's ``config.py``:
    * Strip leading/trailing whitespace.
    * Replace any character that is not alphanumeric, underscore, hyphen, or
      dot with an underscore.
    * Collapse consecutive underscores.
    * Truncate to 50 characters.

    Args:
        name: The raw audit name string.

    Returns:
        A sanitized string safe for use in file/directory names.
    """
    sanitized = name.strip()
    sanitized = re.sub(r"[^a-zA-Z0-9_\-.]", "_", sanitized)
    sanitized = re.sub(r"_+", "_", sanitized)
    sanitized = sanitized[:50]
    return sanitized


def build_config(
    scan_id: str,
    audit_name: str,
    urls: list[str],
    plugins: Optional[dict[str, bool]] = None,
    max_links_per_domain: Optional[int] = None,
    viewport_sizes: Optional[dict[str, dict[str, int]]] = None,
) -> tuple[str, str]:
    """Build a CWAC config file and base-URLs CSV for a single scan.

    The function performs the following steps:

    1. Read ``config_default.json`` as the base configuration.
    2. Sanitize and set the ``audit_name``.
    3. Optionally toggle audit plugins on/off.
    4. Optionally override ``max_links_per_domain``.
    5. Optionally override ``viewport_sizes``.
    6. Point ``base_urls_visit_path`` at a scan-specific subdirectory.
    7. Write the config to ``/workspaces/cwac/config/mcp_{scan_id}.json``.
    8. Create the base-URLs directory and write the URLs CSV.

    Args:
        scan_id: Unique identifier for this scan (UUID4 string).
        audit_name: Human-readable name for the audit.
        urls: List of URLs to scan.
        plugins: Optional mapping of plugin key to enabled flag, e.g.
            ``{"axe_core_audit": True, "language_audit": False}``.
            Only the ``enabled`` field of matching plugins is changed;
            other plugin settings are left at their defaults.
        max_links_per_domain: Optional override for the crawl depth.
        viewport_sizes: Optional override for viewport size definitions,
            e.g. ``{"small": {"width": 320, "height": 450}}``.

    Returns:
        A tuple of ``(config_filename, base_urls_dir_path)`` where
        *config_filename* is just the filename (e.g. ``mcp_{scan_id}.json``)
        suitable for passing directly to ``cwac.py``, and
        *base_urls_dir_path* is the absolute path to the temporary base-URLs
        directory.

    Raises:
        FileNotFoundError: If the default config file does not exist.
        ValueError: If *urls* is empty or *audit_name* is blank after
            sanitization.
    """
    # ------------------------------------------------------------------ #
    # 1. Load default config
    # ------------------------------------------------------------------ #
    with open(_DEFAULT_CONFIG, "r", encoding="utf-8-sig") as fh:
        config: dict = json.load(fh)

    # ------------------------------------------------------------------ #
    # 2. Sanitize and set audit_name
    # ------------------------------------------------------------------ #
    safe_name = _sanitize_audit_name(audit_name)
    if not safe_name:
        raise ValueError("audit_name is empty after sanitization")
    config["audit_name"] = safe_name

    # ------------------------------------------------------------------ #
    # 3. Toggle plugins
    # ------------------------------------------------------------------ #
    if plugins:
        audit_plugins: dict = config.get("audit_plugins", {})
        for plugin_key, enabled in plugins.items():
            if plugin_key in audit_plugins:
                audit_plugins[plugin_key]["enabled"] = enabled
        config["audit_plugins"] = audit_plugins

    # ------------------------------------------------------------------ #
    # 4. Override max_links_per_domain
    # ------------------------------------------------------------------ #
    if max_links_per_domain is not None:
        config["max_links_per_domain"] = max_links_per_domain

    # ------------------------------------------------------------------ #
    # 5. Override viewport_sizes
    # ------------------------------------------------------------------ #
    if viewport_sizes is not None:
        config["viewport_sizes"] = viewport_sizes

    # ------------------------------------------------------------------ #
    # 6. Set base_urls_visit_path to scan-specific subdirectory
    # ------------------------------------------------------------------ #
    base_urls_subdir = f"mcp_{scan_id}"
    # CWAC resolves this relative to its own working directory.
    config["base_urls_visit_path"] = f"./base_urls/visit/{base_urls_subdir}/"

    # ------------------------------------------------------------------ #
    # 7. Write config JSON
    # ------------------------------------------------------------------ #
    config_filename = f"mcp_{scan_id}.json"
    config_path = os.path.join(_CONFIG_DIR, config_filename)
    with open(config_path, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=4)

    # ------------------------------------------------------------------ #
    # 8. Create base-URLs directory and write CSV
    # ------------------------------------------------------------------ #
    base_urls_dir = os.path.join(_BASE_URLS_VISIT_DIR, base_urls_subdir)
    os.makedirs(base_urls_dir, exist_ok=True)

    if not urls:
        raise ValueError("At least one URL must be provided")

    csv_path = os.path.join(base_urls_dir, "urls.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        fh.write("organisation,url,sector\n")
        for url in urls:
            # Escape commas in the URL (unlikely but defensive).
            escaped_url = url.replace('"', '""')
            if "," in escaped_url:
                escaped_url = f'"{escaped_url}"'
            fh.write(f"MCP Scan,{escaped_url},MCP\n")

    return config_filename, base_urls_dir


def build_axe_config(
    scan_id: str,
    audit_name: str,
    urls: list[str],
    max_links_per_domain: Optional[int] = None,
    viewport_sizes: Optional[dict[str, dict[str, int]]] = None,
) -> tuple[str, str]:
    """Build a config for the axe-core fallback scanner.

    Unlike build_config(), this does NOT read CWAC's config_default.json or
    write to CWAC directories. It creates a self-contained JSON config and
    a timestamped output directory under the project root.

    Args:
        scan_id: Unique identifier for this scan.
        audit_name: Human-readable name for the audit.
        urls: List of URLs to scan.
        max_links_per_domain: Max pages to crawl per domain (default 10).
        viewport_sizes: Viewport overrides. Defaults to medium (1280x800).

    Returns:
        A tuple of (config_path, output_dir) as absolute paths.

    Raises:
        ValueError: If urls is empty.
    """
    if not urls:
        raise ValueError("At least one URL must be provided")

    safe_name = _sanitize_audit_name(audit_name)
    if not safe_name:
        raise ValueError("audit_name is empty after sanitization")

    # Create timestamped output directory.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir_name = f"{timestamp}_{safe_name}"
    output_dir = os.path.join(PROJECT_ROOT, "output", output_dir_name)
    os.makedirs(output_dir, exist_ok=True)

    # Default viewports if none provided.
    if viewport_sizes is None:
        viewport_sizes = {"medium": {"width": 1280, "height": 800}}

    # axe-core JS path.
    axe_core_path = os.path.join(PROJECT_ROOT, "node_modules", "axe-core", "axe.min.js")

    config = {
        "audit_name": safe_name,
        "urls": urls,
        "max_links_per_domain": max_links_per_domain or 10,
        "viewport_sizes": viewport_sizes,
        "output_dir": output_dir,
        "axe_core_path": axe_core_path,
    }

    # Write config JSON to output directory.
    config_path = os.path.join(output_dir, f"config_{scan_id}.json")
    with open(config_path, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=4)

    return config_path, output_dir
