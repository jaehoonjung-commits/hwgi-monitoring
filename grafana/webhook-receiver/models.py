"""
Data models and type definitions.
"""

from typing import Any, TypeAlias

# Type aliases for clarity
RecipientData: TypeAlias = dict[str, Any]
AlertData: TypeAlias = dict[str, Any]
ConfigData: TypeAlias = dict[str, Any]
NotificationResult: TypeAlias = dict[str, str]
