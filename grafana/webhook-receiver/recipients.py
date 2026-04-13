"""
Recipient configuration loading, normalization, and routing logic.
"""

import logging
import re

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


def _is_same_instance(recipient_instance: str, alert_instance: str) -> bool:
    return not recipient_instance or recipient_instance == alert_instance


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


def _find_group_recipient_ids(
    recipients_by_id: dict[str, RecipientData],
    group_names: list[object],
) -> list[str]:
    normalized_group_names = {_normalize_string(group_name) for group_name in group_names}
    if not normalized_group_names:
        return []

    return list(
        dict.fromkeys(
            recipient_id
            for recipient_id, recipient in recipients_by_id.items()
            if _normalize_string(recipient.get("recipient_group_name", ""))
            in normalized_group_names
        )
    )


def _rule_matches(rule: RecipientData, instance: str, severity: str) -> bool:
    instance_pattern = str(rule.get("instance_pattern", ""))
    severity_match = _normalize_string(rule.get("severity", ""))
    return (
        (not instance_pattern or re.search(instance_pattern, instance) is not None)
        and (not severity_match or _normalize_string(severity) == severity_match)
    )


def _matches_recipient(
    recipient: RecipientData,
    severity: str,
    instance: str,
    recipient_group_name: str,
    has_routing_config: bool,
) -> bool:
    if not _can_receive_alert(recipient["alert_receive_level"], severity):
        return False

    if has_routing_config:
        return _is_same_instance(recipient.get("instance_name", ""), instance)

    return _is_same_group(
        recipient.get("recipient_group_name", ""),
        recipient_group_name,
    )


def resolve_recipients(
    instance: str,
    severity: str,
    recipient_group_name: str,
    config: ConfigData,
) -> list[RecipientData]:
    routing = config.get("routing", {})
    rules = routing.get("rules", [])
    default_recipient_group_names = routing.get("default_recipient_group_names", [])
    recipients_by_id = _build_recipient_lookup(config.get("recipients", []))
    has_routing_config = bool(rules or default_recipient_group_names)

    matched_recipient_ids = list(
        dict.fromkeys(
            recipient_id
            for rule in rules
            if _rule_matches(rule, instance, severity)
            for recipient_id in _find_group_recipient_ids(
                recipients_by_id,
                [rule.get("recipient_group_name", "")],
            )
        )
    )

    if not matched_recipient_ids:
        matched_recipient_ids = _find_group_recipient_ids(
            recipients_by_id,
            default_recipient_group_names,
        )

    if not matched_recipient_ids and not has_routing_config:
        matched_recipient_ids = list(recipients_by_id.keys())

    return [
        recipient
        for recipient_id in matched_recipient_ids
        if (recipient := recipients_by_id.get(recipient_id))
        and _matches_recipient(
            recipient,
            severity,
            instance,
            recipient_group_name,
            has_routing_config,
        )
    ]
