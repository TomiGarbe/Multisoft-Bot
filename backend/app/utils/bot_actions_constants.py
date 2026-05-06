"""Centralized constants for Bot Actions contracts and validations."""

MAX_TIMEOUT_MS = 120000
MAX_RETRY_COUNT = 5
MAX_RESPONSE_SIZE = 5 * 1024 * 1024
MAX_BODY_SIZE = 1 * 1024 * 1024
MAX_TOOL_NAME_LENGTH = 150
MAX_VARIABLE_NAME_LENGTH = 64

TOOL_NAME_PATTERN = r"^[a-z][a-z0-9_]*$"
VARIABLE_NAME_PATTERN = r"^[a-z][a-z0-9_]*$"
PLACEHOLDER_PATTERN = r"\{\{([a-z][a-z0-9_]*)\}\}"
INVALID_PLACEHOLDER_PATTERN = r"\{\{([^{}]+)\}\}"

SENSITIVE_FIELD_NAMES = frozenset(
    {
        "authorization",
        "token",
        "api_key",
        "password",
        "secret",
    }
)

