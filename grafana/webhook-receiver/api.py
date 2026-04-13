"""
API endpoint handlers for Grafana webhook receiver.

This module contains route handler functions that process HTTP requests
and delegate to business logic modules (recipients, channels).
"""

import logging

from fastapi import Request

from recipients import load_recipient_config, resolve_recipients
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
        recipient_group_name = str(labels.get("recipient_group_name", ""))
        
        # Resolve recipients for this alert
        resolved_recipients = resolve_recipients(
            instance=instance,
            severity=severity,
            recipient_group_name=recipient_group_name,
            config=config_data,
        )
        
        # Add recipients to alert labels for logging/debugging
        labels["recipients"] = resolved_recipients
        
        # Send notifications to each recipient
        for recipient in resolved_recipients:
            delivery_results.extend(send_notification(recipient=recipient, alert=alert))

        # Log alert details
        logger.info("--- alert #%d ---", idx)
        logger.info("status: %s", alert.get("status"))
        logger.info("name: %s", labels.get("alertname"))
        logger.info("severity: %s", severity)
        logger.info("recipient_group_name: %s", recipient_group_name)
        logger.info("instance: %s", instance)
        logger.info("recipients: %s", labels.get("recipients"))
        logger.info("summary: %s", annotations.get("summary"))
        logger.info("description: %s", annotations.get("description"))
        logger.info("startsAt: %s", alert.get("startsAt"))
        logger.info("endsAt: %s", alert.get("endsAt"))

    logger.info("=== End ===")

    return {
        "ok": True,
        "message": "Webhook received",
        "alerts_count": len(alerts),
        "delivery_results": delivery_results,
    }
