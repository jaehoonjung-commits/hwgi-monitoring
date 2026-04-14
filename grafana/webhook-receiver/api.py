"""
API endpoint handlers for Grafana webhook receiver.

This module contains route handler functions that process HTTP requests
and delegate to business logic modules (recipients, channels).
"""

import logging

from fastapi import Request
from fastapi.responses import HTMLResponse

from config import RECIPIENT_CONFIG_PATH
from recipients import load_recipient_config, resolve_recipients
from recipients_view import render_recipients_page
from channels import send_notification
from models import ConfigData

logger = logging.getLogger("grafana_webhook_receiver")


async def healthcheck() -> dict[str, str]:
    """
    Health check endpoint.
    
    Returns:
        Service status and usage information.
    """
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
    """
    Receive and process Grafana alert webhook.
    
    Parses the webhook payload, resolves recipients based on routing rules,
    and sends notifications through configured channels.
    
    Flow:
      1. Parse incoming JSON payload
      2. Load recipient configuration
      3. For each alert:
         a. Resolve recipient list
         b. Send notifications to each recipient via configured channels
         c. Collect delivery results
      4. Return aggregated results
    
    Args:
        request: HTTP request with JSON body containing Grafana alerts.
        
    Returns:
        Response dict with:
          - ok: Success flag
          - message: Status message
          - alerts_count: Number of alerts processed
          - delivery_results: List of delivery status per channel per recipient
    """
    payload = await request.json()
    config_data: ConfigData = load_recipient_config()
    alerts = payload.get("alerts", [])

    logger.info("=== Grafana Webhook Received ===")
    logger.info("receiver: %s", payload.get("receiver"))
    logger.info("status: %s", payload.get("status"))
    logger.info("alerts_count: %d", len(alerts))
    
    delivery_results: list[dict[str, str]] = []

    for idx, alert in enumerate(alerts, start=1):
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})

        instance = str(labels.get("instance", ""))
        severity = str(labels.get("severity", ""))
        alert_group = str(labels.get("alert_group", ""))
        
        # Resolve recipients for this alert
        resolved_recipients = resolve_recipients(
            severity=severity,
            alert_group=alert_group,
            config=config_data,
        )
        
        # Add recipients to alert labels for logging/debugging
        labels["recipients"] = resolved_recipients
        
        # Send notifications to each recipient and collect results
        alert_delivery_results = []
        for recipient in resolved_recipients:
            alert_delivery_results.extend(await send_notification(recipient=recipient, alert=alert))
        
        delivery_results.extend(alert_delivery_results)
        
        # Log alert details for each delivery result
        for delivery_idx, delivery_result in enumerate(alert_delivery_results, start=1):
            logger.info("--- alert #%d-%d --- %s, %s, %s, %s, %s, %s", 
                       idx,
                       delivery_idx,
                       severity,
                       labels.get("alertname"),
                       alert_group,
                       delivery_result.get("recipient_id", ""),
                       delivery_result.get("channel", ""),
                       delivery_result.get("status"))

    logger.info("=== End ===")

    return {
        "ok": True,
        "message": "Webhook received",
        "alerts_count": len(alerts),
        "delivery_results": delivery_results,
    }


async def receive_ums_request(request: Request) -> dict:
    """Receive and validate UMS test payload."""
    payload = await request.json()

    header = payload.get("header")
    body = payload.get("payload")

    def _normalize_header_value(key: str) -> str:
        value = header.get(key) if isinstance(header, dict) else ""
        return str(value) if value is not None else ""

    response_header = {
        "ifGlobalNo": _normalize_header_value("ifGlobalNo"),
        "chnlSysCd": _normalize_header_value("chnlSysCd"),
        "ifOrgCd": _normalize_header_value("ifOrgCd"),
        "applCd": _normalize_header_value("applCd"),
        "ifKindCd": _normalize_header_value("ifKindCd"),
        "ifTxCd": _normalize_header_value("ifTxCd"),
        "sftno": _normalize_header_value("sftno"),
    }

    if not isinstance(header, dict) or not isinstance(body, dict):
        return {
            "ok": False,
            "message": "Invalid payload: 'header' and 'payload' are required objects",
            "header": {
                **response_header,
                "respCd": "9998",
                "respMsg": "INVALID_HEADER_OR_PAYLOAD",
            },
            "payload": {
                "reCode": "9998",
                "reMsg": "INVALID_HEADER_OR_PAYLOAD",
            },
        }

    request_items = body.get("request")
    if not isinstance(request_items, list):
        return {
            "ok": False,
            "message": "Invalid payload: 'payload.request' must be a list",
            "header": {
                **response_header,
                "respCd": "9997",
                "respMsg": "INVALID_REQUEST_LIST",
            },
            "payload": {
                "reCode": "9997",
                "reMsg": "INVALID_REQUEST_LIST",
            },
        }

    logger.info("=== UMS Test Request Received ===")
    logger.info("ifGlobalNo: %s", header.get("ifGlobalNo"))
    logger.info("ifOrgCd: %s", header.get("ifOrgCd"))
    logger.info("applCd: %s", header.get("applCd"))
    logger.info("ifKindCd: %s", header.get("ifKindCd"))
    logger.info("ifTxCd: %s", header.get("ifTxCd"))
    logger.info("request_count: %d", len(request_items))

    for idx, item in enumerate(request_items, start=1):
        if not isinstance(item, dict):
            logger.warning("request #%d is not an object", idx)
            continue

        logger.info("--- ums request #%d ---", idx)
        logger.info("ecardNo: %s", item.get("ecardNo"))
        logger.info("channel: %s", item.get("channel"))
        logger.info("tmplType: %s", item.get("tmplType"))
        logger.info("receiverName(receivcerNm): %s", item.get("receivcerNm"))
        logger.info("receiver: %s", item.get("receiver"))
        logger.info("senderNm: %s", item.get("senderNm"))
        logger.info("reqUserId: %s", item.get("reqUserId"))
        logger.info("jonmun: %s", item.get("jonmun"))

    logger.info("=== End UMS Test Request ===")

    return {
        "ok": True,
        "message": "UMS test request received",
        "request_count": len(request_items),
        "header": {
            **response_header,
            "respCd": "0000",
            "respMsg": "SUCCESS",
        },
        "payload": {
            "reCode": "0000",
            "reMsg": "SUCCESS",
        },
    }
