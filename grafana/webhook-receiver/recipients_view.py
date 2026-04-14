"""Recipient viewer page rendering."""

from html import escape

from models import RecipientData
from recipients import normalize_recipient


def _normalize_recipient_items(recipients_config: object) -> list[RecipientData]:
    if isinstance(recipients_config, dict):
        recipient_items = recipients_config.values()
    elif isinstance(recipients_config, list):
        recipient_items = recipients_config
    else:
        recipient_items = []

    return [
        normalize_recipient(item)
        for item in recipient_items
        if isinstance(item, dict)
    ]


def render_recipients_page(config_path: str, recipients_config: object) -> str:
    normalized_recipients = _normalize_recipient_items(recipients_config)

    rows: list[str] = []
    for recipient in normalized_recipients:
        levels = ", ".join(recipient.get("alert_receive_level", []))
        channels = ", ".join(recipient.get("notification_channels", []))
        rows.append(
            "<tr>"
            f"<td>{escape(str(recipient.get('id', '')))}</td>"
            f"<td>{escape(str(recipient.get('team_name', '')))}</td>"
            f"<td>{escape(str(recipient.get('recipient_group_name', '')))}</td>"
            f"<td>{escape(str(recipient.get('instance_name', '')))}</td>"
            f"<td>{escape(str(recipient.get('email', '')))}</td>"
            f"<td>{escape(str(recipient.get('phone_number', '')))}</td>"
            f"<td>{escape(levels)}</td>"
            f"<td>{escape(channels)}</td>"
            "</tr>"
        )

    rows_html = "".join(rows)
    if not rows_html:
        rows_html = "<tr><td colspan='8'>No recipients configured</td></tr>"

    return (
        "<!doctype html>"
        "<html lang='ko'>"
        "<head>"
        "<meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Recipients Configuration</title>"
        "<style>"
        ":root{color-scheme:light;}"
        "body{font-family:'Noto Sans KR',sans-serif;margin:0;padding:24px;background:#f4f7fb;color:#122033;}"
        ".wrap{max-width:1200px;margin:0 auto;}"
        "h1{margin:0 0 8px;font-size:28px;}"
        "p{margin:0 0 16px;color:#4b5d74;}"
        ".notice{display:inline-block;margin:6px 0 16px;padding:8px 12px;border-radius:999px;background:#e8eef8;color:#29486d;font-size:13px;font-weight:700;}"
        "table{width:100%;border-collapse:collapse;background:#eef2f7;border-radius:10px;overflow:hidden;box-shadow:none;opacity:.78;filter:grayscale(.2);}"
        "th,td{padding:10px 12px;border-bottom:1px solid #e6ebf2;text-align:left;font-size:14px;vertical-align:top;}"
        "th{background:#eef3fa;font-weight:700;color:#1e324a;}"
        "tr:last-child td{border-bottom:none;}"
        "td{background:#f8fafc;color:#53657d;}"
        "</style>"
        "</head>"
        "<body>"
        "<div class='wrap'>"
        "<h1>Recipients Configuration</h1>"
        f"<p>Config file: {escape(str(config_path))}</p>"
        "<span class='notice'>Read-only view</span>"
        "<table>"
        "<thead><tr>"
        "<th>ID</th><th>Team</th><th>Group</th><th>Instance</th><th>Email</th><th>Phone</th><th>Levels</th><th>Channels</th>"
        "</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        "</table>"
        "</div>"
        "</body>"
        "</html>"
    )
