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
from fastapi.middleware.cors import CORSMiddleware

import config
from api import healthcheck, receive_grafana_webhook, receive_ums_request, view_recipients, view_test_page

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
    docs_url="/swagger",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware to allow fetch requests from the UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/curl-test")
async def get_test():
    """Webhook testing UI endpoint."""
    return await view_test_page()
