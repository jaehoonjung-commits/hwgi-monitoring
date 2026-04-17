"""Helpers for building notification messages and payloads."""

from datetime import datetime, timezone

import config
from models import AlertData, RecipientData

_sequence_counter = 0

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
    _sequence_counter = (_sequence_counter % 999999) + 1
    current_time = datetime.now()
    return (
        f"{current_time.strftime('%Y%m%d%H%M%S')}"
        f"{current_time.strftime('%f')[:3]}"
        f"{config.UMS_APPL_CD}"
        f"{_sequence_counter:06d}"
    )


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
    ecare_no_raw = recipient.get("ecare_no", config.UMS_ECARE_NO)
    try:
        ecare_no = int(ecare_no_raw)
    except (TypeError, ValueError):
        ecare_no = config.UMS_ECARE_NO

    return {
        "header": {
            "ifGlobalNo": build_ums_if_global_no(),
            "chnlSysCd": config.UMS_CHNL_SYS_CD,
            "ifOrgCd": config.UMS_IF_ORG_CD,
            "applCd": config.UMS_APPL_CD,
            "ifKindCd": config.UMS_IF_KIND_CD,
            "ifTxCd": config.UMS_IF_TX_CD,
            "stfno": config.UMS_STFNO,
            "respCd": "",
            "respMsg": "",
        },
        "payload": {
            "cnt": 1,
            "request": [
                {
                    "ecareNo": ecare_no,
                    "channel": str(recipient.get("channel", config.UMS_CHANNEL)),
                    "tmplType": str(recipient.get("tmpl_type", config.UMS_TMPL_TYPE)),
                    "receiverNm": str(
                        recipient.get(
                            "receiver_name",
                            recipient.get("team_name", "Grafana"),
                        )
                    ),
                    "receiver": receiver_number,
                    "sender": str(recipient.get("sender_phone", config.UMS_SENDER_PHONE)),
                    "senderNm": str(recipient.get("sender_name", config.UMS_SENDER_NAME)),
                    "reqUserId": str(recipient.get("req_user_id", config.UMS_STFNO)),
                    "jonmun": build_ums_kakao_jonmun(alert),
                }
            ],
        },
    }