"""Standalone Playwright + axe-core scanner (subprocess).

Invoked as: python -m cwac_mcp.axe_scanner <config.json>

Uses the sync Playwright API to:
1. Navigate to each URL
2. Inject axe-core JS
3. Run axe.run() and collect violations
4. Crawl same-domain links
5. Write results to CSV in CWAC-compatible format
"""

import csv
import json
import os
import re
import sys
from html.parser import HTMLParser
from typing import Optional
from urllib.parse import urljoin, urlparse, urlunparse


# CSV column order — must match CWAC's axe_core_audit.csv exactly.
CSV_COLUMNS = [
    "organisation", "sector", "page_title", "base_url", "url",
    "viewport_size", "audit_id", "page_id", "audit_type", "issue_id",
    "description", "target", "num_issues", "help", "helpUrl",
    "id", "impact", "html", "tags", "best-practice",
]


def flatten_violations(
    violations: list[dict],
    page_url: str,
    page_title: str,
    base_url: str,
    viewport_name: str,
    viewport_size: dict[str, int],
    page_index: int,
) -> list[dict]:
    """Flatten axe-core violations into CSV-ready rows.

    Each violation may have multiple nodes; each node becomes one row.

    Args:
        violations: List of axe-core violation objects.
        page_url: The URL of the scanned page.
        page_title: The page's document.title.
        base_url: The base URL from the scan config.
        viewport_name: Name of the viewport (e.g. "medium").
        viewport_size: Dict with "width" and "height" keys.
        page_index: Sequential page index (1-based).

    Returns:
        List of dicts, one per violation node, keyed by CSV_COLUMNS.
    """
    rows: list[dict] = []
    issue_counter = 0
    viewport_str = str(viewport_size)

    for violation in violations:
        tags = violation.get("tags", [])
        tags_str = ",".join(tags)
        is_best_practice = "Yes" if "best-practice" in tags else "No"

        for node in violation.get("nodes", []):
            issue_counter += 1
            target_list = node.get("target", [])
            target_str = ",".join(target_list) if isinstance(target_list, list) else str(target_list)

            rows.append({
                "organisation": "MCP Scan",
                "sector": "MCP",
                "page_title": page_title,
                "base_url": base_url,
                "url": page_url,
                "viewport_size": viewport_str,
                "audit_id": f"{page_index}_{viewport_name}",
                "page_id": str(page_index),
                "audit_type": "AxeCoreAudit",
                "issue_id": str(issue_counter),
                "description": violation.get("description", ""),
                "target": target_str,
                "num_issues": "1",
                "help": violation.get("help", ""),
                "helpUrl": violation.get("helpUrl", ""),
                "id": violation.get("id", ""),
                "impact": violation.get("impact", ""),
                "html": node.get("html", ""),
                "tags": tags_str,
                "best-practice": is_best_practice,
            })

    return rows


def write_csv(rows: list[dict], output_path: str) -> None:
    """Write violation rows to a CSV file.

    Args:
        rows: List of dicts keyed by CSV_COLUMNS.
        output_path: Absolute path to the output CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


class _LinkExtractor(HTMLParser):
    """Simple HTML parser that extracts href attributes from <a> tags."""

    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.links.append(value)


def extract_links(html: str, page_url: str) -> list[str]:
    """Extract same-domain links from HTML.

    Args:
        html: Raw HTML string.
        page_url: The URL of the page the HTML came from.

    Returns:
        List of unique same-domain absolute URLs (no fragments).
    """
    parser = _LinkExtractor()
    try:
        parser.feed(html)
    except Exception:
        return []

    base_parsed = urlparse(page_url)
    base_domain = base_parsed.netloc

    seen: set[str] = set()
    result: list[str] = []

    for href in parser.links:
        # Skip non-HTTP links.
        if href.startswith(("mailto:", "javascript:", "tel:", "#")):
            continue

        # Resolve relative URLs.
        absolute = urljoin(page_url, href)
        parsed = urlparse(absolute)

        # Filter to same domain.
        if parsed.netloc != base_domain:
            continue

        # Filter to HTTP(S).
        if parsed.scheme not in ("http", "https"):
            continue

        # Strip fragment.
        clean = urlunparse(parsed._replace(fragment=""))

        if clean not in seen:
            seen.add(clean)
            result.append(clean)

    return result


def _run_scan(config_path: str) -> None:
    """Run the axe-core scan using Playwright.

    This is the main entry point when invoked as a subprocess.

    Args:
        config_path: Path to the scan config JSON file.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    audit_name = config.get("audit_name", "axe_scan")
    urls = config.get("urls", [])
    max_links = config.get("max_links_per_domain", 10)
    viewports = config.get("viewport_sizes", {"medium": {"width": 1280, "height": 800}})
    output_dir = config.get("output_dir", "output")
    axe_core_path = config.get("axe_core_path", "")

    if not urls:
        print("ERROR: No URLs provided in config.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(axe_core_path):
        print(f"ERROR: axe-core JS not found at {axe_core_path}", file=sys.stderr)
        sys.exit(1)

    # Read axe-core JS.
    with open(axe_core_path, "r", encoding="utf-8") as f:
        axe_js = f.read()

    from playwright.sync_api import sync_playwright

    all_rows: list[dict] = []
    base_url = urls[0]

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(headless=True)
        except Exception:
            # Browser not installed — try to install it automatically.
            print("Playwright browser not found. Installing Chromium...")
            import subprocess as _sp
            _sp.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=True,
            )
            browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Track visited URLs per domain to respect max_links.
        visited: set[str] = set()
        to_visit: list[str] = list(urls)
        page_index = 0

        while to_visit and len(visited) < max_links:
            current_url = to_visit.pop(0)
            if current_url in visited:
                continue

            visited.add(current_url)
            page_index += 1

            print(f"[{page_index}] Scanning: {current_url}")

            try:
                page.goto(current_url, wait_until="domcontentloaded", timeout=30000)
            except Exception as exc:
                print(f"  WARNING: Could not load {current_url}: {exc}")
                continue

            page_title = page.title() or "Untitled"

            # Scan each viewport size.
            for vp_name, vp_size in viewports.items():
                page.set_viewport_size(vp_size)

                # Inject and run axe-core.
                try:
                    page.evaluate(axe_js)
                    results = page.evaluate("() => axe.run()")
                except Exception as exc:
                    print(f"  WARNING: axe.run() failed on {current_url} ({vp_name}): {exc}")
                    continue

                violations = results.get("violations", [])
                rows = flatten_violations(
                    violations=violations,
                    page_url=current_url,
                    page_title=page_title,
                    base_url=base_url,
                    viewport_name=vp_name,
                    viewport_size=vp_size,
                    page_index=page_index,
                )
                all_rows.extend(rows)
                print(f"  [{vp_name}] Found {len(violations)} violations ({len(rows)} nodes)")

            # Crawl same-domain links.
            if len(visited) < max_links:
                try:
                    html_content = page.content()
                    new_links = extract_links(html_content, current_url)
                    for link in new_links:
                        if link not in visited and link not in to_visit:
                            to_visit.append(link)
                except Exception:
                    pass

        browser.close()

    # Write CSV output.
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "axe_core_audit.csv")
    write_csv(all_rows, csv_path)

    print(f"\nScan complete. {len(all_rows)} issues found across {page_index} pages.")
    print(f"Results written to: {csv_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m cwac_mcp.axe_scanner <config.json>", file=sys.stderr)
        sys.exit(1)

    _run_scan(sys.argv[1])
