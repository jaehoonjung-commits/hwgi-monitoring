"""
Grafana Webhook Receiver - FastAPI application.

Main entry point that initializes the FastAPI app and registers route handlers.

Environment variables:
  - LOG_LEVEL: Logging level (default: INFO)
  - RECIPIENT_CONFIG_PATH: Path to recipients.yaml (default: recipients.yaml)
  - GMAIL_USER, GMAIL_APP_PASSWORD: Gmail credentials
  - UMS_API_URL, UMS_API_KEY, ...: UMS relay credentials for kakao channel

Usage:
  uvicorn main:app --host 0.0.0.0 --port 8000
"""

import logging

from fastapi import FastAPI, Request

import config
from api import healthcheck, receive_grafana_webhook, receive_ums_request, view_recipients

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


@app.post("/hwgi/ums/UMSMEMMA020010000")
async def post_ums_request(request: Request):
    """UMS test request receiver endpoint."""
    return await receive_ums_request(request)


@app.get("/recipients")
async def get_recipients():
    """Recipient configuration viewer endpoint."""
    return await view_recipients()
