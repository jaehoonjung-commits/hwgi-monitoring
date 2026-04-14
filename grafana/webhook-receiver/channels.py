"""
Notification channel implementations (Gmail, Kakao via UMS, File).
Each channel has different delivery requirements.
"""

import json
import inspect
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import httpx

import config
from message_formatter import (
    build_alert_summary,
    build_file_record,
    build_gmail_subject,
    build_ums_kakao_payload,
)
from models import RecipientData, AlertData, NotificationResult

logger = logging.getLogger("grafana_webhook_receiver")


def send_gmail(recipient: RecipientData, alert: AlertData) -> NotificationResult:
    """
    Send alert via Gmail SMTP.
    
    Args:
        recipient: Recipient with email field.
        alert: Alert data.
        
    Returns:
        Result dict with channel, status, and optional details.
    """
    recipient_id = recipient.get("id", "")
    to_email = recipient.get("email", "")

    # Dry-run if credentials not configured
    if not config.GMAIL_USER or not config.GMAIL_APP_PASSWORD:
        logger.info("[DRY-RUN] gmail -> id=%s to=%s", recipient_id, to_email)
        return {"recipient_id": recipient_id, "channel": "gmail", "status": "dry-run"}

    # Skip if no email address
    if not to_email:
        logger.warning("gmail: no email address for recipient %s, skipping", recipient_id)
        return {
            "recipient_id": recipient_id,
            "channel": "gmail",
            "status": "skipped",
            "reason": "no email address",
        }

    subject = build_gmail_subject(alert)
    body = build_alert_summary(recipient, alert)

    msg = MIMEMultipart()
    msg["From"] = config.GMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(
            config.GMAIL_SMTP_HOST,
            config.GMAIL_SMTP_PORT,
            timeout=10,
        ) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
            smtp.sendmail(config.GMAIL_USER, to_email, msg.as_string())
        logger.info("gmail sent -> id=%s to=%s", recipient_id, to_email)
        return {"recipient_id": recipient_id, "channel": "gmail", "status": "sent"}
    except smtplib.SMTPException as exc:
        logger.warning("gmail failed for recipient %s: %s", recipient_id, exc)
        return {"recipient_id": recipient_id, "channel": "gmail", "status": "failed"}



async def send_kakao(recipient: RecipientData, alert: AlertData) -> NotificationResult:
    """
    Send Kakao notification through UMS endpoint.

    Args:
        recipient: Recipient with phone_number field.
        alert: Alert data.

    Returns:
        Result dict with channel, status, and optional HTTP/UMS response code.
    """
    recipient_id = str(recipient.get("id", ""))
    phone = str(recipient.get("phone_number", ""))

    if not config.UMS_API_URL:
        logger.info("[DRY-RUN] kakao(ums) -> id=%s to=%s", recipient_id, phone)
        return {
            "recipient_id": recipient_id,
            "channel": "kakao",
            "status": "dry-run",
            "reason": "UMS_API_URL not configured",
        }

    if not phone:
        logger.warning("kakao(ums): no phone number for recipient %s, skipping", recipient_id)
        return {
            "recipient_id": recipient_id,
            "channel": "kakao",
            "status": "skipped",
            "reason": "no phone number",
        }

    request_payload = build_ums_kakao_payload(recipient=recipient, alert=alert)

    headers = {"Content-Type": "application/json"}
    if config.UMS_API_KEY:
        headers["Authorization"] = f"Bearer {config.UMS_API_KEY}"

    try:
        async with httpx.AsyncClient(timeout=config.UMS_TIMEOUT_SEC) as client:
            resp = await client.post(
                config.UMS_API_URL,
                headers=headers,
                json=request_payload,
            )

        http_status = str(resp.status_code)
        raw_response = resp.text

        ums_resp_cd = ""
        try:
            response_json = json.loads(raw_response) if raw_response else {}
            ums_resp_cd = str(response_json.get("payload", {}).get("reCode", ""))
        except json.JSONDecodeError:
            logger.warning("kakao(ums): non-json response for recipient %s", recipient_id)

        logger.info(
            "kakao(ums) sent -> id=%s to=%s http=%s reCode=%s",
            recipient_id,
            phone,
            http_status,
            ums_resp_cd,
        )
        if resp.status_code >= 400:
            return {
                "recipient_id": recipient_id,
                "channel": "kakao",
                "status": "failed",
                "http_status": http_status,
                "reason": f"ums http error: {resp.status_code}",
            }

        return {
            "recipient_id": recipient_id,
            "channel": "kakao",
            "status": "sent",
            "http_status": http_status,
            "re_code": ums_resp_cd,
        }
    except (httpx.TimeoutException, httpx.RequestError, TimeoutError, OSError) as exc:
        logger.warning("kakao(ums) failed for recipient %s: %s", recipient_id, exc)
        return {
            "recipient_id": recipient_id,
            "channel": "kakao",
            "status": "failed",
            "reason": f"ums request failed: {exc}",
        }
    except Exception as exc:
        logger.warning("kakao(ums) failed for recipient %s: %s", recipient_id, exc)
        return {
            "recipient_id": recipient_id,
            "channel": "kakao",
            "status": "failed",
            "reason": f"ums request failed: {exc}",
        }


def send_file(recipient: RecipientData, alert: AlertData) -> NotificationResult:
    """Append alert delivery details to a local file."""
    recipient_id = str(recipient.get("id", ""))
    output_path = Path(config.FILE_OUTPUT_PATH)
    record = build_file_record(recipient, alert)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.info("file written -> id=%s path=%s", recipient_id, output_path)
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


# Channel dispatcher
_CHANNEL_HANDLERS = {
    "file": send_file,
    "gmail": send_gmail,
    "kakao": send_kakao,
}


async def send_notification(
    recipient: RecipientData,
    alert: AlertData,
) -> list[NotificationResult]:
    """
    Send alert through all configured notification channels.
    
    Args:
        recipient: Recipient with notification_channels list.
        alert: Alert data.
        
    Returns:
        List of result dicts (one per channel).
    """
    channels: list[str] = recipient.get("notification_channels", ["gmail"])
    results: list[NotificationResult] = []
    
    for channel in channels:
        handler = _CHANNEL_HANDLERS.get(channel)
        if handler is None:
            logger.warning(
                "unknown notification channel '%s' for recipient %s",
                channel,
                recipient.get("id", ""),
            )
            results.append({
                "recipient_id": recipient.get("id", ""),
                "channel": channel,
                "status": "skipped",
                "reason": "unknown channel",
            })
            continue
        try:
            result = handler(recipient, alert)
            if inspect.isawaitable(result):
                result = await result
            results.append(result)
        except Exception as exc:
            logger.exception(
                "notification channel '%s' failed for recipient %s: %s",
                channel,
                recipient.get("id", ""),
                exc,
            )
            results.append({
                "recipient_id": recipient.get("id", ""),
                "channel": channel,
                "status": "failed",
                "reason": "channel handler exception",
            })
    
    return results
