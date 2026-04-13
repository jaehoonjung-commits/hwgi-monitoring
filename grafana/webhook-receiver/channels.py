"""
Notification channel implementations (Gmail, SMS, Kakao).
Each channel has different API/SMTP requirements.
"""

import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib import error, request as urllib_request

import config
from models import RecipientData, AlertData, NotificationResult

logger = logging.getLogger("grafana_webhook_receiver")


def _build_alert_summary(recipient: RecipientData, alert: AlertData) -> str:
    """
    Build formatted alert summary for email body.
    
    Args:
        recipient: Recipient data.
        alert: Alert data.
        
    Returns:
        Formatted multi-line text.
    """
    labels = alert.get("labels", {})
    annotations = alert.get("annotations", {})
    lines = [
        f"Alert Name : {labels.get('alertname', '-')}",
        f"Severity   : {labels.get('severity', '-')}",
        f"Instance   : {labels.get('instance', '-')}",
        f"Status     : {alert.get('status', '-')}",
        f"Summary    : {annotations.get('summary', '-')}",
        f"Description: {annotations.get('description', '-')}",
        f"Starts At  : {alert.get('startsAt', '-')}",
        f"Ends At    : {alert.get('endsAt', '-')}",
        "",
        f"Team       : {recipient.get('team_name', '-')}",
        f"Group      : {recipient.get('recipient_group_name', '-')}",
        f"Recipient  : {recipient.get('id', '-')}",
    ]
    return "\n".join(lines)


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

    labels = alert.get("labels", {})
    severity = labels.get("severity", "").upper()
    alertname = labels.get("alertname", "Alert")
    subject = f"[Grafana {severity}] {alertname} on {labels.get('instance', '-')}"
    body = _build_alert_summary(recipient, alert)

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


def send_sms(recipient: RecipientData, alert: AlertData) -> NotificationResult:
    """
    Send alert via SMS API (provider-agnostic HTTP).
    
    Args:
        recipient: Recipient with phone_number field.
        alert: Alert data.
        
    Returns:
        Result dict with channel, status, and optional HTTP status.
    """
    recipient_id = recipient.get("id", "")
    phone = recipient.get("phone_number", "")

    # Dry-run if credentials not configured
    if not config.SMS_API_URL or not config.SMS_API_KEY or not config.SMS_SENDER_NUMBER:
        logger.info("[DRY-RUN] sms -> id=%s to=%s", recipient_id, phone)
        return {"recipient_id": recipient_id, "channel": "sms", "status": "dry-run"}

    # Skip if no phone number
    if not phone:
        logger.warning("sms: no phone number for recipient %s, skipping", recipient_id)
        return {
            "recipient_id": recipient_id,
            "channel": "sms",
            "status": "skipped",
            "reason": "no phone number",
        }

    labels = alert.get("labels", {})
    annotations = alert.get("annotations", {})
    text = (
        f"[Grafana {labels.get('severity', '').upper()}] "
        f"{labels.get('alertname', 'Alert')} / {labels.get('instance', '-')}\n"
        f"{annotations.get('summary', '-')}"
    )
    payload = json.dumps({
        "to": phone,
        "from": config.SMS_SENDER_NUMBER,
        "text": text,
    }).encode("utf-8")

    req = urllib_request.Request(
        config.SMS_API_URL,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.SMS_API_KEY}",
        },
        data=payload,
    )
    try:
        with urllib_request.urlopen(req, timeout=5) as resp:
            code = str(resp.getcode())
        logger.info("sms sent -> id=%s to=%s http=%s", recipient_id, phone, code)
        return {
            "recipient_id": recipient_id,
            "channel": "sms",
            "status": "sent",
            "http_status": code,
        }
    except error.URLError as exc:
        logger.warning("sms failed for recipient %s: %s", recipient_id, exc)
        return {"recipient_id": recipient_id, "channel": "sms", "status": "failed"}


def send_kakao(recipient: RecipientData, alert: AlertData) -> NotificationResult:
    """
    Send alert via Kakao Alimtalk API.
    
    Args:
        recipient: Recipient with phone_number field.
        alert: Alert data.
        
    Returns:
        Result dict with channel, status, and optional HTTP status.
    """
    recipient_id = recipient.get("id", "")
    phone = recipient.get("phone_number", "")

    # Dry-run if credentials not configured
    if (
        not config.KAKAO_API_URL
        or not config.KAKAO_API_KEY
        or not config.KAKAO_SENDER_KEY
        or not config.KAKAO_TEMPLATE_CODE
    ):
        logger.info("[DRY-RUN] kakao -> id=%s to=%s", recipient_id, phone)
        return {"recipient_id": recipient_id, "channel": "kakao", "status": "dry-run"}

    # Skip if no phone number
    if not phone:
        logger.warning("kakao: no phone number for recipient %s, skipping", recipient_id)
        return {
            "recipient_id": recipient_id,
            "channel": "kakao",
            "status": "skipped",
            "reason": "no phone number",
        }

    labels = alert.get("labels", {})
    annotations = alert.get("annotations", {})
    payload = json.dumps({
        "senderKey": config.KAKAO_SENDER_KEY,
        "templateCode": config.KAKAO_TEMPLATE_CODE,
        "recipientList": [
            {
                "recipientNo": phone,
                "templateParameter": {
                    "alertname": labels.get("alertname", "-"),
                    "severity": labels.get("severity", "-"),
                    "instance": labels.get("instance", "-"),
                    "status": alert.get("status", "-"),
                    "summary": annotations.get("summary", "-"),
                },
            }
        ],
    }).encode("utf-8")

    req = urllib_request.Request(
        config.KAKAO_API_URL,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.KAKAO_API_KEY}",
        },
        data=payload,
    )
    try:
        with urllib_request.urlopen(req, timeout=5) as resp:
            code = str(resp.getcode())
        logger.info("kakao sent -> id=%s to=%s http=%s", recipient_id, phone, code)
        return {
            "recipient_id": recipient_id,
            "channel": "kakao",
            "status": "sent",
            "http_status": code,
        }
    except error.URLError as exc:
        logger.warning("kakao failed for recipient %s: %s", recipient_id, exc)
        return {"recipient_id": recipient_id, "channel": "kakao", "status": "failed"}


# Channel dispatcher
_CHANNEL_HANDLERS = {
    "gmail": send_gmail,
    "sms": send_sms,
    "kakao": send_kakao,
}


def send_notification(
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
        results.append(handler(recipient, alert))
    
    return results
