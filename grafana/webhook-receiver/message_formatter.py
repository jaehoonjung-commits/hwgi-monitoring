"""Helpers for building notification messages and payloads."""

from datetime import datetime, timezone
from uuid import uuid4

import config
from models import AlertData, RecipientData

# Global sequence counter for unique 6-digit sequence
_sequence_counter = 0

def build_alert_summary(recipient: RecipientData, alert: AlertData) -> str:


def build_alert_summary(recipient: RecipientData, alert: AlertData) -> str:
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


def build_gmail_subject(alert: AlertData) -> str:
    labels = alert.get("labels", {})
    severity = labels.get("severity", "").upper()
    alertname = labels.get("alertname", "Alert")
    return f"[Grafana {severity}] {alertname} on {labels.get('instance', '-')}"





def build_file_record(recipient: RecipientData, alert: AlertData) -> dict[str, str]:
    labels = alert.get("labels", {})
    annotations = alert.get("annotations", {})
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "recipient_id": str(recipient.get("id", "")),
        "team_name": str(recipient.get("team_name", "")),
        "recipient_group_name": str(recipient.get("recipient_group_name", "")),
        "channel": "file",
        "status": str(alert.get("status", "")),
        "alertname": str(labels.get("alertname", "")),
        "severity": str(labels.get("severity", "")),
        "instance": str(labels.get("instance", "")),
        "summary": str(annotations.get("summary", "")),
    }


def normalize_phone_number(phone: str) -> str:
    return "".join(ch for ch in phone if ch.isdigit())


def build_ums_if_global_no() -> str:
    global _sequence_counter
    _sequence_counter += 1
    if _sequence_counter > 999999:
        _sequence_counter = 1  # Reset if exceeds 6 digits
    
    prefix = datetime.now().strftime("%Y%m%d%H%M%S")  # YYYYMMDDHHMMSS (14 digits)
    milliseconds = datetime.now().strftime("%f")[:3]  # milliseconds (3 digits)
    linkage_code = config.UMS_APPL_CD  # linkage institution code (4 digits)
    sequence = f"{_sequence_counter:06d}"  # 6-digit non-overlapping sequence
    return f"{prefix}{milliseconds}{linkage_code}{sequence}"


def build_ums_kakao_jonmun(alert: AlertData) -> str:
    labels = alert.get("labels", {})
    annotations = alert.get("annotations", {})

    title = str(labels.get("alertname", "Alert"))
    summary = str(annotations.get("summary", "-"))
    desc = str(annotations.get("description", "-"))

    now = datetime.now()
    return (
        "@s@|f|6|Grafana|"
        f"{title}|"
        f"{summary} {desc}|"
        f"{now.strftime('%H')}|{now.strftime('%M')}|{now.strftime('%S')}"
    )


def build_ums_kakao_payload(recipient: RecipientData, alert: AlertData) -> dict:
    receiver_number = normalize_phone_number(str(recipient.get("phone_number", "")))

    return {
        "header": {
            "ifGlobalNo": build_ums_if_global_no(),
            "chnlSysCd": config.UMS_CHNL_SYS_CD,
            "ifOrgCd": config.UMS_IF_ORG_CD,
            "applCd": config.UMS_APPL_CD,
            "ifKindCd": config.UMS_IF_KIND_CD,
            "ifTxCd": config.UMS_IF_TX_CD,
            "sftno": config.UMS_SFTNO,
            "respCd": "",
            "respMsg": "",
        },
        "payload": {
            "cnt": 1,
            "request": [
                {
                    "ecardNo": config.UMS_ECARD_NO,
                    "channel": config.UMS_CHANNEL,
                    "tmplType": config.UMS_TMPL_TYPE,
                    "receivcerNm": str(recipient.get("team_name", "Grafana")),
                    "receiver": receiver_number,
                    "senderNm": config.UMS_SENDER_NAME,
                    "reqUserId": config.UMS_SFTNO,
                    "jonmun": build_ums_kakao_jonmun(alert),
                }
            ],
        },
    }