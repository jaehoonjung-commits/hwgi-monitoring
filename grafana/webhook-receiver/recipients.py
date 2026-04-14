"""Recipient configuration loading and recipient matching logic."""

import logging

import yaml

from config import RECIPIENT_CONFIG_PATH
from models import RecipientData, ConfigData

logger = logging.getLogger("grafana_webhook_receiver")


def _normalize_string(value: object) -> str:
    return str(value).strip().lower()


def _normalize_string_list(value: object) -> list[str]:
    items = value if isinstance(value, list) else [value]
    return [_normalize_string(item) for item in items]


def load_recipient_config() -> ConfigData:
    try:
        with open(RECIPIENT_CONFIG_PATH, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
    except FileNotFoundError:
        logger.warning("Recipient config file not found: %s", RECIPIENT_CONFIG_PATH)
        return {}
    except yaml.YAMLError:
        logger.exception("Invalid YAML format in recipient config: %s", RECIPIENT_CONFIG_PATH)
        return {}
    except OSError:
        logger.exception("Failed to read recipient config file: %s", RECIPIENT_CONFIG_PATH)
        return {}

    if not isinstance(data, dict):
        logger.warning("Recipient config root must be a mapping: %s", RECIPIENT_CONFIG_PATH)
        return {}
    return data


def normalize_recipient(recipient: RecipientData) -> RecipientData:
    return {
        "id": str(recipient.get("id", "")),
        "phone_number": str(recipient.get("phone_number", "")),
        "email": str(recipient.get("email", "")),
        "team_name": str(recipient.get("team_name", "")),
        "recipient_group_name": str(recipient.get("recipient_group_name", "")),
        "instance_name": str(recipient.get("instance_name", "")),
        "alert_receive_level": _normalize_string_list(
            recipient.get("alert_receive_level", "info")
        ),
        "notification_channels": _normalize_string_list(
            recipient.get("notification_channels", ["gmail"])
        ),
    }


def _can_receive_alert(recipient_level: str | list[str], severity: str) -> bool:
    return _normalize_string(severity) in _normalize_string_list(recipient_level)


def _is_same_group(recipient_group_name: str, alert_group_name: str) -> bool:
    return _normalize_string(recipient_group_name) == _normalize_string(alert_group_name)


def _build_recipient_lookup(recipients_config: object) -> dict[str, RecipientData]:
    if isinstance(recipients_config, list):
        recipient_items = recipients_config
    elif isinstance(recipients_config, dict):
        recipient_items = recipients_config.values()

    else:
        return {}

    return {
        normalized["id"]: normalized

        for recipient in recipient_items
        if isinstance(recipient, dict)
        if (normalized := normalize_recipient(recipient))["id"]
    }


def _matches_recipient(
    recipient: RecipientData,
    severity: str,
    recipient_group_name: str,
) -> bool:
    if not _can_receive_alert(recipient["alert_receive_level"], severity):
        return False

    return _is_same_group(
        recipient.get("recipient_group_name", ""),
        recipient_group_name,
    )


def resolve_recipients(
    severity: str,
    recipient_group_name: str,
    config: ConfigData,
) -> list[RecipientData]:
    recipients_by_id = _build_recipient_lookup(config.get("recipients", []))
    return [
        recipient
        for recipient in recipients_by_id.values()
        if _matches_recipient(
            recipient,
            severity,
            recipient_group_name,
        )
    ]
