from __future__ import annotations

import re
import unicodedata
from ipaddress import ip_address
from typing import Iterable
from urllib.parse import urlparse

from app.utils.bot_actions_security import BLOCKED_HOSTNAMES, BLOCKED_IP_NETWORKS
from app.utils.bot_actions_constants import (
    INVALID_PLACEHOLDER_PATTERN,
    MAX_TOOL_NAME_LENGTH,
    MAX_VARIABLE_NAME_LENGTH,
    PLACEHOLDER_PATTERN,
    TOOL_NAME_PATTERN,
    VARIABLE_NAME_PATTERN,
)

_TOOL_NAME_RE = re.compile(TOOL_NAME_PATTERN)
_VARIABLE_NAME_RE = re.compile(VARIABLE_NAME_PATTERN)
_PLACEHOLDER_RE = re.compile(PLACEHOLDER_PATTERN)
_INVALID_PLACEHOLDER_RE = re.compile(INVALID_PLACEHOLDER_PATTERN)

def normalize_tool_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower().strip()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized[:MAX_TOOL_NAME_LENGTH]


def validate_tool_name(value: str) -> str:
    if not value:
        raise ValueError("Tool name is required.")
    if len(value) > MAX_TOOL_NAME_LENGTH:
        raise ValueError(f"Tool name cannot exceed {MAX_TOOL_NAME_LENGTH} characters.")
    if not _TOOL_NAME_RE.fullmatch(value):
        raise ValueError("Tool name must be lowercase snake_case and ASCII-safe.")
    return value


def validate_variable_name(value: str) -> str:
    if not value:
        raise ValueError("Variable name is required.")
    if len(value) > MAX_VARIABLE_NAME_LENGTH:
        raise ValueError(f"Variable name cannot exceed {MAX_VARIABLE_NAME_LENGTH} characters.")
    if not _VARIABLE_NAME_RE.fullmatch(value):
        raise ValueError("Variable name must be lowercase snake_case and ASCII-safe.")
    return value


def detect_placeholders(value: str) -> bool:
    return bool(_PLACEHOLDER_RE.search(value))


def extract_placeholders(value: str) -> list[str]:
    return _PLACEHOLDER_RE.findall(value)


def find_duplicate_placeholders(value: str) -> list[str]:
    extracted = extract_placeholders(value)
    seen: set[str] = set()
    duplicates: list[str] = []
    for item in extracted:
        if item in seen and item not in duplicates:
            duplicates.append(item)
        seen.add(item)
    return duplicates


def find_invalid_placeholders(value: str) -> list[str]:
    invalid: list[str] = []
    for token in _INVALID_PLACEHOLDER_RE.findall(value):
        if not _VARIABLE_NAME_RE.fullmatch(token.strip()):
            invalid.append(f"{{{{{token}}}}}")
    return invalid


def validate_placeholders(value: str, allowed_variables: Iterable[str] | None = None) -> list[str]:
    invalid = find_invalid_placeholders(value)
    if invalid:
        raise ValueError(f"Invalid placeholders found: {', '.join(invalid)}")

    placeholders = extract_placeholders(value)
    if allowed_variables is not None:
        allowed = set(allowed_variables)
        unknown = sorted(set(placeholders) - allowed)
        if unknown:
            raise ValueError(f"Unknown placeholders found: {', '.join(unknown)}")
    return placeholders


def validate_external_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("URL must use http or https.")
    if not parsed.hostname:
        raise ValueError("URL must include a valid hostname.")

    hostname = parsed.hostname.lower()
    if hostname in BLOCKED_HOSTNAMES:
        raise ValueError("Local or private hostnames are not allowed.")

    try:
        host_ip = ip_address(hostname)
    except ValueError:
        return value

    for blocked_network in BLOCKED_IP_NETWORKS:
        if host_ip in blocked_network:
            raise ValueError("Private, loopback or link-local addresses are not allowed.")
    return value
