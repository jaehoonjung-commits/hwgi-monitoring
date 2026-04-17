"""FastAPI application entry point."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import config
from api import (
    execute_test_request,
    generate_if_global_no,
    get_grafana_filter_options,
    healthcheck,
    preview_kakao_requests,
    receive_grafana_webhook,
    receive_ums_request,
    view_recipients,
    view_test_page,
    view_test_script,
)

raw_log_level = config.LOG_LEVEL
log_level = getattr(logging, raw_log_level, logging.INFO)

logging.basicConfig(
    level=log_level,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title="Grafana Webhook Receiver",
    description="Receives Grafana alert webhooks and routes to notification channels",
    version="1.0.0",
    docs_url="/swagger",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOW_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def get_health():
    return await healthcheck()


@app.post("/webhook/grafana")
async def post_webhook(request: Request):
    return await receive_grafana_webhook(request)


@app.post("/hwgi/ums/UMSMUMS010010000")
async def post_ums_request(request: Request):
    return await receive_ums_request(request)


@app.get("/recipients")
async def get_recipients():
    return await view_recipients()


@app.get("/curl-test")
async def get_test():
    return await view_test_page()


@app.get("/curl-test.js")
async def get_test_script():
    return await view_test_script()


@app.get("/api/generate-if-global-no")
async def get_if_global_no():
    return await generate_if_global_no()


@app.post("/api/execute-curl-test")
async def post_execute_curl_test(request: Request):
    return await execute_test_request(request)


@app.post("/api/preview-kakao-requests")
async def post_preview_kakao_requests(request: Request):
    return await preview_kakao_requests(request)


@app.get("/api/grafana-filter-options")
async def get_api_grafana_filter_options():
    return await get_grafana_filter_options()
