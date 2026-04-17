"""
Configuration management for Grafana Webhook Receiver.
Environment variables are loaded on module import.
"""

import os

# Paths
RECIPIENT_CONFIG_PATH = os.getenv("RECIPIENT_CONFIG_PATH", "configs/recipients.yaml")
FILE_OUTPUT_PATH = os.getenv("FILE_OUTPUT_PATH", "logs/notification_results.log")

# UMS configuration for kakao channel
UMS_API_URL = os.getenv("UMS_API_URL", "http://ums-service.example.com:8080/api/ums")
UMS_CHNL_SYS_CD = os.getenv("UMS_CHNL_SYS_CD", "AAA")
UMS_IF_ORG_CD = os.getenv("UMS_IF_ORG_CD", "UMS")
UMS_APPL_CD = os.getenv("UMS_APPL_CD", "MUMS")
UMS_IF_KIND_CD = os.getenv("UMS_IF_KIND_CD", "0100")
UMS_IF_TX_CD = os.getenv("UMS_IF_TX_CD", "10000")
UMS_STFNO = os.getenv("UMS_STFNO", "")
UMS_ECARE_NO = int(os.getenv("UMS_ECARE_NO", "3402"))
UMS_CHANNEL = os.getenv("UMS_CHANNEL", "A")
UMS_TMPL_TYPE = os.getenv("UMS_TMPL_TYPE", "J")
UMS_SENDER_NAME = os.getenv("UMS_SENDER_NAME", "Grafana")
UMS_SENDER_PHONE = os.getenv("UMS_SENDER_PHONE", "1566-8000")
UMS_TIMEOUT_SEC = float(os.getenv("UMS_TIMEOUT_SEC", "5"))

# CORS configuration
CORS_ALLOW_ORIGINS = [
	origin.strip()
	for origin in os.getenv(
		"CORS_ALLOW_ORIGINS",
		"http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000",
	).split(",")
	if origin.strip()
]
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
