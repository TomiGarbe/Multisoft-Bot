from __future__ import annotations

import json
import logging
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder

logger = logging.getLogger(__name__)


class JSONSerializationError(ValueError):
    """Raised when a payload cannot be safely converted to JSON."""


def sanitize_for_json(value: Any) -> Any:
    """
    Convert Python objects to JSON-compatible values recursively.

    Guarantees UUID/date/time/Decimal/Pydantic values are converted into
    primitives accepted by JSON/JSONB storage.
    """

    try:
        return jsonable_encoder(
            value,
            custom_encoder={
                UUID: str,
                datetime: lambda v: v.isoformat(),
                date: lambda v: v.isoformat(),
                time: lambda v: v.isoformat(),
                Decimal: lambda v: str(v),
            },
        )
    except Exception as exc:
        logger.exception("Failed to sanitize value for JSON serialization")
        raise JSONSerializationError("Failed to sanitize value for JSON serialization") from exc


def sqlalchemy_json_serializer(value: Any) -> str:
    """
    SQLAlchemy engine-level JSON serializer for JSON/JSONB columns.

    This is applied globally to every JSON bind parameter.
    """

    sanitized = sanitize_for_json(value)
    try:
        return json.dumps(sanitized, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        logger.exception("Failed to serialize sanitized JSON payload")
        raise JSONSerializationError("Failed to serialize sanitized JSON payload") from exc
