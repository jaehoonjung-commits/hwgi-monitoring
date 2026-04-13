"""
Grafana Webhook Receiver - FastAPI application.

Main entry point that initializes the FastAPI app and registers route handlers.

Environment variables:
  - LOG_LEVEL: Logging level (default: INFO)
  - RECIPIENT_CONFIG_PATH: Path to recipients.yaml (default: recipients.yaml)
  - GMAIL_USER, GMAIL_APP_PASSWORD: Gmail credentials
  - SMS_API_URL, SMS_API_KEY, SMS_SENDER_NUMBER: SMS provider credentials
  - KAKAO_API_URL, KAKAO_API_KEY, KAKAO_SENDER_KEY, KAKAO_TEMPLATE_CODE: Kakao credentials

Usage:
  uvicorn main:app --host 0.0.0.0 --port 8000
"""

import logging

from fastapi import FastAPI, Request

import config
from api import healthcheck, receive_grafana_webhook

# Configure logging
raw_log_level = config.LOG_LEVEL
log_level = getattr(logging, raw_log_level, logging.INFO)

logging.basicConfig(
    level=log_level,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

# Create FastAPI application
app = FastAPI(
    title="Grafana Webhook Receiver",
    description="Receives Grafana alert webhooks and routes to notification channels",
    version="1.0.0",
)


# Register routes
@app.get("/")
async def get_health():
    """Health check endpoint."""
    return await healthcheck()


@app.post("/webhook/grafana")
async def post_webhook(request: Request):
    """Grafana webhook receiver endpoint."""
    return await receive_grafana_webhook(request)
