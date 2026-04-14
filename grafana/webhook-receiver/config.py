"""
Configuration management for Grafana Webhook Receiver.
Environment variables are loaded on module import.
"""

import os

# Paths
RECIPIENT_CONFIG_PATH = os.getenv("RECIPIENT_CONFIG_PATH", "recipients.yaml")
FILE_OUTPUT_PATH = os.getenv("FILE_OUTPUT_PATH", "notification_results.log")

# Gmail configuration
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

# UMS configuration for kakao channel
UMS_API_URL = os.getenv("UMS_API_URL", "")
UMS_API_KEY = os.getenv("UMS_API_KEY", "")
UMS_CHNL_SYS_CD = os.getenv("UMS_CHNL_SYS_CD", "AAA")
UMS_IF_ORG_CD = os.getenv("UMS_IF_ORG_CD", "UMS")
UMS_APPL_CD = os.getenv("UMS_APPL_CD", "GRFN")
UMS_IF_KIND_CD = os.getenv("UMS_IF_KIND_CD", "0100")
UMS_IF_TX_CD = os.getenv("UMS_IF_TX_CD", "10000")
UMS_SFTNO = os.getenv("UMS_SFTNO", "")
UMS_ECARD_NO = int(os.getenv("UMS_ECARD_NO", "3402"))
UMS_CHANNEL = os.getenv("UMS_CHANNEL", "A")
UMS_TMPL_TYPE = os.getenv("UMS_TMPL_TYPE", "J")
UMS_SENDER_NAME = os.getenv("UMS_SENDER_NAME", "Grafana")
UMS_TIMEOUT_SEC = float(os.getenv("UMS_TIMEOUT_SEC", "5"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
