from __future__ import annotations

import base64
from typing import Any


def apply_auth_config(
    *,
    auth_config: dict[str, Any],
    headers: dict[str, str],
    query_params: dict[str, Any],
) -> tuple[dict[str, str], dict[str, Any]]:
    auth_type = str(auth_config.get("type", "none")).lower()
    updated_headers = dict(headers)
    updated_query = dict(query_params)

    if auth_type == "bearer":
        token = str(auth_config.get("token", ""))
        updated_headers["Authorization"] = f"Bearer {token}"
    elif auth_type == "api_key":
        key = str(auth_config.get("key", ""))
        value = auth_config.get("value")
        location = str(auth_config.get("location", "header")).lower()
        if location == "query":
            updated_query[key] = value
        else:
            updated_headers[key] = str(value)
    elif auth_type == "basic":
        username = str(auth_config.get("username", ""))
        password = str(auth_config.get("password", ""))
        encoded = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        updated_headers["Authorization"] = f"Basic {encoded}"
    elif auth_type == "custom":
        custom_headers = auth_config.get("headers") or {}
        for key, value in custom_headers.items():
            updated_headers[str(key)] = str(value)

    return updated_headers, updated_query

