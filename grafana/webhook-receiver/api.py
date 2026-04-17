"""API handlers for the Grafana webhook receiver."""

import logging
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from config import RECIPIENT_CONFIG_PATH, UMS_API_URL
from recipients import extract_grafana_filter_options, load_recipient_config, resolve_recipients
from recipients_view import render_recipients_page
from test_ui import render_test_page
from channels import send_notification, _call_ums_api
from message_formatter import build_ums_if_global_no, build_ums_kakao_payload
from models import ConfigData

logger = logging.getLogger("grafana_webhook_receiver")
_TEST_UI_SCRIPT_PATH = Path(__file__).with_name("assets") / "js" / "test_ui.js"


def _compact_ums_result(result: dict) -> dict:
    payload = result.get("payload", {}) if isinstance(result, dict) else {}
    compact = {
        "ok": bool(result.get("ok")),
        "message": result.get("message", ""),
        "ums_api_url": result.get("ums_api_url", UMS_API_URL),
    }
    if "ums_http_status" in result:
        compact["ums_http_status"] = result["ums_http_status"]
    if payload.get("reCode"):
        compact["re_code"] = payload.get("reCode")
    if payload.get("reMsg"):
        compact["re_msg"] = payload.get("reMsg")
    if result.get("ums_response_text"):
        compact["ums_response_text"] = result["ums_response_text"]
    return compact


def _compact_delivery_result(result: dict) -> dict:
    compact = {
        "recipient_id": result.get("recipient_id", ""),
        "channel": result.get("channel", ""),
        "status": result.get("status", ""),
    }
    for key in ("reason", "re_code", "path"):
        if result.get(key):
            compact[key] = result[key]
    if result.get("channel") == "kakao" and result.get("status") == "failed":
        debug = {
            "ums_api_url": result.get("ums_api_url", UMS_API_URL),
        }
        ums_result = result.get("ums_api_result")
        if isinstance(ums_result, dict):
            debug.update(_compact_ums_result(ums_result))
        compact["debug"] = debug
    return compact


async def healthcheck() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "Grafana Webhook Receiver",
        "message": "Use POST /webhook/grafana to send alerts",
    }


async def view_recipients() -> HTMLResponse:
    """Render recipient configuration as an HTML page for browser viewing."""
    config_data: ConfigData = load_recipient_config()
    html = render_recipients_page(
        config_path=RECIPIENT_CONFIG_PATH,
        recipients_config=config_data.get("recipients", []),
    )
    return HTMLResponse(content=html)


async def receive_grafana_webhook(request: Request) -> dict:
    """Receive a Grafana webhook and dispatch notifications."""
    payload = await request.json()
    config_data: ConfigData = load_recipient_config()
    alerts = payload.get("alerts", [])

    logger.info(
        "webhook received receiver=%s status=%s alerts=%d",
        payload.get("receiver"),
        payload.get("status"),
        len(alerts),
    )
    for idx, alert in enumerate(alerts, start=1):
        lbl = alert.get("labels", {})
        logger.info(
            "alert#%d name=%s severity=%s group=%s instance=%s status=%s",
            idx,
            lbl.get("alertname", "-"),
            lbl.get("severity", "-"),
            lbl.get("alert_group", "-"),
            lbl.get("instance", "-"),
            alert.get("status", "-"),
        )
    
    delivery_results: list[dict[str, str]] = []

    for alert in alerts:
        labels = alert.get("labels", {})
        severity = str(labels.get("severity", ""))
        alert_group = str(labels.get("alert_group", ""))

        resolved_recipients = resolve_recipients(
            severity=severity,
            alert_group=alert_group,
            config=config_data,
        )
        labels["recipients"] = resolved_recipients

        for recipient in resolved_recipients:
            delivery_results.extend(await send_notification(recipient=recipient, alert=alert))

    failed_count = sum(1 for r in delivery_results if r.get("status") == "failed")
    logger.info(
        "webhook completed alerts=%d deliveries=%d failed=%d",
        len(alerts),
        len(delivery_results),
        failed_count,
    )

    compact_results = [_compact_delivery_result(result) for result in delivery_results]
    response = {
        "ok": failed_count == 0,
        "message": "Webhook received and all deliveries completed" if failed_count == 0 else "Delivery failed",
        "alerts_count": len(alerts),
        "ums_api_url": UMS_API_URL,
        "delivery_results": compact_results,
    }
    if failed_count > 0:
        return JSONResponse(status_code=500, content=response)
    return response


async def receive_ums_request(request: Request) -> dict:
    """Receive and validate UMS test payload."""
    payload = await request.json()
    ums_result = _compact_ums_result(await _call_ums_api(payload))

    if not ums_result.get("ok"):
        return JSONResponse(status_code=500, content=ums_result)

    return ums_result


async def view_test_page() -> HTMLResponse:
    """Render webhook testing UI page."""
    html = render_test_page()
    return HTMLResponse(content=html)


async def view_test_script() -> Response:
    """Serve curl-test page JavaScript."""
    return Response(
        content=_TEST_UI_SCRIPT_PATH.read_text(encoding="utf-8"),
        media_type="application/javascript",
    )


async def execute_test_request(request: Request) -> dict:
    """Execute a test request from the backend side."""
    request_data = await request.json()

    target_url = str(request_data.get("url", "")).strip()
    method = str(request_data.get("method", "POST")).upper()
    payload = request_data.get("payload", {})
    incoming_headers = request_data.get("headers", {})

    if target_url.startswith("/"):
        target_url = f"{str(request.base_url).rstrip('/')}{target_url}"

    parsed = urlparse(target_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {
            "ok": False,
            "message": "Invalid target URL",
            "request": {
                "method": method,
                "url": target_url,
                "headers": incoming_headers if isinstance(incoming_headers, dict) else {},
            },
        }

    request_headers = {
        str(key): str(value)
        for key, value in (incoming_headers.items() if isinstance(incoming_headers, dict) else [])
    }

    try:
        timeout_sec = float(request_data.get("timeout_sec", 10.0))
    except (TypeError, ValueError):
        timeout_sec = 10.0

    try:
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            response = await client.request(
                method=method,
                url=target_url,
                headers=request_headers,
                json=payload,
            )

        response_text = response.text
        logger.info("test request method=%s url=%s status=%s", method, target_url, response.status_code)

        return {
            "ok": True,
            "request": {
                "method": method,
                "url": target_url,
                "headers": request_headers,
            },
            "response": {
                "status": response.status_code,
                "status_text": response.reason_phrase,
                "headers": dict(response.headers),
                "body": response_text,
            },
        }
    except (httpx.TimeoutException, httpx.RequestError, OSError) as exc:
        logger.warning("test request failed method=%s url=%s error=%s", method, target_url, exc)
        return {
            "ok": False,
            "message": "Upstream request failed",
            "request": {
                "method": method,
                "url": target_url,
                "headers": request_headers,
            },
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc),
            },
        }


async def preview_kakao_requests(request: Request) -> dict:
    """Preview Kakao(UMS) outbound requests resolved from recipients.yaml."""
    payload = await request.json()
    alerts = payload.get("alerts", []) if isinstance(payload, dict) else []
    config_data: ConfigData = load_recipient_config()

    kakao_requests: list[dict] = []
    resolved_recipient_summaries: list[dict] = []

    for alert in alerts:
        if not isinstance(alert, dict):
            continue

        labels = alert.get("labels", {})
        severity = str(labels.get("severity", ""))
        alert_group = str(labels.get("alert_group", ""))

        matched_recipients = resolve_recipients(
            severity=severity,
            alert_group=alert_group,
            config=config_data,
        )

        for recipient in matched_recipients:
            resolved_recipient_summaries.append(
                {
                    "recipient_id": str(recipient.get("id", "")),
                    "team_name": str(recipient.get("team_name", "")),
                    "notification_channels": recipient.get("notification_channels", []),
                }
            )

            channels = recipient.get("notification_channels", [])
            if "kakao" not in channels:
                continue

            request_payload = build_ums_kakao_payload(recipient=recipient, alert=alert)
            kakao_requests.append(
                {
                    "recipient_id": str(recipient.get("id", "")),
                    "recipient_name": str(
                        recipient.get(
                            "receiver_name",
                            recipient.get("team_name", ""),
                        )
                    ),
                    "request_payload": request_payload,
                }
            )

    return {
        "ok": True,
        "kakao_requests": kakao_requests,
        "resolved_recipients": resolved_recipient_summaries,
        "ums_api_url": UMS_API_URL,
    }


async def generate_if_global_no() -> dict[str, str]:
    """Generate a backend-consistent ifGlobalNo."""
    return {"ifGlobalNo": build_ums_if_global_no()}


async def get_grafana_filter_options() -> dict:
    """Return selectable severity/group options from recipients.yaml."""
    config_data: ConfigData = load_recipient_config()
    options = extract_grafana_filter_options(config_data)
    return {
        "ok": True,
        "severities": options.get("severities", []),
        "groups": options.get("groups", []),
    }
