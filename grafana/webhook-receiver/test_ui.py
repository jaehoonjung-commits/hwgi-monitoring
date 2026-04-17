"""Render the curl test page from an external template."""

from pathlib import Path

from config import UMS_API_URL

_TEMPLATE_PATH = Path(__file__).with_name("templates") / "test_ui.html"


def render_test_page() -> str:
    """Render the curl test page from the HTML template."""
    escaped_ums_api_url = UMS_API_URL.replace("\\", "\\\\").replace('"', '\\"')
    return _TEMPLATE_PATH.read_text(encoding="utf-8").replace("__UMS_API_URL__", escaped_ums_api_url)
