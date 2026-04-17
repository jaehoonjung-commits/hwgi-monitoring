"""Notification channel handlers."""

import json
import logging
from pathlib import Path

import httpx

import config
from message_formatter import (
    build_file_record,
    build_ums_kakao_payload,
)
from models import RecipientData, AlertData, NotificationResult

logger = logging.getLogger("grafana_webhook_receiver")


def _ums_error(message: str, code: str, *, status: int | None = None, response_text: str | None = None) -> dict:
    result = {
        "ok": False,
        "message": message,
        "ums_api_url": config.UMS_API_URL,
        "header": {"respCd": "9999", "respMsg": code},
        "payload": {"reCode": "9999", "reMsg": code},
    }
    if status is not None:
        result["ums_http_status"] = status
    if response_text is not None:
        result["ums_response_text"] = response_text
    return result


async def _call_ums_api(payload: dict) -> dict:
    """Call external UMS API."""
    headers = {"Content-Type": "application/json"}
    logger.info("ums request url=%s timeout=%ss", config.UMS_API_URL, config.UMS_TIMEOUT_SEC)
    
    try:
        async with httpx.AsyncClient(timeout=config.UMS_TIMEOUT_SEC) as client:
            resp = await client.post(
                config.UMS_API_URL,
                headers=headers,
                json=payload,
            )
        
        logger.info("ums response status=%d", resp.status_code)
        
        if resp.status_code >= 400:
            return _ums_error(
                f"UMS API HTTP error: {resp.status_code}",
                f"HTTP_{resp.status_code}",
                status=resp.status_code,
                response_text=resp.text,
            )
        
        try:
            response_data = resp.json()
            logger.info("UMS API response JSON: %s", response_data)
            return {
                "ok": True,
                "message": "UMS API call succeeded",
                "ums_api_url": config.UMS_API_URL,
                "ums_http_status": resp.status_code,
                **response_data,
            }
        except json.JSONDecodeError as exc:
            logger.warning("ums response is not json: %s", exc)
            return _ums_error(
                "UMS API response is not JSON",
                "INVALID_RESPONSE",
                status=resp.status_code,
                response_text=resp.text,
            )
    except httpx.TimeoutException as exc:
        logger.warning("ums timeout: %s", exc)
        return _ums_error(f"UMS API timeout: {exc}", "TIMEOUT")
    except httpx.RequestError as exc:
        logger.warning("ums request error: %s", exc)
        return _ums_error(f"UMS API request error: {exc}", "REQUEST_ERROR")
    except OSError as exc:
        logger.warning("ums network error: %s", exc)
        return _ums_error(f"UMS API OS error: {exc}", "OS_ERROR")
    except Exception as exc:
        logger.exception("ums unexpected error")
        return _ums_error(f"UMS API unexpected error: {exc}", "UNKNOWN_ERROR")


async def send_kakao(recipient: RecipientData, alert: AlertData) -> NotificationResult:
    """
    Send Kakao notification by calling UMS API.

    Args:
        recipient: Recipient with phone_number field.
        alert: Alert data.

    Returns:
        Result dict with channel, status, and UMS response code.
    """
    recipient_id = str(recipient.get("id", ""))
    phone = str(recipient.get("phone_number", ""))

    if not phone:
        logger.warning("kakao(ums): no phone number for recipient %s, skipping", recipient_id)
        return {
            "recipient_id": recipient_id,
            "channel": "kakao",
            "status": "skipped",
            "reason": "no phone number",
        }

    request_payload = build_ums_kakao_payload(recipient=recipient, alert=alert)

    req = (request_payload.get("payload", {}).get("request") or [{}])[0]
    logger.info(
        "kakao request id=%s phone=%s ifGlobalNo=%s ecareNo=%s",
        recipient_id,
        phone,
        request_payload.get("header", {}).get("ifGlobalNo", "-"),
        req.get("ecareNo", "-"),
    )

    try:
        ums_response = await _call_ums_api(request_payload)
        ums_resp_cd = str(ums_response.get("payload", {}).get("reCode", ""))

        if not ums_response.get("ok"):
            logger.warning("kakao failed id=%s reCode=%s", recipient_id, ums_resp_cd)
            return {
                "recipient_id": recipient_id,
                "channel": "kakao",
                "status": "failed",
                "re_code": ums_resp_cd,
                "reason": ums_response.get("message", "ums api error"),
                "ums_api_url": config.UMS_API_URL,
                "ums_api_result": ums_response,
                "request_payload": request_payload,
            }

        logger.info("kakao sent id=%s reCode=%s", recipient_id, ums_resp_cd)
        return {
            "recipient_id": recipient_id,
            "channel": "kakao",
            "status": "sent",
            "re_code": ums_resp_cd,
            "ums_api_url": config.UMS_API_URL,
            "ums_api_result": ums_response,
            "request_payload": request_payload,
        }
    except Exception as exc:
        logger.warning("kakao failed id=%s reason=%s", recipient_id, exc)
        return {
            "recipient_id": recipient_id,
            "channel": "kakao",
            "status": "failed",
            "reason": f"ums api call failed: {exc}",
            "ums_api_url": config.UMS_API_URL,
            "request_payload": request_payload,
        }


async def send_file(recipient: RecipientData, alert: AlertData) -> NotificationResult:
    """Append alert delivery details to a local file."""
    recipient_id = str(recipient.get("id", ""))
    output_path = Path(config.FILE_OUTPUT_PATH)
    record = build_file_record(recipient, alert)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.info("file sent id=%s path=%s", recipient_id, output_path)
        return {
            "recipient_id": recipient_id,
            "channel": "file",
            "status": "sent",
            "path": str(output_path),
        }
    except OSError as exc:
        logger.warning("file write failed for recipient %s: %s", recipient_id, exc)
        return {
            "recipient_id": recipient_id,
            "channel": "file",
            "status": "failed",
            "reason": "file write failed",
        }


_CHANNEL_HANDLERS = {
    "file": send_file,
    "kakao": send_kakao,
}


async def send_notification(
    recipient: RecipientData,
    alert: AlertData,
) -> list[NotificationResult]:
    """Send an alert through every configured channel."""
    channels: list[str] = recipient.get("notification_channels", ["gmail"])
    results: list[NotificationResult] = []
    
    for channel in channels:
        handler = _CHANNEL_HANDLERS.get(channel)
        if handler is None:
            logger.warning("unknown channel=%s recipient=%s", channel, recipient.get("id", ""))
            results.append({
                "recipient_id": recipient.get("id", ""),
                "channel": channel,
                "status": "skipped",
                "reason": "unknown channel",
            })
            continue
        try:
            result = await handler(recipient, alert)
            results.append(result)
        except Exception as exc:
            logger.exception("channel failed channel=%s recipient=%s", channel, recipient.get("id", ""))
            results.append({
                "recipient_id": recipient.get("id", ""),
                "channel": channel,
                "status": "failed",
                "reason": "channel handler exception",
            })
    
    return results
