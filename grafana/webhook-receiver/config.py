"""
Configuration management for Grafana Webhook Receiver.
Environment variables are loaded on module import.
"""

import os

# Paths
RECIPIENT_CONFIG_PATH = os.getenv("RECIPIENT_CONFIG_PATH", "recipients.yaml")

# Gmail configuration
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

# SMS configuration (provider-agnostic HTTP API)
SMS_API_URL = os.getenv("SMS_API_URL", "")
SMS_API_KEY = os.getenv("SMS_API_KEY", "")
SMS_SENDER_NUMBER = os.getenv("SMS_SENDER_NUMBER", "")

# Kakao Alimtalk configuration
KAKAO_API_URL = os.getenv("KAKAO_API_URL", "")
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY", "")
KAKAO_SENDER_KEY = os.getenv("KAKAO_SENDER_KEY", "")
KAKAO_TEMPLATE_CODE = os.getenv("KAKAO_TEMPLATE_CODE", "")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
